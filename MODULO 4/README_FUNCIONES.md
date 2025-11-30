# Documentación de Funciones - Sistema de Reconocimiento de Matrículas

Este documento describe en detalle todas las funciones, clases, endpoints y scripts disponibles en el proyecto. Incluye explicaciones sobre cómo funcionan, por qué se implementaron de cierta manera, y ejemplos prácticos de uso.

## Introducción

El Sistema de Reconocimiento de Matrículas es una aplicación completa que combina visión por computadora, reconocimiento óptico de caracteres (OCR) y gestión de base de datos para detectar, reconocer y vincular matrículas vehiculares con información de propietarios. El sistema está diseñado para funcionar tanto en entornos web como móviles, utilizando tecnologías como Node.js para el backend, Python para el procesamiento de imágenes con OpenCV y EasyOCR, y SQL Server para el almacenamiento de datos.

## Arquitectura del Sistema

El sistema está dividido en varias capas:

1. **Capa de Presentación**: Interfaz web HTML/JavaScript que permite capturar imágenes desde la cámara o seleccionarlas de la galería
2. **Capa de API**: Servidor Express.js que maneja las peticiones HTTP y coordina el procesamiento
3. **Capa de Procesamiento**: Scripts Python que utilizan OpenCV y EasyOCR para detectar y reconocer matrículas
4. **Capa de Datos**: Base de datos SQL Server que almacena información de vehículos y registra todas las detecciones

Esta arquitectura permite que el sistema sea escalable, mantenible y fácil de extender con nuevas funcionalidades.

## Tabla de Contenidos

