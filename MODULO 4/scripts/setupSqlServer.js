/**
 * Script para configurar base de datos SQL Server
 * Ejecuta el esquema y crea las tablas optimizadas
 */
const sql = require('mssql');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const config = {
  server: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '1433'),
  database: 'master', // Conectar a master primero para crear la BD
  user: process.env.DB_USER || 'sa',
  password: process.env.DB_PASSWORD || '',
  options: {
    encrypt: process.env.DB_ENCRYPT === 'true',
    trustServerCertificate: true,
    enableArithAbort: true
  }
};

async function setupDatabase() {
  let pool;
  
  try {
    console.log('🔧 Configurando base de datos SQL Server...\n');
    
    // Conectar a master
    pool = await sql.connect(config);
    console.log('✅ Conectado a SQL Server');
    
    const dbName = process.env.DB_NAME || 'vehicles_db';
    
    // Crear base de datos si no existe
    try {
      await pool.request().query(`
        IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '${dbName}')
        BEGIN
          CREATE DATABASE [${dbName}];
        END
      `);
      console.log(`✅ Base de datos "${dbName}" creada o ya existe`);
    } catch (err) {
      if (err.code !== 'EREQUEST') {
        throw err;
      }
    }
    
    // Cerrar conexión a master
    await pool.close();
    
    // Nueva conexión a la base de datos creada
    const dbConfig = {
      ...config,
      database: dbName
    };
    
    pool = await sql.connect(dbConfig);
    
    // Leer y ejecutar esquema
    const schemaPath = path.join(__dirname, '../database/schema_sqlserver.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    
    // Dividir por GO statements
    const statements = schema.split(/^\s*GO\s*$/gim).filter(s => s.trim());
    
    for (const statement of statements) {
      if (statement.trim()) {
        try {
          await pool.request().query(statement);
        } catch (err) {
          // Ignorar errores de "ya existe" para objetos
          if (!err.message.includes('already exists') && 
              !err.message.includes('already an object') &&
              !err.message.includes('There is already')) {
            console.warn('⚠️  Advertencia al ejecutar statement:', err.message.substring(0, 100));
          }
        }
      }
    }
    
    console.log('✅ Esquema ejecutado correctamente');
    
    // Insertar datos de ejemplo
    await insertSampleData(pool);
    
    console.log('\n✅ Base de datos SQL Server configurada exitosamente');
    console.log(`📊 Base de datos: ${dbName}`);
    console.log(`🔗 Servidor: ${config.server}:${config.port}`);
    
  } catch (error) {
    console.error('❌ Error al configurar base de datos:', error.message);
    console.error('💡 Asegúrate de que:');
    console.error('   1. SQL Server esté corriendo');
    console.error('   2. Las credenciales en .env sean correctas');
    console.error('   3. El usuario tenga permisos para crear bases de datos');
    process.exit(1);
  } finally {
    if (pool) {
      await pool.close();
    }
  }
}

async function insertSampleData(pool) {
  try {
    // Verificar si ya hay datos
    const checkResult = await pool.request().query('SELECT COUNT(*) as count FROM vehicles');
    if (parseInt(checkResult.recordset[0].count) > 0) {
      console.log('ℹ️  Ya hay datos en la base de datos, omitiendo datos de ejemplo');
      return;
    }
    
    // Insertar datos de ejemplo
    const sampleVehicles = [
      ['ABC123', 'Juan Pérez', '12345678', 'Toyota', 'Corolla', 2020, 'Blanco'],
      ['XYZ789', 'María González', '87654321', 'Honda', 'Civic', 2019, 'Negro'],
      ['DEF456', 'Carlos Rodríguez', '11223344', 'Ford', 'Focus', 2021, 'Rojo']
    ];
    
    for (const vehicle of sampleVehicles) {
      await pool.request()
        .input('plate', sql.VarChar, vehicle[0])
        .input('owner', sql.NVarChar, vehicle[1])
        .input('ownerId', sql.VarChar, vehicle[2])
        .input('make', sql.VarChar, vehicle[3])
        .input('model', sql.VarChar, vehicle[4])
        .input('year', sql.Int, vehicle[5])
        .input('color', sql.VarChar, vehicle[6])
        .query(`
          IF NOT EXISTS (SELECT 1 FROM vehicles WHERE plate_number = @plate)
          BEGIN
            INSERT INTO vehicles 
            (plate_number, owner_name, owner_id, vehicle_make, vehicle_model, vehicle_year, vehicle_color)
            VALUES (@plate, @owner, @ownerId, @make, @model, @year, @color)
          END
        `);
    }
    
    console.log('✅ Datos de ejemplo insertados');
  } catch (error) {
    console.error('⚠️  Error al insertar datos de ejemplo:', error.message);
  }
}

setupDatabase();



