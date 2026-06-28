"""Testes do utilitário de interpolação de tabelas de norma (Fase 5).

Valores de referência calculados à mão (TDD). Princípio da abstenção:
fora do domínio tabelado -> ValueError (sem extrapolar).
"""

import math

import pytest

from lib.math.interpolation import bilinear_interp, linear_interp, nearest


# --- linear_interp: casos nominais ------------------------------------------
def test_linear_interp_ponto_medio():
    # entre xs=2 (y=20) e xs=3 (y=30): t=0.5 -> 25
    assert linear_interp(2.5, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(25.0)


def test_linear_interp_ponto_exato_interior_devolve_proprio_y():
    assert linear_interp(3.0, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(30.0)


def test_linear_interp_extremos_exatos():
    assert linear_interp(1.0, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(10.0)
    assert linear_interp(4.0, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(40.0)


def test_linear_interp_intervalo_nao_uniforme():
    # xs=[10,20,30], ys=[100,400,900]; x=15 entre 10 e 20: t=0.5 -> 250
    assert linear_interp(15.0, [10, 20, 30], [100, 400, 900]) == pytest.approx(250.0)


def test_linear_interp_dois_pontos():
    assert linear_interp(1.5, [1.0, 2.0], [0.0, 10.0]) == pytest.approx(5.0)


# --- linear_interp: erros (princípio da abstenção) --------------------------
def test_linear_interp_abaixo_do_dominio_levanta():
    with pytest.raises(ValueError):
        linear_interp(0.5, [1, 2, 3, 4], [10, 20, 30, 40])


def test_linear_interp_acima_do_dominio_levanta():
    with pytest.raises(ValueError):
        linear_interp(5.0, [1, 2, 3, 4], [10, 20, 30, 40])


def test_linear_interp_tamanhos_diferentes_levanta():
    with pytest.raises(ValueError):
        linear_interp(2.0, [1, 2, 3], [10, 20])


def test_linear_interp_xs_desordenado_levanta():
    with pytest.raises(ValueError):
        linear_interp(2.0, [1, 3, 2, 4], [10, 30, 20, 40])


def test_linear_interp_xs_com_repeticao_levanta():
    with pytest.raises(ValueError):
        linear_interp(2.0, [1, 2, 2, 4], [10, 20, 25, 40])


def test_linear_interp_lista_curta_levanta():
    with pytest.raises(ValueError):
        linear_interp(1.0, [1.0], [10.0])


# --- bilinear_interp: casos nominais ----------------------------------------
def test_bilinear_centro_da_celula_eh_media_dos_quatro_cantos():
    # grid[i][j]: i<->xs, j<->ys
    xs = [0.0, 1.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    assert bilinear_interp(0.5, 0.5, xs, ys, grid) == pytest.approx(1.5)


def test_bilinear_cantos_devolvem_valor_do_no():
    xs = [0.0, 1.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    assert bilinear_interp(0.0, 0.0, xs, ys, grid) == pytest.approx(0.0)
    assert bilinear_interp(1.0, 1.0, xs, ys, grid) == pytest.approx(3.0)
    assert bilinear_interp(0.0, 1.0, xs, ys, grid) == pytest.approx(1.0)
    assert bilinear_interp(1.0, 0.0, xs, ys, grid) == pytest.approx(2.0)


def test_bilinear_meio_de_aresta():
    xs = [0.0, 1.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    # aresta inferior (y=0): media de grid[0][0] e grid[1][0]
    assert bilinear_interp(0.5, 0.0, xs, ys, grid) == pytest.approx(1.0)
    # aresta esquerda (x=0): media de grid[0][0] e grid[0][1]
    assert bilinear_interp(0.0, 0.5, xs, ys, grid) == pytest.approx(0.5)


def test_bilinear_exato_para_plano_f_igual_x_mais_y():
    # bilinear reproduz exatamente f(x,y)=x+y
    xs = [0.0, 2.0, 5.0]
    ys = [0.0, 4.0, 10.0]
    grid = [[x + y for y in ys] for x in xs]
    assert bilinear_interp(1.0, 2.0, xs, ys, grid) == pytest.approx(3.0)
    assert bilinear_interp(3.5, 7.0, xs, ys, grid) == pytest.approx(10.5)


# --- bilinear_interp: erros -------------------------------------------------
def test_bilinear_fora_do_dominio_x_levanta():
    xs = [0.0, 1.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    with pytest.raises(ValueError):
        bilinear_interp(2.0, 0.5, xs, ys, grid)


def test_bilinear_fora_do_dominio_y_levanta():
    xs = [0.0, 1.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    with pytest.raises(ValueError):
        bilinear_interp(0.5, -1.0, xs, ys, grid)


def test_bilinear_grid_incompativel_levanta():
    xs = [0.0, 1.0, 2.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]  # so 2 linhas, xs tem 3
    with pytest.raises(ValueError):
        bilinear_interp(0.5, 0.5, xs, ys, grid)


def test_bilinear_xs_desordenado_levanta():
    xs = [1.0, 0.0]
    ys = [0.0, 1.0]
    grid = [[0.0, 1.0], [2.0, 3.0]]
    with pytest.raises(ValueError):
        bilinear_interp(0.5, 0.5, xs, ys, grid)


# --- nearest ----------------------------------------------------------------
def test_nearest_escolhe_vizinho_mais_proximo():
    assert nearest(2.4, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(20.0)
    assert nearest(2.6, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(30.0)


def test_nearest_empate_vai_para_menor_indice():
    assert nearest(2.5, [1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(20.0)


def test_nearest_tamanhos_diferentes_levanta():
    with pytest.raises(ValueError):
        nearest(2.0, [1, 2, 3], [10, 20])


def test_nearest_devolve_valor_tabelado_e_nao_extrapola():
    # mesmo fora do intervalo, devolve um y EXISTENTE (no mais proximo), sem extrapolar
    val = nearest(100.0, [1, 2, 3, 4], [10, 20, 30, 40])
    assert val in (10.0, 20.0, 30.0, 40.0)
    assert val == pytest.approx(40.0)


def test_resultados_sao_floats_finitos():
    assert math.isfinite(linear_interp(2.5, [1, 2, 3, 4], [10, 20, 30, 40]))
    assert math.isfinite(bilinear_interp(0.5, 0.5, [0, 1], [0, 1], [[0, 1], [2, 3]]))
