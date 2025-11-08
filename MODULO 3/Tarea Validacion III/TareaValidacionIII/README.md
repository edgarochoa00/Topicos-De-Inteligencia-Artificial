## Algoritmo Genético para Rutas TSP

Este repositorio contiene una reimplementación completa del algoritmo genético que se entregó originalmente. Se respetó el flujo del ejemplo base (mismas clases `municipio`/`Aptitud`, uso de NumPy + Pandas, selección por ruleta con elitismo, crossover parcial y mutación por intercambio) añadiendo únicamente modularización ligera y comentarios.

### Requisitos

- Python 3.10 o superior.
- Dependencias base del algoritmo (se preservaron porque forman parte del ejemplo original):
  - `numpy`
  - `pandas`
- `pytest` (solo para ejecutar las pruebas formales).

Instale todo con:

```bash
python -m pip install --upgrade numpy pandas pytest
```

### Cómo ejecutar el algoritmo

1. Defina los municipios que desea visitar editando la lista `ciudades` en `AG.py` o importando `municipio` y `algoritmoGenetico` desde otro script.
2. Ejecute el archivo principal:

```bash
python AG.py
```

El script imprimirá la mejor ruta encontrada y su distancia aproximada.

### Estructura del código

- `AG.py`: implementación modular del GA con funciones para inicializar poblaciones, evaluar aptitud, selección, crossover, mutación y generación de nuevos individuos. Incluye docstrings y comentarios para facilitar su mantenimiento.
- `tests/test_ag.py`: conjunto de pruebas unitarias que validan la función de aptitud, la preservación de élites en la selección, la validez de los hijos generados y la correcta aplicación de mutaciones.

### Ejecutar pruebas formales

```bash
python -m pytest
```

Las pruebas verifican:

- Cálculo correcto de distancias (función de aptitud).
- Que la selección respeta el elitismo y mantiene el tamaño de la población.
- Que crossover y mutación producen rutas con los mismos municipios, evitando duplicados o pérdidas.

### Documentación rápida de funciones

- `algoritmoGenetico(...)`: orquesta todo el ciclo evolutivo y devuelve la mejor ruta hallada tras las generaciones configuradas.
- `nuevaGeneracion(...)`: aplica selección, reproducción y mutación para formar una generación completa a partir de la población actual.
- `Aptitud`: encapsula el cálculo de distancias y fitness para reutilizarlo en pruebas y durante el ranking de rutas.

Cada función clave incluye docstrings y comentarios mínimos que describen su propósito y decisiones no obvias. Esto facilita que cualquier lector siga el flujo sin consultar documentación externa.
