# Sistema de Reconocimiento de Matrículas

Sistema completo de reconocimiento automático de matrículas vehiculares con IA, vinculación a propietarios y aplicación móvil nativa.

## Características Principales

- **Detección automática de matrículas** con IA (EasyOCR + OpenCV)
- **Reconocimiento de múltiples matrículas** en una sola imagen
- **Aplicación móvil nativa** (Android/iOS) con Capacitor
- **Detección automática** al capturar foto con la cámara
- **Búsqueda automática en BD** después de detectar
- **Registro de vehículos** desde la interfaz móvil
- **Acceso desde cualquier dispositivo** en la misma red WiFi
- **Preprocesamiento avanzado** de imágenes para mejor OCR
- **Sistema experto de OCR** con corrección de perspectiva y eliminación de reflejos

## Requisitos

### Node.js
- Node.js 14+ 
- npm o yarn

### SQL Server
- SQL Server 2017+ (servidor de base de datos)
- SQL Server Express (gratis) o versión completa
- Usuario con permisos para crear bases de datos

### Python
- Python 3.8+
- Librerías: `opencv-python`, `numpy`, `easyocr`

## Instalación Rápida

### 1. Instalar dependencias Node.js
```bash
cd "MODULO 4"
npm install
```

### 2. Instalar SQL Server
- **Windows**: Descargar SQL Server Express (gratis) de https://www.microsoft.com/sql-server/sql-server-downloads
- **Linux**: `sudo apt-get install mssql-server` (ver guía oficial)
- **Mac**: Usar Docker: `docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=TuPassword123" -p 1433:1433 mcr.microsoft.com/mssql/server:2019-latest`

### 3. Configurar variables de entorno
Crea un archivo `.env` en la carpeta MODULO 4:
```env
DB_HOST=localhost
DB_PORT=1433
DB_NAME=vehicles_db
DB_USER=sa
DB_PASSWORD=tu_password_aqui
DB_ENCRYPT=false
DB_TRUST_CERT=true
PORT=3000
```

### 4. Instalar dependencias Python
```bash
pip install opencv-python numpy easyocr
```

O usando requirements.txt:
```bash
pip install -r requirements.txt
```

### 5. Inicializar base de datos SQL Server
```bash
npm run setup-db
```

Esto creará automáticamente la base de datos y las tablas optimizadas con índices.

### 6. Iniciar servidor
```bash
npm start
```

El servidor estará disponible en `http://localhost:3000`

## Uso desde Móvil

### Opción 1: Navegador Web (Más Fácil)

1. **Iniciar servidor** en tu PC:
   ```bash
   npm start
   ```

2. **Encontrar tu IP**:
   ```bash
   # Windows
   ipconfig
   # Linux/Mac
   ifconfig
   ```

3. **Abrir en tu teléfono** (misma WiFi):
   - Abre el navegador
   - Ve a: `http://TU_IP:3000`
   - Ejemplo: `http://192.168.100.40:3000`

4. **Usar la app**:
   - Toca "Capturar y Detectar Matrícula"
   - Se abrirá la cámara del teléfono
   - Captura la foto → se detecta automáticamente

### Opción 2: App Nativa Android

1. **Configurar IP del servidor** en `public/index.html`:
   - Busca la función `getApiUrl()`
   - Cambia la IP por la de tu PC

2. **Sincronizar con Capacitor**:
   ```bash
   npm run cap:sync
   ```

3. **Abrir en Android Studio**:
   ```bash
   npm run cap:open
   ```

4. **Construir y ejecutar** desde Android Studio

## API Endpoints

### Detección de Matrículas

- `POST /api/detect` - Detectar una matrícula
- `POST /api/detect/diagnosis` - Detectar con diagnóstico detallado
- `POST /api/detect/multiple` - Detectar múltiples matrículas en una imagen

### Gestión de Vehículos

- `GET /api/vehicle/:plate` - Consultar vehículo por matrícula
- `POST /api/vehicle` - Registrar nuevo vehículo
- `PUT /api/vehicle/:plate` - Actualizar vehículo
- `GET /api/vehicles` - Listar todos los vehículos (con paginación)

## Estructura del Proyecto

```
MODULO 4/
├── ml/                          # Machine Learning
│   ├── detect.py                # Detector básico
│   ├── detect_enhanced.py       # Detector con diagnóstico
│   ├── multi_plate_detector.py  # Detector múltiple
│   └── preprocess.py             # Preprocesamiento de imágenes
├── database/                    # Base de datos
│   └── schema_sqlserver.sql     # Esquema SQL Server
├── routes/                      # Rutas API
│   ├── detection.js             # Endpoints de detección
│   └── vehicles.js              # Endpoints de vehículos
├── public/                      # Interfaz web/móvil
│   └── index.html               # Aplicación principal
├── scripts/                     # Scripts de utilidad
│   ├── setupDatabase.js        # Configuración de BD SQLite
│   ├── setupSqlServer.js        # Configuración de BD SQL Server
│   └── check_new_vehicles.js   # Verificar vehículos nuevos
├── utils/                       # Utilidades
│   ├── database.js              # Conexión a base de datos
│   ├── linking.js               # Lógica de vinculación
│   └── pythonHelper.js          # Helper para Python
├── server.js                    # Servidor principal
├── package.json                 # Dependencias Node.js
└── requirements.txt             # Dependencias Python
```

## Scripts Disponibles

```bash
npm start              # Iniciar servidor
npm run dev            # Modo desarrollo (nodemon)
npm run setup-db       # Configurar base de datos SQL Server
npm run setup-db-sqlite # Configurar base de datos SQLite
npm run check-vehicles # Verificar vehículos nuevos
```

## Documentación Adicional

- **README_FUNCIONES.md**: Documentación completa de todas las funciones del sistema
- **INSTALACION_SQL_SERVER.md**: Guía detallada de instalación de SQL Server

## Notas

- El sistema está optimizado para matrículas mexicanas
- Funciona mejor con imágenes claras y buena iluminación
- La primera ejecución puede tardar (EasyOCR descarga modelos)
- El servidor muestra automáticamente tu IP local al iniciar

## Licencia

MIT

---

**Desarrollado usando Node.js, Python, OpenCV, EasyOCR y Capacitor**

