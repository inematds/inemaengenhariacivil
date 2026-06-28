"""Testes de perdas de carga localizadas (método dos coeficientes K).

Valores de referência calculados à mão.

Fonte: h_loc = K·V²/(2g), com K por singularidade (método direto / dos
comprimentos, coeficientes usuais — Azevedo Netto, "Manual de Hidráulica").
g = 9,81 m/s².
"""

import pytest

from lib.hydraulic.head_loss import (
    K_SINGULARIDADES,
    HeadLossResult,
    local_loss,
    singularity_K,
    total_head_loss,
)
from lib.validators.hydraulic_check import validate_head_loss


# ----------------------------------------------------------------- perda unitária

def test_local_loss_hand_calc():
    # curva 90° K=0,9 ; V=2 m/s -> h = 0,9·2²/(2·9,81) = 3,6/19,62 = 0,18349 m
    assert local_loss(K=0.9, V_ms=2.0) == pytest.approx(0.18349, abs=1e-4)


def test_singularity_K_lookup():
    assert singularity_K("curva_90") == 0.9
    assert singularity_K("entrada") == 0.5
    assert singularity_K("saida") == 1.0
    assert "curva_90" in K_SINGULARIDADES


def test_singularity_K_unknown_raises():
    with pytest.raises(ValueError):
        singularity_K("teletransporte")


# -------------------------------------------------------------------- perda total

def test_total_head_loss_hand_calc():
    # hf_dist=1,0 m ; V=2 m/s
    # ΣK = entrada(0,5) + 2·curva_90(0,9) + saida(1,0) = 3,3
    # h_loc = 3,3·2²/(2·9,81) = 13,2/19,62 = 0,67278 m
    # total = 1,0 + 0,67278 = 1,67278 m
    r = total_head_loss(
        hf_distribuida_m=1.0,
        singularidades={"entrada": 1, "curva_90": 2, "saida": 1},
        V_ms=2.0,
    )
    assert isinstance(r, HeadLossResult)
    assert r.hf_localizada_m == pytest.approx(0.67278, abs=1e-4)
    assert r.hf_total_m == pytest.approx(1.67278, abs=1e-4)
    assert r.hf_distribuida_m == 1.0
    # itens detalhados por singularidade
    assert len(r.itens) == 3
    curva = next(i for i in r.itens if i.tipo == "curva_90")
    assert curva.quantidade == 2
    assert curva.K == 0.9
    assert curva.h_m == pytest.approx(2 * 0.18349, abs=1e-3)


def test_total_head_loss_unknown_singularity_raises():
    with pytest.raises(ValueError):
        total_head_loss(hf_distribuida_m=1.0, singularidades={"buraco_negro": 1}, V_ms=2.0)


# ------------------------------------------------------------------- validação

def test_validate_head_loss_ok():
    r = total_head_loss(
        hf_distribuida_m=1.0,
        singularidades={"entrada": 1, "curva_90": 2, "saida": 1},
        V_ms=2.0,
    )
    rep = validate_head_loss(r)
    assert rep.passed is True
