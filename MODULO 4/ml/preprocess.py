"""
Módulo de preprocesamiento de imágenes para reconocimiento de matrículas
Incluye normalización, redimensionamiento y mejora de contraste
"""
from typing import Tuple, Optional, TYPE_CHECKING

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


def normalize_image(image: 'np.ndarray') -> 'np.ndarray':
    """
    Normaliza la imagen a valores entre 0 y 1
    
    Args:
        image: Imagen en formato numpy array
        
    Returns:
        Imagen normalizada
    """
    if image.dtype != np.float32:
        image = image.astype(np.float32)
    
    if image.max() > 1.0:
        image = image / 255.0
    
    return image


def resize_image(image: 'np.ndarray', target_size: Tuple[int, int] = (224, 224)) -> 'np.ndarray':
    """
    Redimensiona la imagen a un tamaño consistente
    
    Args:
        image: Imagen original
        target_size: Tamaño objetivo (ancho, alto)
        
    Returns:
        Imagen redimensionada
    """
    return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)


def enhance_contrast(image: 'np.ndarray', method: str = 'clahe') -> 'np.ndarray':
    """
    Mejora el contraste de la imagen
    
    Args:
        image: Imagen original
        method: Método de mejora ('clahe', 'histogram', 'adaptive')
        
    Returns:
        Imagen con contraste mejorado
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    if method == 'clahe':
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
    elif method == 'histogram':
        # Ecualización de histograma
        enhanced = cv2.equalizeHist(gray)
    elif method == 'adaptive':
        # Mejora adaptativa
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
    else:
        enhanced = gray
    
    return enhanced


def preprocess_for_detection(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> 'np.ndarray':
    """
    Preprocesa una imagen completa para detección de matrícula
    
    Args:
        image_path: Ruta a la imagen
        target_size: Tamaño objetivo
        
    Returns:
        Imagen preprocesada lista para el modelo
    """
    # Cargar imagen
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")
    
    # Mejorar contraste
    enhanced = enhance_contrast(image)
    
    # Convertir a RGB si es necesario
    if len(enhanced.shape) == 2:
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    
    # Redimensionar
    resized = resize_image(enhanced, target_size)
    
    # Normalizar
    normalized = normalize_image(resized)
    
    return normalized


def preprocess_for_ocr(plate_region: 'np.ndarray') -> 'np.ndarray':
    """
    Preprocesa una región de matrícula para OCR con técnicas avanzadas optimizadas para velocidad
    
    Args:
        plate_region: Región de la imagen que contiene la matrícula
        
    Returns:
        Imagen preprocesada optimizada para OCR
    """
    if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
        return plate_region
    
    # Convertir a escala de grises si es necesario
    if len(plate_region.shape) == 3:
        gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_region.copy()
    
    # MEJORA: Redimensionar de forma más inteligente para velocidad y calidad
    height, width = gray.shape
    min_height, max_height = 80, 400  # Aumentado para mejor calidad
    min_width, max_width = 200, 1200  # Aumentado para mejor calidad
    
    # Asegurar tamaño óptimo para OCR (más grande = mejor reconocimiento)
    if height < min_height or width < min_width:
        scale = max(min_height / height, min_width / width) * 2.5  # Más agresivo
        new_width = int(width * scale)
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    elif height > max_height or width > max_width:
        scale = min(max_height / height, max_width / width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)  # Más rápido
    
    # Pipeline original para máxima precisión (con optimizaciones menores que no afectan calidad)
    # CLAHE optimizado (tileGridSize más grande solo si la imagen es grande)
    if height * width > 100000:  # Solo para imágenes grandes
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16, 16))  # Tiles más grandes = más rápido
    else:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))  # Original para imágenes pequeñas
    enhanced = clahe.apply(gray)
    
    # Bilateral filter original (necesario para precisión)
    denoised = cv2.bilateralFilter(enhanced, 5, 50, 50)
    
    # Normalización (necesaria para precisión)
    normalized = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX)
    
    # Umbral adaptativo original (mejor precisión)
    thresh = cv2.adaptiveThreshold(
        normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 8  # Original: mejor precisión
    )
    
    # Operaciones morfológicas originales (necesarias para precisión)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    return thresh


def detect_plate_region(image: 'np.ndarray') -> Optional['np.ndarray']:
    """
    Detecta la región de la matrícula en una imagen usando múltiples estrategias
    
    Args:
        image: Imagen completa
        
    Returns:
        Región de la matrícula o None si no se encuentra
    """
    if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
        return None
    
    # Estrategia 1: Detección por contornos (método original mejorado)
    region = _detect_by_contours(image)
    if region is not None:
        return region
    
    # Estrategia 2: Detección por color (matrículas suelen ser claras u oscuras)
    region = _detect_by_color(image)
    if region is not None:
        return region
    
    # Estrategia 3: Detección por textura (regiones con mucho texto)
    region = _detect_by_texture(image)
    if region is not None:
        return region
    
    # Estrategia 4: Usar toda la imagen si es pequeña o recortar región central
    height, width = image.shape[:2]
    if width < 800 and height < 600:
        return image
    
    # Recortar región central (donde suelen estar las matrículas)
    center_y, center_x = height // 2, width // 2
    crop_height, crop_width = int(height * 0.6), int(width * 0.8)
    y1 = max(0, center_y - crop_height // 2)
    y2 = min(height, center_y + crop_height // 2)
    x1 = max(0, center_x - crop_width // 2)
    x2 = min(width, center_x + crop_width // 2)
    
    return image[y1:y2, x1:x2]


def _detect_by_contours(image: 'np.ndarray') -> Optional['np.ndarray']:
    """Detección por contornos mejorada"""
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Múltiples intentos con diferentes parámetros
    for blur_size in [11, 15, 9]:
        for canny_low, canny_high in [(30, 200), (50, 150), (20, 100)]:
            blurred = cv2.bilateralFilter(gray, blur_size, 17, 17)
            edged = cv2.Canny(blurred, canny_low, canny_high)
            
            # Dilatar para conectar líneas
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edged, kernel, iterations=1)
            
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]
            
            for contour in contours:
                peri = cv2.arcLength(contour, True)
                if peri < 100:
                    continue
                
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h) if h > 0 else 0
                    area = cv2.contourArea(contour)
                    extent = area / float(w * h) if (w * h) > 0 else 0
                    
                    # Criterios más flexibles para matrículas
                    if (1.5 <= aspect_ratio <= 6.0 and 
                        extent > 0.5 and 
                        w > 50 and h > 15):
                        # Agregar margen
                        margin = 10
                        y1 = max(0, y - margin)
                        y2 = min(image.shape[0], y + h + margin)
                        x1 = max(0, x - margin)
                        x2 = min(image.shape[1], x + w + margin)
                        return image[y1:y2, x1:x2]
    
    return None


def _detect_by_color(image: 'np.ndarray') -> Optional['np.ndarray']:
    """Detección por color (matrículas suelen tener alto contraste)"""
    if len(image.shape) != 3:
        return None
    
    # Convertir a diferentes espacios de color
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Buscar regiones con alto contraste
    # Matrículas claras (blancas/amarillas)
    lower_light = np.array([0, 0, 200])
    upper_light = np.array([180, 30, 255])
    mask_light = cv2.inRange(hsv, lower_light, upper_light)
    
    # Matrículas oscuras (negras/grises oscuros)
    _, mask_dark = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Combinar máscaras
    mask = cv2.bitwise_or(mask_light, mask_dark)
    
    # Encontrar contornos en la máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    # Buscar el contorno más grande con forma rectangular
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h) if h > 0 else 0
        
        if 1.5 <= aspect_ratio <= 6.0 and w > 50 and h > 15:
            margin = 15
            y1 = max(0, y - margin)
            y2 = min(image.shape[0], y + h + margin)
            x1 = max(0, x - margin)
            x2 = min(image.shape[1], x + w + margin)
            return image[y1:y2, x1:x2]
    
    return None


def _detect_by_texture(image: 'np.ndarray') -> Optional['np.ndarray']:
    """Detección por textura (regiones con muchas líneas horizontales)"""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Detectar líneas horizontales (caracteres de matrícula)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    detected_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Encontrar regiones con muchas líneas
    contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    # Agrupar contornos cercanos
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 100]
    if not boxes:
        return None
    
    # Encontrar el rectángulo que agrupa las cajas
    x_min = min(b[0] for b in boxes)
    y_min = min(b[1] for b in boxes)
    x_max = max(b[0] + b[2] for b in boxes)
    y_max = max(b[1] + b[3] for b in boxes)
    
    w, h = x_max - x_min, y_max - y_min
    aspect_ratio = w / float(h) if h > 0 else 0
    
    if 1.5 <= aspect_ratio <= 6.0 and w > 50 and h > 15:
        margin = 20
        y1 = max(0, y_min - margin)
        y2 = min(image.shape[0], y_max + margin)
        x1 = max(0, x_min - margin)
        x2 = min(image.shape[1], x_max + margin)
        return image[y1:y2, x1:x2]
    
    return None

