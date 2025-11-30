/**
 * Configuración de base de datos SQL Server con connection pooling
 * Optimizado para velocidad y rendimiento
 */
const sql = require('mssql');
require('dotenv').config();

// Configuración de conexión SQL Server
const config = {
  server: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '1433'),
  database: process.env.DB_NAME || 'vehicles_db',
  user: process.env.DB_USER || 'sa',
  password: process.env.DB_PASSWORD || '',
  options: {
    encrypt: process.env.DB_ENCRYPT === 'true', // true para Azure, false para local
    trustServerCertificate: process.env.DB_TRUST_CERT === 'true' || true, // Para desarrollo local
    enableArithAbort: true,
    requestTimeout: 5000, // 5 segundos timeout
    connectionTimeout: 2000, // 2 segundos para conectar
    pool: {
      max: 20, // Máximo de conexiones en el pool
      min: 0,
      idleTimeoutMillis: 30000
    }
  }
};

// Pool global
let pool = null;

/**
 * Obtiene o crea el pool de conexiones
 */
async function getPool() {
  if (!pool) {
    try {
      pool = await sql.connect(config);
      console.log(`Conectado a SQL Server: ${config.database}`);
    } catch (err) {
      console.error('Error al conectar con SQL Server:', err.message);
      throw err;
    }
  }
  return pool;
}

// Caché simple en memoria para consultas frecuentes
const cache = new Map();
const CACHE_TTL = 60000; // 1 minuto

function getCacheKey(plate) {
  return `plate:${plate.toUpperCase().trim()}`;
}

function getCached(key) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  cache.delete(key);
  return null;
}

function setCache(key, data) {
  cache.set(key, {
    data,
    timestamp: Date.now()
  });
}

// Limpiar caché periódicamente
setInterval(() => {
  const now = Date.now();
  for (const [key, value] of cache.entries()) {
    if (now - value.timestamp >= CACHE_TTL) {
      cache.delete(key);
    }
  }
}, 30000); // Limpiar cada 30 segundos

/**
 * Ejecuta una query con retry automático
 */
async function query(text, params = []) {
  const start = Date.now();
  try {
    const pool = await getPool();
    
    // Convertir parámetros a formato SQL Server
    const request = pool.request();
    
    // Agregar parámetros si existen
    if (params && params.length > 0) {
      // SQL Server usa @p1, @p2, etc.
      params.forEach((param, index) => {
        const paramName = `p${index + 1}`;
        // Detectar tipo de dato para mejor rendimiento
        let sqlType = sql.VarChar;
        if (typeof param === 'number') {
          sqlType = Number.isInteger(param) ? sql.Int : sql.Float;
        } else if (param === null) {
          sqlType = sql.VarChar;
        } else if (param instanceof Date) {
          sqlType = sql.DateTime2;
        }
        request.input(paramName, sqlType, param);
      });
      
      // Reemplazar $1, $2, etc. con @p1, @p2, etc.
      let sqlText = text;
      params.forEach((param, index) => {
        const paramName = `p${index + 1}`;
        sqlText = sqlText.replace(new RegExp(`\\$${index + 1}`, 'g'), `@${paramName}`);
        // También reemplazar si ya viene con @p
        sqlText = sqlText.replace(new RegExp(`@p${index + 1}\\b`, 'g'), `@${paramName}`);
      });
      
      const result = await request.query(sqlText);
      const duration = Date.now() - start;
      if (duration > 1000) {
        console.warn(`Query lenta (${duration}ms):`, text.substring(0, 100));
      }
      return result;
    } else {
      const result = await request.query(text);
      const duration = Date.now() - start;
      if (duration > 1000) {
        console.warn(`Query lenta (${duration}ms):`, text.substring(0, 100));
      }
      return result;
    }
  } catch (error) {
    console.error('Error en query:', error.message);
    console.error('Query:', text.substring(0, 200));
    throw error;
  }
}

/**
 * Obtiene una conexión del pool
 */
async function getClient() {
  const pool = await getPool();
  return pool.request();
}

/**
 * Cierra todas las conexiones del pool
 */
async function close() {
  if (pool) {
    try {
      await pool.close();
      pool = null;
      console.log('Conexión a SQL Server cerrada');
    } catch (err) {
      console.error('Error al cerrar pool:', err.message);
    }
  }
}

module.exports = {
  sql,
  getPool,
  query,
  getClient,
  close,
  getCacheKey,
  getCached,
  setCache,
  config
};
