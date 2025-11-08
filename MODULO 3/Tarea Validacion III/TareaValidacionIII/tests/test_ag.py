import random

from AG import (
    Aptitud,
    algoritmoGenetico,
    clasificacionRutas,
    grupoApareamiento,
    municipio,
    mutacion,
    poblacionInicial,
    reproduccion,
    seleccionRutas,
)


def _ciudades():
    return [
        municipio(0, 0),
        municipio(0, 3),
        municipio(4, 0),
        municipio(4, 3),
    ]


def test_distancia_total_coincide_con_aptitud():
    ruta = _ciudades()
    aptitud = Aptitud(ruta)
    distancia = aptitud.distanciaRuta()
    assert round(1 / aptitud.rutaApta(), 6) == round(distancia, 6)


def test_seleccion_mantiene_elite():
    random.seed(10)
    poblacion = poblacionInicial(5, _ciudades())
    rank = clasificacionRutas(poblacion)
    seleccionados = seleccionRutas(rank, indivSelecionados=2)
    assert set(seleccionados[:2]) == {rank[0][0], rank[1][0]}
    assert len(seleccionados) == len(rank)


def test_reproduccion_genera_descendencia_sin_perdidas():
    random.seed(3)
    padres = poblacionInicial(2, _ciudades())
    hijo = reproduccion(padres[0], padres[1])
    assert len(hijo) == len(padres[0])
    assert set(hijo) == set(padres[0])


def test_mutacion_preserva_conjunto_de_municipios():
    random.seed(4)
    individuo = _ciudades()
    mutado = mutacion(individuo[:], 0.9)
    assert set(mutado) == set(individuo)


def test_algoritmo_genetico_retorna_ruta_valida():
    random.seed(5)
    mejor_ruta = algoritmoGenetico(
        poblacion=_ciudades(),
        tamanoPoblacion=20,
        indivSelecionados=4,
        razonMutacion=0.05,
        generaciones=50,
        verbose=False,
    )
    assert len(mejor_ruta) == len(_ciudades())
    coords_resultado = {(m.x, m.y) for m in mejor_ruta}
    coords_objetivo = {(m.x, m.y) for m in _ciudades()}
    assert coords_resultado == coords_objetivo
