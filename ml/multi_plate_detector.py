"""
Detector de múltiples matrículas en una sola imagen
Detecta y procesa todas las matrículas presentes en una imagen usando OCR y visión por computadora.

Autor: Sistema de Reconocimiento de Matrículas
Versión: 2.0
"""
import sys
import json
import os
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
from preprocess import preprocess_for_ocr
import easyocr
import re
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Advertencia: pytesseract no está instalado. Ejecuta: pip install pytesseract", file=sys.stderr)

# ============================================================================
# CONSTANTES DE CONFIGURACIÓN
# ============================================================================

# Configuración de detección de regiones
MAX_DIMENSION_IMAGE = 1200  # Tamaño máximo de imagen antes de redimensionar (px)
MAX_CONTOURS_TO_PROCESS = 50  # Máximo número de contornos a procesar
MAX_REGIONS_TO_PROCESS = 8  # Máximo número de regiones de matrícula a procesar
MIN_CONTOUR_PERIMETER = 100  # Perímetro mínimo de contorno para considerar
MIN_PLATE_WIDTH = 100  # Ancho mínimo de matrícula (px)
MIN_PLATE_HEIGHT = 30  # Alto mínimo de matrícula (px)
MIN_ASPECT_RATIO = 2.0  # Relación de aspecto mínima (ancho/alto)
MAX_ASPECT_RATIO = 5.0  # Relación de aspecto máxima
MIN_EXTENT = 0.5  # Extensión mínima (área del contorno / área del rectángulo)
REGION_MARGIN = 15  # Margen alrededor de la región detectada (px)
OVERLAP_THRESHOLD = 0.5  # Umbral de solapamiento para eliminar duplicados (50%)

# Configuración de OCR para regiones
OCR_WIDTH_THS_REGION = 0.5  # Umbral de ancho para OCR en regiones
OCR_HEIGHT_THS_REGION = 0.5  # Umbral de alto para OCR en regiones
OCR_TEXT_THRESHOLD_REGION = 0.3  # Umbral de texto para OCR en regiones
OCR_LINK_THRESHOLD_REGION = 0.3  # Umbral de enlace para OCR en regiones

# Configuración de OCR para imagen completa
OCR_WIDTH_THS_FULL = 0.4  # Umbral de ancho para OCR en imagen completa
OCR_HEIGHT_THS_FULL = 0.4  # Umbral de alto para OCR en imagen completa
OCR_TEXT_THRESHOLD_FULL = 0.2  # Umbral de texto para OCR en imagen completa
OCR_LINK_THRESHOLD_FULL = 0.2  # Umbral de enlace para OCR en imagen completa

# Configuración de filtrado de texto
PALABRAS_DESCRIPTIVAS = [
    'SINALOA', 'MEXICO', 'MÉXICO', 'TRANSPORTE', 'PRIVADO', 
    'AUTOMOVIL', 'AUTOMÓVIL', 'TRASERA', 'FRONTAL', 'ESTADO',
    'REPUBLICA', 'REPÚBLICA', 'ESTADOS', 'UNIDOS',
    'AUE', 'TRASE', 'PRIVA', 'AUTOM', 'TRANS', 'PRIV', 'TRAS'
]

PREFIJOS_DESCRIPTIVOS = [
    'MEXICO', 'MÉXICO', 'SINALOA', 'TRANSPORTE', 'PRIVADO', 
    'AUTOMOVIL', 'AUTOMÓVIL', 'ESTADO', 'REPUBLICA', 'REPÚBLICA',
    'AUE', 'TRASE', 'PRIVA', 'AUTOM', 'TRANS', 'PRIV', 'TRAS'
]

# Patrones de matrícula mexicana (ordenados por prioridad)
PATRONES_MATRICULA = [
    r'^[A-Z]{2,4}-?\d{2}-?\d{2,3}$',  # VPM-45-32, ABC-12-34
    r'^[A-Z]{2,4}\d{2}-?\d{2,3}$',    # VPM45-32, ABC1234
    r'^[A-Z]{2,4}-?\d{3,4}$',         # VPM-123, ABC1234
    r'^[A-Z]{2,4}\d{3,4}$',           # VPM123, ABC1234
]

# Configuración de scoring
SCORE_BASE_PATRON = 100  # Score base para coincidencia con patrón
SCORE_DESCUENTO_PATRON = 10  # Descuento por cada patrón menos prioritario
SCORE_MULTIPLICADOR_CONFIANZA = 50  # Multiplicador para confianza OCR
SCORE_BONUS_LETRAS_NUMEROS = 20  # Bonus por tener letras y números
SCORE_BONUS_LONGITUD_TIPICA = 15  # Bonus por longitud típica (7-10 caracteres)
SCORE_BONUS_GUIONES = 10  # Bonus por formato con guiones
SCORE_BONUS_PATRON_EXACTO = 30  # Bonus extra por patrón exacto XXX-XX-XX

