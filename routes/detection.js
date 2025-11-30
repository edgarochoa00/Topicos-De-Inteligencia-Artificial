/**
 * Rutas para detección de matrículas
 */
const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const { promisify } = require('util');
const { getLinkingSystem } = require('../utils/linking');
const { getPythonCommand } = require('../utils/pythonHelper');

const execAsync = promisify(exec);

// Configurar multer para subida de archivos
const uploadDir = process.env.UPLOAD_DIR || './uploads';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, 'plate-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|bmp|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Solo se permiten archivos de imagen (jpeg, jpg, png, gif, bmp, webp)'));
    }
  }
});

/**
 * POST /api/detect
 * Detecta matrícula en una imagen subida
 */
router.post('/detect', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No se proporcionó ninguna imagen'
      });
    }

    const imagePath = req.file.path;
    const linkingSystem = getLinkingSystem();

    console.log(`Procesando imagen: ${imagePath}`);

    // Usar sistema mejorado con diagnóstico si se solicita
    const useDiagnosis = req.query.diagnosis === 'true' || req.body.diagnosis === true;
    const pythonScript = useDiagnosis 
      ? path.join(__dirname, '../ml/detect_enhanced.py')
      : path.join(__dirname, '../ml/detect.py');
    
    let plateNumber = null;
    let diagnosis = null;

    if (useDiagnosis) {
      // Usar sistema con diagnóstico
      const pythonCmd = getPythonCommand();
      const env = process.platform === 'win32' 
        ? { ...process.env, PYTHONIOENCODING: 'utf-8' }
        : process.env;
      const { stdout, stderr } = await execAsync(
        `"${pythonCmd}" "${pythonScript}" "${imagePath}"`,
        { 
          env,
          maxBuffer: 10 * 1024 * 1024
        }
      );

      if (stderr && !stderr.includes('Using CPU') && !stderr.includes('Advertencia')) {
        console.error('Advertencia del detector:', stderr);
      }

      // Parsear resultado JSON del diagnóstico
      try {
        const lines = stdout.split('\n');
        const jsonLine = lines.find(line => line.startsWith('{') || line.startsWith('{"'));
        if (jsonLine) {
          const result = JSON.parse(jsonLine);
          plateNumber = result.plate_number;
          diagnosis = result.diagnosis;
        } else {
          const match = stdout.match(/Matrícula detectada: (.+)/);
          if (match) {
            plateNumber = match[1].trim();
          }
        }
      } catch (e) {
        const match = stdout.match(/Matrícula detectada: (.+)/);
        if (match) {
          plateNumber = match[1].trim();
        }
      }
    } else {
      // Usar sistema normal
      const pythonCmd = getPythonCommand();
      const env = process.platform === 'win32' 
        ? { ...process.env, PYTHONIOENCODING: 'utf-8' }
        : process.env;
      const { stdout, stderr } = await execAsync(
        `"${pythonCmd}" "${pythonScript}" "${imagePath}"`,
        { 
          env,
          maxBuffer: 10 * 1024 * 1024
        }
      );

      if (stderr && !stderr.includes('Using CPU')) {
        console.error('Advertencia del detector:', stderr);
      }

      if (stdout) {
        const match = stdout.match(/Matrícula detectada: (.+)/);
        if (match) {
          plateNumber = match[1].trim();
        }
      }
    }

    if (!plateNumber) {
      if (!useDiagnosis) {
        fs.unlinkSync(imagePath);
      }
      
      return res.status(200).json({
        success: false,
        message: 'No se pudo detectar ninguna matrícula en la imagen',
        plate_number: null,
        vehicle: null,
        diagnosis: diagnosis || {
          message: 'Usa ?diagnosis=true para obtener información detallada sobre por qué falló la detección'
        }
      });
    }

    console.log(`Matrícula detectada: ${plateNumber}`);

    // Búsqueda automática en la base de datos
    let vehicle = null;
    let errorMessage = null;

    try {
      vehicle = await linkingSystem.findVehicleByPlate(plateNumber);
      
      await linkingSystem.recordDetection(plateNumber, {
        image_path: imagePath,
        confidence_score: null,
        location: req.body.location || null
      });

      if (!vehicle) {
        errorMessage = `Matrícula "${plateNumber}" detectada pero no encontrada en la base de datos`;
        console.log(`Matrícula ${plateNumber} no registrada - disponible para registro`);
      } else {
        console.log(`Vehículo encontrado: ${vehicle.owner_name} (${vehicle.plate_number})`);
      }
    } catch (error) {
      console.error('Error al consultar base de datos:', error.message);
      errorMessage = `Error al consultar base de datos: ${error.message}`;
    }

    // Respuesta exitosa
    res.json({
      success: true,
      plate_number: plateNumber,
      vehicle: vehicle,
      message: vehicle 
        ? `Vehículo encontrado para matrícula: ${plateNumber}`
        : errorMessage || `Matrícula detectada: ${plateNumber}`,
      image_path: imagePath,
      detection_timestamp: new Date().toISOString(),
      diagnosis: diagnosis || undefined
    });

  } catch (error) {
    console.error('Error en detección:', error.message);
    
    if (req.file && fs.existsSync(req.file.path)) {
      try {
        fs.unlinkSync(req.file.path);
      } catch (unlinkError) {
        console.error('Error al limpiar archivo:', unlinkError.message);
      }
    }

    res.status(500).json({
      success: false,
      error: 'Error al procesar la imagen',
      message: error.message
    });
  }
});

