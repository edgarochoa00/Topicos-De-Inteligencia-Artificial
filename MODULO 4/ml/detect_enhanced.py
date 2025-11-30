"""
Módulo mejorado de detección con diagnóstico detallado
Proporciona información sobre por qué falla la detección
"""
from typing import Optional, Tuple, Dict, List, TYPE_CHECKING
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


class EnhancedLicensePlateDetector:
    """
    Detector mejorado con diagnóstico detallado
    """
    
    def __init__(self, languages: list = ['en'], debug: bool = False):
        """
        Inicializa el detector
        
        Args:
            languages: Lista de idiomas para OCR
            debug: Modo debug para mostrar información detallada
        """
        if not EASYOCR_AVAILABLE:
            raise ImportError(
                "easyocr no está instalado. Por favor, instálalo ejecutando: "
                "pip install easyocr"
            )
        
        self.debug = debug
        self.diagnosis = {
            'strategies_tried': [],
            'errors': [],
            'warnings': [],
            'image_info': {},
            'ocr_results': []
        }
        
        if self.debug:
            print("Inicializando detector de matrículas (modo debug)...")
        # OPTIMIZACIÓN: Configurar EasyOCR para máxima velocidad
        self.reader = easyocr.Reader(
            languages, 
            gpu=False,
            verbose=False,
            quantize=True,
            cudnn_benchmark=False,
            model_storage_directory=None,
            download_enabled=True
        )
        if self.debug:
            print("Detector inicializado (modo rápido)")
    
    def detect_with_diagnosis(self, image_path: str, use_expert_mode: bool = False) -> Dict:
        """
        Detecta matrícula con diagnóstico completo
        
        Returns:
            Dict con 'plate_number', 'success', 'diagnosis'
        """
        self.diagnosis = {
            'strategies_tried': [],
            'errors': [],
            'warnings': [],
            'image_info': {},
            'ocr_results': [],
            'recommendations': []
        }
        
        if not CV2_AVAILABLE:
            self.diagnosis['errors'].append("OpenCV no está disponible")
            return {
                'plate_number': None,
                'success': False,
                'diagnosis': self.diagnosis
            }
        
        # Validar que el archivo existe
        if not os.path.exists(image_path):
            self.diagnosis['errors'].append(f"La imagen no existe: {image_path}")
            return {
                'plate_number': None,
                'success': False,
                'diagnosis': self.diagnosis
            }
        
        # Cargar y analizar imagen
        image = cv2.imread(image_path)
        if image is None:
            self.diagnosis['errors'].append(
                f"No se pudo cargar la imagen: {image_path}. "
                "Verifica que sea un formato válido (JPG, PNG, BMP, etc.)"
            )
            return {
                'plate_number': None,
                'success': False,
                'diagnosis': self.diagnosis
            }
        
        # Validar que la imagen tenga contenido
        if image.size == 0:
            self.diagnosis['errors'].append(f"La imagen está vacía o corrupta: {image_path}")
            return {
                'plate_number': None,
                'success': False,
                'diagnosis': self.diagnosis
            }
        
        # Información de la imagen (convertir a tipos nativos)
        height, width = image.shape[:2]
        self.diagnosis['image_info'] = {
            'width': int(width),
            'height': int(height),
            'channels': int(image.shape[2]) if len(image.shape) == 3 else 1,
            'aspect_ratio': float(width / height if height > 0 else 0)
        }
        
        # Validar calidad de imagen
        self._validate_image_quality(image)
        
        # Estrategia 1: Detectar región y procesar
        self.diagnosis['strategies_tried'].append({
            'name': 'Detección de región + OCR preprocesado',
            'status': 'trying'
        })
        
        try:
            plate_region = detect_plate_region(image)
            
            if plate_region is not None:
                region_h, region_w = plate_region.shape[:2]
                self.diagnosis['strategies_tried'][-1]['region_detected'] = True
                self.diagnosis['strategies_tried'][-1]['region_size'] = f"{int(region_w)}x{int(region_h)}"
                
                processed = preprocess_for_ocr(plate_region)
                if processed is not None and processed.size > 0:
                    # MEJORA: Parámetros optimizados para OCR - priorizar texto más grande
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
                    self.diagnosis['ocr_results'].append({
                        'strategy': 'region_preprocessed',
                        'results': results
                    })
                    
                    if results:
                        plate_number = self._extract_plate_number_from_results(results)
                        if plate_number:
                            self.diagnosis['strategies_tried'][-1]['status'] = 'success'
                            self.diagnosis['strategies_tried'][-1]['plate_number'] = plate_number
                            return {
                                'plate_number': plate_number,
                                'success': True,
                                'diagnosis': self.diagnosis
                            }
                    
                    self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                    self.diagnosis['strategies_tried'][-1]['reason'] = f"No se encontró texto válido en región ({len(results)} resultados)"
                else:
                    self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                    self.diagnosis['strategies_tried'][-1]['reason'] = 'Error en preprocesamiento de región'
            else:
                self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                self.diagnosis['strategies_tried'][-1]['reason'] = 'No se pudo detectar región de matrícula'
                self.diagnosis['warnings'].append("No se detectó región específica de matrícula, probando en imagen completa")
        except Exception as e:
            self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
            self.diagnosis['strategies_tried'][-1]['reason'] = f"Error: {str(e)}"
            self.diagnosis['errors'].append(f"Error en estrategia 1: {str(e)}")
        
        # Estrategia 2: Procesar toda la imagen
        self.diagnosis['strategies_tried'].append({
            'name': 'OCR en imagen completa preprocesada',
            'status': 'trying'
        })
        
        try:
            processed_full = preprocess_for_ocr(image)
            if processed_full is not None and processed_full.size > 0:
                # MEJORA: Parámetros optimizados - priorizar texto más grande
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
                self.diagnosis['ocr_results'].append({
                    'strategy': 'full_preprocessed',
                    'results': results_full
                })
                
                if results_full:
                    plate_number = self._extract_plate_number_from_results(results_full)
                    if plate_number:
                        self.diagnosis['strategies_tried'][-1]['status'] = 'success'
                        self.diagnosis['strategies_tried'][-1]['plate_number'] = plate_number
                        return {
                            'plate_number': plate_number,
                            'success': True,
                            'diagnosis': self.diagnosis
                        }
                
                self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                self.diagnosis['strategies_tried'][-1]['reason'] = f"Texto encontrado pero no válido como matrícula ({len(results_full)} resultados)"
            else:
                self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                self.diagnosis['strategies_tried'][-1]['reason'] = 'Error en preprocesamiento de imagen completa'
        except Exception as e:
            self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
            self.diagnosis['strategies_tried'][-1]['reason'] = f"Error: {str(e)}"
            self.diagnosis['errors'].append(f"Error en estrategia 2: {str(e)}")
        
        # Estrategia 3: OCR directo
        self.diagnosis['strategies_tried'].append({
            'name': 'OCR directo en imagen original',
            'status': 'trying'
        })
        
        try:
            # Convertir a RGB si es necesario (EasyOCR espera RGB)
            if len(image.shape) == 2:
                image_for_ocr = image
            else:
                image_for_ocr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # MEJORA: Parámetros optimizados para OCR directo - priorizar texto más grande
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
            self.diagnosis['ocr_results'].append({
                'strategy': 'direct',
                'results': results_direct
            })
            
            if results_direct:
                plate_number = self._extract_plate_number_from_results(results_direct)
                if plate_number:
                    self.diagnosis['strategies_tried'][-1]['status'] = 'success'
                    self.diagnosis['strategies_tried'][-1]['plate_number'] = plate_number
                    return {
                        'plate_number': plate_number,
                        'success': True,
                        'diagnosis': self.diagnosis
                    }
            
            self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
            self.diagnosis['strategies_tried'][-1]['reason'] = f"OCR no encontró texto válido ({len(results_direct)} resultados)"
        except Exception as e:
            error_msg = str(e)
            self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
            self.diagnosis['strategies_tried'][-1]['reason'] = f"Error en OCR: {error_msg}"
            self.diagnosis['errors'].append(f"Error en estrategia 3 (OCR directo): {error_msg}")
            
            # Si es el error de "pattern", agregar información específica
            if 'pattern' in error_msg.lower() or 'string' in error_msg.lower():
                self.diagnosis['warnings'].append(
                    "Error de formato de imagen detectado. La imagen puede estar corrupta o en un formato no soportado."
                )
        
        # Estrategia 4: Rotaciones
        for angle in [-10, -5, 5, 10]:
            self.diagnosis['strategies_tried'].append({
                'name': f'OCR con rotación {angle}°',
                'status': 'trying'
            })
            
            try:
                rotated = self._rotate_image(image, angle)
                if len(rotated.shape) == 2:
                    rotated_for_ocr = rotated
                else:
                    rotated_for_ocr = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
                
                # MEJORA: Parámetros optimizados para rotaciones - priorizar texto más grande
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
                        self.diagnosis['strategies_tried'][-1]['status'] = 'success'
                        self.diagnosis['strategies_tried'][-1]['plate_number'] = plate_number
                        return {
                            'plate_number': plate_number,
                            'success': True,
                            'diagnosis': self.diagnosis
                        }
                
                self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                self.diagnosis['strategies_tried'][-1]['reason'] = f"No se encontró matrícula válida"
            except Exception as e:
                self.diagnosis['strategies_tried'][-1]['status'] = 'failed'
                self.diagnosis['strategies_tried'][-1]['reason'] = f"Error: {str(e)}"
        
        # Generar recomendaciones
        self._generate_recommendations()
        
        return {
            'plate_number': None,
            'success': False,
            'diagnosis': self.diagnosis
        }
    
    def _validate_image_quality(self, image: 'np.ndarray'):
        """Valida la calidad de la imagen y genera advertencias"""
        height, width = image.shape[:2]
        width_int = int(width)
        height_int = int(height)
        
        # Resolución muy baja
        if width_int < 320 or height_int < 240:
            self.diagnosis['warnings'].append(
                f"Resolución muy baja ({width_int}x{height_int}). Recomendado: mínimo 640x480"
            )
        
        # Imagen muy pequeña
        if width_int * height_int < 100000:
            self.diagnosis['warnings'].append(
                "Imagen muy pequeña. Puede afectar la detección"
            )
        
        # Verificar contraste
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        std_dev = float(np.std(gray))
        if std_dev < 20:
            self.diagnosis['warnings'].append(
                f"Bajo contraste detectado (std: {std_dev:.1f}). La imagen puede estar muy oscura o muy clara"
            )
        
        # Verificar brillo
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 30:
            self.diagnosis['warnings'].append(
                f"Imagen muy oscura (brillo promedio: {mean_brightness:.1f})"
            )
        elif mean_brightness > 225:
            self.diagnosis['warnings'].append(
                f"Imagen muy brillante (brillo promedio: {mean_brightness:.1f})"
            )
    
    def _extract_plate_number_from_results(self, results: List) -> Optional[str]:
        """Extrae número de matrícula de resultados de OCR (mejorado) - Prioriza texto más grande"""
        import re
        
        # MEJORA: Procesar todos y elegir el mejor, priorizando tamaño de texto
        candidates = []
        
        for result in results:
            if len(result) < 2:
                continue
            
            text = result[1]
            confidence = result[2] if len(result) > 2 else 0.5
            
            # MEJORA: Obtener tamaño del bounding box si está disponible (result[0])
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
            
            # MEJORA: Umbral de confianza más flexible (0.2 en lugar de 0.3)
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
            
            # MEJORA: Priorizar texto más ancho (matrículas suelen ser más anchas que altas)
            if text_width > 0 and text_height > 0:
                aspect_ratio = text_width / text_height
                if 2.0 <= aspect_ratio <= 8.0:  # Matrículas suelen ser más anchas
                    score += 25  # Bonus significativo por formato horizontal
            
            # Bonus por tener letras Y números (matrícula completa)
            if re.search(r'[0-9]', cleaned) and re.search(r'[A-Z]', cleaned):
                score += 20
            
            # Bonus por longitud típica (7-10 caracteres sin guiones)
            if 7 <= length <= 10:
                score += 15
            
            # Bonus por formato con guiones (más legible)
            if '-' in cleaned:
                score += 5
            
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
    
    def _rotate_image(self, image: 'np.ndarray', angle: float) -> 'np.ndarray':
        """Rota una imagen"""
        if not CV2_AVAILABLE:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, matrix, (width, height),
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    def _generate_recommendations(self):
        """Genera recomendaciones basadas en el diagnóstico"""
        recommendations = []
        
        # Analizar resultados de OCR
        all_texts = []
        for ocr_result in self.diagnosis['ocr_results']:
            for result in ocr_result.get('results', []):
                if len(result) >= 2:
                    all_texts.append(result[1])
        
        if not all_texts:
            recommendations.append("No se detectó ningún texto. Verifica que:")
            recommendations.append("   - La imagen contenga una matrícula visible")
            recommendations.append("   - La matrícula esté enfocada y legible")
            recommendations.append("   - La iluminación sea adecuada")
        else:
            recommendations.append(f"Se detectó texto pero no se reconoció como matrícula válida")
            recommendations.append(f"   Textos encontrados: {', '.join(all_texts[:5])}")
            recommendations.append("   Posibles causas:")
            recommendations.append("   - La matrícula está parcialmente oculta")
            recommendations.append("   - El formato no coincide con el esperado")
            recommendations.append("   - La calidad de imagen es insuficiente")
        
        # Recomendaciones basadas en advertencias
        if any('baja' in w.lower() or 'pequeña' in w.lower() for w in self.diagnosis['warnings']):
            recommendations.append("Mejora la calidad de la imagen:")
            recommendations.append("   - Acércate más a la matrícula")
            recommendations.append("   - Usa una resolución más alta (mínimo 640x480)")
        
        if any('contraste' in w.lower() or 'oscura' in w.lower() or 'brillante' in w.lower() for w in self.diagnosis['warnings']):
            recommendations.append("Mejora la iluminación:")
            recommendations.append("   - Asegúrate de tener buena iluminación")
            recommendations.append("   - Evita reflejos excesivos")
            recommendations.append("   - Evita sombras sobre la matrícula")
        
        if not any(s['status'] == 'success' for s in self.diagnosis['strategies_tried']):
            recommendations.append("Intenta:")
            recommendations.append("   - Tomar la foto desde un ángulo más frontal")
            recommendations.append("   - Asegurar que la matrícula esté horizontal")
            recommendations.append("   - Verificar que la matrícula esté completa y visible")
        
        self.diagnosis['recommendations'] = recommendations


