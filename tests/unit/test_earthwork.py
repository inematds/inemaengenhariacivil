"""Testes de terraplenagem — volumes, empolamento e balanço corte/aterro.

Valores de referência calculados à mão (a conta está nos comentários).

Fonte do método: método das áreas médias (average end area), V=(A1+A2)/2·L
(DNIT, Manual de Implantação Básica de Rodovia; topografia/terraplenagem).
Estados de volume: corte/banco -> solto (fator de empolamento Fe>=1) ->
compactado (fator de compactação Fc<1).
"""

import pytest

from lib.earthwork.volumes import (
    EarthworkResult,
    ajustar_empolamento,
    balanco_corte_aterro,
    volume_compactado,
    volume_entre_secoes,
    volume_total,
)


def test_volume_entre_secoes_areas_medias():
    # V = (A1+A2)/2·L = (10+20)/2·20 = 300 m³  (âncora)
    assert volume_entre_secoes(10.0, 20.0, 20.0) == pytest.approx(300.0)


def test_volume_total_somatorio_por_trechos():
    # trecho 1: (10+20)/2·20 = 300 ; trecho 2: (20+15)/2·30 = 525 ; total 825 m³
    v = volume_total([10.0, 20.0, 15.0], [20.0, 30.0])
    assert v == pytest.approx(825.0)


def test_ajustar_empolamento():
    # empolamento 30% -> volume solto = corte·1,30 = 1300 m³  (âncora)
    assert ajustar_empolamento(1000.0, 1.30) == pytest.approx(1300.0)


def test_volume_compactado_chain():
    # corte->solto->compactado: 1000·Fe·Fc = 1000·1,25·0,72 = 900 m³
    assert volume_compactado(1000.0, fator_empolamento=1.25,
                             fator_compactacao=0.72) == pytest.approx(900.0)


def test_balanco_excesso():
    # corte=1000, aterro=600 -> balanço = +400 (excesso/bota-fora)
    # solto do bota-fora = 400·1,30 = 520 m³
    r = balanco_corte_aterro(1000.0, 600.0, fator_empolamento=1.30)
    assert isinstance(r, EarthworkResult)
    assert r.balanco_m3 == pytest.approx(400.0)
    assert r.situacao == "excesso"
    assert r.volume_bota_fora_m3 == pytest.approx(400.0)
    assert r.volume_emprestimo_m3 == pytest.approx(0.0)
    assert r.volume_bota_fora_solto_m3 == pytest.approx(520.0)
    assert r.volume_corte_solto_m3 == pytest.approx(1300.0)


def test_balanco_deficit():
    # corte=500, aterro=800 -> balanço = -300 (déficit/empréstimo)
    r = balanco_corte_aterro(500.0, 800.0)
    assert r.balanco_m3 == pytest.approx(-300.0)
    assert r.situacao == "deficit"
    assert r.volume_emprestimo_m3 == pytest.approx(300.0)
    assert r.volume_bota_fora_m3 == pytest.approx(0.0)


def test_balanco_equilibrio():
    r = balanco_corte_aterro(700.0, 700.0)
    assert r.situacao == "equilibrio"
    assert r.balanco_m3 == pytest.approx(0.0)


def test_volume_entre_secoes_abstem_invalido():
    with pytest.raises(ValueError):
        volume_entre_secoes(-1.0, 20.0, 20.0)   # área negativa
    with pytest.raises(ValueError):
        volume_entre_secoes(10.0, 20.0, 0.0)    # distância <= 0


def test_volume_total_abstem_tamanhos_incompativeis():
    with pytest.raises(ValueError):
        volume_total([10.0, 20.0, 15.0], [20.0])  # precisa de n-1 distâncias


def test_ajustar_empolamento_abstem_fator_menor_que_um():
    with pytest.raises(ValueError):
        ajustar_empolamento(1000.0, 0.9)


def test_balanco_abstem_invalido():
    with pytest.raises(ValueError):
        balanco_corte_aterro(-10.0, 600.0)                       # volume negativo
    with pytest.raises(ValueError):
        balanco_corte_aterro(1000.0, 600.0, fator_empolamento=1.8)  # Fe fora de faixa


# --------------------------------------------------------------- validação

from lib.validators.earthwork_check import validate_earthwork  # noqa: E402


def _good_earthwork():
    return balanco_corte_aterro(1000.0, 600.0, fator_empolamento=1.30)


def test_validate_earthwork_good_passes_all_categories():
    rep = validate_earthwork(_good_earthwork())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_earthwork_flags_negative_volume():
    r = _good_earthwork().model_copy(update={"volume_corte_m3": -10.0})
    rep = validate_earthwork(r)
    assert rep.passed is False


def test_validate_earthwork_flags_swell_out_of_range():
    r = _good_earthwork().model_copy(update={"fator_empolamento": 1.8})
    rep = validate_earthwork(r)
    assert rep.passed is False
