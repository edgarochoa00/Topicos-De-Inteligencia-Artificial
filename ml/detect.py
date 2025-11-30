"""
Módulo de detección y reconocimiento de matrículas
Combina detección de región y OCR para extraer números de matrícula
"""
from typing import Optional, Tuple, List, TYPE_CHECKING
import os
from preprocess import detect_plate_region, preprocess_for_ocr

if TYPE_CHECKING:
    import numpy as np  # type: ignore

# Importar cv2 con manejo de errores
try:
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore
    print("Advertencia: opencv-python no está instalado. Ejecuta: pip install opencv-python")

# Importar numpy con manejo de errores
try:
    import numpy as np  # type: ignore
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore
    print("Advertencia: numpy no está instalado. Ejecuta: pip install numpy")

# Importar easyocr con manejo de errores
try:
    import easyocr  # type: ignore
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None  # type: ignore
    print("Advertencia: easyocr no está instalado. Ejecuta: pip install easyocr")


class LicensePlateDetector:
    """
    Clase para detectar y reconocer números de matrícula en imágenes
    """
    
    def __init__(self, languages: list = ['en']):
        """
        Inicializa el detector
        
        Args:
            languages: Lista de idiomas para OCR (por defecto inglés)
        """
        if not EASYOCR_AVAILABLE:
            raise ImportError(
                "easyocr no está instalado. Por favor, instálalo ejecutando: "
                "pip install easyocr"
            )
        
        print("Inicializando detector de matrículas...")
        # OPTIMIZACIÓN: Configurar EasyOCR para máxima velocidad
        self.reader = easyocr.Reader(
            languages, 
            gpu=False,
            verbose=False,
            quantize=True,
            cudnn_benchmark=False,
            model_storage_directory=None,  # Usar directorio por defecto
            download_enabled=True  # Permitir descarga de modelos
        )
        print("Detector inicializado (modo rápido)")
    
    def detect_and_recognize(self, image_path: str) -> Optional[str]:
        """
        Detecta y reconoce el número de matrícula en una imagen usando múltiples estrategias
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Número de matrícula detectado o None
        """
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python no está instalado")
        
        # Validar que el archivo existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"La imagen no existe: {image_path}")
        
        # Cargar imagen
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}. Verifica que sea un formato válido (JPG, PNG, etc.)")
        
        # Validar que la imagen tenga contenido
        if image.size == 0:
            raise ValueError(f"La imagen está vacía: {image_path}")
        
        # Estrategia 1: Detectar región y procesar
        try:
            plate_region = detect_plate_region(image)
            if plate_region is not None:
                processed = preprocess_for_ocr(plate_region)
                if processed is not None and processed.size > 0:
                    # Parámetros optimizados para máxima precisión (restaurados desde detect_enhanced.py)
                    results = self.reader.readtext(
                        processed, 
                        detail=1, 
                        paragraph=False,
                        width_ths=0.5,  # Más flexible para capturar texto más grande
                        height_ths=0.5,  # Más flexible para capturar texto más grande
                        allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                        text_threshold=0.4,  # Umbral más bajo para capturar más texto
                        link_threshold=0.4,  # Umbral más bajo para conectar caracteres
                        blocklist=''  # No bloquear ningún carácter
                    )
                    if results:
                        plate_number = self._extract_plate_number_from_results(results)
                        if plate_number:
                            return plate_number
        except Exception as e:
            # Continuar con otras estrategias si esta falla
            pass
        
        # Estrategia 2: Procesar toda la imagen
        try:
            processed_full = preprocess_for_ocr(image)
            if processed_full is not None and processed_full.size > 0:
                # Parámetros optimizados para máxima precisión (restaurados desde detect_enhanced.py)
                results_full = self.reader.readtext(
                    processed_full, 
                    detail=1, 
                    paragraph=False,
                    width_ths=0.5,
                    height_ths=0.5,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                    text_threshold=0.4,
                    link_threshold=0.4
                )
                if results_full:
                    plate_number = self._extract_plate_number_from_results(results_full)
                    if plate_number:
                        return plate_number
        except Exception as e:
            # Continuar con otras estrategias
            pass
        
        # Estrategia 3: OCR directo en imagen original (sin preprocesamiento)
        try:
            # Convertir a formato que EasyOCR pueda procesar
            if len(image.shape) == 2:
                # Ya es escala de grises
                image_for_ocr = image
            else:
                # Convertir a RGB (EasyOCR espera RGB)
                image_for_ocr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Parámetros optimizados para máxima precisión (restaurados desde detect_enhanced.py)
            results_direct = self.reader.readtext(
                image_for_ocr, 
                detail=1, 
                paragraph=False,
                width_ths=0.5,
                height_ths=0.5,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                text_threshold=0.4,
                link_threshold=0.4
            )
            if results_direct:
                plate_number = self._extract_plate_number_from_results(results_direct)
                if plate_number:
                    return plate_number
        except Exception as e:
            # Si falla, intentar con BGR directamente usando detail=1
            try:
                results_direct = self.reader.readtext(
                    image, 
                    detail=1, 
                    paragraph=False,
                    width_ths=0.5,
                    height_ths=0.5,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                    text_threshold=0.4,
                    link_threshold=0.4
                )
                if results_direct:
                    plate_number = self._extract_plate_number_from_results(results_direct)
                    if plate_number:
                        return plate_number
            except Exception:
                pass
        
        # Estrategia 4: Probar con diferentes rotaciones
        for angle in [-10, -5, 5, 10]:
            try:
                rotated = self._rotate_image(image, angle)
                if len(rotated.shape) == 2:
                    rotated_for_ocr = rotated
                else:
                    rotated_for_ocr = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
                
                # Parámetros optimizados para máxima precisión (restaurados desde detect_enhanced.py)
                results_rot = self.reader.readtext(
                    rotated_for_ocr, 
                    detail=1, 
                    paragraph=False,
                    width_ths=0.5,
                    height_ths=0.5,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
                    text_threshold=0.4,
                    link_threshold=0.4
                )
                if results_rot:
                    plate_number = self._extract_plate_number_from_results(results_rot)
                    if plate_number:
                        return plate_number
            except Exception:
                continue
        
        return None
    
    def _rotate_image(self, image: 'np.ndarray', angle: float) -> 'np.ndarray':
        """Rota una imagen un ángulo dado"""
        if not CV2_AVAILABLE:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, matrix, (width, height), 
                                 flags=cv2.INTER_LINEAR, 
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    def _extract_plate_number_from_results(self, results: List) -> Optional[str]:
        """Extrae número de matrícula de resultados de OCR (mejorado) - Prioriza texto más grande"""
        import re
        
        # Procesar todos y elegir el mejor, priorizando tamaño de texto
        candidates = []
        
        for result in results:
            if len(result) < 2:
                continue
            
            text = result[1]
            confidence = result[2] if len(result) > 2 else 0.5
            
            # Obtener tamaño del bounding box si está disponible (result[0])
            bbox = result[0] if len(result) > 0 and isinstance(result[0], (list, tuple)) else None
            text_size = 0
            text_width = 0
            text_height = 0
            if bbox and len(bbox) >= 2:
                # Calcular área del bounding box como indicador de tamaño
                try:
                    if len(bbox) == 4:
                        # bbox es [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        x_coords = [p[0] for p in bbox if len(p) >= 2]
                        y_coords = [p[1] for p in bbox if len(p) >= 2]
                        if x_coords and y_coords:
                            text_width = max(x_coords) - min(x_coords)
                            text_height = max(y_coords) - min(y_coords)
                            text_size = text_width * text_height  # Área del texto
                except:
                    pass
            
            # Umbral de confianza más flexible (0.2 en lugar de 0.3)
            if confidence < 0.2:
                continue
            
            # Limpiar texto (más agresivo)
            cleaned = re.sub(r'[^A-Z0-9-]', '', str(text).upper())
            cleaned = cleaned.replace(' ', '').replace('_', '').replace('.', '')
            
            # Patrones de matrícula mexicana (prioridad alta)
            plate_patterns = [
                r'^[A-Z]{2,4}-?\d{2}-?\d{2,3}$',  # VPM-45-32, ABC-12-34
                r'^[A-Z]{2,4}\d{2}-?\d{2,3}$',    # VPM45-32, ABC1234
                r'^[A-Z]{2,4}-?\d{3,4}$',         # VPM-123, ABC1234
                r'^[A-Z]{2,4}\d{3,4}$',           # VPM123, ABC1234
            ]
            
            # Textos descriptivos comunes a filtrar (estados, palabras descriptivas)
            descriptive_words = [
                'SINALOA', 'MEXICO', 'MÉXICO', 'TRANSPORTE', 'PRIVADO', 
                'AUTOMOVIL', 'AUTOMÓVIL', 'TRASERA', 'FRONTAL', 'ESTADO',
                'REPUBLICA', 'REPÚBLICA', 'ESTADOS', 'UNIDOS'
            ]
            
            # FILTRAR: Textos descriptivos conocidos
            if cleaned in descriptive_words:
                continue
            
            # FILTRAR: Textos largos solo con letras (probablemente descriptivos)
            if len(cleaned) > 6 and re.match(r'^[A-Z]+$', cleaned):
                continue
            
            # FILTRAR: Solo números (fragmentos como "32", "45", "28", "96")
            # Rechazar TODOS los textos que sean solo números
            if re.match(r'^\d+$', cleaned):
                continue
            
            # FILTRAR: Textos muy cortos (menos de 5 caracteres sin guiones)
            # Esto filtra fragmentos como "32", "45", "VPM", etc.
            if len(cleaned.replace('-', '')) < 5:
                continue
            
            # VALIDAR: Usar regex para verificar si coincide con patrón de matrícula
            matches_plate_pattern = False
            pattern_score = 0
            
            for i, pattern in enumerate(plate_patterns):
                if re.match(pattern, cleaned):
                    matches_plate_pattern = True
                    pattern_score = 100 - (i * 10)  # Primer patrón tiene score más alto
                    break
            
            length = len(cleaned.replace('-', ''))
            
            # Si NO coincide con patrón de matrícula, solo considerar si tiene letras Y números
            if not matches_plate_pattern:
                # Debe tener al menos una letra Y un número para ser candidato
                has_letters = bool(re.search(r'[A-Z]', cleaned))
                has_numbers = bool(re.search(r'[0-9]', cleaned))
                
                if not (has_letters and has_numbers):
                    continue  # Saltar si no tiene ambos
                
                # Validar longitud razonable
                if not (5 <= length <= 12):
                    continue
            
            # Calcular score combinado: confianza + tamaño + preferencia por formato de matrícula
            score = pattern_score  # Score base por coincidir con patrón (0 si no coincide)
            score += confidence * 50  # Bonus por confianza
            score += text_size / 500  # Bonus por tamaño (normalizado)
            
            # Priorizar texto más ancho (matrículas suelen ser más anchas que altas)
            if text_width > 0 and text_height > 0:
                aspect_ratio = text_width / text_height
                if 2.0 <= aspect_ratio <= 8.0:  # Matrículas suelen ser más anchas
                    score += 25  # Bonus significativo por formato horizontal
            
            # Bonus por tener letras Y números (matrícula completa)
            if re.search(r'[0-9]', cleaned) and re.search(r'[A-Z]', cleaned):
                score += 20
            
            # Bonus por longitud típica (7-10 caracteres sin guiones)
            if 7 <= length <= 10:
                score += 25  # Aumentado de 15 a 25 para priorizar matrículas completas
            
            # Bonus por formato con guiones (más legible) - muy importante
            if '-' in cleaned:
                score += 15  # Aumentado de 5 a 15 para priorizar formato estándar
            
            # Penalizar textos muy cortos (aunque ya pasaron el filtro mínimo)
            if length < 7:
                score -= 30  # Penalización fuerte para textos cortos
            
            candidates.append((cleaned, length, confidence, text_size, text_width, text_height, score, matches_plate_pattern))
        
        # ORDENAR: Priorizar candidatos que coincidan con patrón de matrícula
        if candidates:
            # Ordenar por: 1) Coincide con patrón, 2) Score, 3) Tamaño, 4) Confianza
            candidates.sort(key=lambda x: (
                not x[7],  # False primero (coincide con patrón)
                -x[6],     # Score descendente
                -x[3],     # Tamaño descendente
                -x[2]      # Confianza descendente
            ))
            
            # Retornar el mejor candidato
            return candidates[0][0]
        
        return None
    
    def _extract_plate_number_from_list(self, text_list: list) -> Optional[str]:
        """
        Extrae número de matrícula de una lista de textos usando regex para validar formato.
        Prioriza textos COMPLETOS que coincidan con el patrón de matrícula mexicana (ej: VPM-45-32).
        MEJORA: Intenta combinar fragmentos cercanos que podrían formar una matrícula completa.
        """
        import re
        
        # Patrones de matrícula mexicana (prioridad alta)
        # Formato: 2-4 letras seguidas de números (con o sin guiones)
        # Ejemplos: VPM-45-32, ABC123, XYZ-12-34
        plate_patterns = [
            r'^[A-Z]{2,4}-?\d{2}-?\d{2,3}$',  # VPM-45-32, ABC-12-34
            r'^[A-Z]{2,4}\d{2}-?\d{2,3}$',    # VPM45-32, ABC1234
            r'^[A-Z]{2,4}-?\d{3,4}$',         # VPM-123, ABC1234
            r'^[A-Z]{2,4}\d{3,4}$',           # VPM123, ABC1234
        ]
        
        # Textos descriptivos comunes a filtrar (estados, palabras descriptivas)
        descriptive_words = [
            'SINALOA', 'MEXICO', 'MÉXICO', 'TRANSPORTE', 'PRIVADO', 
            'AUTOMOVIL', 'AUTOMÓVIL', 'TRASERA', 'FRONTAL', 'ESTADO',
            'REPUBLICA', 'REPÚBLICA', 'ESTADOS', 'UNIDOS'
        ]
        
        # MEJORA: Primero intentar combinar textos cercanos que podrían formar una matrícula completa
        combined_texts = []
        for i, text1 in enumerate(text_list):
            if not text1:
                continue
            cleaned1 = re.sub(r'[^A-Z0-9-]', '', str(text1).upper()).replace(' ', '').replace('_', '').replace('.', '')
            
            # Intentar combinar con otros textos
            for j, text2 in enumerate(text_list):
                if i == j or not text2:
                    continue
                cleaned2 = re.sub(r'[^A-Z0-9-]', '', str(text2).upper()).replace(' ', '').replace('_', '').replace('.', '')
                
                # Combinar diferentes formas
                combinations = [
                    cleaned1 + cleaned2,  # VPM + 4532 = VPM4532
                    cleaned1 + '-' + cleaned2,  # VPM + 45-32 = VPM-45-32
                    cleaned1 + '-' + cleaned2 if cleaned1.isalpha() and cleaned2.isdigit() else None,
                    cleaned2 + cleaned1,  # 4532 + VPM = 4532VPM
                ]
                
                for combo in combinations:
                    if combo and len(combo) >= 5:
                        combined_texts.append(combo)
        
        # Agregar textos originales y combinados
        all_texts = list(text_list) + combined_texts
        
        candidates = []
        
        for text in all_texts:
            if not text:
                continue
            
            # Limpiar y normalizar
            cleaned = re.sub(r'[^A-Z0-9-]', '', str(text).upper())
            cleaned = cleaned.replace(' ', '').replace('_', '').replace('.', '')
            
            # FILTRAR: Textos muy cortos (menos de 5 caracteres sin guiones) - probablemente fragmentos
            # Esto filtra "32", "45", "VPM", etc. que son solo partes de la matrícula
            if len(cleaned.replace('-', '')) < 5:
                continue
            
            # FILTRAR: Textos descriptivos conocidos (estados, palabras comunes)
            if cleaned in descriptive_words:
                continue
            
            # FILTRAR: Textos largos solo con letras (probablemente descriptivos)
            if len(cleaned) > 6 and re.match(r'^[A-Z]+$', cleaned):
                continue
            
            # FILTRAR: Solo números (probablemente fragmentos como "32", "45", "28", "96")
            # Rechazar cualquier texto que sea solo números y tenga menos de 5 caracteres
            if re.match(r'^\d+$', cleaned):
                continue  # Rechazar TODOS los números solos, sin importar la longitud
            
            # VALIDAR: Usar regex para verificar si coincide con patrón de matrícula
            matches_plate_pattern = False
            pattern_score = 0
            
            for i, pattern in enumerate(plate_patterns):
                if re.match(pattern, cleaned):
                    matches_plate_pattern = True
                    pattern_score = 100 - (i * 10)  # Primer patrón tiene score más alto
                    break
            
            # Si NO coincide con patrón de matrícula, solo considerar si tiene letras Y números
            if not matches_plate_pattern:
                # Debe tener al menos una letra Y un número para ser candidato
                has_letters = bool(re.search(r'[A-Z]', cleaned))
                has_numbers = bool(re.search(r'[0-9]', cleaned))
                
                if not (has_letters and has_numbers):
                    continue  # Saltar si no tiene ambos
                
                # Validar longitud razonable (priorizar textos más largos)
                length = len(cleaned.replace('-', ''))
                if not (5 <= length <= 12):
                    continue
            else:
                # Si coincide con patrón, calcular longitud
                length = len(cleaned.replace('-', ''))
            
            # Calcular score final
            score = pattern_score  # Score base por coincidir con patrón
            
            # MEJORA: Bonus MUY ALTO por longitud completa (7-10 caracteres sin guiones)
            length_no_dashes = len(cleaned.replace('-', ''))
            if 7 <= length_no_dashes <= 10:
                score += 30  # Aumentado de 15 a 30
            
            # Bonus por tener letras Y números
            if re.search(r'[0-9]', cleaned) and re.search(r'[A-Z]', cleaned):
                score += 20
            
            # Bonus por formato con guiones (más legible) - muy importante
            if '-' in cleaned:
                score += 15  # Aumentado de 5 a 15
            
            # MEJORA: Penalizar textos muy cortos (fragmentos)
            if length_no_dashes < 5:
                score -= 50
            
            candidates.append((cleaned, length_no_dashes, score, matches_plate_pattern))
        
        # ORDENAR: Priorizar candidatos que coincidan con patrón de matrícula Y sean más largos
        if candidates:
            # Ordenar por: 1) Coincide con patrón, 2) Score, 3) Longitud (más largo primero)
            candidates.sort(key=lambda x: (
                not x[3],  # False primero (coincide con patrón)
                -x[2],     # Score descendente
                -x[1]      # Longitud descendente (más largo primero)
            ))
            
            # Retornar el mejor candidato
            return candidates[0][0]
        
        return None
    
    def _extract_plate_number(self, ocr_results: list) -> Optional[str]:
        """
        Extrae y limpia el número de matrícula de los resultados de OCR (formato detallado)
        
        Args:
            ocr_results: Resultados de EasyOCR con detalles [(bbox, text, confidence), ...]
            
        Returns:
            Número de matrícula limpio
        """
        if not ocr_results:
            return None
        
        import re
        
        # Ordenar por confianza
        sorted_results = sorted(ocr_results, key=lambda x: x[2] if len(x) > 2 else 0, reverse=True)
        
        for result in sorted_results:
            if len(result) < 2:
                continue
            
            text = result[1]
            confidence = result[2] if len(result) > 2 else 0.5
            
            # Filtrar resultados con muy baja confianza
            if confidence < 0.3:
                continue
            
            # Limpiar el texto
            cleaned = re.sub(r'[^A-Z0-9-]', '', str(text).upper())
            cleaned = cleaned.replace(' ', '').replace('_', '').replace('.', '')
            
            # Validar formato de matrícula
            if len(cleaned) >= 3 and re.match(r'^[A-Z0-9-]+$', cleaned):
                if 3 <= len(cleaned.replace('-', '')) <= 10:
                    return cleaned
        
        return None
    
    def detect_from_array(self, image_array: 'np.ndarray') -> Optional[str]:
        """
        Detecta matrícula desde un array numpy (útil para video streams)
        
        Args:
            image_array: Array numpy de la imagen
            
        Returns:
            Número de matrícula detectado o None
        """
        # Detectar región de matrícula
        plate_region = detect_plate_region(image_array)
        
        if plate_region is None:
            plate_region = image_array
        
        # Preprocesar para OCR
        processed = preprocess_for_ocr(plate_region)
        
        # Realizar OCR
        results = self.reader.readtext(processed)
        
        if not results:
            return None
        
        # Extraer y limpiar el texto
        plate_number = self._extract_plate_number(results)
        
        return plate_number


