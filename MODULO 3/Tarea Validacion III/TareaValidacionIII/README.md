# Algoritmo Genético aplicado al Problema del Viajero (TSP)

**Autor:** Edgar Ochoa Aviles, Herrera Quiñones Abraham Gael
**Materia:** Tarea de Validación III  
**Lenguaje:** Python 3  

https://github.com/edgarochoa00/Topicos-De-Inteligencia-Artificial/tree/main/MODULO%203/Tarea%20Validacion%20III

**Archivos incluidos:**  
(código fuente principal)  


---

##  Descripción general

Este proyecto implementa un **algoritmo genético** para resolver el **Problema del Viajero (TSP)**, un problema clásico de optimización combinatoria.  
El objetivo es **encontrar la ruta más corta** que permita recorrer un conjunto de municipios de México, visitando cada uno exactamente una vez y regresando al punto inicial.

El algoritmo se inspira en los principios de la **evolución natural**, aplicando operadores de **selección, cruce y mutación** sobre una población de rutas para mejorar su calidad generación tras generación.

---

## Fundamento teórico

Un **algoritmo genético (GA)** es una técnica de búsqueda y optimización basada en la evolución biológica.  
Opera sobre una población de soluciones potenciales, seleccionando y recombinando las más aptas mediante operadores genéticos:

| Etapa | Descripción |
|-------|--------------|
| **Inicialización** | Se crean rutas aleatorias (población inicial). |
| **Evaluación (aptitud)** | Se calcula la distancia total de cada ruta (menor distancia = mayor aptitud). |
| **Selección** | Se eligen las rutas más aptas como padres. |
| **Crossover (cruce)** | Se combinan fragmentos de dos rutas para crear nuevas soluciones. |
| **Mutación** | Se intercambian posiciones de ciudades aleatoriamente para mantener diversidad. |
| **Iteración** | El proceso se repite durante varias generaciones, mejorando progresivamente la solución. |

El criterio de aptitud se define como:

\[
Fitness = \frac{1}{Distancia_{total}}
\]

---

##  Estructura del código

El archivo `AG.py` está dividido en módulos bien documentados:

| Módulo | Función principal |
|---------|-------------------|
| **Municipio** | Representa una ciudad con coordenadas (x, y). |
| **Aptitud** | Evalúa la calidad de una ruta según su distancia. |
| **Funciones auxiliares** | Generan rutas, crean población y aplican operadores genéticos. |
| **Algoritmo principal** | Ejecuta el ciclo evolutivo y muestra análisis automático. |

---

##  Datos utilizados

El algoritmo trabaja con 10 **municipios de México**, cuyas coordenadas son aproximadas:

| Municipio | Latitud | Longitud |
|------------|----------|-----------|
| Ciudad de México | 19.43 | -99.13 |
| Guadalajara | 20.67 | -103.35 |
| Monterrey | 25.68 | -100.31 |
| Puebla | 19.04 | -98.20 |
| Toluca | 19.29 | -99.66 |
| Querétaro | 20.59 | -100.39 |
| San Luis Potosí | 22.15 | -100.98 |
| León | 21.12 | -101.68 |
| Morelia | 19.70 | -101.19 |
| Aguascalientes | 21.88 | -102.29 |

---

##  Ejecución del programa

### Requisitos
Asegúrese de tener instalado Python 3 y las librerías necesarias:
```bash
pip install numpy pandas
