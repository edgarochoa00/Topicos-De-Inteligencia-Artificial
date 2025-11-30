/**
 * Sistema de vinculación de matrículas con propietarios
 * Optimizado para SQL Server con connection pooling y caché
 */
const { query, getCacheKey, getCached, setCache } = require('./database');

class VehicleLinkingSystem {
  constructor() {
    // Verificar conexión al inicializar
    this.testConnection();
  }

  async testConnection() {
    try {
      await query('SELECT 1 as test');
      console.log('Conectado a SQL Server');
    } catch (err) {
      console.error('Error al conectar con SQL Server:', err.message);
      throw err;
    }
  }

  /**
   * Normaliza el número de matrícula para búsqueda
   */
  normalizePlateNumber(plateNumber) {
    if (!plateNumber) return null;
    return plateNumber.toUpperCase().trim().replace(/[^A-Z0-9-]/g, '');
  }

  /**
   * Busca un vehículo por número de matrícula (OPTIMIZADO)
   * Usa caché y consultas optimizadas con índices
   */
  async findVehicleByPlate(plateNumber) {
    try {
      if (!plateNumber) {
        return null;
      }

      const normalizedPlate = this.normalizePlateNumber(plateNumber);
      if (!normalizedPlate) {
        return null;
      }

      // Verificar caché primero
      const cacheKey = getCacheKey(normalizedPlate);
      const cached = getCached(cacheKey);
      if (cached !== null) {
        return cached;
      }

      // Consulta optimizada usando índice
      // Primero búsqueda exacta (más rápida)
      let result = await query(
        `SELECT TOP 1 id, plate_number, owner_name, owner_id, vehicle_make, 
                vehicle_model, vehicle_year, vehicle_color, registration_date,
                created_at, updated_at
         FROM vehicles 
         WHERE plate_number = @p1`,
        [normalizedPlate]
      );

      if (result.recordset && result.recordset.length > 0) {
        const vehicle = result.recordset[0];
        setCache(cacheKey, vehicle);
        return vehicle;
      }

      // Búsqueda normalizada (sin guiones) usando columna computada
      const flexiblePlate = normalizedPlate.replace(/[- ]/g, '');
      result = await query(
        `SELECT TOP 1 id, plate_number, owner_name, owner_id, vehicle_make,
                vehicle_model, vehicle_year, vehicle_color, registration_date,
                created_at, updated_at
         FROM vehicles 
         WHERE plate_normalized = @p1`,
        [flexiblePlate.toUpperCase()]
      );

      if (result.recordset && result.recordset.length > 0) {
        const vehicle = result.recordset[0];
        setCache(cacheKey, vehicle);
        return vehicle;
      }

      // No encontrado, cachear null para evitar búsquedas repetidas
      setCache(cacheKey, null);
      return null;

    } catch (err) {
      console.error('Error en consulta de base de datos:', err.message);
      throw new Error(`Error al consultar base de datos: ${err.message}`);
    }
  }

  /**
   * Registra una detección de matrícula (OPTIMIZADO)
   */
  async recordDetection(plateNumber, options = {}) {
    try {
      const normalizedPlate = this.normalizePlateNumber(plateNumber);
      if (!normalizedPlate) {
        throw new Error('Número de matrícula inválido');
      }

      // Buscar vehículo (usa caché si está disponible)
      const vehicle = await this.findVehicleByPlate(normalizedPlate);
      const vehicleId = vehicle ? vehicle.id : null;

      // Insertar detección (optimizado para velocidad con OUTPUT)
      const result = await query(
        `INSERT INTO detections 
         (plate_number, vehicle_id, image_path, confidence_score, location)
         OUTPUT INSERTED.id
         VALUES (@p1, @p2, @p3, @p4, @p5)`,
        [
          normalizedPlate,
          vehicleId,
          options.image_path || null,
          options.confidence_score || null,
          options.location || null
        ]
      );

      return {
        detection_id: result.recordset?.[0]?.id || null,
        plate_number: normalizedPlate,
        vehicle_found: vehicle !== null,
        vehicle: vehicle
      };
    } catch (err) {
      console.error('Error al registrar detección:', err.message);
      throw new Error(`Error al registrar detección: ${err.message}`);
    }
  }

  /**
   * Obtiene el historial de detecciones (OPTIMIZADO con índice)
   */
  async getDetectionHistory(plateNumber, limit = 10) {
    try {
      const normalizedPlate = this.normalizePlateNumber(plateNumber);

      const result = await query(
        `SELECT TOP (@p2) * FROM detections
         WHERE plate_number = @p1
         ORDER BY detection_timestamp DESC`,
        [normalizedPlate, limit]
      );

      return result.recordset || [];
    } catch (err) {
      throw new Error(`Error al obtener historial: ${err.message}`);
    }
  }

  /**
   * Obtiene la instancia de la base de datos (para compatibilidad)
   */
  get db() {
    return {
      prepare: (sql) => ({
        run: async (...params) => {
          const result = await query(sql, params);
          return { lastInsertRowid: result.recordset?.[0]?.id || null };
        },
        get: async (...params) => {
          const result = await query(sql, params);
          return result.recordset?.[0] || null;
        },
        all: async (...params) => {
          const result = await query(sql, params);
          return result.recordset || [];
        }
      })
    };
  }
}

// Instancia singleton
let linkingSystemInstance = null;

function getLinkingSystem() {
  if (!linkingSystemInstance) {
    linkingSystemInstance = new VehicleLinkingSystem();
  }
  return linkingSystemInstance;
}

module.exports = {
  VehicleLinkingSystem,
  getLinkingSystem
};
