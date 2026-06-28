"""Testes de pavimento flexível — método empírico DNER/DNIT (CBR / número N).

Valores de referência calculados à mão (a conta está nos comentários).

Fonte do método: DNER (1981) "Método de Projeto de Pavimentos Flexíveis"
(Eng. Murillo Lopes de Souza) e DNIT (2006) "Manual de Pavimentação".
Equação de ajuste do ábaco de dimensionamento (espessura de material granular
equivalente, em cm):  H = 77,67 · N^0,0482 · CBR^-0,598.
"""

import math

import pytest

from lib.pavement.flexible import (
    PavementResult,
    design_flexible_pavement,
    espessura_total,
    numero_n,
    revestimento_minimo_cm,
)


def test_espessura_total_known_case():
    # H = 77,67 · N^0,0482 · CBR^-0,598, com N=1e6, CBR=10
    # N^0,0482 = exp(0,0482·ln1e6) = exp(0,665907) = 1,946274
    # CBR^-0,598 = exp(-0,598·ln10) = exp(-1,376946) = 0,252418
    # H = 77,67 · 1,946274 · 0,252418 = 38,16 cm
    h = espessura_total(cbr=10.0, n=1.0e6)
    assert h == pytest.approx(38.16, abs=0.05)


def test_espessura_total_decresce_com_cbr():
    # subleito melhor (CBR maior) -> menor espessura necessária
    assert espessura_total(15.0, 1.0e6) < espessura_total(5.0, 1.0e6)


def test_numero_n_sem_crescimento():
    # N = 365 · P · Vm · FV · FR  (tráfego constante, taxa=0)
    # = 365 · 10 · 1000 · 2,0 · 1,0 = 7 300 000
    n = numero_n(volume_medio_diario=1000.0, periodo_anos=10.0,
                 fator_veiculo=2.0, fator_regional=1.0)
    assert n == pytest.approx(7.3e6, rel=1e-9)


def test_numero_n_com_crescimento_maior():
    # crescimento geométrico aumenta o N acumulado
    n0 = numero_n(1000.0, 10.0, 2.0, 1.0, taxa_crescimento=0.0)
    ng = numero_n(1000.0, 10.0, 2.0, 1.0, taxa_crescimento=0.05)
    assert ng > n0


def test_revestimento_minimo_tabela_dner():
    assert revestimento_minimo_cm(8.0e5) == pytest.approx(2.0)
    assert revestimento_minimo_cm(2.0e6) == pytest.approx(5.0)
    assert revestimento_minimo_cm(1.0e7) == pytest.approx(7.5)
    assert revestimento_minimo_cm(3.0e7) == pytest.approx(10.0)
    assert revestimento_minimo_cm(8.0e7) == pytest.approx(12.5)


def test_design_flexible_pavement_sem_reforco():
    # CBR_subleito=8, N=2e6, K_R=2,0 K_B=K_S=1,0
    # Hm = 77,67·(2e6)^0,0482·8^-0,598
    #    = 77,67·2,012410·0,288382 = 45,08 cm
    # H20 = 77,67·2,012410·20^-0,598 = 77,67·2,012410·0,166718 = 26,06 cm
    # R = 5,0 cm (1e6<N<=5e6); R·K_R = 10,0
    # B >= (26,06-10)/1,0 = 16,06 -> ceil 17 cm
    #   ineq1: 5·2 + 17·1 = 27 >= 26,06  OK
    # S >= (45,08-10-17)/1,0 = 18,08 -> ceil 19 cm
    #   ineq2: 10+17+19 = 46 >= 45,08  OK
    # total = 5+17+19 = 41 cm
    r = design_flexible_pavement(cbr_subleito=8.0, n_trafego=2.0e6)
    assert isinstance(r, PavementResult)
    assert r.hm_cm == pytest.approx(45.08, abs=0.1)
    assert r.h20_cm == pytest.approx(26.06, abs=0.1)
    assert r.r_cm == pytest.approx(5.0)
    assert r.b_cm == pytest.approx(17.0)
    assert r.s_cm == pytest.approx(19.0)
    assert r.reforco_cm is None
    assert r.hn_cm is None
    assert r.espessura_total_cm == pytest.approx(41.0)
    assert all(i.atende for i in r.inequacoes)