1. [API Endpoints](#api-endpoints)
2. [Funciones Python - Módulo ML](#funciones-python---módulo-ml)
3. [Funciones JavaScript - Utilidades](#funciones-javascript---utilidades)
4. [Funciones JavaScript - Rutas](#funciones-javascript---rutas)
5. [Scripts Disponibles](#scripts-disponibles)
6. [Clases Principales](#clases-principales)
7. [Flujo de Procesamiento](#flujo-de-procesamiento)

---

## API Endpoints

Los endpoints de la API REST permiten interactuar con el sistema desde cualquier cliente HTTP. Todos los endpoints retornan respuestas en formato JSON y manejan errores de manera consistente. El sistema utiliza Express.js como framework web y Multer para el manejo de archivos.

### Detección de Matrículas

Los endpoints de detección procesan imágenes para extraer números de matrícula. El sistema soporta múltiples formatos de imagen (JPEG, PNG, GIF, BMP, WEBP) y puede procesar imágenes de hasta 10MB. El procesamiento se realiza mediante scripts Python que utilizan técnicas avanzadas de visión por computadora y OCR.

#### POST /api/detect
Detecta una matrícula en una imagen subida. Este es el endpoint principal para la detección de matrículas. El sistema carga la imagen, la procesa usando algoritmos de visión por computadora para encontrar la región de la matrícula, y luego aplica OCR para extraer el texto. Si se detecta una matrícula, el sistema automáticamente busca información del vehículo en la base de datos y registra la detección.

**Parámetros:**
- `image` (FormData, requerido): Archivo de imagen en formato multipart/form-data. El sistema acepta los formatos más comunes: jpeg, jpg, png, gif, bmp, webp. La imagen debe tener un tamaño máximo de 10MB para evitar problemas de memoria durante el procesamiento.
- `diagnosis` (query/body, opcional): Si se establece en `true`, el sistema retorna información detallada sobre el proceso de detección, incluyendo las estrategias que se probaron, advertencias sobre la calidad de la imagen, y recomendaciones para mejorar la detección. Esto es útil para debugging y para entender por qué una detección falló.
- `location` (body, opcional): Cadena de texto que describe la ubicación geográfica donde se detectó la matrícula. Esta información se almacena junto con el registro de detección para análisis posteriores.

**Respuesta exitosa:**

Cuando la detección es exitosa, el sistema retorna un objeto JSON con toda la información relevante. El campo `success` indica que la operación fue exitosa. El `plate_number` contiene la matrícula detectada después de ser normalizada (mayúsculas, sin espacios extra). Si el vehículo está registrado en la base de datos, el objeto `vehicle` contiene toda la información del propietario y del vehículo. El `image_path` indica dónde se almacenó la imagen procesada en el servidor, y el `detection_timestamp` registra el momento exacto de la detección en formato ISO 8601.

```json
{
  "success": true,
  "plate_number": "VPM-45-32",
  "vehicle": {
    "id": 1,
    "plate_number": "VPM-45-32",
    "owner_name": "Juan Pérez",
    "owner_id": "12345678",
    "vehicle_make": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_year": 2020,
    "vehicle_color": "Blanco",
    "registration_date": "2020-01-15",
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-01T00:00:00.000Z"
  },
  "message": "Vehículo encontrado para matrícula: VPM-45-32",
  "image_path": "./uploads/plate-1234567890.jpg",
  "detection_timestamp": "2024-01-15T10:30:00.000Z",
  "diagnosis": { ... } // Solo si diagnosis=true
}
```

Si el vehículo no está registrado, el campo `vehicle` será `null` y el mensaje indicará que la matrícula fue detectada pero no se encontró en la base de datos. En este caso, el sistema aún registra la detección para análisis posterior.

**Respuesta de error:**

Cuando la detección falla, el sistema retorna un objeto con `success: false` y un mensaje descriptivo que explica por qué no se pudo detectar la matrícula. Esto puede ocurrir por varias razones: la imagen no contiene una matrícula visible, la calidad de la imagen es insuficiente, la matrícula está parcialmente oculta, o hay problemas de iluminación. Si se solicitó diagnóstico, el campo `diagnosis` contendrá información detallada sobre qué estrategias se probaron y por qué fallaron.

```json
{
  "success": false,
  "message": "No se pudo detectar ninguna matrícula en la imagen",
  "plate_number": null,
  "vehicle": null,
  "diagnosis": {
    "message": "Usa ?diagnosis=true para obtener información detallada sobre por qué falló la detección"
  }
}
```

El sistema no elimina la imagen subida cuando falla la detección si se solicitó diagnóstico, permitiendo análisis posterior. En caso contrario, la imagen se elimina automáticamente para ahorrar espacio en disco.

---

#### POST /api/detect/base64
Detecta matrícula desde una imagen en formato base64. Este endpoint es útil cuando la imagen ya está en memoria como string base64, evitando la necesidad de crear un archivo temporal. Es especialmente útil para aplicaciones móviles que capturan imágenes directamente desde la cámara y las convierten a base64 antes de enviarlas al servidor. El sistema decodifica el base64, crea un archivo temporal, procesa la imagen, y luego elimina el archivo temporal automáticamente.

**Parámetros:**
- `image` (body): String base64 de la imagen
- `location` (body, opcional): Ubicación donde se detectó la matrícula

**Respuesta:** Similar a `/api/detect`

---

#### POST /api/detect/diagnosis
Detecta matrícula con diagnóstico detallado del proceso. Este endpoint es una versión extendida del endpoint básico de detección que proporciona información exhaustiva sobre cómo se procesó la imagen. Es especialmente útil para debugging, para entender por qué una detección falló, o para optimizar el proceso de captura de imágenes. El diagnóstico incluye información sobre la calidad de la imagen, las estrategias de detección que se probaron, los resultados de OCR en cada etapa, y recomendaciones específicas para mejorar la detección.

**Parámetros:**
- `image` (FormData): Archivo de imagen

**Respuesta:**
```json
{
  "success": true,
  "plate_number": "VPM-45-32",
  "vehicle": { ... },
  "diagnosis": {
    "strategies_tried": [
      {
        "name": "Detección de región + OCR preprocesado",
        "status": "success",
        "plate_number": "VPM-45-32"
      }
    ],
    "warnings": [],
    "errors": [],
    "image_info": {
      "width": 1920,
      "height": 1080,
      "channels": 3,
      "aspect_ratio": 1.78
    },
    "recommendations": []
  },
  "detection_timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

#### POST /api/detect/multiple
Detecta múltiples matrículas en una sola imagen. Este endpoint utiliza algoritmos avanzados de visión por computadora para identificar todas las regiones que podrían contener matrículas en una imagen, y luego procesa cada región independientemente. Es útil para escenarios donde una imagen puede contener varios vehículos, como en estacionamientos o en fotos de tráfico. El sistema utiliza detección de contornos, análisis de formas rectangulares, y filtrado por relación de aspecto para encontrar las regiones candidatas. Cada matrícula detectada se valida independientemente y se busca en la base de datos.

**Parámetros:**
- `image` (FormData): Archivo de imagen

**Respuesta:**
```json
{
  "success": true,
  "plates": [
    {
      "plate_number": "VPM-45-32",
      "confidence": 0.95,
      "plate_index": 1,
      "vehicle": { ... }
    },
    {
      "plate_number": "ABC-12-34",
      "confidence": 0.87,
      "plate_index": 2,
      "vehicle": null
    }
  ],
  "total_found": 2,
  "detection_timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

### Gestión de Vehículos

Los endpoints de gestión de vehículos permiten crear, leer, actualizar y listar vehículos en la base de datos. Todos los endpoints utilizan el sistema de vinculación optimizado que incluye caché en memoria y consultas optimizadas con índices. El sistema normaliza automáticamente las matrículas antes de buscar o almacenar, permitiendo búsquedas flexibles que ignoran diferencias en mayúsculas/minúsculas y espacios.

#### GET /api/vehicle/:plate
Consulta información de un vehículo por matrícula. Este endpoint realiza una búsqueda optimizada en la base de datos utilizando el sistema de caché y índices. Primero intenta una búsqueda exacta de la matrícula normalizada, y si no encuentra resultados, intenta una búsqueda flexible que ignora guiones y espacios. Además de la información del vehículo, retorna el historial de las últimas 5 detecciones de esa matrícula, lo que permite rastrear cuándo y dónde se ha detectado el vehículo anteriormente.

**Parámetros:**
- `plate` (URL): Número de matrícula a consultar

**Respuesta exitosa:**
```json
{
  "success": true,
  "plate_number": "VPM-45-32",
  "vehicle": {
    "id": 1,
    "plate_number": "VPM-45-32",
    "owner_name": "Juan Pérez",
    "owner_id": "12345678",
    "vehicle_make": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_year": 2020,
    "vehicle_color": "Blanco",
    "registration_date": "2020-01-15",
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-01T00:00:00.000Z"
  },
  "detection_history": [
    {
      "id": 1,
      "plate_number": "VPM-45-32",
      "vehicle_id": 1,
      "detection_timestamp": "2024-01-15T10:30:00.000Z",
      ...
    }
  ],
  "message": "Vehículo encontrado para matrícula: VPM-45-32"
}
```

**Respuesta de error (404):**
```json
{
  "success": false,
  "error": "No se encontró ningún vehículo con la matrícula: VPM-45-32",
  "message": "La matrícula \"VPM-45-32\" no está registrada en la base de datos",
  "plate_number": "VPM-45-32",
  "vehicle": null
}
```

---

#### POST /api/vehicle
Registra un nuevo vehículo en la base de datos. Este endpoint valida que no exista ya un vehículo con la misma matrícula antes de insertar. Si el vehículo ya existe, retorna un error 409 (Conflict) con la información del vehículo existente. El sistema normaliza automáticamente la matrícula antes de almacenarla, asegurando consistencia en la base de datos. Utiliza la cláusula OUTPUT de SQL Server para retornar el vehículo insertado en una sola operación, mejorando el rendimiento. Todos los campos excepto `plate_number` y `owner_name` son opcionales, permitiendo registrar vehículos con información mínima y completar los datos posteriormente.

**Parámetros (body JSON):**
- `plate_number` (requerido): Número de matrícula
- `owner_name` (requerido): Nombre del propietario
- `owner_id` (opcional): ID del propietario
- `vehicle_make` (opcional): Marca del vehículo
- `vehicle_model` (opcional): Modelo del vehículo
- `vehicle_year` (opcional): Año del vehículo
- `vehicle_color` (opcional): Color del vehículo
- `registration_date` (opcional): Fecha de registro

**Respuesta exitosa (201):**
```json
{
  "success": true,
  "message": "Vehículo registrado exitosamente con matrícula: VPM-45-32",
  "vehicle": {
    "id": 1,
    "plate_number": "VPM-45-32",
    ...
  }
}
```

**Respuesta de error (409 - Conflicto):**
```json
{
  "success": false,
  "error": "Ya existe un vehículo con la matrícula: VPM-45-32",
  "vehicle": { ... }
}
```

---

#### PUT /api/vehicle/:plate
Actualiza información de un vehículo existente. Este endpoint permite actualizar cualquier campo de un vehículo sin necesidad de proporcionar todos los campos. Solo los campos que se envían en el body serán actualizados, manteniendo los valores existentes para los campos no proporcionados. El sistema verifica que el vehículo exista antes de intentar actualizarlo, retornando un error 404 si no se encuentra. Utiliza la cláusula OUTPUT de SQL Server para retornar el vehículo actualizado en una sola operación. El campo `updated_at` se actualiza automáticamente con la fecha y hora actual.

**Parámetros:**
- `plate` (URL): Número de matrícula del vehículo a actualizar
- Body JSON con campos opcionales a actualizar (mismos campos que POST)

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Vehículo actualizado exitosamente",
  "vehicle": { ... }
}
```

---

#### GET /api/vehicles
Lista todos los vehículos con paginación. Este endpoint implementa paginación para manejar eficientemente grandes cantidades de vehículos. Utiliza OFFSET y FETCH NEXT de SQL Server para realizar la paginación a nivel de base de datos, lo que es más eficiente que cargar todos los registros y paginar en memoria. Retorna información de paginación que incluye el número total de vehículos, el número total de páginas, y la página actual, permitiendo a los clientes implementar controles de navegación. Los vehículos se ordenan por fecha de creación descendente, mostrando los más recientes primero.

**Parámetros (query):**
- `page` (opcional, default: 1): Número de página
- `limit` (opcional, default: 10): Cantidad de vehículos por página

**Respuesta:**
```json
{
  "success": true,
  "vehicles": [
    { ... },
    { ... }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50,
    "total_pages": 5
  }
}
```

---

#### GET /health
Endpoint de salud del servidor.

**Respuesta:**
```json
{
  "status": "ok",
  "message": "Sistema de reconocimiento de matrículas funcionando",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Funciones Python - Módulo ML

El módulo ML (Machine Learning) contiene toda la lógica de procesamiento de imágenes y reconocimiento de matrículas. Utiliza OpenCV para el procesamiento de imágenes y EasyOCR para el reconocimiento óptico de caracteres. El sistema está optimizado para matrículas mexicanas, pero puede adaptarse a otros formatos modificando los patrones de validación.

### ml/detect.py

Este módulo contiene la implementación básica del detector de matrículas. Utiliza múltiples estrategias de detección para maximizar las posibilidades de éxito, incluso en condiciones subóptimas de iluminación o ángulo.

#### Clase: LicensePlateDetector

Esta clase encapsula toda la lógica de detección y reconocimiento de matrículas. Utiliza EasyOCR como motor de OCR, que es una biblioteca de código abierto que puede reconocer texto en múltiples idiomas. La clase está diseñada para ser eficiente y robusta, probando múltiples estrategias antes de fallar.

##### `__init__(self, languages: list = ['en'])`
Inicializa el detector de matrículas. Este método configura EasyOCR con parámetros optimizados para velocidad y precisión. El parámetro `languages` permite especificar qué idiomas debe reconocer el OCR, aunque para matrículas mexicanas el inglés funciona bien ya que las matrículas generalmente contienen letras latinas y números. El sistema está configurado para usar CPU en lugar de GPU para mayor compatibilidad, aunque se puede cambiar si hay GPU disponible. La cuantización está habilitada para reducir el tamaño de los modelos y mejorar la velocidad de carga.

**Parámetros:**
- `languages`: Lista de idiomas para OCR (por defecto inglés)

**Lanza:**
- `ImportError`: Si easyocr no está instalado

---

##### `detect_and_recognize(self, image_path: str) -> Optional[str]`
Detecta y reconoce el número de matrícula en una imagen usando múltiples estrategias. Este es el método principal de la clase y implementa un sistema de fallback que prueba diferentes enfoques hasta encontrar la matrícula o agotar todas las opciones. El método valida primero que la imagen exista y sea válida antes de comenzar el procesamiento, evitando errores costosos más adelante en el proceso.

**Parámetros:**
- `image_path`: Ruta completa al archivo de imagen. El sistema acepta los formatos más comunes de imagen.

**Retorna:**
- `str`: Número de matrícula detectado y normalizado (mayúsculas, sin espacios extra) o `None` si no se encuentra ninguna matrícula válida.

**Lanza:**
- `FileNotFoundError`: Si el archivo de imagen no existe en la ruta especificada.
- `ValueError`: Si la imagen no se puede cargar (formato inválido) o está vacía (archivo corrupto).

**Estrategias utilizadas (en orden de prioridad):**

1. **Detección de región y procesamiento**: El sistema primero intenta identificar la región específica de la imagen que contiene la matrícula usando algoritmos de visión por computadora. Esto es más eficiente porque procesa solo una porción de la imagen. Utiliza detección de contornos, análisis de formas rectangulares, y filtrado por relación de aspecto para encontrar la región. Una vez identificada, la región se preprocesa específicamente para OCR (mejora de contraste, binarización, etc.) antes de aplicar el reconocimiento.

2. **Procesamiento de toda la imagen**: Si no se puede identificar una región específica, el sistema procesa toda la imagen. Esto es útil cuando la matrícula ocupa una porción significativa de la imagen o cuando los algoritmos de detección de región fallan. La imagen completa se preprocesa con las mismas técnicas de mejora de contraste y binarización.

3. **OCR directo en imagen original**: Si el preprocesamiento no produce resultados, el sistema intenta OCR directamente en la imagen original sin preprocesamiento. Esto puede funcionar cuando la imagen ya tiene buena calidad y contraste.

4. **Procesamiento con diferentes rotaciones**: Si todas las estrategias anteriores fallan, el sistema prueba rotar la imagen en diferentes ángulos (-10°, -5°, 5°, 10°) y aplicar OCR en cada rotación. Esto es útil cuando la matrícula está ligeramente inclinada, lo cual es común en fotos tomadas desde ángulos no frontales.

Cada estrategia utiliza parámetros optimizados de EasyOCR que priorizan texto más grande (como las matrículas) y son más permisivos con el umbral de confianza para capturar texto que podría ser una matrícula pero tiene confianza ligeramente baja.

---

##### `detect_from_array(self, image_array: np.ndarray) -> Optional[str]`
Detecta matrícula desde un array numpy (útil para video streams).

**Parámetros:**
- `image_array`: Array numpy de la imagen

**Retorna:**
- `str`: Número de matrícula detectado o `None`

---

##### `_extract_plate_number_from_results(self, results: List) -> Optional[str]`
Extrae número de matrícula de resultados de OCR, priorizando texto más grande y válido. Este método implementa un sistema sofisticado de filtrado y scoring que identifica el texto más probable que sea una matrícula entre todos los textos detectados por OCR. El sistema no solo busca texto que parezca una matrícula, sino que valida activamente que no sea texto descriptivo común en las placas mexicanas.

**Parámetros:**
- `results`: Lista de resultados de EasyOCR donde cada resultado es una tupla con formato `[(bbox, text, confidence), ...]`. El `bbox` contiene las coordenadas del bounding box del texto detectado, `text` es el texto reconocido, y `confidence` es un valor entre 0 y 1 que indica la confianza del OCR en ese reconocimiento.

**Retorna:**
- `str`: Matrícula detectada y normalizada (mayúsculas, solo letras, números y guiones) o `None` si no se encuentra ningún texto válido.

**Lógica detallada:**

El método implementa un sistema de scoring que evalúa cada texto detectado según múltiples criterios:

1. **Filtrado de textos descriptivos**: El sistema mantiene una lista de palabras descriptivas comunes en placas mexicanas (como "SINALOA", "MEXICO", "TRANSPORTE", "PRIVADO", etc.) y filtra automáticamente estos textos. También filtra textos largos que son solo letras (probablemente palabras descriptivas) y textos que son solo números (probablemente fragmentos de la matrícula, no la matrícula completa).

2. **Validación de formato de matrícula mexicana**: El sistema utiliza expresiones regulares para validar que el texto coincida con patrones conocidos de matrículas mexicanas. Los patrones incluyen formatos con y sin guiones, como "VPM-45-32", "VPM45-32", "VPM-4532", etc. Los textos que coinciden con estos patrones reciben un score base alto.

3. **Priorización de textos completos**: El sistema prioriza textos que tienen tanto letras como números, ya que las matrículas mexicanas siempre contienen ambos. También prioriza textos con longitud típica de matrícula (7-10 caracteres sin guiones) y textos que tienen formato con guiones (más legible y estándar).

4. **Cálculo de score**: Para cada candidato, se calcula un score combinado que considera:
   - Score base por coincidir con patrón de matrícula (100 puntos para el patrón más común, menos para otros)
   - Bonus por confianza de OCR (hasta 50 puntos)
   - Bonus por tamaño del texto (área del bounding box normalizada)
   - Bonus por relación de aspecto horizontal (las matrículas son más anchas que altas)
   - Bonus por tener letras Y números (20 puntos)
   - Bonus por longitud típica (25 puntos)
   - Bonus por formato con guiones (15 puntos)
   - Penalización por textos muy cortos (-30 puntos)

5. **Selección del mejor candidato**: Todos los candidatos se ordenan primero por si coinciden con un patrón de matrícula, luego por score descendente, luego por tamaño, y finalmente por confianza. Se retorna el candidato con el score más alto que pase todos los filtros.

---

##### `_rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray`
Rota una imagen un ángulo dado.

**Parámetros:**
- `image`: Imagen a rotar
- `angle`: Ángulo en grados

**Retorna:**
- `np.ndarray`: Imagen rotada

---

#### Función: `detect_license_plate(image_path: str) -> Optional[str]`
Función de conveniencia para detectar matrícula en una imagen.

**Parámetros:**
- `image_path`: Ruta a la imagen

**Retorna:**
- `str`: Número de matrícula detectado o `None`

---

### ml/detect_enhanced.py

Este módulo extiende la funcionalidad básica de detección agregando capacidades de diagnóstico detallado. Es especialmente útil para entender por qué una detección falla y cómo mejorar las imágenes para obtener mejores resultados.

#### Clase: EnhancedLicensePlateDetector

Esta clase hereda conceptualmente la funcionalidad de `LicensePlateDetector` pero agrega un sistema completo de diagnóstico que rastrea cada paso del proceso de detección, registra advertencias y errores, y genera recomendaciones específicas basadas en los resultados.

##### `__init__(self, languages: list = ['en'], debug: bool = False)`
Inicializa el detector mejorado con diagnóstico. El modo debug permite ver información detallada en la consola durante el procesamiento, lo cual es útil para desarrollo y debugging. El sistema mantiene un diccionario de diagnóstico que se va llenando durante el proceso de detección con información sobre cada estrategia probada, errores encontrados, advertencias sobre la calidad de la imagen, y recomendaciones para mejorar los resultados.

**Parámetros:**
- `languages`: Lista de idiomas para OCR
- `debug`: Modo debug para mostrar información detallada

---

##### `detect_with_diagnosis(self, image_path: str, use_expert_mode: bool = False) -> Dict`
Detecta matrícula con diagnóstico completo del proceso. Este método implementa el mismo sistema de múltiples estrategias que el detector básico, pero además registra información detallada sobre cada paso. Para cada estrategia, registra si se intentó, si tuvo éxito o falló, y si falló, por qué razón. También analiza la calidad de la imagen (resolución, contraste, brillo) y genera advertencias si la calidad es subóptima. Al final, genera recomendaciones específicas basadas en los resultados obtenidos, como sugerir mejorar la iluminación si la imagen es muy oscura, o acercarse más a la matrícula si la resolución es baja.

**Parámetros:**
- `image_path`: Ruta a la imagen
- `use_expert_mode`: Modo experto (actualmente no implementado)

**Retorna:**
```python
{
    'plate_number': str | None,
    'success': bool,
    'diagnosis': {
        'strategies_tried': List[Dict],
        'errors': List[str],
        'warnings': List[str],
        'image_info': Dict,
        'ocr_results': List[Dict],
        'recommendations': List[str]
    }
}
```

**Diagnóstico incluye:**
- Información de la imagen (resolución, canales, aspecto)
- Estrategias probadas y su resultado
- Advertencias sobre calidad de imagen
- Errores encontrados
- Recomendaciones para mejorar la detección

---

##### `_validate_image_quality(self, image: np.ndarray)`
Valida la calidad de la imagen y genera advertencias. Este método analiza varios aspectos de la calidad de la imagen que pueden afectar la detección de matrículas. Realiza análisis estadísticos sobre la imagen (como desviación estándar para contraste y media para brillo) para identificar problemas potenciales antes de intentar la detección.

**Parámetros:**
- `image`: Imagen en formato numpy array (BGR o escala de grises) a validar.

**Advertencias generadas:**

1. **Resolución muy baja**: Si la imagen tiene menos de 320x240 píxeles, se genera una advertencia indicando que la resolución es muy baja y recomendando un mínimo de 640x480. Las imágenes de baja resolución dificultan el reconocimiento de caracteres pequeños.

2. **Imagen muy pequeña**: Si el área total de la imagen (ancho × alto) es menor a 100,000 píxeles, se advierte que la imagen es muy pequeña y puede afectar la detección. Esto es independiente de la resolución, ya que una imagen puede tener buena resolución pero ser muy pequeña en términos de área.

3. **Bajo contraste**: Se calcula la desviación estándar de los valores de píxeles en escala de grises. Si la desviación estándar es menor a 20, se considera que la imagen tiene bajo contraste. El contraste bajo hace difícil distinguir los caracteres del fondo de la placa.

4. **Imagen muy oscura o muy brillante**: Se calcula el brillo promedio de la imagen. Si es menor a 30 (en escala de 0-255), la imagen se considera muy oscura. Si es mayor a 225, se considera muy brillante. Ambas condiciones dificultan el OCR porque los caracteres pueden no contrastar suficientemente con el fondo.

---

##### `_generate_recommendations(self)`
Genera recomendaciones basadas en el diagnóstico.

**Recomendaciones incluyen:**
- Mejoras de calidad de imagen
- Mejoras de iluminación
- Sugerencias de ángulo y posición

---

#### Función: `detect_with_diagnosis(image_path: str, debug: bool = False) -> Dict`
Función de conveniencia para detección con diagnóstico.

**Parámetros:**
- `image_path`: Ruta a la imagen
- `debug`: Mostrar información detallada

**Retorna:** Diccionario con resultados y diagnóstico

---

#### Función: `convert_to_serializable(obj)`
Convierte objetos numpy y otros tipos no serializables a tipos nativos de Python.

**Parámetros:**
- `obj`: Objeto a convertir

**Retorna:** Objeto serializable (int, float, list, dict, etc.)

---

### ml/multi_plate_detector.py

Este módulo implementa un detector especializado para encontrar múltiples matrículas en una sola imagen. Utiliza técnicas avanzadas de visión por computadora para identificar todas las regiones candidatas que podrían contener matrículas, y luego procesa cada región independientemente. Es especialmente útil para escenarios como estacionamientos, fotos de tráfico, o cualquier situación donde una imagen puede contener varios vehículos.

#### Clase: DetectorDeMultiplesMatriculas

Esta clase implementa un pipeline completo de detección múltiple que combina detección de regiones con OCR. Utiliza tanto EasyOCR como Pytesseract (si está disponible) para maximizar las posibilidades de reconocimiento. El sistema está optimizado para velocidad, limitando el número de regiones y contornos que procesa para mantener tiempos de respuesta razonables.

##### `__init__(self, idiomas: list = ['en'])`
Inicializa el detector de múltiples matrículas. Configura EasyOCR con parámetros optimizados para velocidad, ya que puede necesitar procesar múltiples regiones. El sistema está configurado para usar CPU para mayor compatibilidad, aunque se puede cambiar si hay GPU disponible. La cuantización está habilitada para reducir el tamaño de los modelos y mejorar la velocidad de carga inicial.

**Parámetros:**
- `idiomas`: Lista de idiomas para OCR (por defecto inglés)

---

##### `detectar_todas_las_matriculas(self, ruta_imagen: str) -> Dict`
Detecta todas las matrículas presentes en una imagen. Este método implementa un pipeline completo que primero identifica todas las regiones candidatas en la imagen, luego procesa cada región con OCR, y finalmente valida y filtra los resultados para retornar solo matrículas válidas. El sistema está diseñado para ser robusto y eficiente, limitando el número de regiones procesadas para mantener tiempos de respuesta razonables.

**Parámetros:**
- `ruta_imagen`: Ruta completa al archivo de imagen a procesar. El sistema valida que el archivo exista antes de comenzar el procesamiento.

**Retorna:**
Un diccionario con la siguiente estructura:
```python
{
    'success': bool,  # True si se detectó al menos una matrícula
    'plates': [       # Lista de matrículas detectadas
        {
            'plate_number': str,      # Matrícula normalizada
            'confidence': float,       # Nivel de confianza (0-1)
            'plate_index': int,        # Índice de la matrícula (1, 2, 3...)
            'raw_results': List[str]   # Resultados crudos de OCR para debugging
        }
    ],
    'total_found': int,  # Número total de matrículas encontradas
    'error': str         # Mensaje de error solo si hay un error fatal
}
```

**Proceso detallado:**

1. **Carga de imagen**: El sistema carga la imagen usando OpenCV. Si la imagen es muy grande (más de 1200 píxeles en cualquier dimensión), la redimensiona automáticamente para acelerar el procesamiento sin perder demasiada información.

2. **Búsqueda de regiones candidatas**: Utiliza algoritmos de visión por computadora para encontrar todas las regiones rectangulares que podrían contener matrículas. El proceso incluye:
   - Conversión a escala de grises
   - Suavizado con filtro bilateral para reducir ruido
   - Detección de bordes con Canny
   - Dilatación de bordes para conectar líneas cercanas
   - Búsqueda de contornos
   - Análisis de contornos para encontrar rectángulos con relación de aspecto típica de matrículas (2:1 a 5:1)
   - Filtrado por tamaño mínimo (100px ancho, 30px alto)
   - Eliminación de duplicados verificando solapamiento

3. **Procesamiento de cada región**: Para cada región candidata encontrada:
   - Se intenta primero con Pytesseract (si está disponible) usando un pipeline completo de ANPR que incluye corrección de perspectiva y binarización adaptativa
   - Si Pytesseract no está disponible o no detecta nada, se usa EasyOCR con preprocesamiento
   - Se valida que el texto detectado sea una matrícula válida (no descriptivo, tiene letras y números, longitud adecuada)

4. **Filtrado y validación**: Todos los textos detectados se filtran usando el mismo sistema de validación que el detector básico:
   - Se eliminan palabras descriptivas conocidas
   - Se valida formato de matrícula mexicana
   - Se calcula un score para cada candidato
   - Se ordenan por score y se retornan solo los válidos

Si no se encuentran regiones candidatas, el sistema intenta OCR en toda la imagen como fallback, agrupando resultados cercanos que podrían ser parte de la misma matrícula.

---

##### `_encontrar_regiones_matricula(self, imagen: np.ndarray) -> List[Tuple]`
Encuentra todas las regiones en la imagen que podrían contener matrículas.

**Parámetros:**
- `imagen`: Imagen en formato numpy array (BGR)

**Retorna:**
- Lista de tuplas: `(region_imagen, (x, y, ancho, alto))`

**Método:**
- Detección de contornos
- Análisis de forma (rectángulos con relación de aspecto 2:1 a 5:1)
- Filtrado por tamaño mínimo y extensión

---

##### `_procesar_region_matricula(self, region: np.ndarray, numero_region: int) -> Optional[Dict]`
Procesa una región de imagen para extraer el texto de la matrícula usando OCR.

**Parámetros:**
- `region`: Array numpy con la imagen de la región
- `numero_region`: Número de región (para identificación)

**Retorna:**
```python
{
    'plate_number': str,
    'confidence': float,
    'plate_index': int,
    'raw_results': List[str]
}
```
o `None` si no se encuentra matrícula

---

##### `tu_funcion_de_detectar_placas(self, image_bytes: np.ndarray) -> List[str]`
Pipeline completo de ANPR usando OpenCV y Pytesseract.

**Parámetros:**
- `image_bytes`: Array numpy de la imagen (BGR) o bytes de imagen

**Retorna:**
- Lista de placas detectadas (ej: ['VPM-45-32'])

**Pipeline:**
1. Pre-procesamiento (escala de grises, reducción de ruido, detección de bordes)
2. Detección y aislamiento de la placa (contornos, filtrado, recorte)
3. Corrección de perspectiva (endereza la placa)
4. Binarización y limpieza de la placa
5. OCR con Pytesseract (configuración optimizada)
6. Post-procesamiento (limpieza de string)

---

##### `_extraer_mejor_matricula(self, resultados_ocr: List) -> Optional[Dict]`
Extrae el mejor candidato de matrícula de los resultados OCR.

**Parámetros:**
- `resultados_ocr`: Lista de resultados de EasyOCR

**Retorna:**
```python
{
    'text': str,
    'confidence': float,
    'score': float,
    'matches_pattern': bool
}
```
o `None` si no hay candidatos válidos

**Sistema de scoring:**
- Prioriza textos que coinciden con patrones de matrícula mexicana
- Considera confianza de OCR
- Valida formato típico (letras + números + guiones)

---

##### `_limpiar_texto(self, texto: str) -> str`
Limpia y normaliza el texto extraído por OCR.

**Parámetros:**
- `texto`: Texto crudo del OCR

**Retorna:**
- Texto limpio en mayúsculas, solo letras, números y guiones

---

##### `_es_texto_valido(self, texto: str) -> bool`
Verifica si un texto es un candidato válido para ser una matrícula.

**Parámetros:**
- `texto`: Texto a validar

**Retorna:**
- `bool`: True si es válido, False si debe filtrarse

**Filtros aplicados:**
- Palabras descriptivas conocidas
- Textos largos solo con letras
- Fragmentos muy cortos (menos de 7 caracteres)
- Solo números

---

##### `_validar_patron_matricula(self, texto: str) -> Tuple[bool, int]`
Valida si un texto coincide con algún patrón de matrícula mexicana.

**Parámetros:**
- `texto`: Texto a validar

**Retorna:**
- Tupla `(coincide_patron, score_patron)`

**Patrones:**
- `^[A-Z]{2,4}-?\d{2}-?\d{2,3}$` (VPM-45-32, ABC-12-34)
- `^[A-Z]{2,4}\d{2}-?\d{2,3}$` (VPM45-32)
- `^[A-Z]{2,4}-?\d{3,4}$` (VPM-123)
- `^[A-Z]{2,4}\d{3,4}$` (VPM123)

---

##### `_calcular_score_candidato(self, texto: str, confianza: float, coincide_patron: bool, score_patron: int) -> float`
Calcula el score total de un candidato a matrícula.

**Parámetros:**
- `texto`: Texto del candidato
- `confianza`: Confianza del OCR (0-1)
- `coincide_patron`: Si coincide con patrón de matrícula
- `score_patron`: Score del patrón

**Retorna:**
- `float`: Score total del candidato

**Factores considerados:**
- Score base por patrón
- Bonus por confianza
- Bonus por tener letras Y números
- Bonus por longitud típica (7-10 caracteres)
- Bonus por formato con guiones
- Bonus extra por patrón exacto (XXX-XX-XX)

---

##### `_ocr_imagen_completa(self, imagen: np.ndarray) -> Dict`
Realiza OCR en toda la imagen cuando no se encuentran regiones específicas.

**Parámetros:**
- `imagen`: Imagen completa en formato numpy array

**Retorna:** Diccionario con matrículas detectadas

---

### ml/preprocess.py

Este módulo contiene todas las funciones de preprocesamiento de imágenes. El preprocesamiento es crucial para el éxito del OCR, ya que mejora la calidad de la imagen antes del reconocimiento, haciendo que los caracteres sean más claros y fáciles de reconocer. Las funciones están optimizadas para matrículas, que generalmente tienen texto oscuro sobre fondo claro o viceversa.

#### Función: `normalize_image(image: np.ndarray) -> np.ndarray`
Normaliza la imagen a valores entre 0 y 1. Esta función convierte los valores de píxeles de cualquier rango (generalmente 0-255 para imágenes de 8 bits) a un rango normalizado entre 0 y 1. Esto es útil cuando se trabaja con modelos de machine learning que esperan valores normalizados, aunque en este proyecto principalmente se usa para consistencia. La función detecta automáticamente si la imagen ya está normalizada o si necesita conversión.

**Parámetros:**
- `image`: Imagen en formato numpy array

**Retorna:**
- Imagen normalizada

---

#### Función: `resize_image(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray`
Redimensiona la imagen a un tamaño consistente.

**Parámetros:**
- `image`: Imagen original
- `target_size`: Tamaño objetivo (ancho, alto)

**Retorna:**
- Imagen redimensionada

---

#### Función: `enhance_contrast(image: np.ndarray, method: str = 'clahe') -> np.ndarray`
Mejora el contraste de la imagen.

**Parámetros:**
- `image`: Imagen original
- `method`: Método de mejora ('clahe', 'histogram', 'adaptive')

**Retorna:**
- Imagen con contraste mejorado

---

#### Función: `preprocess_for_detection(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray`
Preprocesa una imagen completa para detección de matrícula.

**Parámetros:**
- `image_path`: Ruta a la imagen
- `target_size`: Tamaño objetivo

**Retorna:**
- Imagen preprocesada lista para el modelo

---

#### Función: `preprocess_for_ocr(plate_region: np.ndarray) -> np.ndarray`
Preprocesa una región de matrícula para OCR con técnicas avanzadas. Esta es la función más importante del módulo de preprocesamiento, ya que implementa un pipeline completo de mejoras de imagen específicamente diseñado para maximizar la precisión del OCR en matrículas. El pipeline está optimizado para manejar diferentes condiciones de iluminación, ángulos, y calidad de imagen.

**Parámetros:**
- `plate_region`: Región de la imagen que contiene la matrícula, en formato numpy array. Puede ser en color (BGR) o escala de grises.

**Retorna:**
- Imagen preprocesada en formato binario (blanco y negro) optimizada para OCR. La imagen resultante tiene fondo blanco y texto negro, que es el formato ideal para la mayoría de motores OCR.

**Pipeline de procesamiento detallado:**

1. **Conversión a escala de grises**: Si la imagen está en color, se convierte a escala de grises. Esto simplifica el procesamiento y es suficiente para OCR ya que el color no aporta información relevante para reconocer caracteres.

2. **Redimensionamiento inteligente**: El sistema verifica el tamaño de la imagen y la redimensiona si es necesario:
   - Si la imagen es muy pequeña (menos de 80px de alto o 200px de ancho), se amplía con interpolación cúbica para mejorar la calidad. Las imágenes pequeñas son difíciles de reconocer para el OCR.
   - Si la imagen es muy grande (más de 400px de alto o 1200px de ancho), se reduce con interpolación de área para acelerar el procesamiento sin perder demasiada información.
   - El redimensionamiento mantiene la relación de aspecto original.

3. **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: Esta técnica mejora el contraste de la imagen de manera adaptativa, dividiendo la imagen en pequeñas regiones y ecualizando el histograma de cada región independientemente. Esto es especialmente útil cuando hay variaciones de iluminación en la imagen. El sistema usa diferentes tamaños de tile según el tamaño de la imagen para optimizar el rendimiento.

4. **Filtro bilateral para reducción de ruido**: El filtro bilateral reduce el ruido mientras preserva los bordes, que son cruciales para el reconocimiento de caracteres. Es más efectivo que un filtro gaussiano simple porque no difumina los bordes.

5. **Normalización**: Se normalizan los valores de píxeles al rango 0-255 para asegurar que la imagen tenga el máximo contraste posible.

6. **Umbralización adaptativa**: Se convierte la imagen a binaria (blanco y negro) usando umbralización adaptativa. A diferencia de la umbralización global, la adaptativa calcula un umbral diferente para cada región de la imagen, lo que es crucial cuando hay variaciones de iluminación. El sistema usa el método gaussiano que calcula el umbral basándose en la media ponderada de los píxeles vecinos.

7. **Operaciones morfológicas**: Se aplica una operación de cierre morfológico (dilatación seguida de erosión) para conectar caracteres que puedan estar fragmentados y eliminar pequeños puntos de ruido. Esto mejora la legibilidad de los caracteres para el OCR.

---

#### Función: `detect_plate_region(image: np.ndarray) -> Optional[np.ndarray]`
Detecta la región de la matrícula en una imagen usando múltiples estrategias.

**Parámetros:**
- `image`: Imagen completa

**Retorna:**
- Región de la matrícula o `None` si no se encuentra

**Estrategias:**
1. Detección por contornos
2. Detección por color
3. Detección por textura
4. Recorte de región central (si la imagen es pequeña)

---

#### Función: `_detect_by_contours(image: np.ndarray) -> Optional[np.ndarray]`
Detección de región por contornos mejorada.

**Parámetros:**
- `image`: Imagen a procesar

**Retorna:**
- Región detectada o `None`

---

#### Función: `_detect_by_color(image: np.ndarray) -> Optional[np.ndarray]`
Detección por color (matrículas suelen tener alto contraste).

**Parámetros:**
- `image`: Imagen a procesar

**Retorna:**
- Región detectada o `None`

---

#### Función: `_detect_by_texture(image: np.ndarray) -> Optional[np.ndarray]`
Detección por textura (regiones con muchas líneas horizontales).

**Parámetros:**
- `image`: Imagen a procesar

**Retorna:**
- Región detectada o `None`

---

## Funciones JavaScript - Utilidades

Las utilidades proporcionan funcionalidades compartidas que son utilizadas por múltiples partes del sistema. Están diseñadas para ser eficientes, reutilizables y robustas, con manejo adecuado de errores y optimizaciones de rendimiento.

### utils/database.js

Este módulo maneja todas las interacciones con la base de datos SQL Server. Implementa un sistema de connection pooling para mejorar el rendimiento, un sistema de caché en memoria para consultas frecuentes, y funciones auxiliares para ejecutar queries de manera segura y eficiente.

#### Función: `getPool() -> Promise<ConnectionPool>`
Obtiene o crea el pool de conexiones a SQL Server. Esta función implementa el patrón singleton para asegurar que solo existe un pool de conexiones en toda la aplicación. El pool se crea la primera vez que se llama a la función y se reutiliza en llamadas posteriores, mejorando significativamente el rendimiento al evitar crear nuevas conexiones para cada query.

**Retorna:**
- Promise que resuelve al pool de conexiones configurado y listo para usar.

**Configuración del pool:**

El pool está configurado con parámetros optimizados para balancear rendimiento y uso de recursos:

- **Máximo 20 conexiones simultáneas**: Permite manejar hasta 20 queries concurrentes sin crear nuevas conexiones. Esto es suficiente para la mayoría de aplicaciones y evita sobrecargar el servidor de base de datos.

- **Mínimo 0 conexiones**: El pool puede reducirse a cero conexiones cuando no hay actividad, ahorrando recursos del servidor.

- **Timeout de conexión: 2 segundos**: Si no se puede establecer una conexión en 2 segundos, se lanza un error. Esto evita que la aplicación se quede colgada esperando una conexión que nunca llegará.

- **Timeout de request: 5 segundos**: Si una query tarda más de 5 segundos en ejecutarse, se cancela y se lanza un error. Esto previene que queries lentas bloqueen el pool.

- **Idle timeout: 30 segundos**: Las conexiones inactivas se cierran después de 30 segundos para liberar recursos.

- **Trust Server Certificate: true**: Habilitado para desarrollo local, permite conexiones sin certificados SSL verificados.

El sistema también detecta automáticamente si debe usar encriptación basándose en variables de entorno, lo que es útil para conexiones a Azure SQL Database que requieren SSL.

---

#### Función: `query(text: string, params: Array = []) -> Promise<Object>`
Ejecuta una query SQL de manera segura y eficiente. Esta función es el punto de entrada principal para todas las operaciones de base de datos. Maneja la conversión de parámetros, la detección automática de tipos de datos, y proporciona logging útil para debugging y monitoreo de rendimiento.

**Parámetros:**
- `text`: Query SQL como string. Puede usar parámetros con sintaxis `@p1`, `@p2`, etc. (nativa de SQL Server) o `$1`, `$2`, etc. (estilo PostgreSQL), y la función los convertirá automáticamente a la sintaxis de SQL Server.

- `params`: Array de parámetros que se insertarán en la query. Los parámetros se pasan de manera segura usando prepared statements, previniendo inyección SQL.

**Retorna:**
- Promise que resuelve al resultado de la query. El resultado tiene la estructura estándar de mssql con un campo `recordset` que contiene los registros retornados.

**Características detalladas:**

1. **Conversión automática de tipos de datos**: La función detecta automáticamente el tipo de cada parámetro (número entero, número decimal, string, fecha, null) y lo mapea al tipo SQL Server correspondiente (Int, Float, VarChar, DateTime2, etc.). Esto optimiza el rendimiento y previene errores de tipo.

2. **Conversión de sintaxis de parámetros**: Si la query usa sintaxis `$1`, `$2` (estilo PostgreSQL), la función automáticamente la convierte a `@p1`, `@p2` (sintaxis SQL Server). Esto permite reutilizar queries escritas para otros sistemas de base de datos.

3. **Monitoreo de rendimiento**: La función mide el tiempo que tarda cada query en ejecutarse. Si una query tarda más de 1 segundo, se registra una advertencia en la consola con los primeros 100 caracteres de la query. Esto ayuda a identificar queries lentas que pueden necesitar optimización.

4. **Manejo de errores con logging**: Si una query falla, la función registra el error completo en la consola junto con los primeros 200 caracteres de la query para facilitar el debugging. Luego relanza el error para que el código que llama pueda manejarlo apropiadamente.

5. **Medición de tiempo**: Cada query tiene su tiempo de ejecución medido desde el inicio hasta el final, permitiendo análisis de rendimiento detallado.

---

#### Función: `getClient() -> Promise<Request>`
Obtiene una conexión del pool.

**Retorna:**
- Promise que resuelve a un Request object

---

#### Función: `close() -> Promise<void>`
Cierra todas las conexiones del pool.

**Retorna:**
- Promise que se resuelve cuando se cierran las conexiones

---

#### Función: `getCacheKey(plate: string) -> string`
Genera una clave de caché normalizada para una matrícula. Esta función asegura que las claves de caché sean consistentes, normalizando la matrícula a mayúsculas y eliminando espacios antes de generar la clave. Esto permite que búsquedas con diferentes formatos de la misma matrícula (por ejemplo, "vpm-45-32" y "VPM-45-32") usen el mismo caché.

**Parámetros:**
- `plate`: Número de matrícula en cualquier formato (mayúsculas, minúsculas, con o sin espacios).

**Retorna:**
- Clave de caché en formato "plate:VPM-45-32" donde la matrícula está normalizada a mayúsculas y sin espacios extra.

**Ejemplo:**
- "vpm-45-32" → "plate:VPM-45-32"
- "VPM 45 32" → "plate:VPM-45-32"
- "  vpm-45-32  " → "plate:VPM-45-32"

---

#### Función: `getCached(key: string) -> Object | null`
Obtiene un valor del caché si aún es válido. El sistema de caché utiliza un TTL (Time To Live) de 1 minuto, lo que significa que los valores cacheados expiran después de 60 segundos. Esto asegura que los datos no se vuelvan obsoletos mientras mantiene el beneficio de rendimiento para consultas repetidas en corto tiempo. El sistema también limpia automáticamente entradas expiradas cada 30 segundos para evitar que el caché crezca indefinidamente.

**Parámetros:**
- `key`: Clave de caché generada por `getCacheKey()`.

**Retorna:**
- El valor cacheado (generalmente un objeto con información del vehículo) si existe y no ha expirado, o `null` si no existe en el caché o ya expiró.

**TTL:** 1 minuto (60000ms). Este tiempo es un balance entre mantener datos frescos y maximizar el beneficio del caché. Para datos que cambian frecuentemente, se puede reducir el TTL, y para datos más estables, se puede aumentar.

**Limpieza automática:** El sistema ejecuta una limpieza del caché cada 30 segundos que elimina todas las entradas expiradas, previniendo fugas de memoria.

---

#### Función: `setCache(key: string, data: Object) -> void`
Almacena un valor en el caché.

**Parámetros:**
- `key`: Clave de caché
- `data`: Datos a almacenar

---

### utils/pythonHelper.js

Este módulo proporciona funciones para detectar y usar el comando correcto de Python en diferentes sistemas operativos. Es crucial porque diferentes sistemas y distribuciones de Python usan diferentes comandos (python, python3, py), y el sistema necesita encontrar el correcto para ejecutar los scripts de procesamiento de imágenes.

#### Función: `detectPythonCommand() -> string`
Detecta el comando correcto de Python disponible en el sistema. Esta función es esencial para la portabilidad del sistema, ya que diferentes sistemas operativos y configuraciones usan diferentes comandos para Python. La función prueba los comandos más comunes en orden de probabilidad y retorna el primero que funciona.

**Retorna:**
- Comando de Python ('python', 'python3', 'py', etc.) que está disponible y funciona en el sistema.

**Lanza:**
- `Error`: Si Python no está instalado o no se encuentra ningún comando válido. El mensaje de error incluye instrucciones sobre cómo instalar Python y configurar el PATH.

**Orden de búsqueda:**

La función prueba los comandos en un orden específico basado en el sistema operativo:

- **Windows**: python, py, python3
  - En Windows, `python` es el comando más común cuando Python está instalado desde python.org
  - `py` es el launcher de Python que viene con instalaciones modernas de Python en Windows
  - `python3` es menos común en Windows pero se prueba por compatibilidad

- **Linux/Mac**: python3, python
  - En Linux y Mac, `python3` es el comando estándar para Python 3, ya que `python` generalmente apunta a Python 2 (que está deprecado)
  - `python` se prueba como fallback por si acaso

**Caché**: El resultado se cachea en una variable de módulo para evitar ejecutar la detección múltiples veces, mejorando el rendimiento en llamadas posteriores.

**Validación**: Para cada comando, la función ejecuta `--version` con un timeout de 2 segundos para verificar que el comando existe y funciona correctamente, no solo que existe en el PATH.

---

#### Función: `getPythonCommand() -> string`
Obtiene el comando de Python (con caché).

**Retorna:**
- Comando de Python

---

#### Función: `isPythonAvailable() -> boolean`
Verifica que Python está instalado y disponible.

**Retorna:**
- `true` si Python está disponible, `false` en caso contrario

---

### utils/linking.js

Este módulo implementa el sistema de vinculación que conecta las matrículas detectadas con la información de vehículos y propietarios almacenada en la base de datos. Es el corazón del sistema de gestión de vehículos, proporcionando funciones optimizadas para búsqueda, registro de detecciones, y gestión de historial. El sistema está diseñado para ser eficiente, utilizando caché en memoria y consultas optimizadas con índices.

#### Clase: VehicleLinkingSystem

Esta clase encapsula toda la lógica de vinculación entre matrículas y vehículos. Implementa el patrón singleton para asegurar que solo existe una instancia en toda la aplicación, lo que permite compartir el caché y optimizar las conexiones a la base de datos. La clase se inicializa automáticamente cuando se crea la primera instancia y verifica la conexión a la base de datos antes de permitir operaciones.

##### `constructor()`
Inicializa el sistema de vinculación y verifica la conexión a la base de datos. Este constructor es crucial porque asegura que el sistema esté listo para usar antes de permitir cualquier operación. Verifica la conexión ejecutando una query simple (`SELECT 1`), lo que no solo confirma que la base de datos está accesible, sino que también inicializa el pool de conexiones si aún no está creado. Si la conexión falla, lanza un error inmediatamente en lugar de fallar silenciosamente más adelante.

---

##### `testConnection() -> Promise<void>`
Verifica la conexión a SQL Server.

**Lanza:**
- `Error`: Si no se puede conectar

---

##### `normalizePlateNumber(plateNumber: string) -> string | null`
Normaliza el número de matrícula para búsqueda y almacenamiento. Esta función es fundamental para la consistencia del sistema, ya que las matrículas pueden ingresarse en diferentes formatos (mayúsculas, minúsculas, con o sin espacios, con diferentes tipos de guiones). La normalización asegura que todas las búsquedas y comparaciones se hagan con un formato consistente, evitando problemas donde "VPM-45-32" y "vpm 45 32" se traten como matrículas diferentes.

**Parámetros:**
- `plateNumber`: Número de matrícula en cualquier formato. Puede ser null o undefined, en cuyo caso la función retorna null.

**Retorna:**
- Matrícula normalizada en formato estándar (mayúsculas, sin espacios extra, solo letras, números y guiones) o `null` si la entrada es inválida.

**Proceso de normalización:**
1. Convierte a mayúsculas para estandarizar
2. Elimina espacios al inicio y final con `trim()`
3. Elimina todos los caracteres que no sean letras, números o guiones usando una expresión regular
4. Retorna null si el resultado está vacío después de la normalización

**Ejemplos:**
- "vpm-45-32" → "VPM-45-32"
- "vpm 45 32" → "VPM-45-32" (los espacios se eliminan)
- "  VPM-45-32  " → "VPM-45-32" (espacios extra eliminados)
- "vpm@45#32" → "VPM-45-32" (caracteres especiales eliminados)
- "" → null (cadena vacía)
- null → null (valor nulo)

---

##### `findVehicleByPlate(plateNumber: string) -> Promise<Object | null>`
Busca un vehículo por número de matrícula utilizando un sistema de búsqueda optimizado de múltiples niveles. Esta función implementa varias optimizaciones para maximizar la velocidad y la precisión de las búsquedas, que son las operaciones más frecuentes en el sistema.

**Parámetros:**
- `plateNumber`: Número de matrícula en cualquier formato. La función normaliza automáticamente la matrícula antes de buscar.

**Retorna:**
- Objeto con información completa del vehículo (id, matrícula, propietario, información del vehículo, fechas) o `null` si no se encuentra ningún vehículo con esa matrícula.

**Optimizaciones implementadas:**

1. **Caché en memoria (TTL: 1 minuto)**: Antes de consultar la base de datos, la función verifica si el resultado está en el caché. Si está y no ha expirado (menos de 1 minuto), retorna inmediatamente el valor cacheado. Esto permite respuestas instantáneas para consultas repetidas, que son muy comunes cuando se procesan múltiples imágenes del mismo vehículo en corto tiempo. El caché también almacena resultados negativos (null) para evitar búsquedas repetidas de matrículas que no existen.

2. **Búsqueda exacta primero**: La primera búsqueda intenta encontrar la matrícula exacta normalizada. Esta es la búsqueda más rápida porque puede usar el índice primario en la columna `plate_number`. Si encuentra un resultado, lo retorna inmediatamente y lo almacena en el caché.

3. **Búsqueda normalizada (sin guiones) como fallback**: Si la búsqueda exacta no encuentra resultados, el sistema intenta una búsqueda más flexible usando la columna `plate_normalized`, que contiene la matrícula sin guiones ni espacios. Esto permite encontrar vehículos incluso si la matrícula se ingresó con un formato ligeramente diferente (por ejemplo, "VPM-45-32" vs "VPM4532"). Esta búsqueda también utiliza un índice para mantener la velocidad.

4. **Consultas optimizadas con índices**: Ambas búsquedas utilizan la cláusula `TOP 1` para limitar los resultados a uno (ya que las matrículas deben ser únicas) y utilizan índices optimizados en las columnas de búsqueda. Los índices permiten que SQL Server encuentre los registros sin escanear toda la tabla, reduciendo el tiempo de búsqueda de milisegundos a microsegundos en tablas grandes.

5. **Almacenamiento en caché de resultados**: Tanto los resultados positivos como los negativos se almacenan en el caché para evitar búsquedas repetidas innecesarias. Esto es especialmente útil cuando se procesan múltiples imágenes de la misma matrícula en un corto período.

**Flujo de ejecución:**
1. Validar y normalizar la matrícula de entrada
2. Generar clave de caché
3. Verificar caché - si existe y es válido, retornar inmediatamente
4. Ejecutar búsqueda exacta en base de datos
5. Si no se encuentra, ejecutar búsqueda flexible
6. Almacenar resultado en caché (positivo o negativo)
7. Retornar resultado

---

##### `recordDetection(plateNumber: string, options: Object = {}) -> Promise<Object>`
Registra una detección de matrícula en la base de datos. Esta función es llamada automáticamente después de cada detección exitosa para mantener un historial completo de todas las detecciones realizadas. El registro de detecciones permite análisis posteriores, como rastrear cuántas veces se ha detectado un vehículo, en qué ubicaciones, y con qué nivel de confianza.

**Parámetros:**
- `plateNumber`: Número de matrícula detectado. Se normaliza automáticamente antes de almacenar.

- `options`: Objeto con opciones adicionales para el registro:
  - `image_path`: Ruta al archivo de imagen donde se detectó la matrícula. Se almacena para referencia futura y permite recuperar la imagen original si es necesario.
  - `confidence_score`: Nivel de confianza del OCR (valor entre 0 y 1). Indica qué tan seguro está el sistema de que la matrícula detectada es correcta. Valores altos (cercanos a 1) indican alta confianza, valores bajos indican que la detección podría ser incorrecta.
  - `location`: Ubicación geográfica donde se detectó la matrícula (string descriptivo). Útil para análisis de patrones de movimiento y para sistemas de seguridad.

**Retorna:**
Un objeto con información sobre la detección registrada:
```javascript
{
  detection_id: number,        // ID único de la detección en la base de datos
  plate_number: string,         // Matrícula normalizada
  vehicle_found: boolean,       // true si el vehículo está registrado, false si no
  vehicle: Object | null        // Información del vehículo si se encontró, null si no
}
```

**Proceso interno:**

1. **Normalización**: La matrícula se normaliza para asegurar consistencia.

2. **Búsqueda de vehículo**: Se busca el vehículo en la base de datos usando `findVehicleByPlate()`, que utiliza el caché para eficiencia. Si se encuentra, se obtiene el ID del vehículo para vincular la detección.

3. **Inserción optimizada**: Se inserta el registro de detección usando la cláusula `OUTPUT INSERTED.id` de SQL Server, que permite obtener el ID generado automáticamente en una sola operación, evitando una query adicional.

4. **Retorno de información**: Se retorna un objeto con toda la información relevante, incluyendo si el vehículo fue encontrado y la información completa del vehículo si existe.

**Uso del historial**: El historial de detecciones se puede consultar usando `getDetectionHistory()` para ver todas las veces que se ha detectado una matrícula específica, lo que es útil para análisis de patrones, seguridad, y auditoría.

---

##### `getDetectionHistory(plateNumber: string, limit: number = 10) -> Promise<Array>`
Obtiene el historial de detecciones para una matrícula específica. Esta función es útil para rastrear el historial de un vehículo, ver cuándo y dónde se ha detectado, y analizar patrones de uso. El historial está ordenado por fecha descendente, mostrando las detecciones más recientes primero.

**Parámetros:**
- `plateNumber`: Número de matrícula para la cual se desea obtener el historial. Se normaliza automáticamente antes de buscar.

- `limit`: Número máximo de detecciones a retornar. Por defecto es 10, pero se puede aumentar si se necesita más historial. Se recomienda mantener límites razonables (50-100 máximo) para evitar respuestas muy grandes que puedan afectar el rendimiento.

**Retorna:**
- Array de objetos de detección, cada uno conteniendo:
  - `id`: ID único de la detección
  - `plate_number`: Matrícula detectada
  - `vehicle_id`: ID del vehículo si se encontró, null si no
  - `image_path`: Ruta a la imagen donde se detectó
  - `confidence_score`: Nivel de confianza del OCR
  - `location`: Ubicación donde se detectó
  - `detection_timestamp`: Fecha y hora de la detección

Los registros están ordenados por `detection_timestamp` descendente, mostrando las detecciones más recientes primero.

**Optimizaciones:**
- Utiliza la cláusula `TOP` de SQL Server para limitar los resultados a nivel de base de datos, evitando cargar más registros de los necesarios.
- Utiliza un índice en `plate_number` y `detection_timestamp` para acelerar la búsqueda y el ordenamiento.
- La query está optimizada para retornar solo los campos necesarios, reduciendo el ancho de banda y el tiempo de procesamiento.

---

#### Función: `getLinkingSystem() -> VehicleLinkingSystem`
Obtiene la instancia singleton del sistema de vinculación.

**Retorna:**
- Instancia de VehicleLinkingSystem

---

## Funciones JavaScript - Rutas

Las rutas definen los endpoints de la API REST y manejan la lógica de negocio para cada operación. Cada ruta es un middleware de Express que recibe la petición HTTP, valida los datos, ejecuta la lógica necesaria (como llamar a scripts Python o consultar la base de datos), y retorna una respuesta JSON apropiada.

### routes/detection.js

Este archivo contiene todos los endpoints relacionados con la detección de matrículas. Las funciones son middleware de Express que manejan las peticiones HTTP, coordinan la ejecución de los scripts Python de procesamiento de imágenes, y gestionan las respuestas al cliente. Cada endpoint maneja errores apropiadamente, limpia archivos temporales si es necesario, y proporciona mensajes de error descriptivos.

**Características comunes de los endpoints:**
- Validación de archivos de imagen (tipo, tamaño)
- Ejecución de scripts Python en procesos separados
- Captura y parsing de salida de los scripts Python
- Búsqueda automática en base de datos después de detectar
- Registro automático de detecciones
- Limpieza de archivos temporales en caso de error
- Manejo robusto de errores con mensajes descriptivos

Ver sección [API Endpoints](#api-endpoints) para detalles específicos de cada endpoint, incluyendo parámetros, formatos de respuesta, y ejemplos de uso.

---

### routes/vehicles.js

Este archivo contiene todos los endpoints relacionados con la gestión de vehículos. Las funciones implementan operaciones CRUD (Create, Read, Update) sobre la información de vehículos almacenada en la base de datos. Cada endpoint utiliza el sistema de vinculación optimizado que incluye caché y consultas eficientes.

**Características comunes de los endpoints:**
- Normalización automática de matrículas
- Validación de datos de entrada
- Verificación de duplicados antes de insertar
- Uso de consultas optimizadas con OUTPUT clause
- Manejo de errores de base de datos
- Respuestas consistentes en formato JSON

**Operaciones implementadas:**
- **GET**: Consulta de vehículos individuales y listado con paginación
- **POST**: Registro de nuevos vehículos con validación de duplicados
- **PUT**: Actualización parcial de información de vehículos existentes

Ver sección [API Endpoints](#api-endpoints) para detalles específicos de cada endpoint, incluyendo parámetros requeridos y opcionales, códigos de estado HTTP, y formatos de respuesta.

---

## Scripts Disponibles

### scripts/setupDatabase.js

Este script configura una base de datos SQLite inicial para el sistema. SQLite es una base de datos ligera que no requiere un servidor separado, lo que la hace ideal para desarrollo, pruebas, o despliegues pequeños. El script crea todas las tablas necesarias, índices, y opcionalmente inserta datos de ejemplo para facilitar las pruebas.

#### Función: `setupDatabase()`
Configura la base de datos SQLite inicial. Esta función es idempotente, lo que significa que se puede ejecutar múltiples veces de manera segura. Si las tablas ya existen, el script las omite (usando `IF NOT EXISTS` en SQL o `INSERT OR IGNORE` para datos). Esto permite ejecutar el script sin preocuparse por si la base de datos ya está configurada.

**Proceso detallado:**

1. **Creación del directorio**: Verifica si el directorio donde se almacenará la base de datos existe. Si no existe, lo crea automáticamente con todos los directorios padres necesarios. Esto asegura que el script funcione incluso en sistemas nuevos donde el directorio aún no ha sido creado.

2. **Lectura del esquema**: Lee el archivo de esquema SQL desde `database/schema.sql`. Este archivo contiene todas las definiciones de tablas, índices, triggers, y otros objetos de base de datos necesarios para el funcionamiento del sistema.

3. **Ejecución del esquema**: Ejecuta todas las sentencias SQL del esquema usando `db.exec()`, que puede ejecutar múltiples sentencias SQL en una sola llamada. Si alguna sentencia falla, el script detiene la ejecución y muestra el error.

4. **Inserción de datos de ejemplo**: Opcionalmente inserta datos de ejemplo (3 vehículos de prueba) para facilitar las pruebas del sistema. Los datos de ejemplo permiten probar la funcionalidad sin necesidad de registrar vehículos manualmente primero.

**Uso:**
```bash
npm run setup-db-sqlite
```

**Nota**: Este script está diseñado para SQLite. Para SQL Server, usa `npm run setup-db` que ejecuta `setupSqlServer.js`.

---

#### Función: `insertSampleData(db: Database)`
Inserta datos de ejemplo en la base de datos.

**Parámetros:**
- `db`: Instancia de la base de datos SQLite

**Datos insertados:**
- 3 vehículos de ejemplo con diferentes matrículas

---

### scripts/setupSqlServer.js

Este script configura la base de datos SQL Server para el sistema. SQL Server es una base de datos empresarial más robusta que SQLite, con mejor rendimiento, soporte para conexiones concurrentes, y características avanzadas. El script maneja la creación de la base de datos, la ejecución del esquema, y la inserción de datos iniciales.

#### Función: `setupDatabase() -> Promise<void>`
Configura la base de datos SQL Server completa. Esta función es asíncrona y debe ser esperada. Maneja toda la configuración inicial del sistema, desde la creación de la base de datos hasta la inserción de datos de ejemplo. El script es robusto y maneja errores comunes como objetos que ya existen, permitiendo ejecutarlo múltiples veces de manera segura.

**Proceso detallado:**

1. **Conexión inicial a 'master'**: Se conecta primero a la base de datos 'master', que es la base de datos del sistema en SQL Server. Esto es necesario porque no se puede crear una base de datos mientras se está conectado a ella. La conexión utiliza las credenciales especificadas en las variables de entorno (.env).

2. **Creación de la base de datos**: Verifica si la base de datos especificada en `DB_NAME` existe. Si no existe, la crea. Si ya existe, continúa sin error. La verificación se hace consultando la vista del sistema `sys.databases`, que contiene información sobre todas las bases de datos en el servidor.

3. **Conexión a la nueva base de datos**: Cierra la conexión a 'master' y abre una nueva conexión a la base de datos recién creada (o existente). Esta conexión se usará para ejecutar el esquema y crear las tablas.

4. **Lectura y ejecución del esquema**: Lee el archivo `database/schema_sqlserver.sql` que contiene todas las definiciones de tablas, índices, funciones, triggers, y otros objetos. El esquema se divide por sentencias `GO` (que es el separador de lotes en SQL Server) y cada sentencia se ejecuta independientemente. Si una sentencia falla porque el objeto ya existe, se ignora el error y se continúa, permitiendo ejecutar el script múltiples veces.

5. **Inserción de datos de ejemplo**: Verifica si ya hay datos en la tabla `vehicles`. Si la tabla está vacía, inserta 3 vehículos de ejemplo. Si ya hay datos, omite la inserción para no duplicar información. Los datos de ejemplo permiten probar el sistema inmediatamente después de la instalación.

**Uso:**
```bash
npm run setup-db
```

**Requisitos previos:**
- SQL Server debe estar instalado y corriendo
- Las credenciales en el archivo `.env` deben ser correctas
- El usuario debe tener permisos para crear bases de datos

**Lanza:**
- `Error`: Si hay problemas de conexión (servidor no disponible, credenciales incorrectas), permisos insuficientes (usuario no puede crear bases de datos), o errores al ejecutar el esquema (sintaxis SQL incorrecta, objetos conflictivos).

**Manejo de errores**: El script proporciona mensajes de error descriptivos que ayudan a identificar el problema. Si falla, verifica que SQL Server esté corriendo, que las credenciales sean correctas, y que el usuario tenga los permisos necesarios.

---

#### Función: `insertSampleData(pool: ConnectionPool) -> Promise<void>`
Inserta datos de ejemplo en SQL Server.

**Parámetros:**
- `pool`: Pool de conexiones a SQL Server

**Características:**
- Verifica si ya hay datos antes de insertar
- Usa parámetros preparados para seguridad

---

### scripts/check_new_vehicles.js

Este script proporciona una herramienta de línea de comandos para consultar y analizar el estado de la base de datos. Es útil para monitoreo, debugging, y para obtener información rápida sobre los vehículos registrados y las detecciones realizadas. El script utiliza consultas optimizadas y paralelas para maximizar la velocidad.

#### Función: `checkVehicles() -> Promise<void>`
Verifica y muestra información sobre vehículos y detecciones en la base de datos. Esta función es asíncrona y debe ser esperada. Proporciona una vista completa del estado del sistema, incluyendo estadísticas, listas detalladas, y análisis temporal.

**Proceso detallado:**

1. **Consultas paralelas**: Ejecuta dos consultas en paralelo usando `Promise.all()` para maximizar la eficiencia:
   - Consulta de todos los vehículos ordenados por fecha de creación (más recientes primero)
   - Consulta de las últimas 10 detecciones ordenadas por timestamp (más recientes primero)

   Las consultas paralelas reducen significativamente el tiempo total de ejecución comparado con ejecutarlas secuencialmente.

2. **Análisis de vehículos**: Procesa la lista de vehículos y muestra información detallada de cada uno, incluyendo matrícula, propietario, información del vehículo, y fecha de registro. Si no hay vehículos, muestra un mensaje informativo.

3. **Análisis de detecciones**: Muestra las últimas 10 detecciones con información sobre si el vehículo estaba registrado o no en el momento de la detección. Para cada detección, muestra la matrícula, la fecha, y si se encontró información del propietario.

4. **Identificación de vehículos nuevos**: Calcula qué vehículos fueron registrados en las últimas 24 horas comparando la fecha de creación con la fecha actual. Esto es útil para monitorear la actividad reciente del sistema y identificar nuevos registros.

**Uso:**
```bash
npm run check-vehicles
```

**Salida en consola:**

El script produce una salida formateada y legible en la consola que incluye:

1. **Resumen estadístico**: Número total de vehículos registrados y número total de detecciones. Esto proporciona una vista rápida del tamaño y actividad del sistema.

2. **Lista completa de vehículos**: Para cada vehículo, muestra:
   - Número de matrícula
   - Nombre del propietario
   - ID del propietario (si está disponible)
   - Información del vehículo (marca, modelo, año, color)
   - Fecha y hora de registro formateada en español

3. **Últimas 10 detecciones**: Para cada detección, muestra:
   - Número de matrícula detectada
   - Estado (Registrado o No registrado)
   - Fecha y hora de la detección
   - Nombre del propietario (si el vehículo está registrado)

4. **Vehículos nuevos (últimas 24 horas)**: Lista especial de vehículos registrados en el último día, con:
   - Matrícula y propietario
   - Fecha y hora exacta de registro

**Manejo de errores**: Si hay un error al consultar la base de datos, el script muestra un mensaje de error descriptivo con sugerencias sobre qué verificar (servidor corriendo, configuración correcta, etc.) y termina con código de salida 1 para indicar fallo.

**Cierre de conexiones**: Al finalizar, el script cierra todas las conexiones a la base de datos para liberar recursos y permitir que el proceso termine limpiamente.

---

## Clases Principales

Las clases principales encapsulan la funcionalidad core del sistema. Cada clase tiene responsabilidades específicas y está diseñada para ser reutilizable y extensible.

### LicensePlateDetector (ml/detect.py)
Clase principal para detección básica de matrículas. Esta clase proporciona la funcionalidad fundamental de detección y reconocimiento de matrículas. Está diseñada para ser simple de usar pero robusta internamente, implementando múltiples estrategias de fallback para maximizar las posibilidades de éxito. La clase utiliza EasyOCR como motor de OCR, que es una biblioteca de código abierto que puede reconocer texto en múltiples idiomas sin necesidad de entrenamiento adicional.

**Características principales:**
- Inicialización simple con configuración optimizada
- Sistema de múltiples estrategias de detección
- Validación robusta de resultados
- Manejo de errores completo

**Métodos principales:**
- `detect_and_recognize()`: Método principal que implementa detección con múltiples estrategias. Prueba diferentes enfoques (detección de región, procesamiento completo, OCR directo, rotaciones) hasta encontrar la matrícula o agotar todas las opciones.
- `detect_from_array()`: Permite detectar matrículas desde arrays numpy, lo que es útil para procesamiento de video en tiempo real o para integración con otros sistemas de visión por computadora.
- `_extract_plate_number_from_results()`: Implementa el sistema de filtrado y scoring que identifica el texto más probable que sea una matrícula entre todos los textos detectados por OCR.

---

### EnhancedLicensePlateDetector (ml/detect_enhanced.py)
Clase para detección con diagnóstico detallado. Esta clase extiende la funcionalidad básica agregando capacidades completas de diagnóstico y análisis. Es especialmente útil para debugging, optimización del proceso de captura, y para entender por qué una detección falla. El sistema de diagnóstico rastrea cada paso del proceso, registra métricas de calidad de imagen, y genera recomendaciones específicas basadas en los resultados.

**Características principales:**
- Sistema completo de diagnóstico que rastrea cada estrategia probada
- Análisis de calidad de imagen (resolución, contraste, brillo)
- Generación automática de recomendaciones
- Modo debug para información detallada en consola

**Métodos principales:**
- `detect_with_diagnosis()`: Implementa el mismo sistema de múltiples estrategias que la clase básica, pero además registra información detallada sobre cada paso. Retorna un diccionario completo con el resultado de la detección y un objeto de diagnóstico que incluye todas las estrategias probadas, advertencias, errores, y recomendaciones.
- `_validate_image_quality()`: Analiza la imagen antes del procesamiento para identificar problemas potenciales que puedan afectar la detección. Calcula métricas estadísticas (desviación estándar para contraste, media para brillo) y genera advertencias específicas si la calidad es subóptima.
- `_generate_recommendations()`: Analiza los resultados del diagnóstico y genera recomendaciones específicas y accionables. Las recomendaciones se basan en los problemas identificados (baja resolución, bajo contraste, etc.) y proporcionan sugerencias concretas sobre cómo mejorar la imagen para obtener mejores resultados.

---

### DetectorDeMultiplesMatriculas (ml/multi_plate_detector.py)
Clase para detectar múltiples matrículas en una sola imagen. Esta clase implementa un sistema especializado que puede identificar y procesar múltiples matrículas simultáneamente en una imagen. Utiliza técnicas avanzadas de visión por computadora para encontrar todas las regiones candidatas, y luego procesa cada región independientemente con OCR. El sistema está optimizado para velocidad, limitando el número de regiones procesadas y utilizando algoritmos eficientes de detección.

**Características principales:**
- Detección de múltiples regiones candidatas usando algoritmos de visión por computadora
- Procesamiento paralelo de regiones (conceptualmente)
- Sistema de filtrado y validación robusto
- Soporte para múltiples motores OCR (EasyOCR y Pytesseract)
- Pipeline completo de ANPR (Automatic Number Plate Recognition)

**Métodos principales:**
- `detectar_todas_las_matriculas()`: Método principal que orquesta todo el proceso. Carga la imagen, encuentra todas las regiones candidatas, procesa cada una, y retorna una lista de todas las matrículas válidas encontradas con sus niveles de confianza.
- `_encontrar_regiones_matricula()`: Implementa algoritmos de visión por computadora para encontrar regiones rectangulares que podrían contener matrículas. Utiliza detección de contornos, análisis de formas, y filtrado por relación de aspecto y tamaño. El método está optimizado para procesar imágenes grandes eficientemente.
- `_procesar_region_matricula()`: Procesa una región individual para extraer el texto de la matrícula. Intenta primero con Pytesseract usando un pipeline completo de ANPR, y si no está disponible o no detecta nada, usa EasyOCR como fallback. Valida que el texto detectado sea una matrícula válida antes de retornarlo.
- `tu_funcion_de_detectar_placas()`: Implementa un pipeline completo de ANPR (Automatic Number Plate Recognition) que incluye pre-procesamiento avanzado, detección y aislamiento de la placa, corrección de perspectiva, binarización adaptativa, y OCR optimizado. Este método es especialmente efectivo para imágenes donde la matrícula está claramente visible pero puede estar en un ángulo.

---

### VehicleLinkingSystem (utils/linking.js)
Sistema de vinculación de matrículas con propietarios. Esta clase es el núcleo del sistema de gestión de vehículos, proporcionando todas las funciones necesarias para buscar, registrar, y gestionar información de vehículos y sus detecciones. Implementa múltiples optimizaciones de rendimiento, incluyendo caché en memoria, consultas optimizadas con índices, y búsquedas flexibles que permiten encontrar vehículos incluso con variaciones menores en el formato de la matrícula.

**Características principales:**
- Sistema de caché en memoria con TTL configurable
- Búsquedas optimizadas con múltiples niveles de fallback
- Normalización automática de matrículas
- Registro automático de detecciones
- Gestión de historial de detecciones

**Métodos principales:**
- `findVehicleByPlate()`: Implementa un sistema de búsqueda de múltiples niveles que primero verifica el caché, luego intenta búsqueda exacta, y finalmente búsqueda flexible. Utiliza índices de base de datos para máxima velocidad y almacena resultados en caché para consultas repetidas.
- `recordDetection()`: Registra automáticamente cada detección en la base de datos, vinculándola con el vehículo si existe. Utiliza la cláusula OUTPUT de SQL Server para obtener el ID generado en una sola operación, mejorando el rendimiento.
- `getDetectionHistory()`: Proporciona acceso al historial completo de detecciones para una matrícula específica. Utiliza consultas optimizadas con TOP y ORDER BY para retornar solo las detecciones más recientes de manera eficiente.
- `normalizePlateNumber()`: Normaliza matrículas a un formato estándar, asegurando consistencia en toda la base de datos. Esta función es crucial para la integridad de los datos y permite búsquedas flexibles que ignoran diferencias menores en formato.

---

## Ejemplos de Uso

Los siguientes ejemplos muestran cómo utilizar las diferentes funciones y endpoints del sistema en situaciones prácticas. Cada ejemplo incluye código completo que puede ser copiado y adaptado para necesidades específicas.

### Detectar una matrícula (JavaScript)

Este ejemplo muestra cómo detectar una matrícula desde una aplicación web o móvil. El código crea un objeto FormData con la imagen capturada y la envía al servidor. El servidor procesa la imagen, detecta la matrícula, busca información del vehículo en la base de datos, y retorna toda la información en una sola respuesta.

```javascript
// Obtener el archivo de imagen desde un input file o desde la cámara
const imageFile = document.getElementById('imageInput').files[0];

// Crear FormData para enviar la imagen
const formData = new FormData();
formData.append('image', imageFile);

// Opcional: solicitar diagnóstico detallado
formData.append('diagnosis', 'true');

// Opcional: agregar ubicación donde se detectó
formData.append('location', 'Entrada principal - Estacionamiento');

// Enviar petición al servidor
const response = await fetch('http://localhost:3000/api/detect', {
  method: 'POST',
  body: formData
});

// Procesar la respuesta
const data = await response.json();

if (data.success) {
  console.log('Matrícula detectada:', data.plate_number);
  
  if (data.vehicle) {
    console.log('Vehículo encontrado:', data.vehicle.owner_name);
    console.log('Información completa:', data.vehicle);
  } else {
    console.log('Vehículo no registrado. Puede registrarse usando POST /api/vehicle');
  }
  
  // Si se solicitó diagnóstico, mostrar información detallada
  if (data.diagnosis) {
    console.log('Diagnóstico:', data.diagnosis);
    console.log('Estrategias probadas:', data.diagnosis.strategies_tried);
    console.log('Recomendaciones:', data.diagnosis.recommendations);
  }
} else {
  console.error('Error:', data.message);
  // Si hay diagnóstico, puede ayudar a entender por qué falló
  if (data.diagnosis) {
    console.error('Razones del fallo:', data.diagnosis.errors);
  }
}
```

---

### Detectar con diagnóstico (Python)

Este ejemplo muestra cómo usar el detector mejorado con diagnóstico desde un script Python. El diagnóstico proporciona información detallada sobre el proceso de detección, lo que es especialmente útil cuando una detección falla y necesitas entender por qué. El modo debug muestra información adicional en la consola durante el procesamiento.

```python
from ml.detect_enhanced import detect_with_diagnosis

# Detectar con diagnóstico detallado
result = detect_with_diagnosis('imagen.jpg', debug=True)

if result['success']:
    print(f"Matrícula detectada: {result['plate_number']}")
    print(f"Éxito en estrategia: {result['diagnosis']['strategies_tried'][-1]['name']}")
else:
    print("No se pudo detectar la matrícula")
    print("\n=== DIAGNÓSTICO DETALLADO ===")
    
    # Información de la imagen
    if result['diagnosis']['image_info']:
        img_info = result['diagnosis']['image_info']
        print(f"Resolución: {img_info['width']}x{img_info['height']}")
        print(f"Canales: {img_info['channels']}")
        print(f"Relación de aspecto: {img_info['aspect_ratio']:.2f}")
    
    # Advertencias
    if result['diagnosis']['warnings']:
        print("\nAdvertencias:")
        for warning in result['diagnosis']['warnings']:
            print(f"  - {warning}")
    
    # Estrategias probadas
    if result['diagnosis']['strategies_tried']:
        print("\nEstrategias probadas:")
        for strategy in result['diagnosis']['strategies_tried']:
            status = "OK" if strategy['status'] == 'success' else "Fallo"
            print(f"  [{status}] {strategy['name']}")
            if strategy['status'] == 'failed' and 'reason' in strategy:
                print(f"    Razón: {strategy['reason']}")
    
    # Recomendaciones
    if result['diagnosis']['recommendations']:
        print("\nRecomendaciones:")
        for rec in result['diagnosis']['recommendations']:
            print(f"  - {rec}")
    
    # Resultados de OCR (útil para debugging)
    if result['diagnosis']['ocr_results']:
        print("\nResultados de OCR:")
        for ocr_result in result['diagnosis']['ocr_results']:
            print(f"  Estrategia: {ocr_result['strategy']}")
            for item in ocr_result['results'][:3]:  # Mostrar solo los primeros 3
                if len(item) >= 2:
                    text = item[1]
                    conf = item[2] if len(item) > 2 else 0
                    print(f"    - '{text}' (confianza: {conf:.2f})")
```

---

### Registrar un vehículo (JavaScript)

Este ejemplo muestra cómo registrar un nuevo vehículo en la base de datos. El sistema valida que la matrícula no esté duplicada y normaliza automáticamente la matrícula antes de almacenarla. Solo los campos `plate_number` y `owner_name` son requeridos; todos los demás son opcionales y pueden completarse posteriormente.

```javascript
// Preparar los datos del vehículo
const vehicleData = {
  plate_number: 'VPM-45-32',        // Requerido: Matrícula del vehículo
  owner_name: 'Juan Pérez',         // Requerido: Nombre del propietario
  owner_id: '12345678',             // Opcional: ID o documento del propietario
  vehicle_make: 'Toyota',           // Opcional: Marca del vehículo
  vehicle_model: 'Corolla',         // Opcional: Modelo del vehículo
  vehicle_year: 2020,               // Opcional: Año del vehículo
  vehicle_color: 'Blanco',          // Opcional: Color del vehículo
  registration_date: '2020-01-15'   // Opcional: Fecha de registro (formato YYYY-MM-DD)
};

// Enviar petición al servidor
const response = await fetch('http://localhost:3000/api/vehicle', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(vehicleData)
});

// Procesar la respuesta
const data = await response.json();

if (data.success) {
  console.log('Vehículo registrado exitosamente');
  console.log('ID del vehículo:', data.vehicle.id);
  console.log('Matrícula normalizada:', data.vehicle.plate_number);
  console.log('Información completa:', data.vehicle);
} else {
  // Manejar errores
  if (response.status === 409) {
    console.error('Error: Ya existe un vehículo con esa matrícula');
    console.log('Vehículo existente:', data.vehicle);
  } else {
    console.error('Error al registrar vehículo:', data.error);
    console.error('Mensaje:', data.message);
  }
}
```

---

### Consultar vehículo (JavaScript)

Este ejemplo muestra cómo consultar información de un vehículo y su historial de detecciones. La consulta utiliza el sistema de búsqueda optimizado que primero verifica el caché, luego intenta búsqueda exacta, y finalmente búsqueda flexible. El historial incluye las últimas 5 detecciones ordenadas por fecha descendente.

```javascript
// Matrícula a consultar (puede estar en cualquier formato, el sistema la normaliza)
const plate = 'VPM-45-32';

// Realizar la consulta
const response = await fetch(`http://localhost:3000/api/vehicle/${encodeURIComponent(plate)}`);
const data = await response.json();

if (data.success) {
  console.log('=== INFORMACIÓN DEL VEHÍCULO ===');
  console.log('Matrícula:', data.vehicle.plate_number);
  console.log('Propietario:', data.vehicle.owner_name);
  console.log('ID Propietario:', data.vehicle.owner_id || 'No especificado');
  console.log('Vehículo:', `${data.vehicle.vehicle_make || 'N/A'} ${data.vehicle.vehicle_model || ''}`.trim());
  console.log('Año:', data.vehicle.vehicle_year || 'No especificado');
  console.log('Color:', data.vehicle.vehicle_color || 'No especificado');
  console.log('Fecha de registro:', data.vehicle.registration_date || 'No especificada');
  console.log('Registrado el:', new Date(data.vehicle.created_at).toLocaleString());
  console.log('Última actualización:', new Date(data.vehicle.updated_at).toLocaleString());
  
  // Historial de detecciones
  if (data.detection_history && data.detection_history.length > 0) {
    console.log('\n=== HISTORIAL DE DETECCIONES ===');
    console.log(`Total de detecciones: ${data.detection_history.length}`);
    data.detection_history.forEach((detection, index) => {
      console.log(`\n${index + 1}. Detección #${detection.id}`);
      console.log(`   Fecha: ${new Date(detection.detection_timestamp).toLocaleString()}`);
      console.log(`   Ubicación: ${detection.location || 'No especificada'}`);
      console.log(`   Confianza: ${detection.confidence_score ? (detection.confidence_score * 100).toFixed(1) + '%' : 'No disponible'}`);
      if (detection.image_path) {
        console.log(`   Imagen: ${detection.image_path}`);
      }
    });
  } else {
    console.log('\nNo hay historial de detecciones para este vehículo');
  }
} else {
  console.error('Vehículo no encontrado');
  console.error('Error:', data.error);
  console.error('Mensaje:', data.message);
}
```

---

### Detectar múltiples matrículas (Python)

Este ejemplo muestra cómo usar el detector de múltiples matrículas para encontrar todas las matrículas en una imagen. Este es especialmente útil para escenarios como estacionamientos, fotos de tráfico, o cualquier situación donde una imagen puede contener varios vehículos. El detector utiliza algoritmos avanzados de visión por computadora para identificar todas las regiones candidatas y luego procesa cada una independientemente.

```python
from ml.multi_plate_detector import DetectorDeMultiplesMatriculas
import json

# Crear instancia del detector
detector = DetectorDeMultiplesMatriculas()

# Detectar todas las matrículas en la imagen
resultado = detector.detectar_todas_las_matriculas('imagen.jpg')

# Verificar si la detección fue exitosa
if resultado['success']:
    print(f"Se encontraron {resultado['total_found']} matrículas:\n")
    
    # Procesar cada matrícula detectada
    for i, plate in enumerate(resultado['plates'], 1):
        print(f"Matrícula {i}:")
        print(f"  Número: {plate['plate_number']}")
        print(f"  Confianza: {plate['confidence']:.1%}")
        print(f"  Índice en imagen: {plate['plate_index']}")
        
        # Si hay resultados crudos de OCR, mostrarlos para debugging
        if 'raw_results' in plate and plate['raw_results']:
            print(f"  Resultados OCR: {', '.join(plate['raw_results'][:3])}")
        print()
    
    # Si se necesita el resultado en formato JSON (por ejemplo, para API)
    json_result = json.dumps(resultado, indent=2, ensure_ascii=False)
    print("Resultado en JSON:")
    print(json_result)
else:
    print("No se detectaron matrículas en la imagen")
    if 'error' in resultado:
        print(f"Error: {resultado['error']}")
```

**Casos de uso comunes:**
- Monitoreo de estacionamientos: Detectar todas las matrículas en una foto de un estacionamiento completo
- Control de acceso: Procesar imágenes de entrada/salida con múltiples vehículos
- Análisis de tráfico: Detectar matrículas en fotos de tráfico con varios vehículos visibles
- Auditoría: Revisar imágenes históricas para encontrar todas las matrículas presentes

---

## Notas Técnicas

Esta sección proporciona información detallada sobre las decisiones técnicas, optimizaciones, y consideraciones de diseño del sistema. Esta información es útil para desarrolladores que necesitan entender el sistema en profundidad, hacer modificaciones, o integrar el sistema con otras aplicaciones.

### Optimizaciones Implementadas

El sistema implementa múltiples optimizaciones de rendimiento para asegurar tiempos de respuesta rápidos incluso bajo carga. Estas optimizaciones fueron implementadas basándose en análisis de rendimiento y mejores prácticas de la industria.

1. **Caché en memoria**: Las consultas frecuentes se cachean en memoria por 1 minuto (60000ms). Esto es especialmente efectivo para búsquedas repetidas de la misma matrícula, que son comunes cuando se procesan múltiples imágenes del mismo vehículo en corto tiempo. El caché reduce el tiempo de respuesta de consultas repetidas de milisegundos a microsegundos. El sistema también cachea resultados negativos (matrículas que no existen) para evitar búsquedas repetidas innecesarias. La limpieza automática del caché cada 30 segundos previene fugas de memoria.

2. **Connection pooling**: El sistema utiliza un pool de conexiones que mantiene hasta 20 conexiones simultáneas a SQL Server. Esto permite manejar múltiples peticiones concurrentes sin crear nuevas conexiones para cada query, lo que es costoso en términos de tiempo y recursos. El pool reutiliza conexiones existentes, reduciendo significativamente la latencia de las queries. Las conexiones inactivas se cierran automáticamente después de 30 segundos para liberar recursos.

3. **Índices optimizados**: Las tablas tienen índices estratégicamente colocados en las columnas más consultadas (`plate_number`, `plate_normalized`, `detection_timestamp`). Los índices permiten que SQL Server encuentre registros sin escanear toda la tabla, reduciendo el tiempo de búsqueda de milisegundos a microsegundos en tablas grandes. Las búsquedas con índices son típicamente 10-20 veces más rápidas que búsquedas sin índices en tablas con miles de registros.

4. **Consultas paralelas**: Donde es posible, el sistema ejecuta múltiples consultas en paralelo usando `Promise.all()`. Por ejemplo, cuando se consulta información de vehículos y detecciones, ambas consultas se ejecutan simultáneamente en lugar de secuencialmente, reduciendo el tiempo total a aproximadamente el tiempo de la consulta más lenta en lugar de la suma de ambas.

5. **OUTPUT clause**: Para operaciones de inserción y actualización, el sistema utiliza la cláusula `OUTPUT INSERTED.*` de SQL Server. Esto permite obtener el registro insertado o actualizado en una sola operación, evitando la necesidad de una query adicional para recuperar el ID generado o los datos actualizados. Esto reduce el número de round-trips a la base de datos y mejora el rendimiento.

6. **Paginación eficiente**: Las consultas de listado utilizan `OFFSET` y `FETCH NEXT` de SQL Server para realizar la paginación a nivel de base de datos. Esto es más eficiente que cargar todos los registros y paginar en memoria, especialmente para tablas grandes. La paginación a nivel de base de datos reduce el uso de memoria y el ancho de banda de red.

7. **Límites de procesamiento**: En detección múltiple, el sistema limita el número de regiones y contornos procesados para mantener tiempos de respuesta razonables. Esto balancea precisión y velocidad, procesando las regiones más prometedoras primero.

8. **Redimensionamiento inteligente**: Las imágenes muy grandes se redimensionan automáticamente antes del procesamiento para acelerar la detección de regiones sin perder demasiada información. Las imágenes muy pequeñas se amplían para mejorar la calidad del OCR.

### Formatos de Matrícula Soportados

El sistema está optimizado para matrículas mexicanas, que generalmente siguen un patrón de letras seguidas de números, con o sin guiones. El sistema puede reconocer y normalizar múltiples variaciones de formato, lo que permite flexibilidad en cómo se ingresan o detectan las matrículas.

**Formatos reconocidos:**
- `VPM-45-32` (formato estándar con guiones): Este es el formato más común y preferido. Los guiones mejoran la legibilidad y el sistema los prioriza en el scoring.
- `VPM45-32` (sin guión entre letras y números): Variación común donde solo hay guión entre los grupos de números.
- `VPM-4532` (sin guión entre números): Variación donde solo hay guión después de las letras.
- `VPM4532` (sin guiones): Formato compacto sin guiones. El sistema puede reconocerlo pero prioriza formatos con guiones.

**Normalización automática:**
Independientemente del formato en que se detecte o ingrese una matrícula, el sistema la normaliza automáticamente antes de almacenarla o buscarla. La normalización:
- Convierte a mayúsculas
- Elimina espacios extra
- Elimina caracteres especiales excepto guiones
- Mantiene la estructura básica (letras-números)

**Búsqueda flexible:**
El sistema puede encontrar vehículos incluso si la matrícula se busca con un formato ligeramente diferente al almacenado. Por ejemplo, si un vehículo está registrado como "VPM-45-32", se puede encontrar buscando "VPM4532" o "vpm 45 32". Esto se logra mediante la columna `plate_normalized` que almacena la matrícula sin guiones ni espacios para búsquedas flexibles.

**Validación de formato:**
El sistema valida que las matrículas detectadas o ingresadas tengan un formato razonable antes de aceptarlas. Las validaciones incluyen:
- Debe tener al menos 5 caracteres (sin contar guiones)
- Debe tener letras Y números (no solo letras o solo números)
- No debe ser una palabra descriptiva conocida (SINALOA, MEXICO, etc.)
- Debe coincidir con patrones de matrícula mexicana o tener estructura similar

### Dependencias Principales

El sistema utiliza varias bibliotecas y frameworks que proporcionan funcionalidades específicas. Cada dependencia fue elegida por su robustez, rendimiento, y compatibilidad con los requisitos del sistema.

**Python:**

- **opencv-python**: Biblioteca fundamental para procesamiento de imágenes. Proporciona funciones para cargar, procesar, y analizar imágenes. Se utiliza para detección de regiones (contornos, análisis de formas), preprocesamiento (filtros, mejora de contraste, binarización), y transformaciones (rotación, redimensionamiento). OpenCV es una de las bibliotecas más maduras y optimizadas para visión por computadora.

- **numpy**: Biblioteca esencial para operaciones numéricas y manejo de arrays multidimensionales. Todas las imágenes se representan como arrays numpy, y numpy proporciona funciones eficientes para operaciones matemáticas sobre estos arrays. Es fundamental para el procesamiento de imágenes y cálculos estadísticos (como media y desviación estándar para análisis de calidad).

- **easyocr**: Motor de OCR (Reconocimiento Óptico de Caracteres) de código abierto que puede reconocer texto en múltiples idiomas. Es el motor principal utilizado para extraer texto de las imágenes de matrículas. EasyOCR es especialmente bueno para texto en imágenes naturales y no requiere entrenamiento adicional. La primera vez que se usa, descarga modelos pre-entrenados automáticamente.

- **pytesseract**: Wrapper de Python para Tesseract OCR, un motor OCR alternativo desarrollado por Google. Se utiliza como fallback en el detector de múltiples matrículas cuando está disponible. Tesseract es especialmente bueno para texto bien formateado y puede complementar a EasyOCR en ciertos casos. Es opcional pero recomendado para mejor cobertura.

**Node.js:**

- **express**: Framework web minimalista y flexible para Node.js. Proporciona la infraestructura para crear el servidor HTTP, manejar rutas, middleware, y respuestas. Express es el framework más popular para Node.js y tiene un ecosistema extenso de middleware y extensiones.

- **mssql**: Cliente oficial de Microsoft para SQL Server en Node.js. Proporciona todas las funciones necesarias para conectarse a SQL Server, ejecutar queries, manejar transacciones, y utilizar connection pooling. El paquete maneja automáticamente la conversión de tipos de datos y proporciona una API moderna basada en Promises.

- **multer**: Middleware para Express que maneja la subida de archivos multipart/form-data. Se utiliza para recibir las imágenes desde los clientes. Multer valida tipos de archivo, limita el tamaño de archivos, y proporciona información sobre los archivos subidos. Está configurado para aceptar solo archivos de imagen y limitar el tamaño a 10MB.

- **cors**: Middleware que permite Cross-Origin Resource Sharing (CORS). Es necesario cuando el cliente web se ejecuta en un dominio diferente al servidor, o cuando se accede desde aplicaciones móviles. CORS permite que el navegador haga peticiones al servidor desde diferentes orígenes de manera segura.

- **dotenv**: Módulo que carga variables de entorno desde un archivo `.env`. Permite configurar el sistema (credenciales de base de datos, puerto del servidor, etc.) sin modificar el código. Esto es esencial para seguridad (no hardcodear credenciales) y para diferentes entornos (desarrollo, producción).

**Otras dependencias:**
- **better-sqlite3** (solo para SQLite): Cliente SQLite de alto rendimiento utilizado en el script de configuración de SQLite. Proporciona una API síncrona simple para operaciones de base de datos en SQLite.

---

## Flujo de Procesamiento

Para entender mejor cómo funciona el sistema, aquí se describe el flujo completo desde que se captura una imagen hasta que se retorna el resultado:

### Flujo de Detección de Matrícula

Este flujo describe paso a paso cómo el sistema procesa una imagen desde que el usuario la captura hasta que recibe la respuesta con la matrícula detectada y la información del vehículo.

1. **Captura de Imagen**: El usuario captura una imagen desde la cámara del dispositivo móvil o la selecciona de la galería. La aplicación web convierte la imagen a un formato que puede enviarse al servidor (generalmente un objeto File o Blob). La imagen se incluye en un objeto FormData que se envía mediante una petición POST HTTP al endpoint `/api/detect`. El FormData permite enviar archivos binarios de manera eficiente a través de HTTP.

2. **Recepción en el Servidor**: El servidor Express.js recibe la petición HTTP. El middleware Multer intercepta la petición, valida que el archivo sea una imagen válida (verificando el tipo MIME y la extensión), verifica que el tamaño no exceda 10MB, y guarda la imagen en el directorio `./uploads` con un nombre único generado combinando un timestamp (milisegundos desde epoch) y un número aleatorio. Esto previene colisiones de nombres y permite identificar fácilmente cuándo se subió cada imagen. El nombre del archivo se genera en formato `plate-{timestamp}-{random}.{extension}`.

3. **Ejecución del Script Python**: El servidor determina qué script Python ejecutar basándose en si se solicitó diagnóstico (`detect_enhanced.py`) o no (`detect.py`). El servidor obtiene el comando de Python correcto usando `pythonHelper.js`, que detecta automáticamente si debe usar `python`, `python3`, o `py` según el sistema operativo. El script Python se ejecuta en un proceso separado usando `child_process.exec()`, pasando la ruta de la imagen como argumento de línea de comandos. Esto es crucial porque permite que el servidor Node.js siga manejando otras peticiones mientras el procesamiento de imágenes ocurre en paralelo. El buffer de salida está configurado a 10MB para manejar imágenes grandes y salidas detalladas de diagnóstico.

4. **Procesamiento de Imagen (Python)**: El script Python ejecuta el siguiente pipeline:
   - **Carga de imagen**: Usa OpenCV para cargar la imagen desde el disco. Valida que el archivo exista, que sea un formato de imagen válido, y que tenga contenido.
   - **Detección de región**: Intenta identificar la región específica de la imagen que contiene la matrícula usando algoritmos de visión por computadora (detección de contornos, análisis de formas rectangulares, filtrado por relación de aspecto). Esto es más eficiente que procesar toda la imagen.
   - **Preprocesamiento**: Si se encuentra una región, se preprocesa específicamente para OCR usando técnicas como CLAHE (mejora de contraste), filtrado bilateral (reducción de ruido), normalización, y umbralización adaptativa. El preprocesamiento es crucial para el éxito del OCR.
   - **Aplicación de OCR**: Se aplica EasyOCR con parámetros optimizados que priorizan texto más grande (como las matrículas) y son más permisivos con el umbral de confianza. El OCR retorna una lista de textos detectados con sus coordenadas y niveles de confianza.
   - **Filtrado y validación**: Los resultados del OCR se filtran para eliminar textos descriptivos conocidos (como "SINALOA", "MEXICO"), textos que son solo números o solo letras, y textos muy cortos. Los textos restantes se validan contra patrones de matrícula mexicana y se calcula un score para cada candidato.
   - **Estrategias alternativas**: Si la primera estrategia (detección de región + OCR) falla, el sistema prueba automáticamente otras estrategias: procesamiento de toda la imagen, OCR directo sin preprocesamiento, y procesamiento con diferentes rotaciones (-10°, -5°, 5°, 10°). Esto maximiza las posibilidades de éxito incluso en condiciones subóptimas.

5. **Retorno del Resultado**: El script Python imprime el resultado en stdout. Si se detectó una matrícula, imprime "Matrícula detectada: {plate_number}". Si se solicitó diagnóstico, imprime un objeto JSON completo con toda la información del diagnóstico. El servidor Node.js captura esta salida usando `execAsync()` y la parsea. Para diagnóstico, busca la línea que contiene el JSON y la parsea. Para detección básica, busca el patrón "Matrícula detectada:" y extrae la matrícula.

6. **Búsqueda en Base de Datos**: Si se detectó una matrícula, el servidor busca automáticamente información del vehículo en la base de datos. Esto se hace usando `VehicleLinkingSystem.findVehicleByPlate()`, que primero verifica el caché en memoria (respuesta instantánea si la matrícula se consultó recientemente), luego intenta búsqueda exacta, y finalmente búsqueda flexible si es necesario. La búsqueda utiliza índices optimizados para máxima velocidad.

7. **Registro de Detección**: Independientemente de si se encontró el vehículo o no, el sistema registra la detección en la tabla `detections` usando `VehicleLinkingSystem.recordDetection()`. Esto crea un historial completo de todas las detecciones, incluyendo la matrícula detectada, el ID del vehículo (si se encontró), la ruta de la imagen, el nivel de confianza del OCR, la ubicación (si se proporcionó), y el timestamp exacto. Este historial es útil para análisis, auditoría, y para rastrear patrones de uso.

8. **Respuesta al Cliente**: El servidor construye una respuesta JSON completa que incluye:
   - `success`: Indica si la detección fue exitosa
   - `plate_number`: La matrícula detectada (normalizada)
   - `vehicle`: Información completa del vehículo si se encontró, o `null` si no está registrado
   - `message`: Mensaje descriptivo del resultado
   - `image_path`: Ruta donde se almacenó la imagen en el servidor
   - `detection_timestamp`: Fecha y hora exacta de la detección en formato ISO 8601
   - `diagnosis`: Información detallada del proceso (solo si se solicitó)

La respuesta se envía al cliente con el código de estado HTTP apropiado (200 para éxito, 400 para errores de validación, 500 para errores del servidor).

### Flujo de Registro de Vehículo

Este flujo describe cómo se registra un nuevo vehículo en el sistema, desde que el usuario completa el formulario hasta que el vehículo está disponible para búsquedas.

1. **Solicitud del Cliente**: El cliente (aplicación web, aplicación móvil, o cualquier cliente HTTP) envía una petición POST al endpoint `/api/vehicle` con los datos del vehículo en formato JSON en el body de la petición. El cliente puede obtener estos datos de un formulario web, de una aplicación móvil, o de otro sistema que se integre con la API. Los datos incluyen información básica del vehículo y del propietario.

2. **Validación de Datos**: El servidor valida que los campos requeridos estén presentes y tengan valores válidos. Los campos requeridos son `plate_number` (matrícula) y `owner_name` (nombre del propietario). Si faltan campos requeridos, el servidor retorna un error 400 (Bad Request) con un mensaje descriptivo indicando qué campos faltan. Esta validación temprana evita procesamiento innecesario y proporciona feedback inmediato al usuario.

3. **Normalización de Matrícula**: La matrícula se normaliza usando `VehicleLinkingSystem.normalizePlateNumber()`, que convierte a mayúsculas, elimina espacios extra, y elimina caracteres especiales excepto guiones. Esta normalización es crucial para la consistencia de los datos y permite búsquedas flexibles más adelante. Por ejemplo, "vpm-45-32", "VPM 45 32", y "vpm@45#32" se normalizan todos a "VPM-45-32".

4. **Verificación de Duplicados**: El sistema busca si ya existe un vehículo con la matrícula normalizada usando `findVehicleByPlate()`. Esta búsqueda utiliza el caché y los índices optimizados para ser muy rápida. Si se encuentra un vehículo existente, el servidor retorna un error 409 (Conflict) con un mensaje descriptivo y la información del vehículo existente. Esto previene duplicados y permite al cliente saber que el vehículo ya está registrado. El código 409 es el estándar HTTP para conflictos de recursos.

5. **Inserción en Base de Datos**: Si no hay duplicados, el sistema inserta el nuevo vehículo en la base de datos. La inserción utiliza una query SQL optimizada con la cláusula `OUTPUT INSERTED.*` de SQL Server, que permite obtener el vehículo insertado completo (incluyendo el ID generado automáticamente, timestamps, y la matrícula normalizada) en una sola operación. Esto es más eficiente que insertar y luego hacer una query adicional para obtener el registro insertado. La query utiliza parámetros preparados para prevenir inyección SQL y para optimizar el rendimiento.

6. **Generación de Timestamps**: SQL Server genera automáticamente los timestamps `created_at` y `updated_at` usando valores por defecto (`CURRENT_TIMESTAMP`). Estos timestamps permiten rastrear cuándo se registró el vehículo y cuándo se actualizó por última vez.

7. **Respuesta al Cliente**: El servidor retorna una respuesta HTTP 201 (Created) con un objeto JSON que incluye:
   - `success`: `true` indicando que la operación fue exitosa
   - `message`: Mensaje descriptivo confirmando el registro
   - `vehicle`: Objeto completo con toda la información del vehículo insertado, incluyendo el ID generado, timestamps, y la matrícula normalizada

El código 201 es el estándar HTTP para recursos creados exitosamente. El vehículo ahora está disponible inmediatamente para búsquedas y se cachea automáticamente para consultas futuras.

### Optimizaciones del Sistema

El sistema implementa múltiples optimizaciones de rendimiento que fueron diseñadas y probadas para maximizar la velocidad y eficiencia. Estas optimizaciones trabajan juntas para proporcionar tiempos de respuesta rápidos incluso bajo carga.

1. **Connection Pooling**: El sistema utiliza un pool de conexiones que mantiene un conjunto de conexiones a SQL Server abiertas y listas para usar. Cuando se necesita ejecutar una query, el sistema toma una conexión del pool en lugar de crear una nueva. Esto elimina el overhead de establecer una nueva conexión TCP, autenticarse, y negociar parámetros, que puede tomar cientos de milisegundos. El pool mantiene hasta 20 conexiones simultáneas, permitiendo manejar múltiples peticiones concurrentes eficientemente. Las conexiones inactivas se cierran automáticamente después de 30 segundos para liberar recursos cuando no hay actividad.

2. **Caché en Memoria**: El sistema implementa un caché en memoria con TTL (Time To Live) de 1 minuto para las búsquedas de vehículos. Cuando se busca una matrícula, el sistema primero verifica el caché. Si el resultado está en el caché y no ha expirado, se retorna inmediatamente sin consultar la base de datos, proporcionando respuestas en microsegundos en lugar de milisegundos. El caché también almacena resultados negativos (matrículas que no existen) para evitar búsquedas repetidas innecesarias. La limpieza automática del caché cada 30 segundos previene fugas de memoria y asegura que los datos no se vuelvan demasiado obsoletos.

3. **Índices de Base de Datos**: Las tablas tienen índices estratégicamente colocados en las columnas más consultadas. Un índice es una estructura de datos que permite a la base de datos encontrar registros sin escanear toda la tabla. El índice en `plate_number` permite búsquedas exactas en tiempo constante O(log n) en lugar de tiempo lineal O(n). El índice en `plate_normalized` permite búsquedas flexibles rápidas. El índice en `detection_timestamp` acelera las consultas de historial ordenadas por fecha. Estos índices pueden acelerar las búsquedas 10-20 veces en tablas con miles de registros.

4. **Consultas Optimizadas**: El sistema utiliza varias técnicas de optimización de queries:
   - **TOP**: Limita el número de registros retornados a nivel de base de datos, evitando transferir datos innecesarios por la red.
   - **OUTPUT clause**: Permite obtener datos insertados o actualizados en la misma operación, eliminando la necesidad de queries adicionales.
   - **OFFSET/FETCH**: Realiza paginación a nivel de base de datos, que es más eficiente que cargar todos los registros y paginar en memoria.
   - **Parámetros preparados**: Las queries usan parámetros preparados que SQL Server puede cachear y reutilizar, mejorando el rendimiento de queries repetidas.

5. **Procesamiento Asíncrono**: Todas las operaciones de base de datos y procesamiento de imágenes son asíncronas (usando Promises y async/await). Esto permite que el servidor Node.js maneje múltiples peticiones concurrentemente sin bloquear. Mientras una petición espera una respuesta de la base de datos, el servidor puede procesar otras peticiones. Esto es especialmente importante para operaciones de OCR que pueden tardar varios segundos, permitiendo que el servidor siga respondiendo a otras peticiones durante ese tiempo.

6. **Límites de Procesamiento**: En detección múltiple, el sistema limita el número de regiones candidatas procesadas (máximo 8) y el número de contornos analizados (máximo 50). Esto balancea precisión y velocidad, procesando las regiones más prometedoras primero y evitando procesar regiones poco probables que consumirían tiempo sin aportar valor. Los límites fueron determinados empíricamente para proporcionar un buen balance entre cobertura y velocidad.

7. **Redimensionamiento Inteligente**: Las imágenes muy grandes (más de 1200px en cualquier dimensión) se redimensionan automáticamente antes del procesamiento para acelerar la detección de regiones sin perder información crítica. Las imágenes muy pequeñas se amplían para mejorar la calidad del OCR. Esto reduce el tiempo de procesamiento mientras mantiene la precisión.

8. **Ejecución de Scripts en Procesos Separados**: Los scripts Python se ejecutan en procesos separados del servidor Node.js. Esto permite que el procesamiento de imágenes (que puede tardar varios segundos) no bloquee el event loop de Node.js, permitiendo que el servidor siga manejando otras peticiones. El buffer de salida está configurado a 10MB para manejar imágenes grandes y salidas detalladas de diagnóstico.

## Consideraciones de Seguridad

La seguridad es una consideración importante en el diseño del sistema. Se implementan múltiples capas de protección para prevenir vulnerabilidades comunes y proteger los datos.

1. **Prepared Statements**: Todas las queries a la base de datos usan parámetros preparados en lugar de concatenar valores directamente en las queries SQL. Esto previene completamente la inyección SQL, que es una de las vulnerabilidades más comunes en aplicaciones web. Los parámetros se pasan separadamente y la base de datos los trata como datos, no como código SQL ejecutable. Por ejemplo, en lugar de `SELECT * FROM vehicles WHERE plate_number = '${plate}'` (vulnerable), se usa `SELECT * FROM vehicles WHERE plate_number = @p1` con el valor pasado como parámetro.

2. **Validación de Archivos**: Multer valida exhaustivamente los archivos subidos antes de aceptarlos. Verifica el tipo MIME (que debe ser un tipo de imagen válido) y la extensión del archivo (debe ser .jpg, .jpeg, .png, .gif, .bmp, o .webp). Esto previene la subida de archivos maliciosos que podrían ser scripts ejecutables disfrazados como imágenes. Solo se aceptan formatos de imagen conocidos y seguros.

3. **Límite de Tamaño**: Las imágenes están limitadas a 10MB para prevenir ataques de denegación de servicio (DoS). Sin este límite, un atacante podría subir archivos extremadamente grandes que consumirían toda la memoria del servidor o saturarían el ancho de banda. El límite de 10MB es suficiente para imágenes de alta calidad mientras previene abusos. Si se intenta subir un archivo más grande, Multer rechaza la petición inmediatamente con un error descriptivo.

4. **Normalización de Entrada**: Todas las matrículas se normalizan antes de almacenar o buscar en la base de datos. Esto previene problemas donde diferentes formatos de la misma matrícula se traten como diferentes, y también ayuda a prevenir algunos tipos de ataques que intentan usar caracteres especiales o espacios para evadir validaciones. La normalización elimina caracteres potencialmente peligrosos y asegura consistencia.

5. **Manejo de Errores**: Los errores se manejan apropiadamente sin exponer información sensible al cliente. Los mensajes de error son descriptivos para el usuario pero no revelan detalles internos del sistema como rutas de archivos completas, nombres de tablas, o stack traces completos. Los errores internos se registran en el servidor para debugging pero no se envían al cliente. Esto previene que atacantes obtengan información sobre la estructura interna del sistema que podría ser usada para ataques más sofisticados.

6. **Validación de Tipos de Datos**: El sistema valida que los tipos de datos recibidos sean los esperados antes de procesarlos. Por ejemplo, se verifica que los años sean números, que las fechas tengan formato válido, y que los strings no excedan longitudes razonables. Esto previene errores y posibles vulnerabilidades relacionadas con tipos de datos incorrectos.

7. **Sanitización de Rutas**: Las rutas de archivos se construyen de manera segura usando funciones de path de Node.js que previenen directory traversal attacks. Los nombres de archivo generados son únicos y no contienen caracteres especiales que podrían ser interpretados como comandos del sistema operativo.

8. **Timeout en Ejecución de Scripts**: Los scripts Python tienen timeouts configurados para prevenir que scripts maliciosos o con errores bloqueen el servidor indefinidamente. Si un script tarda demasiado, se cancela automáticamente.

## Extensibilidad

El sistema está diseñado con extensibilidad en mente, permitiendo agregar nuevas funcionalidades sin modificar el código core. La arquitectura modular y el uso de patrones de diseño comunes facilitan la extensión.

1. **Nuevos Formatos de Matrícula**: El sistema puede adaptarse fácilmente a otros formatos de matrícula (de otros países, por ejemplo) modificando las expresiones regulares en los archivos Python. Los patrones se definen en listas al inicio de las funciones de extracción, haciendo fácil agregar nuevos patrones. Por ejemplo, para agregar soporte para matrículas europeas, simplemente se agregan nuevas expresiones regulares a la lista `plate_patterns` en `_extract_plate_number_from_results()`. El sistema de scoring priorizará automáticamente los patrones que coincidan.

2. **Nuevos Endpoints**: Se pueden agregar nuevos endpoints creando nuevos archivos en el directorio `routes/` o agregando nuevas rutas a los archivos existentes. Cada endpoint es un middleware de Express independiente, lo que permite agregar funcionalidad sin afectar el código existente. Por ejemplo, se podría agregar un endpoint para exportar datos, generar reportes, o integrar con sistemas externos. Los nuevos endpoints pueden reutilizar las utilidades existentes como `getLinkingSystem()` y `query()`.

3. **Nuevas Estrategias de Detección**: Se pueden agregar nuevas estrategias de detección simplemente agregando código adicional en los métodos `detect_and_recognize()` o `detect_with_diagnosis()`. Las estrategias se prueban secuencialmente hasta que una tenga éxito, por lo que agregar una nueva estrategia es tan simple como agregar un nuevo bloque try/except con la lógica de la estrategia. Por ejemplo, se podría agregar una estrategia que use deep learning para detectar matrículas, o una que use técnicas de procesamiento de imágenes más avanzadas.

4. **Soporte para Otros OCR**: El sistema puede extenderse para usar otros motores OCR además de EasyOCR y Pytesseract. La arquitectura permite fácilmente agregar nuevos motores OCR creando nuevas clases o funciones que implementen la misma interfaz. Por ejemplo, se podría agregar soporte para Google Cloud Vision API, AWS Textract, o cualquier otro servicio de OCR. El sistema ya tiene un ejemplo de esto con el uso de Pytesseract como alternativa a EasyOCR en el detector de múltiples matrículas.

5. **Integración con Otros Sistemas**: La API REST estándar permite fácil integración con otros sistemas mediante peticiones HTTP simples. Cualquier sistema que pueda hacer peticiones HTTP puede integrarse con este sistema. Esto incluye aplicaciones móviles nativas, sistemas de gestión empresarial, sistemas de seguridad, o cualquier otra aplicación que necesite funcionalidad de reconocimiento de matrículas. La API sigue estándares REST comunes, haciendo la integración intuitiva para desarrolladores familiarizados con APIs REST.

6. **Nuevos Tipos de Datos**: Se pueden agregar nuevos campos a las tablas de base de datos y extender los objetos de vehículo sin romper la funcionalidad existente. El sistema está diseñado para ser tolerante a campos adicionales en las respuestas JSON.

7. **Middleware Personalizado**: Express permite agregar middleware personalizado para funcionalidades como autenticación, logging, rate limiting, etc. Esto permite extender el sistema con funcionalidades de seguridad y monitoreo sin modificar el código core.

8. **Plugins de Procesamiento**: El sistema de preprocesamiento está diseñado de manera modular, permitiendo agregar nuevos pasos de procesamiento fácilmente. Por ejemplo, se podría agregar un paso de mejora de imagen específico para ciertos tipos de matrículas, o un paso de corrección de distorsión de lente.

## Soporte

Para más información sobre instalación y configuración, consulta el archivo `README.md` principal. Para problemas técnicos o preguntas sobre la implementación, revisa los comentarios en el código fuente, que contienen información detallada sobre las decisiones de diseño y optimizaciones implementadas.

