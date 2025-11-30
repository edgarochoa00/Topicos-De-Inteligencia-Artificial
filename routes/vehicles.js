/**
 * Rutas para gestión de vehículos
 */
const express = require('express');
const router = express.Router();
const { getLinkingSystem } = require('../utils/linking');

/**
 * GET /api/vehicle/:plate
 * Consulta información de un vehículo por matrícula
 */
router.get('/vehicle/:plate', async (req, res) => {
  try {
    const { plate } = req.params;
    const linkingSystem = getLinkingSystem();

    console.log(`Consultando vehículo con matrícula: ${plate}`);

    const vehicle = await linkingSystem.findVehicleByPlate(plate);

    if (!vehicle) {
      return res.status(404).json({
        success: false,
        error: `No se encontró ningún vehículo con la matrícula: ${plate}`,
        message: `La matrícula "${plate}" no está registrada en la base de datos`,
        plate_number: plate,
        vehicle: null
      });
    }

    // Obtener historial de detecciones
    const detectionHistory = await linkingSystem.getDetectionHistory(plate, 5);

    res.json({
      success: true,
      plate_number: plate,
      vehicle: vehicle,
      detection_history: detectionHistory,
      message: `Vehículo encontrado para matrícula: ${plate}`
    });

  } catch (error) {
    console.error('Error al consultar vehículo:', error.message);
    res.status(500).json({
      success: false,
      error: 'Error al consultar la base de datos',
      message: error.message
    });
  }
});

/**
 * POST /api/vehicle
 * Registra un nuevo vehículo
 */
router.post('/vehicle', async (req, res) => {
  try {
    const {
      plate_number,
      owner_name,
      owner_id,
      vehicle_make,
      vehicle_model,
      vehicle_year,
      vehicle_color,
      registration_date
    } = req.body;

    const linkingSystem = getLinkingSystem();

    // Normalizar matrícula
    const normalizedPlate = linkingSystem.normalizePlateNumber(plate_number);
    console.log('Intentando registrar vehículo:', {
      plate_original: plate_number,
      plate_normalized: normalizedPlate,
      owner: owner_name
    });

    // Verificar si ya existe
    const existing = await linkingSystem.findVehicleByPlate(plate_number);
    if (existing) {
      console.warn(`Vehículo ya existe: ${existing.plate_number} (ID: ${existing.id})`);
      return res.status(409).json({
        success: false,
        error: `Ya existe un vehículo con la matrícula: ${plate_number}`,
        vehicle: existing
      });
    }

    // OPTIMIZACIÓN: Insertar con OUTPUT (más rápido, una sola query)
    const { query } = require('../utils/database');
    
    try {
      const insertParams = [
        normalizedPlate,
        owner_name,
        owner_id || null,
        vehicle_make || null,
        vehicle_model || null,
        vehicle_year || null,
        vehicle_color || null,
        registration_date || null
      ];
      
      const result = await query(
        `INSERT INTO vehicles 
         (plate_number, owner_name, owner_id, vehicle_make, vehicle_model, vehicle_year, vehicle_color, registration_date)
         OUTPUT INSERTED.*
         VALUES (@p1, @p2, @p3, @p4, @p5, @p6, @p7, @p8)`,
        insertParams
      );

      const vehicle = result.recordset[0];
      
      if (vehicle) {
        console.log('Vehículo registrado exitosamente:', {
          id: vehicle.id,
          plate: vehicle.plate_number,
          plate_normalized: vehicle.plate_normalized,
          owner: vehicle.owner_name
        });
      } else {
        console.error('Error: No se recibió vehículo insertado en la respuesta');
      }

      res.status(201).json({
        success: true,
        message: `Vehículo registrado exitosamente con matrícula: ${plate_number}`,
        vehicle: vehicle
      });
    } catch (err) {
      console.error('Error al registrar vehículo:', err.message);
      res.status(500).json({
        success: false,
        error: 'Error al registrar vehículo en la base de datos',
        message: err.message
      });
    }

  } catch (error) {
    console.error('Error al registrar vehículo:', error.message);
    res.status(500).json({
      success: false,
      error: 'Error al procesar la solicitud',
      message: error.message
    });
  }
});

