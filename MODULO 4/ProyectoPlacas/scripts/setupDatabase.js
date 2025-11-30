/**
 * Script para configurar la base de datos inicial
 */
const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = process.env.DB_PATH || './database/vehicles.db';
const SCHEMA_PATH = path.join(__dirname, '../database/schema.sql');

function setupDatabase() {
  console.log('Configurando base de datos...');
  
  // Crear directorio de base de datos si no existe
  const dbDir = path.dirname(DB_PATH);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
    console.log(`Directorio creado: ${dbDir}`);
  }
  
  // Leer esquema SQL
  const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
  
  try {
    // Crear conexión a la base de datos
    const db = new Database(DB_PATH);
    console.log(`Conectado a la base de datos: ${DB_PATH}`);
    
    // Ejecutar esquema
    db.exec(schema);
    console.log('Esquema de base de datos creado exitosamente');
    
    // Insertar datos de ejemplo (opcional)
    insertSampleData(db);
    
    db.close();
  } catch (err) {
    console.error('Error al configurar base de datos:', err.message);
    process.exit(1);
  }
}

function insertSampleData(db) {
  const sampleVehicles = [
    {
      plate_number: 'ABC123',
      owner_name: 'Juan Pérez',
      owner_id: '12345678',
      vehicle_make: 'Toyota',
      vehicle_model: 'Corolla',
      vehicle_year: 2020,
      vehicle_color: 'Blanco'
    },
    {
      plate_number: 'XYZ789',
      owner_name: 'María González',
      owner_id: '87654321',
      vehicle_make: 'Honda',
      vehicle_model: 'Civic',
      vehicle_year: 2019,
      vehicle_color: 'Negro'
    },
    {
      plate_number: 'DEF456',
      owner_name: 'Carlos Rodríguez',
      owner_id: '11223344',
      vehicle_make: 'Ford',
      vehicle_model: 'Focus',
      vehicle_year: 2021,
      vehicle_color: 'Rojo'
    }
  ];
  
  try {
    const stmt = db.prepare(`
      INSERT OR IGNORE INTO vehicles 
      (plate_number, owner_name, owner_id, vehicle_make, vehicle_model, vehicle_year, vehicle_color)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    
    sampleVehicles.forEach(vehicle => {
      stmt.run(
        vehicle.plate_number,
        vehicle.owner_name,
        vehicle.owner_id,
        vehicle.vehicle_make,
        vehicle.vehicle_model,
        vehicle.vehicle_year,
        vehicle.vehicle_color
      );
    });
    
    console.log('Datos de ejemplo insertados');
    console.log('Configuración de base de datos completada');
  } catch (err) {
    console.error('Error al insertar datos de ejemplo:', err.message);
  }
}

// Ejecutar si se llama directamente
if (require.main === module) {
  setupDatabase();
}

module.exports = { setupDatabase };