/**
 * POST /api/detect/base64
 * Detecta matrícula desde imagen en base64
 */
router.post('/detect/base64', async (req, res) => {
  try {
    const { image, location } = req.body;

    // Guardar imagen temporalmente
    const imageBuffer = Buffer.from(image, 'base64');
    const tempPath = path.join(uploadDir, `temp-${Date.now()}.jpg`);
    fs.writeFileSync(tempPath, imageBuffer);

    const linkingSystem = getLinkingSystem();

    // Ejecutar detección
    const pythonScript = path.join(__dirname, '../ml/detect.py');
    const pythonCmd = getPythonCommand();
    const env = process.platform === 'win32' 
      ? { ...process.env, PYTHONIOENCODING: 'utf-8' }
      : process.env;
    const { stdout } = await execAsync(
      `"${pythonCmd}" "${pythonScript}" "${tempPath}"`,
      { env }
    );

    let plateNumber = null;
    if (stdout) {
      const match = stdout.match(/Matrícula detectada: (.+)/);
      if (match) {
        plateNumber = match[1].trim();
      }
    }

    // Limpiar archivo temporal
    fs.unlinkSync(tempPath);

    if (!plateNumber) {
      return res.status(200).json({
        success: false,
        message: 'No se pudo detectar ninguna matrícula',
        plate_number: null,
        vehicle: null
      });
    }

    // Buscar vehículo
    let vehicle = null;
    try {
      vehicle = await linkingSystem.findVehicleByPlate(plateNumber);
      await linkingSystem.recordDetection(plateNumber, {
        image_path: null,
        location: location || null
      });
    } catch (error) {
      console.error('Error al consultar base de datos:', error.message);
    }

    res.json({
      success: true,
      plate_number: plateNumber,
      vehicle: vehicle,
      message: vehicle 
        ? `Vehículo encontrado para matrícula: ${plateNumber}`
        : `Matrícula detectada: ${plateNumber} (no encontrada en base de datos)`
    });

  } catch (error) {
    console.error('Error en detección base64:', error.message);
    res.status(500).json({
      success: false,
      error: 'Error al procesar la imagen',
      message: error.message
    });
  }
});

/**
 * POST /api/detect/diagnosis
 * Detecta matrícula con diagnóstico detallado
 */