/**
 * PUT /api/vehicle/:plate
 * Actualiza información de un vehículo
 */
router.put('/vehicle/:plate', async (req, res) => {
  try {
    const { plate } = req.params;
    const linkingSystem = getLinkingSystem();

    // Verificar que existe
    const existing = await linkingSystem.findVehicleByPlate(plate);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: `No se encontró ningún vehículo con la matrícula: ${plate}`
      });
    }

    const {
      owner_name,
      owner_id,
      vehicle_make,
      vehicle_model,
      vehicle_year,
      vehicle_color,
      registration_date
    } = req.body;

    // Construir query de actualización dinámicamente (PostgreSQL)
    const updates = [];
    const values = [];
    let paramIndex = 1;

    if (owner_name) { 
      updates.push(`owner_name = $${paramIndex}`); 
      values.push(owner_name); 
      paramIndex++;
    }
    if (owner_id !== undefined) { 
      updates.push(`owner_id = $${paramIndex}`); 
      values.push(owner_id); 
      paramIndex++;
    }
    if (vehicle_make) { 
      updates.push(`vehicle_make = $${paramIndex}`); 
      values.push(vehicle_make); 
      paramIndex++;
    }
    if (vehicle_model) { 
      updates.push(`vehicle_model = $${paramIndex}`); 
      values.push(vehicle_model); 
      paramIndex++;
    }
    if (vehicle_year) { 
      updates.push(`vehicle_year = $${paramIndex}`); 
      values.push(vehicle_year); 
      paramIndex++;
    }
    if (vehicle_color) { 
      updates.push(`vehicle_color = $${paramIndex}`); 
      values.push(vehicle_color); 
      paramIndex++;
    }
    if (registration_date) { 
      updates.push(`registration_date = $${paramIndex}`); 
      values.push(registration_date); 
      paramIndex++;
    }

    if (updates.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No se proporcionaron campos para actualizar'
      });
    }

    updates.push('updated_at = CURRENT_TIMESTAMP');
    values.push(linkingSystem.normalizePlateNumber(plate));

    try {
      const { query } = require('../utils/database');
      
      // OPTIMIZACIÓN: UPDATE con OUTPUT (SQL Server)
      const updateQuery = `
        UPDATE vehicles 
        SET ${updates.join(', ')}
        OUTPUT INSERTED.*
        WHERE plate_number = @p${paramIndex}
      `;
      
      const result = await query(updateQuery, values);
      
      res.json({
        success: true,
        message: `Vehículo actualizado exitosamente`,
        vehicle: result.recordset[0]
      });
    } catch (err) {
      console.error('Error al actualizar vehículo:', err.message);
      res.status(500).json({
        success: false,
        error: 'Error al actualizar vehículo',
        message: err.message
      });
    }

  } catch (error) {
    console.error('Error al actualizar vehículo:', error.message);
    res.status(500).json({
      success: false,
      error: 'Error al procesar la solicitud',
      message: error.message
    });
  }
});

/**
 * GET /api/vehicles
 * Lista todos los vehículos (con paginación)
 */
router.get('/vehicles', async (req, res) => {
  try {
    const { page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;

    try {
      const { query } = require('../utils/database');
      
      // OPTIMIZACIÓN: Query optimizada con TOP y OFFSET (SQL Server)
      const vehiclesResult = await query(
        `SELECT * FROM vehicles
         ORDER BY created_at DESC
         OFFSET @p1 ROWS
         FETCH NEXT @p2 ROWS ONLY`,
        [parseInt(offset), parseInt(limit)]
      );

      const countResult = await query('SELECT COUNT(*) as total FROM vehicles');

      res.json({
        success: true,
        vehicles: vehiclesResult.recordset || [],
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: parseInt(countResult.recordset[0].total),
          total_pages: Math.ceil(parseInt(countResult.recordset[0].total) / limit)
        }
      });
    } catch (err) {
      console.error('Error al listar vehículos:', err.message);
      res.status(500).json({
        success: false,
        error: 'Error al consultar vehículos',
        message: err.message
      });
    }

  } catch (error) {
    console.error('Error al listar vehículos:', error.message);
    res.status(500).json({
      success: false,
      error: 'Error al procesar la solicitud',
      message: error.message
    });
  }
});

module.exports = router;

