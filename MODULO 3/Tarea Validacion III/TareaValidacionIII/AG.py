"""
Algoritmo Genético aplicado al Problema del Viajero (TSP)
---------------------------------------------------------
Autor: Edgar Ochoa

Objetivo:
    Este programa utiliza los principios de los algoritmos genéticos para
    encontrar la ruta más corta que conecta un conjunto de municipios.
    Cada generación mejora las soluciones mediante selección, cruce y mutación.
    El resultado demuestra la optimización progresiva de rutas posibles.

Dependencias:
    - numpy
    - pandas
"""

import random
import numpy as np
import pandas as pd
import operator

# -------------------------------------------------------------------
# Clase Municipio:
# Define un punto geográfico con nombre y coordenadas cartesianas (x, y).
# Se utiliza para calcular distancias entre ciudades aplicando la fórmula
# de Pitágoras. Esta clase permite representar el mapa del problema del
# viajero. Cada municipio es un nodo en el recorrido total a optimizar.
# -------------------------------------------------------------------
class Municipio:
    def __init__(self, nombre, x, y):
        """Inicializa un municipio con nombre y coordenadas (x, y)."""
        self.nombre = nombre
        self.x = x
        self.y = y

    def distancia(self, municipio):
        """
        Calcula la distancia euclidiana entre este municipio y otro usando
        la fórmula: √((x1 - x2)^2 + (y1 - y2)^2). Este cálculo se aplica
        repetidamente para obtener la distancia total de una ruta completa.
        """
        xDis = abs(self.x - municipio.x)
        yDis = abs(self.y - municipio.y)
        return np.sqrt((xDis ** 2) + (yDis ** 2))

    def __repr__(self):
        """
        Devuelve una representación legible del municipio mostrando su nombre
        y coordenadas. Esta función facilita la impresión de rutas completas
        durante la ejecución del algoritmo genético y el análisis de resultados.
        """
        return f"{self.nombre} ({self.x:.2f}, {self.y:.2f})"


# -------------------------------------------------------------------
# Clase Aptitud:
# Evalúa la calidad de una ruta (lista de municipios). Calcula la distancia
# total recorrida y asigna un valor de aptitud proporcional a su eficiencia.
# Una ruta más corta implica una mayor aptitud. Permite comparar soluciones.
# -------------------------------------------------------------------
class Aptitud:
    def __init__(self, ruta):
        """Guarda la ruta y prepara variables para calcular aptitud."""
        self.ruta = ruta
        self.distancia = 0
        self.f_aptitud = 0.0

    def distanciaRuta(self):
        """
        Calcula la distancia total de la ruta sumando las distancias entre
        ciudades consecutivas. Incluye el regreso al punto inicial cerrando
        el ciclo. Almacena el resultado para evitar cálculos repetitivos.
        """
        if self.distancia == 0:
            distancia_total = 0
            for i in range(len(self.ruta)):
                inicio = self.ruta[i]
                fin = self.ruta[(i + 1) % len(self.ruta)]
                distancia_total += inicio.distancia(fin)
            self.distancia = distancia_total
        return self.distancia

    def rutaApta(self):
        """
        Calcula la aptitud como el inverso de la distancia total recorrida.
        Cuanto menor sea la distancia, mayor será el valor del fitness. Este
        valor guía la selección natural del algoritmo en cada generación.
        """
        if self.f_aptitud == 0:
            self.f_aptitud = 1 / float(self.distanciaRuta())
        return self.f_aptitud


# -------------------------------------------------------------------
# Funciones auxiliares:
# Se encargan de generar rutas iniciales, crear la población base y evaluar
# la aptitud de cada individuo. Representan el punto de partida del proceso
# evolutivo del algoritmo genético antes de aplicar operadores genéticos.
# -------------------------------------------------------------------
def crearRuta(listaMunicipios):
    """Crea una ruta aleatoria con todos los municipios sin repetición."""
    return random.sample(listaMunicipios, len(listaMunicipios))

def poblacionInicial(tamanoPob, listaMunicipios):
    """
    Crea una población inicial compuesta por rutas aleatorias. Cada ruta
    representa un individuo dentro del proceso evolutivo. Este paso inicial
    proporciona diversidad genética y evita soluciones sesgadas o repetidas.
    """
    return [crearRuta(listaMunicipios) for _ in range(tamanoPob)]