# Configuración de validación
LONGITUD_MINIMA = 5  # Longitud mínima de matrícula
LONGITUD_MAXIMA = 12  # Longitud máxima de matrícula
LONGITUD_TIPICA_MIN = 7  # Longitud típica mínima
LONGITUD_TIPICA_MAX = 10  # Longitud típica máxima
MAX_LONGITUD_SOLO_LETRAS = 6  # Máxima longitud para textos solo con letras


# ============================================================================
# CLASE PRINCIPAL: DetectorDeMultiplesMatriculas
# ============================================================================

class DetectorDeMultiplesMatriculas:
    """
    Clase principal para detectar múltiples matrículas en una sola imagen.
    
    Utiliza técnicas de visión por computadora (OpenCV) para encontrar regiones
    candidatas y OCR (EasyOCR) para extraer el texto de las matrículas.
    
    Ejemplo de uso:
        detector = DetectorDeMultiplesMatriculas()
        resultado = detector.detectar_todas_las_matriculas('ruta/imagen.jpg')
        print(resultado['plates'])  # Lista de matrículas detectadas
    """
    
    def __init__(self, idiomas: list = ['en']):
        """
        Inicializa el detector de matrículas.
        
        Args:
            idiomas: Lista de idiomas para OCR (por defecto inglés).
                    El inglés funciona bien para matrículas mexicanas.
        """
        # Inicializar el lector de OCR (EasyOCR)
        # Se carga una sola vez para mejorar el rendimiento
        self.lector_ocr = easyocr.Reader(
            idiomas,
            gpu=False,  # Usar CPU (más estable, GPU sería más rápido si está disponible)
            verbose=False,  # No mostrar mensajes de depuración
            quantize=True  # Cuantización para modelos más pequeños y rápidos
        )
    
    def detectar_todas_las_matriculas(self, ruta_imagen: str) -> Dict:
        """
        Detecta todas las matrículas presentes en una imagen.
        
        Proceso:
            1. Carga la imagen
            2. Encuentra regiones candidatas que podrían ser matrículas
            3. Procesa cada región con OCR para extraer el texto
            4. Filtra y valida los resultados usando patrones de matrícula mexicana
        
        Args:
            ruta_imagen: Ruta al archivo de imagen a procesar
        
        Returns:
            Diccionario con:
                - success: bool - Indica si se detectaron matrículas
                - plates: List[Dict] - Lista de matrículas detectadas con:
                    - plate_number: str - Número de matrícula
                    - confidence: float - Nivel de confianza (0-1)
                    - plate_index: int - Índice de la matrícula en la imagen
                - total_found: int - Número total de matrículas encontradas
                - error: str (opcional) - Mensaje de error si falla
        """
        # Cargar imagen
        imagen = cv2.imread(ruta_imagen)
        if imagen is None:
            return {
                'success': False,
                'plates': [],
                'error': f'No se pudo cargar la imagen: {ruta_imagen}'
            }
        
        # Encontrar todas las regiones candidatas que podrían ser matrículas
        regiones_candidatas = self._encontrar_regiones_matricula(imagen)
        
        # Si no se encontraron regiones, intentar OCR en toda la imagen
        if not regiones_candidatas:
            return self._ocr_imagen_completa(imagen)
        
        # Procesar cada región candidata con OCR
        matriculas_detectadas = []
        for indice, datos_region in enumerate(regiones_candidatas):
            # datos_region es una tupla: (array_imagen, (x, y, ancho, alto))
            if isinstance(datos_region, tuple) and len(datos_region) == 2:
                region = datos_region[0]  # Extraer solo el array de la imagen
            else:
                region = datos_region  # Si ya es un array, usarlo directamente
            
            resultado = self._procesar_region_matricula(region, indice + 1)
            if resultado:
                matriculas_detectadas.append(resultado)
        
        return {
            'success': len(matriculas_detectadas) > 0,
            'plates': matriculas_detectadas,
            'total_found': len(matriculas_detectadas)
        }
    
    def _encontrar_regiones_matricula(self, imagen: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Encuentra todas las regiones en la imagen que podrían contener matrículas.
        
        Utiliza detección de contornos y análisis de forma para identificar
        regiones rectangulares que coinciden con las características típicas
        de una matrícula (aspecto rectangular, tamaño razonable, etc.).
        
        Args:
            imagen: Imagen en formato numpy array (BGR)
        
        Returns:
            Lista de tuplas: (region_imagen, (x, y, ancho, alto))
        """
        # OPTIMIZACIÓN: Reducir tamaño de imágenes muy grandes para procesamiento más rápido
        alto, ancho = imagen.shape[:2]
        if ancho > MAX_DIMENSION_IMAGE or alto > MAX_DIMENSION_IMAGE:
            escala = MAX_DIMENSION_IMAGE / max(ancho, alto)
            nuevo_ancho = int(ancho * escala)
            nuevo_alto = int(alto * escala)
            imagen = cv2.resize(imagen, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_AREA)
        
        # Convertir a escala de grises para procesamiento
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY) if len(imagen.shape) == 3 else imagen
        
        regiones_encontradas = []
        
        # Paso 1: Suavizar imagen para reducir ruido
        imagen_suavizada = cv2.bilateralFilter(gris, 11, 17, 17)
        
        # Paso 2: Detectar bordes usando Canny
        bordes = cv2.Canny(imagen_suavizada, 30, 200)
        
        # Paso 3: Dilatar bordes para conectar líneas cercanas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        bordes_dilatados = cv2.dilate(bordes, kernel, iterations=2)
        
        # Paso 4: Encontrar contornos
        contornos, _ = cv2.findContours(bordes_dilatados, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # OPTIMIZACIÓN: Solo procesar los contornos más grandes (no afecta precisión)
        contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:MAX_CONTOURS_TO_PROCESS]
        
        # Paso 5: Analizar cada contorno para encontrar rectángulos
        for contorno in contornos:
            perimetro = cv2.arcLength(contorno, True)
            if perimetro < MIN_CONTOUR_PERIMETER:
                continue
            
            # Aproximar contorno a polígono
            aproximacion = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)
            
            # Buscar rectángulos (polígonos con 4 o más esquinas)
            if len(aproximacion) >= 4:
                x, y, ancho_rect, alto_rect = cv2.boundingRect(aproximacion)
                relacion_aspecto = ancho_rect / float(alto_rect) if alto_rect > 0 else 0
                area_contorno = cv2.contourArea(contorno)
                extension = area_contorno / float(ancho_rect * alto_rect) if (ancho_rect * alto_rect) > 0 else 0
                
                # Validar criterios de matrícula:
                # - Relación de aspecto entre 2:1 y 5:1 (matrículas son anchas)
                # - Tamaño mínimo razonable
                # - Extensión > 0.5 (no muy irregular, forma rectangular)
                if (MIN_ASPECT_RATIO <= relacion_aspecto <= MAX_ASPECT_RATIO and 
                    ancho_rect > MIN_PLATE_WIDTH and alto_rect > MIN_PLATE_HEIGHT and 
                    extension > MIN_EXTENT):
                    
                    # Extraer región con margen para incluir contexto
                    y1 = max(0, y - REGION_MARGIN)
                    y2 = min(imagen.shape[0], y + alto_rect + REGION_MARGIN)
                    x1 = max(0, x - REGION_MARGIN)
                    x2 = min(imagen.shape[1], x + ancho_rect + REGION_MARGIN)
                    
                    region = imagen[y1:y2, x1:x2]
                    
                    # Evitar duplicados verificando solapamiento con regiones ya encontradas
                    es_duplicado = self._verificar_solapamiento(
                        (x1, y1, x2 - x1, y2 - y1),
                        regiones_encontradas,
                        ancho_rect * alto_rect
                    )
                    
                    if not es_duplicado:
                        regiones_encontradas.append((region, (x1, y1, x2 - x1, y2 - y1)))
        
        # Ordenar regiones por posición (de arriba a abajo, izquierda a derecha)
        regiones_encontradas.sort(key=lambda r: (r[1][1], r[1][0]))
        
        # OPTIMIZACIÓN: Limitar número de regiones a procesar (balance velocidad/precisión)
        return regiones_encontradas[:MAX_REGIONS_TO_PROCESS]
    
    def _verificar_solapamiento(self, nueva_region: Tuple[int, int, int, int], 
                                regiones_existentes: List, area_region: int) -> bool:
        """
        Verifica si una nueva región se solapa significativamente con regiones existentes.
        
        Args:
            nueva_region: Tupla (x, y, ancho, alto) de la nueva región
            regiones_existentes: Lista de regiones ya encontradas
            area_region: Área de la nueva región
        
        Returns:
            True si hay solapamiento significativo (>50%), False en caso contrario
        """
        x1, y1, w1, h1 = nueva_region
        x2 = x1 + w1
        y2 = y1 + h1
        
        for _, (ex, ey, ew, eh) in regiones_existentes:
            # Calcular área de solapamiento
            solapamiento_x = max(0, min(x2, ex + ew) - max(x1, ex))
            solapamiento_y = max(0, min(y2, ey + eh) - max(y1, ey))
            area_solapamiento = solapamiento_x * solapamiento_y
            
            # Si el solapamiento es mayor al umbral, es duplicado
            if area_solapamiento > area_region * OVERLAP_THRESHOLD:
                return True
        
        return False
    
    def _procesar_region_matricula(self, region: np.ndarray, numero_region: int) -> Optional[Dict]:
        """
        Procesa una región de imagen para extraer el texto de la matrícula usando OCR.
        
        Args:
            region: Array numpy con la imagen de la región
            numero_region: Número de región (para identificación)
        
        Returns:
            Diccionario con información de la matrícula detectada o None si no se encuentra
        """
        try:
            # Intentar primero con el nuevo pipeline de ANPR (Pytesseract)
            if PYTESSERACT_AVAILABLE:
                placas_detectadas = self.tu_funcion_de_detectar_placas(region)
                if placas_detectadas and len(placas_detectadas) > 0:
                    # Validar y limpiar el texto detectado
                    # Priorizar la matrícula más larga que coincida con el patrón
                    placas_validas = []
                    for placa in placas_detectadas:
                        texto_limpio = self._limpiar_texto(placa)
                        longitud_sin_guiones = len(texto_limpio.replace('-', ''))
                        
                        # Filtrar fragmentos muy cortos (menos de 7 caracteres)
                        if longitud_sin_guiones < 7:
                            continue
                        
                        # Filtrar solo letras o solo números
                        if re.match(r'^[A-Z]+$', texto_limpio) or re.match(r'^\d+$', texto_limpio):
                            continue
                        
                        # Debe tener letras Y números
                        tiene_letras = bool(re.search(r'[A-Z]', texto_limpio))
                        tiene_numeros = bool(re.search(r'[0-9]', texto_limpio))
                        
                        if tiene_letras and tiene_numeros and self._es_texto_valido(texto_limpio):
                            # Validar si coincide con patrón de matrícula
                            coincide_patron, _ = self._validar_patron_matricula(texto_limpio)
                            placas_validas.append({
                                'text': texto_limpio,
                                'length': longitud_sin_guiones,
                                'matches_pattern': coincide_patron
                            })
                    
                    if placas_validas:
                        # Ordenar: primero las que coinciden con patrón, luego por longitud
                        placas_validas.sort(key=lambda x: (not x['matches_pattern'], -x['length']))
                        mejor_placa = placas_validas[0]['text']
                        
                        return {
                            'plate_number': mejor_placa,
                            'confidence': 0.85,  # Confianza estimada para Pytesseract
                            'plate_index': numero_region,
                            'raw_results': placas_detectadas
                        }
            
            # Fallback a EasyOCR si Pytesseract no está disponible o no detectó nada
            imagen_procesada = preprocess_for_ocr(region)
            
            if imagen_procesada is None or imagen_procesada.size == 0:
                return None
            
            # Realizar OCR en la región preprocesada
            resultados_ocr = self.lector_ocr.readtext(
                imagen_procesada,
                detail=1,
                paragraph=False,
                width_ths=OCR_WIDTH_THS_REGION,
                height_ths=OCR_HEIGHT_THS_REGION,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                text_threshold=OCR_TEXT_THRESHOLD_REGION,
                link_threshold=OCR_LINK_THRESHOLD_REGION,
                blocklist=''
            )
            
            if not resultados_ocr:
                return None
            
            # Extraer el mejor candidato de matrícula de los resultados OCR
            mejor_matricula = self._extraer_mejor_matricula(resultados_ocr)
            
            if mejor_matricula:
                return {
                    'plate_number': mejor_matricula['text'],
                    'confidence': mejor_matricula['confidence'],
                    'plate_index': numero_region,
                    'raw_results': [r[1] for r in resultados_ocr[:3]]  # Top 3 resultados para depuración
                }
            
            return None
            
        except Exception as e:
            # Imprimir error a stderr para que no interfiera con el JSON de salida
            import sys
            print(f"Error procesando región {numero_region}: {e}", file=sys.stderr)
            return None
    
    def tu_funcion_de_detectar_placas(self, image_bytes: np.ndarray) -> List[str]:
        """
        Pipeline completo de ANPR (Reconocimiento Automático de Matrículas) usando OpenCV y Pytesseract.
        
        Este método implementa un pipeline robusto que:
        1. Pre-procesa la imagen (escala de grises, reducción de ruido, detección de bordes)
        2. Detecta y aísla la placa (contornos, filtrado, recorte)
        3. Corrige la perspectiva (endereza la placa)
        4. Binariza y limpia la placa
        5. Realiza OCR con Pytesseract (configuración optimizada)
        6. Post-procesa el resultado (limpieza de string)
        
        Args:
            image_bytes: Array numpy de la imagen (BGR) o bytes de imagen
        
        Returns:
            Lista de placas detectadas (ej. ['VPM-45-32'])
        """
        if not PYTESSERACT_AVAILABLE:
            return []
        
        try:
            # ========================================================================
            # 1. PRE-PROCESAMIENTO DE LA IMAGEN
            # ========================================================================
            
            # Decodificar imagen si es necesario
            if isinstance(image_bytes, bytes):
                imagen = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            else:
                imagen = image_bytes.copy()
            
            if imagen is None or imagen.size == 0:
                return []
            
            # Escala de Grises
            if len(imagen.shape) == 3:
                gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            else:
                gris = imagen.copy()
            
            # Reducción de Ruido: Bilateral Filter (preserva bordes mejor que Gaussian)
            imagen_suavizada = cv2.bilateralFilter(gris, 11, 17, 17)
            
            # Detección de Bordes: Canny
            bordes = cv2.Canny(imagen_suavizada, 30, 200)
            
            # ========================================================================
            # 2. DETECCIÓN Y AISLAMIENTO DE LA PLACA
            # ========================================================================
            
            # Dilatar bordes para conectar líneas cercanas
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            bordes_dilatados = cv2.dilate(bordes, kernel, iterations=2)
            
            # Encontrar Contornos
            contornos, _ = cv2.findContours(bordes_dilatados, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Ordenar contornos por área (más grandes primero)
            contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:MAX_CONTOURS_TO_PROCESS]
            
            placas_detectadas = []
            
            # Filtrar Contornos y encontrar rectángulos que parezcan placas
            for contorno in contornos:
                perimetro = cv2.arcLength(contorno, True)
                if perimetro < MIN_CONTOUR_PERIMETER:
                    continue
                
                # Aproximar contorno a polígono
                aproximacion = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)
                
                # Buscar rectángulos (polígonos con 4 esquinas)
                if len(aproximacion) == 4:
                    x, y, ancho, alto = cv2.boundingRect(aproximacion)
                    relacion_aspecto = ancho / float(alto) if alto > 0 else 0
                    area_contorno = cv2.contourArea(contorno)
                    extension = area_contorno / float(ancho * alto) if (ancho * alto) > 0 else 0
                    
                    # Validar criterios de matrícula
                    if (MIN_ASPECT_RATIO <= relacion_aspecto <= MAX_ASPECT_RATIO and 
                        ancho > MIN_PLATE_WIDTH and alto > MIN_PLATE_HEIGHT and 
                        extension > MIN_EXTENT):
                        
                        # Recortar la Placa con margen
                        y1 = max(0, y - REGION_MARGIN)
                        y2 = min(imagen.shape[0], y + alto + REGION_MARGIN)
                        x1 = max(0, x - REGION_MARGIN)
                        x2 = min(imagen.shape[1], x + ancho + REGION_MARGIN)
                        
                        placa_recortada = gris[y1:y2, x1:x2]
                        
                        if placa_recortada.size == 0:
                            continue
                        
                        # ========================================================================
                        # 3. CORRECCIÓN DE PERSPECTIVA
                        # ========================================================================
                        
                        # Obtener puntos de las esquinas del contorno
                        puntos_originales = aproximacion.reshape(4, 2)
                        
                        # Ordenar puntos: [top-left, top-right, bottom-right, bottom-left]
                        puntos_ordenados = self._ordenar_puntos(puntos_originales)
                        
                        # Calcular dimensiones de la placa enderezada
                        (tl, tr, br, bl) = puntos_ordenados
                        ancho_superior = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                        ancho_inferior = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                        ancho_max = max(int(ancho_superior), int(ancho_inferior))
                        
                        alto_izquierdo = np.sqrt(((bl[0] - tl[0]) ** 2) + ((bl[1] - tl[1]) ** 2))
                        alto_derecho = np.sqrt(((br[0] - tr[0]) ** 2) + ((br[1] - tr[1]) ** 2))
                        alto_max = max(int(alto_izquierdo), int(alto_derecho))
                        
                        # Puntos de destino para la transformación
                        puntos_destino = np.array([
                            [0, 0],
                            [ancho_max - 1, 0],
                            [ancho_max - 1, alto_max - 1],
                            [0, alto_max - 1]
                        ], dtype="float32")
                        
                        # Aplicar transformación de perspectiva
                        matriz_perspectiva = cv2.getPerspectiveTransform(
                            puntos_ordenados.astype("float32"), 
                            puntos_destino
                        )
                        placa_enderezada = cv2.warpPerspective(
                            placa_recortada, 
                            matriz_perspectiva, 
                            (ancho_max, alto_max)
                        )
                        
                        # ========================================================================
                        # 4. BINARIZACIÓN Y LIMPIEZA DE LA PLACA
                        # ========================================================================
                        
                        # Redimensionar si es muy pequeña o muy grande
                        alto_placa, ancho_placa = placa_enderezada.shape
                        if ancho_placa < 100 or alto_placa < 30:
                            factor_escala = max(100.0 / ancho_placa, 30.0 / alto_placa)
                            nuevo_ancho = int(ancho_placa * factor_escala)
                            nuevo_alto = int(alto_placa * factor_escala)
                            placa_enderezada = cv2.resize(
                                placa_enderezada, 
                                (nuevo_ancho, nuevo_alto), 
                                interpolation=cv2.INTER_CUBIC
                            )
                        
                        # Umbralización Adaptativa (mejor para condiciones de iluminación variables)
                        placa_binarizada = cv2.adaptiveThreshold(
                            placa_enderezada,
                            255,
                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY,
                            11,
                            2
                        )
                        
                        # Apertura morfológica para eliminar pequeños puntos de ruido
                        kernel_limpieza = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                        placa_limpia = cv2.morphologyEx(
                            placa_binarizada, 
                            cv2.MORPH_OPEN, 
                            kernel_limpieza, 
                            iterations=1
                        )
                        
                        # ========================================================================
                        # 5. CONFIGURACIÓN DE OCR (PYTESSERACT)
                        # ========================================================================
                        
                        # Configuración optimizada para matrículas mexicanas
                        # PSM 7: Tratar la imagen como una sola línea de texto
                        # Whitelist: Solo letras mayúsculas, números y guiones
                        custom_config = r'--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
                        
                        # Realizar OCR
                        plate_text = pytesseract.image_to_string(placa_limpia, config=custom_config)
                        
                        # ========================================================================
                        # 6. POST-PROCESAMIENTO
                        # ========================================================================
                        
                        # Limpiar el String
                        plate_text_limpio = plate_text.strip().replace(" ", "").replace("\n", "").replace("\r", "")
                        
                        # Validar que tenga contenido y formato razonable
                        # LONGITUD MÍNIMA: 7 caracteres sin guiones (ej: QMF1815, VPM4532)
                        if plate_text_limpio and len(plate_text_limpio.replace('-', '')) >= 7:
                            # Filtrar solo números (fragmentos)
                            if re.match(r'^\d+$', plate_text_limpio):
                                continue
                            
                            # Filtrar palabras descriptivas conocidas
                            plate_text_upper = plate_text_limpio.upper()
                            if plate_text_upper in PALABRAS_DESCRIPTIVAS:
                                continue
                            
                            # Filtrar textos que empiezan con prefijos descriptivos
                            es_descriptivo = False
                            for prefijo in PREFIJOS_DESCRIPTIVOS:
                                if plate_text_upper.startswith(prefijo) and len(plate_text_upper) <= len(prefijo) + 3:
                                    es_descriptivo = True
                                    break
                            
                            if es_descriptivo:
                                continue
                            
                            # Filtrar textos largos solo con letras (probablemente descriptivos)
                            if len(plate_text_upper) > 6 and re.match(r'^[A-Z]+$', plate_text_upper):
                                continue
                            
                            # Debe tener letras Y números para ser una matrícula válida
                            tiene_letras = bool(re.search(r'[A-Z]', plate_text_upper))
                            tiene_numeros = bool(re.search(r'[0-9]', plate_text_upper))
                            
                            if tiene_letras and tiene_numeros:
                                placas_detectadas.append(plate_text_limpio)
                        
                        # Si no se detectó nada con perspectiva, intentar sin corrección
                        if not placas_detectadas:
                            # Intentar OCR directamente en la placa binarizada sin corrección de perspectiva
                            plate_text_directo = pytesseract.image_to_string(
                                placa_binarizada, 
                                config=custom_config
                            )
                            plate_text_directo_limpio = plate_text_directo.strip().replace(" ", "").replace("\n", "").replace("\r", "")
                            
                            # LONGITUD MÍNIMA: 7 caracteres sin guiones
                            if plate_text_directo_limpio and len(plate_text_directo_limpio.replace('-', '')) >= 7:
                                # Filtrar solo números (fragmentos)
                                if re.match(r'^\d+$', plate_text_directo_limpio):
                                    continue
                                
                                # Filtrar palabras descriptivas conocidas
                                plate_text_upper = plate_text_directo_limpio.upper()
                                if plate_text_upper in PALABRAS_DESCRIPTIVAS:
                                    continue
                                
                                # Filtrar textos que empiezan con prefijos descriptivos
                                es_descriptivo = False
                                for prefijo in PREFIJOS_DESCRIPTIVOS:
                                    if plate_text_upper.startswith(prefijo) and len(plate_text_upper) <= len(prefijo) + 3:
                                        es_descriptivo = True
                                        break
                                
                                if es_descriptivo:
                                    continue
                                
                                # Filtrar textos largos solo con letras
                                if len(plate_text_upper) > 6 and re.match(r'^[A-Z]+$', plate_text_upper):
                                    continue
                                
                                # Debe tener letras Y números para ser una matrícula válida
                                tiene_letras = bool(re.search(r'[A-Z]', plate_text_upper))
                                tiene_numeros = bool(re.search(r'[0-9]', plate_text_upper))
                                
                                if tiene_letras and tiene_numeros:
                                    placas_detectadas.append(plate_text_directo_limpio)
            
            return placas_detectadas
            
        except Exception as e:
            # Imprimir error a stderr para que no interfiera con el JSON de salida
            print(f"Error en tu_funcion_de_detectar_placas: {e}", file=sys.stderr)
            return []
    
    def _ordenar_puntos(self, puntos: np.ndarray) -> np.ndarray:
        """
        Ordena los puntos de un rectángulo en el orden:
        [top-left, top-right, bottom-right, bottom-left]
        
        Args:
            puntos: Array de 4 puntos (x, y)
        
        Returns:
            Array de puntos ordenados
        """
        # Inicializar lista de coordenadas ordenadas
        puntos_ordenados = np.zeros((4, 2), dtype="float32")
        
        # Suma y diferencia para encontrar esquinas
        suma = puntos.sum(axis=1)
        diferencia = np.diff(puntos, axis=1)
        
        # Top-left tendrá la suma más pequeña
        puntos_ordenados[0] = puntos[np.argmin(suma)]
        # Bottom-right tendrá la suma más grande
        puntos_ordenados[2] = puntos[np.argmax(suma)]
        
        # Top-right tendrá la diferencia más pequeña (x - y es mínimo)
        puntos_ordenados[1] = puntos[np.argmin(diferencia)]
        # Bottom-left tendrá la diferencia más grande (x - y es máximo)
        puntos_ordenados[3] = puntos[np.argmax(diferencia)]
        
        return puntos_ordenados
    
    def _extraer_mejor_matricula(self, resultados_ocr: List) -> Optional[Dict]:
        """
        Extrae el mejor candidato de matrícula de los resultados OCR.
        
        Utiliza un sistema de scoring que prioriza:
        1. Textos que coinciden con patrones de matrícula mexicana
        2. Textos con alta confianza de OCR
        3. Textos con formato típico de matrícula (letras + números + guiones)
        
        Filtra textos descriptivos como "MEXICO", "SINALOA", etc.
        
        Args:
            resultados_ocr: Lista de resultados de EasyOCR
        
        Returns:
            Diccionario con el mejor candidato o None si no hay candidatos válidos
        """
        candidatos = []
        
        for resultado in resultados_ocr:
            if len(resultado) < 2:
                continue
            
            texto = resultado[1]
            confianza = resultado[2] if len(resultado) > 2 else 0.5
            
            # Limpiar y normalizar texto
            texto_limpio = self._limpiar_texto(texto)
            
            # Filtrar textos no válidos
            if not self._es_texto_valido(texto_limpio):
                continue
            
            # Validar si coincide con patrón de matrícula
            coincide_patron, score_patron = self._validar_patron_matricula(texto_limpio)
            
            # Calcular score total del candidato
            score_total = self._calcular_score_candidato(
                texto_limpio, confianza, coincide_patron, score_patron
            )
            
            candidatos.append({
                'text': texto_limpio,
                'confidence': confianza,
                'score': score_total,
                'matches_pattern': coincide_patron
            })
        
        if not candidatos:
            return None
        
        # Ordenar candidatos: primero los que coinciden con patrón, luego por score
        candidatos.sort(key=lambda x: (
            not x['matches_pattern'],  # False primero (coincide con patrón)
            -x['score']                # Score descendente
        ))
        
        return candidatos[0]
    
    def _limpiar_texto(self, texto: str) -> str:
        """
        Limpia y normaliza el texto extraído por OCR.
        
        Args:
            texto: Texto crudo del OCR
        
        Returns:
            Texto limpio en mayúsculas, solo letras, números y guiones
        """
        texto_limpio = re.sub(r'[^A-Z0-9-]', '', str(texto).upper())
        texto_limpio = texto_limpio.replace(' ', '').replace('_', '').replace('.', '')
        return texto_limpio
    
    def _es_texto_valido(self, texto: str) -> bool:
        """
        Verifica si un texto es un candidato válido para ser una matrícula.
        
        Filtra:
        - Palabras descriptivas conocidas (MEXICO, SINALOA, etc.)
        - Textos que empiezan con prefijos descriptivos seguidos de pocos números
        - Textos largos solo con letras
        - Fragmentos muy cortos (menos de 7 caracteres sin guiones)
        - Textos de un solo carácter
        
        Args:
            texto: Texto a validar
        
        Returns:
            True si es válido, False si debe filtrarse
        """
        # Filtrar textos muy cortos (fragmentos)
        longitud_sin_guiones = len(texto.replace('-', ''))
        if longitud_sin_guiones < 7:
            return False
        
        # Filtrar textos de un solo carácter
        if longitud_sin_guiones == 1:
            return False
        
        # Filtrar palabras descriptivas exactas
        if texto in PALABRAS_DESCRIPTIVAS:
            return False
        
        # Filtrar textos que empiezan con prefijos descriptivos (ej: "MEXICO5")
        for prefijo in PREFIJOS_DESCRIPTIVOS:
            if texto.startswith(prefijo) and len(texto) > len(prefijo):
                # Si tiene muy pocos números después, filtrar
                if len(texto) <= len(prefijo) + 2:  # "MEXICO5" = 7 caracteres
                    return False
            # Filtrar textos principalmente descriptivos con números al final
            if texto.startswith(prefijo) and len(texto) <= len(prefijo) + 3:
                return False
        
        # Filtrar textos largos solo con letras
        if len(texto) > MAX_LONGITUD_SOLO_LETRAS and re.match(r'^[A-Z]+$', texto):
            return False
        
        # Filtrar solo números (fragmentos)
        if re.match(r'^\d+$', texto):
            return False
        
        # Filtrar solo letras (fragmentos descriptivos)
        if re.match(r'^[A-Z]+$', texto) and longitud_sin_guiones < 7:
            return False
        
        return True
    
    def _validar_patron_matricula(self, texto: str) -> Tuple[bool, int]:
        """
        Valida si un texto coincide con algún patrón de matrícula mexicana.
        
        Args:
            texto: Texto a validar
        
        Returns:
            Tupla (coincide_patron, score_patron)
        """
        for indice, patron in enumerate(PATRONES_MATRICULA):
            if re.match(patron, texto):
                score = SCORE_BASE_PATRON - (indice * SCORE_DESCUENTO_PATRON)
                return True, score
        
        return False, 0
    
    def _calcular_score_candidato(self, texto: str, confianza: float, 
                                  coincide_patron: bool, score_patron: int) -> float:
        """
        Calcula el score total de un candidato a matrícula.
        
        Args:
            texto: Texto del candidato
            confianza: Confianza del OCR (0-1)
            coincide_patron: Si coincide con patrón de matrícula
            score_patron: Score del patrón
        
        Returns:
            Score total del candidato
        """
        score = score_patron  # Score base por patrón
        score += confianza * SCORE_MULTIPLICADOR_CONFIANZA  # Bonus por confianza
        
        longitud = len(texto.replace('-', ''))
        
        # Bonus por tener letras Y números
        if re.search(r'[0-9]', texto) and re.search(r'[A-Z]', texto):
            score += SCORE_BONUS_LETRAS_NUMEROS
        
        # Bonus por longitud típica de matrícula
        if LONGITUD_TIPICA_MIN <= longitud <= LONGITUD_TIPICA_MAX:
            score += SCORE_BONUS_LONGITUD_TIPICA
        
        # Bonus por formato con guiones (muy importante para matrículas mexicanas)
        if '-' in texto:
            score += SCORE_BONUS_GUIONES
        
        # Bonus EXTRA por patrón exacto de matrícula mexicana (ej: VPM-45-32)
        if re.match(r'^[A-Z]{3}-\d{2}-\d{2}$', texto):
            score += SCORE_BONUS_PATRON_EXACTO
        
        return score
    
    def _ocr_imagen_completa(self, imagen: np.ndarray) -> Dict:
        """
        Realiza OCR en toda la imagen cuando no se encuentran regiones específicas.
        
        Útil para imágenes donde la matrícula ocupa gran parte de la imagen
        o cuando la detección de regiones falla.
        
        Args:
            imagen: Imagen completa en formato numpy array
        
        Returns:
            Diccionario con matrículas detectadas
        """
        try:
            imagen_procesada = preprocess_for_ocr(imagen)
            
            # Parámetros más permisivos para imagen completa
            resultados_ocr = self.lector_ocr.readtext(
                imagen_procesada,
                detail=1,
                paragraph=False,
                width_ths=OCR_WIDTH_THS_FULL,
                height_ths=OCR_HEIGHT_THS_FULL,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                text_threshold=OCR_TEXT_THRESHOLD_FULL,
                link_threshold=OCR_LINK_THRESHOLD_FULL,
                blocklist=''
            )
            
            # Agrupar resultados cercanos (misma matrícula)
            matriculas = []
            indices_procesados = set()
            
            for i, resultado in enumerate(resultados_ocr):
                if i in indices_procesados:
                    continue
                
                texto = resultado[1]
                confianza = resultado[2] if len(resultado) > 2 else 0.5
                bbox = resultado[0] if len(resultado) > 0 else None
                
                # Limpiar texto
                texto_limpio = self._limpiar_texto(texto)
                
                # Validar formato básico
                if (len(texto_limpio) >= 3 and 
                    re.match(r'^[A-Z0-9-]+$', texto_limpio) and
                    3 <= len(texto_limpio.replace('-', '')) <= 15):
                    
                    # Buscar resultados cercanos (misma matrícula)
                    resultados_cercanos = [resultado]
                    for j, otro_resultado in enumerate(resultados_ocr[i+1:], start=i+1):
                        if j in indices_procesados:
                            continue
                        
                        otro_bbox = otro_resultado[0] if len(otro_resultado) > 0 else None
                        if bbox and otro_bbox:
                            # Calcular distancia entre bounding boxes
                            centro1 = np.mean(bbox, axis=0)
                            centro2 = np.mean(otro_bbox, axis=0)
                            distancia = np.linalg.norm(centro1 - centro2)
                            
                            # Si están cerca, podrían ser parte de la misma matrícula
                            if distancia < 200:  # 200 píxeles de distancia
                                resultados_cercanos.append(otro_resultado)
                                indices_procesados.add(j)
                    
                    # Combinar resultados cercanos
                    texto_combinado = ' '.join([r[1] for r in resultados_cercanos])
                    texto_combinado_limpio = self._limpiar_texto(texto_combinado)
                    
                    if len(texto_combinado_limpio) >= 3:
                        mejor = self._extraer_mejor_matricula([(None, texto_combinado_limpio, confianza)])
                        if mejor:
                            matriculas.append({
                                'plate_number': mejor['text'],
                                'confidence': mejor['confidence'],
                                'plate_index': len(matriculas) + 1
                            })
                    
                    indices_procesados.add(i)
            
            return {
                'success': len(matriculas) > 0,
                'plates': matriculas,
                'total_found': len(matriculas)
            }
            
        except Exception as e:
            return {
                'success': False,
                'plates': [],
                'error': str(e)
            }


# ============================================================================
# ALIAS PARA COMPATIBILIDAD HACIA ATRÁS
# ============================================================================

# Mantener el nombre original en inglés para compatibilidad
MultiPlateDetector = DetectorDeMultiplesMatriculas


# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'plates': [],
            'error': 'No se proporcionó ruta de imagen'
        }))
        sys.exit(1)
    
    ruta_imagen = sys.argv[1]
    
    if not os.path.exists(ruta_imagen):
        print(json.dumps({
            'success': False,
            'plates': [],
            'error': f'La imagen no existe: {ruta_imagen}'
        }))
        sys.exit(1)
    
    try:
        detector = DetectorDeMultiplesMatriculas()
        resultado = detector.detectar_todas_las_matriculas(ruta_imagen)
        print(json.dumps(resultado, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({
            'success': False,
            'plates': [],
            'error': str(e)
        }))
        sys.exit(1)