// Ruta para detectar múltiples matrículas
router.post('/detect/multiple', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No se proporcionó ninguna imagen'
      });
    }

    const imagePath = req.file.path;
    console.log(`Detectando múltiples matrículas en: ${imagePath}`);

    // Ejecutar script Python para detección múltiple
    const pythonScript = path.join(__dirname, '../ml/multi_plate_detector.py');
    const pythonCmd = getPythonCommand();
    const env = process.platform === 'win32' 
      ? { ...process.env, PYTHONIOENCODING: 'utf-8' }
      : process.env;
    
    const { stdout, stderr } = await execAsync(
      `"${pythonCmd}" "${pythonScript}" "${imagePath}"`,
      { 
        env,
        maxBuffer: 10 * 1024 * 1024  // 10MB buffer
      }
    );

    if (stderr && !stderr.includes('Warning')) {
      console.warn('Advertencia en detección múltiple:', stderr);
    }

    // Parsear resultado JSON
    // Filtrar líneas que no son JSON (errores que se imprimieron antes del JSON)
    let jsonOutput = stdout;
    const jsonMatch = stdout.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonOutput = jsonMatch[0];
    }
    
    let result;
    try {
      result = JSON.parse(jsonOutput);
    } catch (e) {
      console.error('Error parseando JSON:', e.message);
      result = {
        success: false,
        plates: [],
        error: 'Error al procesar resultado',
        raw_output: stdout.substring(0, 500)
      };
    }

    // Buscar vehículos en BD para cada matrícula detectada
    const linkingSystem = getLinkingSystem();
    const plates_with_vehicles = [];

    for (const plate_info of result.plates || []) {
      try {
        const vehicle = await linkingSystem.findVehicleByPlate(plate_info.plate_number);
        plates_with_vehicles.push({
          ...plate_info,
          vehicle: vehicle
        });
      } catch (error) {
        plates_with_vehicles.push({
          ...plate_info,
          vehicle: null
        });
      }
    }

    res.json({
      success: result.success,
      plates: plates_with_vehicles,
      total_found: result.total_found || plates_with_vehicles.length,
      detection_timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error en detección múltiple:', error.message);
    
    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }

    res.status(500).json({
      success: false,
      error: 'Error al procesar la imagen',
      message: error.message
    });
  }
});

router.post('/detect/diagnosis', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No se proporcionó ninguna imagen'
      });
    }

    const imagePath = req.file.path;
    const pythonScript = path.join(__dirname, '../ml/detect_enhanced.py');

    console.log(`Procesando imagen con diagnóstico: ${imagePath}`);

    // Ejecutar script de detección con diagnóstico (formato JSON)
    const pythonCmd = getPythonCommand();
    const env = process.platform === 'win32' 
      ? { ...process.env, PYTHONIOENCODING: 'utf-8' }
      : process.env;
    const { stdout, stderr } = await execAsync(
      `"${pythonCmd}" "${pythonScript}" "${imagePath}" --json`,
      { 
        env,
        maxBuffer: 10 * 1024 * 1024
      }
    );

    // Parsear resultado JSON
    let result = {
      success: false,
      plate_number: null,
      diagnosis: null
    };

    try {
      const jsonMatch = stdout.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        result = JSON.parse(jsonMatch[0]);
      } else {
        if (stdout.includes('Matrícula detectada:')) {
          const match = stdout.match(/Matrícula detectada: (.+)/);
          if (match) {
            result.success = true;
            result.plate_number = match[1].trim();
          }
        }
      }
    } catch (e) {
      console.error('Error parsing diagnosis:', e);
      console.error('Output:', stdout.substring(0, 500));
    }

    // Búsqueda automática en BD si se detectó matrícula
    let vehicle = null;
    if (result.success && result.plate_number) {
      const linkingSystem = getLinkingSystem();
      try {
        vehicle = await linkingSystem.findVehicleByPlate(result.plate_number);
        
        await linkingSystem.recordDetection(result.plate_number, {
          image_path: imagePath,
          location: req.body.location || null
        });
        
        if (vehicle) {
          console.log(`Vehículo encontrado automáticamente: ${vehicle.owner_name}`);
        } else {
          console.log(`Matrícula ${result.plate_number} no registrada - disponible para registro`);
        }
      } catch (error) {
        console.error('Error al consultar base de datos:', error.message);
      }
    }

    res.json({
      success: result.success,
      plate_number: result.plate_number,
      vehicle: vehicle,
      diagnosis: result.diagnosis || {
        message: 'No se pudo obtener diagnóstico detallado',
        raw_output: stdout.substring(0, 500)
      },
      detection_timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error en detección con diagnóstico:', error.message);
    
    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }

    res.status(500).json({
      success: false,
      error: 'Error al procesar la imagen',
      message: error.message
    });
  }
});

module.exports = router;