def clasificacionRutas(poblacion):
    """
    Evalúa la aptitud de todas las rutas generadas en la población. Ordena
    las soluciones de mejor a peor. Este ordenamiento se usa para aplicar
    la selección natural, priorizando las rutas más eficientes (más aptas).
    """
    fitnessResults = {i: Aptitud(poblacion[i]).rutaApta() for i in range(len(poblacion))}
    return sorted(fitnessResults.items(), key=operator.itemgetter(1), reverse=True)


# -------------------------------------------------------------------
# Operadores genéticos:
# Aplican los principios de la evolución biológica. Incluyen la selección de
# las rutas más aptas, el cruce entre padres para generar descendientes y la
# mutación aleatoria que mantiene la diversidad en la población evolutiva.
# -------------------------------------------------------------------
def seleccionRutas(popRanked, indivSeleccionados):
    """
    Selecciona los individuos más aptos usando el método de ruleta ponderada.
    Las rutas con mayor aptitud tienen mayor probabilidad de reproducirse. El
    resultado es una lista de índices de rutas que pasarán a la siguiente fase.
    """
    resultados = []
    df = pd.DataFrame(np.array(popRanked), columns=["Indice", "Aptitud"])
    df["cum_sum"] = df.Aptitud.cumsum()
    df["cum_perc"] = 100 * df.cum_sum / df.Aptitud.sum()
    for i in range(indivSeleccionados):
        resultados.append(popRanked[i][0])
    for _ in range(len(popRanked) - indivSeleccionados):
        sel = 100 * random.random()
        for i in range(len(popRanked)):
            if sel <= df.iat[i, 3]:
                resultados.append(popRanked[i][0])
                break
    return resultados

def grupoApareamiento(poblacion, resultadosSeleccion):
    """
    Crea un grupo de apareamiento con los individuos seleccionados.
    Este grupo se utilizará para generar nuevas combinaciones genéticas
    en la fase de reproducción, manteniendo las características exitosas.
    """
    return [poblacion[i] for i in resultadosSeleccion]

def reproduccion(padre1, padre2):
    """
    Realiza el cruce genético entre dos rutas (padres). Se toma un segmento
    del primer padre y se completa la secuencia con ciudades del segundo.
    Así se genera un hijo con rasgos heredados de ambos progenitores.
    """
    hijoP1 = []
    genX, genY = int(random.random() * len(padre1)), int(random.random() * len(padre2))
    inicio, fin = min(genX, genY), max(genX, genY)
    for i in range(inicio, fin):
        hijoP1.append(padre1[i])
    hijoP2 = [item for item in padre2 if item not in hijoP1]
    return hijoP1 + hijoP2

def reproduccionPoblacion(grupoApareamiento, indivSeleccionados):
    """
    Aplica la reproducción entre los individuos seleccionados. Los mejores
    individuos se conservan sin cambios (elitismo) y el resto se cruza para
    generar hijos. Esto permite balancear estabilidad y exploración genética.
    """
    hijos = []
    tamano = len(grupoApareamiento) - indivSeleccionados
    espacio = random.sample(grupoApareamiento, len(grupoApareamiento))
    for i in range(indivSeleccionados):
        hijos.append(grupoApareamiento[i])
    for i in range(tamano):
        hijo = reproduccion(espacio[i], espacio[len(grupoApareamiento) - i - 1])
        hijos.append(hijo)
    return hijos

def mutacion(individuo, razonMutacion):
    """
    Intercambia posiciones entre dos ciudades con cierta probabilidad. Este
    proceso introduce variabilidad genética, previene la convergencia prematura
    y permite explorar rutas alternativas sin alterar toda la estructura.
    """
    for swapped in range(len(individuo)):
        if random.random() < razonMutacion:
            swapWith = int(random.random() * len(individuo))
            individuo[swapped], individuo[swapWith] = individuo[swapWith], individuo[swapped]
    return individuo

def mutacionPoblacion(poblacion, razonMutacion):
    """
    Aplica la función de mutación a toda la población generada. Este paso
    asegura que cada generación mantenga cierto nivel de diversidad, lo que
    evita que el algoritmo quede atrapado en soluciones locales subóptimas.
    """
    return [mutacion(individuo, razonMutacion) for individuo in poblacion]


