# MÓDULO 4 - Sistema de Reconocimiento de Matrículas con Inteligencia Artificial

**INSTITUTO TECNOLOGICO DE CULIACAN**

**Materia:** Topicos de IA  
**Profesor:** ZURIEL DATHAN MORA FELIX  
**Grupo:** 12:00 a 13:00 p.m

**Integrantes:**
- Herrera Quiñones Abraham Gael
- Edgar Ochoa Aviles

---

## Descripción del Módulo

Este módulo presenta un sistema completo de reconocimiento automático de matrículas vehiculares utilizando técnicas avanzadas de Inteligencia Artificial, visión por computadora y reconocimiento óptico de caracteres (OCR). El sistema integra múltiples tecnologías para proporcionar una solución robusta y escalable.

## Objetivos del Proyecto

1. **Detección Automática**: Implementar un sistema capaz de detectar y reconocer matrículas vehiculares en imágenes de manera automática.

2. **Vinculación con Propietarios**: Crear un sistema de base de datos que vincule las matrículas detectadas con información de propietarios y vehículos.

3. **Interfaz Móvil**: Desarrollar una aplicación accesible desde dispositivos móviles para captura y procesamiento en tiempo real.

4. **Optimización de Rendimiento**: Implementar técnicas de optimización para procesamiento rápido y eficiente de imágenes.

## Tecnologías Utilizadas

### Backend
- **Node.js**: Servidor web y API REST
- **Express.js**: Framework web para Node.js
- **SQL Server**: Base de datos relacional para almacenamiento de información

### Machine Learning y Visión por Computadora
- **Python 3.8+**: Lenguaje principal para procesamiento de imágenes
- **OpenCV**: Procesamiento de imágenes y detección de regiones
- **EasyOCR**: Motor de reconocimiento óptico de caracteres
- **NumPy**: Operaciones numéricas y procesamiento de arrays

### Frontend
- **HTML5/CSS3/JavaScript**: Interfaz web responsive
- **Capacitor**: Framework para aplicaciones móviles nativas

## Estructura del Proyecto

```
MODULO 4/
├── ProyectoPlacas/              # Proyecto principal
│   ├── ml/                      # Módulo de Machine Learning
│   │   ├── detect.py            # Detector básico de matrículas
│   │   ├── detect_enhanced.py   # Detector con diagnóstico detallado
│   │   ├── multi_plate_detector.py  # Detector de múltiples matrículas
│   │   └── preprocess.py        # Preprocesamiento de imágenes
│   ├── routes/                  # Rutas de la API REST
│   │   ├── detection.js         # Endpoints de detección
│   │   └── vehicles.js          # Endpoints de gestión de vehículos
│   ├── utils/                   # Utilidades del sistema
│   │   ├── database.js          # Conexión y consultas a base de datos
│   │   ├── linking.js           # Sistema de vinculación de matrículas
│   │   └── pythonHelper.js      # Helper para ejecutar scripts Python
│   ├── scripts/                 # Scripts de configuración
│   │   ├── setupDatabase.js     # Configuración de SQLite
│   │   ├── setupSqlServer.js    # Configuración de SQL Server
│   │   └── check_new_vehicles.js # Verificación de vehículos
│   ├── public/                  # Interfaz web/móvil
│   │   └── index.html           # Aplicación principal
│   ├── database/                # Esquemas de base de datos
│   │   └── schema_sqlserver.sql # Esquema para SQL Server
│   ├── server.js                # Servidor principal
│   ├── package.json             # Dependencias Node.js
│   ├── requirements.txt         # Dependencias Python
│   ├── README.md                # Documentación del proyecto
│   └── README_FUNCIONES.md      # Documentación técnica completa
└── README.md                    # Este archivo
```

## Características Principales

### 1. Detección Inteligente de Matrículas
- **Múltiples estrategias de detección**: El sistema implementa varias estrategias de fallback para maximizar las posibilidades de éxito.
- **Preprocesamiento avanzado**: Mejora de contraste, binarización adaptativa, y corrección de perspectiva.
- **Detección de múltiples matrículas**: Capacidad de detectar varias matrículas en una sola imagen.

### 2. Reconocimiento Óptico de Caracteres (OCR)
- **EasyOCR**: Motor principal de OCR con soporte para múltiples idiomas.
- **Validación de formato**: Sistema de validación específico para matrículas mexicanas.
- **Filtrado inteligente**: Eliminación automática de texto descriptivo y validación de patrones.

### 3. Sistema de Base de Datos
- **SQL Server**: Base de datos robusta con índices optimizados.
- **Caché en memoria**: Sistema de caché para consultas frecuentes.
- **Connection pooling**: Optimización de conexiones para mejor rendimiento.