def detect_with_diagnosis(image_path: str, debug: bool = False) -> Dict:
    """
    Función de conveniencia para detección con diagnóstico
    
    Args:
        image_path: Ruta a la imagen
        debug: Mostrar información detallada
        
    Returns:
        Dict con resultados y diagnóstico
    """
    detector = EnhancedLicensePlateDetector(debug=debug)
    return detector.detect_with_diagnosis(image_path)


def convert_to_serializable(obj):
    """
    Convierte objetos numpy y otros tipos no serializables a tipos nativos de Python
    """
    import numpy as np
    
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, set):
        return list(obj)
    else:
        return obj


if __name__ == "__main__":
    import sys
    import json
    import traceback
    
    if len(sys.argv) < 2:
        print("Uso: python detect_enhanced.py <ruta_imagen> [--debug]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    debug = '--debug' in sys.argv
    
    try:
        if debug:
            print(f"Iniciando detección en: {image_path}")
        
        result = detect_with_diagnosis(image_path, debug=debug)
        
        if debug:
            print("Detección completada")
        
        # Salida en formato JSON para API
        if '--json' in sys.argv:
            # Convertir todos los tipos numpy a tipos nativos antes de serializar
            serializable_result = convert_to_serializable(result)
            print(json.dumps(serializable_result, indent=2, ensure_ascii=False))
        else:
            # Salida legible para humanos
            if result['success']:
                print(f"Matrícula detectada: {result['plate_number']}")
                if debug:
                    serializable_result = convert_to_serializable(result)
                    print(json.dumps(serializable_result, indent=2, ensure_ascii=False))
            else:
                print("No se pudo detectar la matrícula\n")
                print("=" * 60)
                print("DIAGNÓSTICO:")
                print("=" * 60)
                
                print("\nInformación de la imagen:")
                for key, value in result['diagnosis']['image_info'].items():
                    print(f"   {key}: {value}")
                
                if result['diagnosis']['warnings']:
                    print("\nAdvertencias:")
                    for warning in result['diagnosis']['warnings']:
                        print(f"   - {warning}")
                
                if result['diagnosis']['errors']:
                    print("\nErrores:")
                    for error in result['diagnosis']['errors']:
                        print(f"   - {error}")
                
                print("\nEstrategias probadas:")
                for i, strategy in enumerate(result['diagnosis']['strategies_tried'], 1):
                    status_text = "OK" if strategy['status'] == 'success' else "Fallo"
                    print(f"   {i}. [{status_text}] {strategy['name']}")
                    if strategy['status'] == 'failed' and 'reason' in strategy:
                        print(f"      Razón: {strategy['reason']}")
                
                if result['diagnosis']['recommendations']:
                    print("\nRecomendaciones:")
                    for rec in result['diagnosis']['recommendations']:
                        print(f"   {rec}")
                
                if debug:
                    print("\nDetalles de OCR (modo debug):")
                    for ocr_result in result['diagnosis']['ocr_results']:
                        print(f"   Estrategia: {ocr_result['strategy']}")
                        for result_item in ocr_result['results'][:3]:
                            if len(result_item) >= 2:
                                text = result_item[1]
                                conf = result_item[2] if len(result_item) > 2 else 0
                                print(f"      - '{text}' (confianza: {conf:.2f})")
                
                # También imprimir JSON para que la API lo capture
                print("\n" + "=" * 60)
                print("JSON OUTPUT:")
                serializable_result = convert_to_serializable(result)
                print(json.dumps(serializable_result, indent=2, ensure_ascii=False))
    
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        error_msg = {
            'success': False,
            'plate_number': None,
            'error': str(e),
            'error_type': type(e).__name__,
            'diagnosis': {
                'errors': [f"Error fatal: {str(e)}"],
                'traceback': traceback.format_exc() if debug else None
            }
        }
        
        if '--json' in sys.argv:
            print(json.dumps(error_msg, indent=2, ensure_ascii=False))
        else:
            print(f"Error fatal: {e}", file=sys.stderr)
            if debug:
                print("\nTraceback completo:", file=sys.stderr)
                traceback.print_exc()
        
        sys.exit(1)