def test_design_flexible_pavement_com_reforco():
    # CBR_subleito=4, CBR_reforco=10, N=1e7
    # Hm = 77,67·(1e7)^0,0482·4^-0,598 = 77,67·2,174688·0,436513 = 73,73 cm
    # Hn = 77,67·2,174688·10^-0,598 = 77,67·2,174688·0,252418 = 42,64 cm
    # H20 = 77,67·2,174688·0,166718 = 28,16 cm
    # R = 7,5 cm (5e6<N<=1e7); R·K_R = 15,0
    # B >= (28,16-15)/1 = 13,16 -> ceil 14 -> min 15 cm
    #   ineq1: 7,5·2 + 15 = 30 >= 28,16  OK
    # S >= (42,64-15-15)/1 = 12,64 -> ceil 13 -> min 15 cm
    #   ineq2: 15+15+15 = 45 >= 42,64  OK
    # Ref >= (73,73-15-15-15)/1 = 28,73 -> ceil 29 cm
    #   ineq3: 15+15+15+29 = 74 >= 73,73  OK
    r = design_flexible_pavement(cbr_subleito=4.0, n_trafego=1.0e7, cbr_reforco=10.0)
    assert r.hm_cm == pytest.approx(73.73, abs=0.1)
    assert r.hn_cm == pytest.approx(42.64, abs=0.1)
    assert r.h20_cm == pytest.approx(28.16, abs=0.1)
    assert r.r_cm == pytest.approx(7.5)
    assert r.reforco_cm == pytest.approx(29.0)
    assert len(r.inequacoes) == 3
    assert all(i.atende for i in r.inequacoes)


def test_design_flexible_pavement_inequacoes_satisfeitas():
    # qualquer projeto válido deve fechar todas as inequações
    r = design_flexible_pavement(cbr_subleito=12.0, n_trafego=5.0e6)
    for i in r.inequacoes:
        assert i.esquerda_cm + 1e-9 >= i.direita_cm
        assert i.atende


def test_design_flexible_pavement_aceita_n_direto():
    # N entra diretamente (sem cálculo de tráfego)
    r = design_flexible_pavement(cbr_subleito=10.0, n_trafego=1.0e6)
    assert r.n_trafego == pytest.approx(1.0e6)
    assert r.hm_cm == pytest.approx(espessura_total(10.0, 1.0e6), abs=1e-6)


def test_design_flexible_pavement_abstem_cbr_fora_de_faixa():
    with pytest.raises(ValueError):
        design_flexible_pavement(cbr_subleito=1.0, n_trafego=1.0e6)  # < 2
    with pytest.raises(ValueError):
        design_flexible_pavement(cbr_subleito=25.0, n_trafego=1.0e6)  # > 20


def test_design_flexible_pavement_abstem_n_fora_de_faixa():
    with pytest.raises(ValueError):
        design_flexible_pavement(cbr_subleito=10.0, n_trafego=1.0e3)  # < 1e4
    with pytest.raises(ValueError):
        design_flexible_pavement(cbr_subleito=10.0, n_trafego=1.0e9)  # > 1e8


def test_design_flexible_pavement_abstem_reforco_fora_de_faixa():
    with pytest.raises(ValueError):
        design_flexible_pavement(cbr_subleito=4.0, n_trafego=1.0e6, cbr_reforco=1.0)


def test_espessura_total_ceil_consistente():
    # a espessura total adotada é a soma das camadas inteiras (cm)
    r = design_flexible_pavement(cbr_subleito=6.0, n_trafego=3.0e6)
    soma = r.r_cm + r.b_cm + r.s_cm + (r.reforco_cm or 0.0)
    assert r.espessura_total_cm == pytest.approx(soma)
    assert r.b_cm == math.ceil(r.b_cm)  # camadas granulares em cm inteiros


# --------------------------------------------------------------- validação

from lib.validators.pavement_check import validate_pavement  # noqa: E402


def _good_pavement():
    return design_flexible_pavement(cbr_subleito=8.0, n_trafego=2.0e6)


def test_validate_pavement_good_passes_all_categories():
    rep = validate_pavement(_good_pavement())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_pavement_flags_cbr_out_of_range():
    r = _good_pavement().model_copy(update={"cbr_subleito": 1.0})
    rep = validate_pavement(r)
    assert rep.passed is False


def test_validate_pavement_flags_n_out_of_range():
    r = _good_pavement().model_copy(update={"n_trafego": 1.0e9})
    rep = validate_pavement(r)
    assert rep.passed is False


def test_validate_pavement_flags_unsatisfied_inequality():
    # base esmagada -> a inequação R·K_R + B·K_B >= H20 não fecha
    r = _good_pavement().model_copy(update={"b_cm": 1.0})
    rep = validate_pavement(r)
    assert rep.passed is False
    norm = next(c for c in rep.checks if c.name == "normative")
    assert norm.status == "fail"
