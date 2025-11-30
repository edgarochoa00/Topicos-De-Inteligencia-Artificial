/**
 * Servidor principal de la aplicación
 * Sistema de reconocimiento de matrículas con vinculación a propietarios
 */
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const multer = require('multer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Servir archivos estáticos (interfaz web)
app.use(express.static('public'));

// Crear directorios necesarios
const dirs = ['./uploads', './models', './database'];
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Rutas
const detectionRoutes = require('./routes/detection');
const vehicleRoutes = require('./routes/vehicles');

app.use('/api', detectionRoutes);
app.use('/api', vehicleRoutes);

// Ruta de salud
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Sistema de reconocimiento de matrículas funcionando',
    timestamp: new Date().toISOString()
  });
});

// Ruta raíz - redirigir a la interfaz web
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Manejo de errores
app.use((err, req, res, next) => {
  console.error('Error no manejado:', err.message);
  
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'El archivo es demasiado grande. Tamaño máximo: 10MB'
      });
    }
  }

  res.status(err.status || 500).json({
    success: false,
    error: err.message || 'Error interno del servidor'
  });
});

// MEJORA: Obtener IP local para mostrar en consola
const os = require('os');
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      // Ignorar direcciones internas y no IPv4
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

const LOCAL_IP = getLocalIP();

// Iniciar servidor - escuchar en todas las interfaces (0.0.0.0) para permitir acceso desde otros dispositivos
app.listen(PORT, '0.0.0.0', () => {
  console.log('Servidor iniciado');
  console.log(`Escuchando en puerto ${PORT}`);
  console.log(`Acceso local: http://localhost:${PORT}`);
  console.log(`Acceso desde red: http://${LOCAL_IP}:${PORT}`);
  console.log(`Health check: http://${LOCAL_IP}:${PORT}/health`);
  console.log('\nPara acceder desde otro dispositivo:');
  console.log(`   1. Asegúrate de estar en la misma red WiFi`);
  console.log(`   2. Abre el navegador y ve a: http://${LOCAL_IP}:${PORT}`);
  console.log(`   3. O desde móvil: http://${LOCAL_IP}:${PORT}`);
  console.log('\nEndpoints disponibles:');
  console.log('  POST /api/detect - Detectar matrícula en imagen');
  console.log('  POST /api/detect/base64 - Detectar desde base64');
  console.log('  GET  /api/vehicle/:plate - Consultar vehículo');
  console.log('  POST /api/vehicle - Registrar vehículo');
  console.log('  PUT  /api/vehicle/:plate - Actualizar vehículo');
  console.log('  GET  /api/vehicles - Listar vehículos\n');
});

module.exports = app;
