/**
 * Script para verificar vehículos nuevos registrados en la base de datos
 * Optimizado para SQL Server
 */
const { query, close } = require('../utils/database');

async function checkVehicles() {
  try {
    console.log('Analizando base de datos...\n');
    console.log('='.repeat(60));
    
    // OPTIMIZACIÓN: Consultas paralelas para mayor velocidad
    const [vehiclesResult, detectionsResult] = await Promise.all([
      query('SELECT * FROM vehicles ORDER BY created_at DESC'),
      query('SELECT TOP 10 * FROM detections ORDER BY detection_timestamp DESC')
    ]);
    
    const vehicles = vehiclesResult.recordset || [];
    const detections = detectionsResult.recordset || [];
    
    console.log(`\nRESUMEN:`);
    console.log(`   Total de vehículos registrados: ${vehicles.length}`);
    console.log(`   Total de detecciones: ${detections.length}\n`);
    
    if (vehicles.length === 0) {
      console.log('No hay vehículos registrados en la base de datos.\n');
    } else {
      console.log('VEHÍCULOS REGISTRADOS:\n');
      vehicles.forEach((v, i) => {
        const fecha = new Date(v.created_at).toLocaleString('es-ES');
        console.log(`${i + 1}. Matrícula: ${v.plate_number}`);
        console.log(`   Propietario: ${v.owner_name}`);
        if (v.owner_id) console.log(`   ID Propietario: ${v.owner_id}`);
        if (v.vehicle_make || v.vehicle_model) {
          console.log(`   Vehículo: ${v.vehicle_make || 'N/A'} ${v.vehicle_model || ''}`.trim());
        }
        if (v.vehicle_year) console.log(`   Año: ${v.vehicle_year}`);
        if (v.vehicle_color) console.log(`   Color: ${v.vehicle_color}`);
        console.log(`   Registrado: ${fecha}`);
        console.log('');
      });
    }
    
    // Mostrar detecciones recientes
    if (detections.length > 0) {
      console.log('ÚLTIMAS 10 DETECCIONES:\n');
      detections.forEach((d, i) => {
        const fecha = new Date(d.detection_timestamp).toLocaleString('es-ES');
        const vehicleInfo = vehicles.find(v => v.id === d.vehicle_id);
        const status = vehicleInfo ? 'Registrado' : 'No registrado';
        console.log(`${i + 1}. Matrícula: ${d.plate_number} - ${status}`);
        console.log(`   Fecha: ${fecha}`);
        if (vehicleInfo) {
          console.log(`   Propietario: ${vehicleInfo.owner_name}`);
        }
        console.log('');
      });
    }
    
    // Verificar si hay vehículos nuevos (últimas 24 horas)
    const last24Hours = new Date();
    last24Hours.setHours(last24Hours.getHours() - 24);
    
    const recentVehicles = vehicles.filter(v => {
      const created = new Date(v.created_at);
      return created >= last24Hours;
    });
    
    if (recentVehicles.length > 0) {
      console.log('VEHÍCULOS NUEVOS (últimas 24 horas):\n');
      recentVehicles.forEach((v, i) => {
        const fecha = new Date(v.created_at).toLocaleString('es-ES');
        console.log(`${i + 1}. ${v.plate_number} - ${v.owner_name}`);
        console.log(`   Registrado: ${fecha}\n`);
      });
    } else {
      console.log('No hay vehículos nuevos en las últimas 24 horas.\n');
    }
    
    console.log('='.repeat(60));
    
  } catch (error) {
    console.error('Error al consultar la base de datos:', error.message);
    console.error('Asegúrate de que SQL Server esté corriendo y configurado en .env');
    process.exit(1);
  } finally {
    // Cerrar conexiones
    await close();
  }
}

checkVehicles();