# -------------------------------------------------------------------
# Proceso evolutivo:
# Combina selección, cruce y mutación para crear una nueva generación de
# soluciones. Este proceso iterativo constituye el ciclo de evolución que
# caracteriza a los algoritmos genéticos y los aproxima a soluciones óptimas.
# -------------------------------------------------------------------
def nuevaGeneracion(generacionActual, indivSeleccionados, razonMutacion):
    """Genera una nueva generación aplicando selección, cruce y mutación."""
    popRanked = clasificacionRutas(generacionActual)
    seleccionados = seleccionRutas(popRanked, indivSeleccionados)
    grupo = grupoApareamiento(generacionActual, seleccionados)
    hijos = reproduccionPoblacion(grupo, indivSeleccionados)
    return mutacionPoblacion(hijos, razonMutacion)


# -------------------------------------------------------------------
# Función principal del algoritmo genético:
# Ejecuta todo el proceso de evolución, desde la generación inicial hasta
# la final. Muestra resultados explicativos, distancias obtenidas, mejora
# alcanzada y análisis interpretativo de la eficacia del algoritmo.
# -------------------------------------------------------------------
def algoritmoGenetico(poblacion, tamanoPoblacion, indivSeleccionados, razonMutacion, generaciones):
    """Ejecuta el ciclo evolutivo completo y presenta análisis automático."""
    print("\n================ ALGORITMO GENÉTICO TSP ================")
    print("Optimización de ruta mínima entre municipios mexicanos.\n")

    pop = poblacionInicial(tamanoPoblacion, poblacion)
    distancia_inicial = 1 / clasificacionRutas(pop)[0][1]
    print(f"Distancia inicial (población aleatoria): {distancia_inicial:.4f}")

    for i in range(generaciones):
        pop = nuevaGeneracion(pop, indivSeleccionados, razonMutacion)
        if i % 50 == 0:
            mejor = 1 / clasificacionRutas(pop)[0][1]
            print(f"Generación {i:3d} | mejor distancia actual: {mejor:.4f}")

    distancia_final = 1 / clasificacionRutas(pop)[0][1]
    mejorRuta = pop[clasificacionRutas(pop)[0][0]]

    print("\n================ RESULTADOS Y ANÁLISIS =================")
    print(f"Distancia final optimizada: {distancia_final:.4f}")
    mejora = ((distancia_inicial - distancia_final) / distancia_inicial) * 100
    print(f"Mejora total lograda: {mejora:.2f}% respecto a la inicial.\n")
    print("Ruta óptima aproximada encontrada:\n")
    for ciudad in mejorRuta:
        print(" →", ciudad)

    print("\nInterpretación automática del resultado:")
    print(f"- La distancia disminuyó de {distancia_inicial:.2f} a {distancia_final:.2f}.")
    print("- La evolución fue efectiva: las rutas más aptas prevalecieron.")
    print("- Cada ejecución puede variar por la naturaleza aleatoria del algoritmo.")
    print("==========================================================\n")
    return mejorRuta


# -------------------------------------------------------------------
# Conjunto de municipios utilizados (coordenadas reales aproximadas).
# Este conjunto define el mapa sobre el cual se aplicará la optimización.
# -------------------------------------------------------------------
ciudades = [
    Municipio("Ciudad de México", 19.43, -99.13),
    Municipio("Guadalajara", 20.67, -103.35),
    Municipio("Monterrey", 25.68, -100.31),
    Municipio("Puebla", 19.04, -98.20),
    Municipio("Toluca", 19.29, -99.66),
    Municipio("Querétaro", 20.59, -100.39),
    Municipio("San Luis Potosí", 22.15, -100.98),
    Municipio("León", 21.12, -101.68),
    Municipio("Morelia", 19.70, -101.19),
    Municipio("Aguascalientes", 21.88, -102.29)
]

# -------------------------------------------------------------------
# Ejecución principal:
# Llama a la función principal del algoritmo genético con parámetros
# configurables. Imprime el proceso completo de optimización y resultados.
# -------------------------------------------------------------------
if __name__ == "__main__":
    mejorRuta = algoritmoGenetico(
        poblacion=ciudades,
        tamanoPoblacion=100,
        indivSeleccionados=20,
        razonMutacion=0.01,
        generaciones=300
    )