def detect_license_plate(image_path: str) -> Optional[str]:
    """
    Función de conveniencia para detectar matrícula en una imagen
    
    Args:
        image_path: Ruta a la imagen
        
    Returns:
        Número de matrícula detectado o None
    """
    detector = LicensePlateDetector()
    return detector.detect_and_recognize(image_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python detect.py <ruta_imagen>")
        sys.exit(1)
    
    # Verificar dependencias antes de continuar
    if not CV2_AVAILABLE:
        print("Error: opencv-python no está instalado")
        print("   Instala con: pip install opencv-python")
        sys.exit(1)
    
    if not NUMPY_AVAILABLE:
        print("Error: numpy no está instalado")
        print("   Instala con: pip install numpy")
        sys.exit(1)
    
    if not EASYOCR_AVAILABLE:
        print("Error: easyocr no está instalado")
        print("   Instala con: pip install easyocr")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        detector = LicensePlateDetector()
        plate_number = detector.detect_and_recognize(image_path)
        
        if plate_number:
            print(f"Matrícula detectada: {plate_number}")
        else:
            print("No se pudo detectar la matrícula")
            print("\nSugerencia: Usa detect_enhanced.py para obtener diagnóstico detallado:")
            print(f"   python ml/detect_enhanced.py {image_path} --debug")
    except Exception as e:
        print(f"Error al procesar la imagen: {e}")
        sys.exit(1)