### 4. API REST Completa
- **Endpoints de detección**: Múltiples endpoints para diferentes casos de uso.
- **Gestión de vehículos**: CRUD completo para vehículos y propietarios.
- **Diagnóstico detallado**: Endpoint especializado para debugging y análisis.

### 5. Interfaz Móvil
- **Acceso desde navegador**: Funciona en cualquier dispositivo con navegador web.
- **Captura desde cámara**: Integración con la cámara del dispositivo móvil.
- **Aplicación nativa**: Soporte para aplicaciones Android/iOS con Capacitor.

## Instalación y Configuración

Para instalar y configurar el proyecto, consulta la documentación detallada en:

📁 **`ProyectoPlacas/README.md`** - Guía de instalación y uso

### Requisitos Previos

1. **Node.js 14+** y npm
2. **Python 3.8+** con pip
3. **SQL Server 2017+** (o SQL Server Express)
4. **Git** para clonar el repositorio

### Instalación Rápida

```bash
# 1. Navegar a la carpeta del proyecto
cd "MODULO 4/ProyectoPlacas"

# 2. Instalar dependencias Node.js
npm install

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Crear archivo .env con las credenciales de SQL Server

# 5. Inicializar base de datos
npm run setup-db

# 6. Iniciar servidor
npm start
```

## Uso del Sistema

### Desde Navegador Web

1. Iniciar el servidor: `npm start`
2. Abrir navegador en: `http://localhost:3000`
3. Capturar o seleccionar imagen con matrícula
4. El sistema detecta automáticamente y busca en la base de datos

### Desde Dispositivo Móvil

1. Asegurarse de estar en la misma red WiFi
2. Obtener la IP del servidor (se muestra en la consola)
3. Abrir navegador móvil en: `http://TU_IP:3000`
4. Usar la cámara del dispositivo para capturar matrículas

### API REST

El sistema expone una API REST completa. Consulta la documentación técnica en:

📁 **`ProyectoPlacas/README_FUNCIONES.md`** - Documentación completa de la API

**Endpoints principales:**
- `POST /api/detect` - Detectar matrícula en imagen
- `GET /api/vehicle/:plate` - Consultar vehículo por matrícula
- `POST /api/vehicle` - Registrar nuevo vehículo
- `GET /api/vehicles` - Listar todos los vehículos

## Resultados y Aprendizajes

### Técnicas de IA Implementadas

1. **Visión por Computadora**: Uso de OpenCV para detección de regiones de interés
2. **Reconocimiento de Patrones**: Validación de formatos de matrículas mexicanas
3. **Procesamiento de Imágenes**: Técnicas de preprocesamiento para mejorar OCR
4. **Optimización de Algoritmos**: Múltiples estrategias de detección con fallback

### Optimizaciones Implementadas

- **Caché en memoria**: Reducción de consultas a base de datos
- **Connection pooling**: Reutilización de conexiones SQL Server
- **Índices de base de datos**: Búsquedas 10-20x más rápidas
- **Procesamiento asíncrono**: Manejo concurrente de múltiples peticiones

### Desafíos Resueltos

1. **Calidad de imagen variable**: Implementación de múltiples estrategias de preprocesamiento
2. **Diferentes formatos de matrícula**: Sistema de validación flexible
3. **Rendimiento**: Optimizaciones en base de datos y caché
4. **Integración móvil**: Solución multiplataforma con Capacitor

## Documentación Adicional

- **`ProyectoPlacas/README.md`**: Guía completa de instalación y uso
- **`ProyectoPlacas/README_FUNCIONES.md`**: Documentación técnica detallada de todas las funciones
- **`ProyectoPlacas/INSTALACION_SQL_SERVER.md`**: Guía de instalación de SQL Server

## Conclusiones

Este proyecto demuestra la aplicación práctica de técnicas de Inteligencia Artificial y visión por computadora para resolver un problema real: el reconocimiento automático de matrículas vehiculares. El sistema integra múltiples tecnologías y optimizaciones para proporcionar una solución robusta, escalable y fácil de usar.

### Logros Principales

✅ Sistema funcional de detección y reconocimiento de matrículas  
✅ Integración completa con base de datos SQL Server  
✅ API REST bien documentada y optimizada  
✅ Interfaz móvil accesible desde cualquier dispositivo  
✅ Documentación técnica completa  
✅ Optimizaciones de rendimiento implementadas  

## Licencia

MIT

---

**Desarrollado como parte del curso de Tópicos de Inteligencia Artificial**  
**Instituto Tecnológico de Culiacán**  
**2024**
