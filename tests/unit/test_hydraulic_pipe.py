"""Testes de escoamento em conduto forçado (Hazen-Williams e Darcy-Weisbach).

Valores de referência calculados à mão.

Fontes:
- Hazen-Williams (SI): hf = 10,67·Q^1,852·L / (C^1,852·D^4,87)
  (Azevedo Netto, "Manual de Hidráulica", 8ª ed.; forma SI usual).
- Darcy-Weisbach: hf = f·(L/D)·V²/(2g).
- Swamee-Jain (1976): f = 0,25 / [log10(ε/(3,7D) + 5,74/Re^0,9)]².
- ν da água ≈ 1,0e-6 m²/s a 20 °C; g = 9,81 m/s².
"""

import pytest

from lib.hydraulic.pipe_flow import (
    PipeFlowResult,
    darcy_weisbach_headloss,
    flow_from_velocity,
    hazen_williams_headloss,
    pipe_area,
    pipe_flow_darcy_weisbach,
    pipe_flow_hazen_williams,
    reynolds,
    swamee_jain_friction,
    velocity_from_flow,
)
from lib.validators.hydraulic_check import validate_pipe_flow


# ------------------------------------------------------------- geometria/cinemática

def test_pipe_area_and_velocity():
    # D=0,3 m -> A = π·0,3²/4 = 0,0706858 m²; V = Q/A = 0,05/0,0706858 = 0,7074 m/s
    a = pipe_area(0.3)
    assert a == pytest.approx(0.0706858, abs=1e-6)
    assert velocity_from_flow(0.05, 0.3) == pytest.approx(0.70736, abs=1e-4)
    assert flow_from_velocity(0.70736, 0.3) == pytest.approx(0.05, abs=1e-5)


# ------------------------------------------------------------------ Hazen-Williams

def test_hazen_williams_headloss_hand_calc():
    # Q=0,05 m³/s, D=0,3 m, L=1000 m, C=130
    # hf = 10,67·0,05^1,852·1000 / (130^1,852·0,3^4,87)
    #    = 41,561 / 23,367 = 1,779 m
    hf = hazen_williams_headloss(Q_m3s=0.05, D_m=0.3, L_m=1000.0, C=130.0)
    assert hf == pytest.approx(1.779, abs=0.01)


def test_pipe_flow_hazen_williams_result():
    r = pipe_flow_hazen_williams(Q_m3s=0.05, D_m=0.3, L_m=1000.0, C=130.0)
    assert isinstance(r, PipeFlowResult)
    assert r.metodo.startswith("Hazen-Williams")
    assert r.hf_m == pytest.approx(1.779, abs=0.01)
    assert r.V_ms == pytest.approx(0.70736, abs=1e-4)
    assert r.coef_C == 130.0
    assert r.reynolds is None and r.f is None


def test_hazen_williams_rejects_nonpositive_diameter():
    with pytest.raises(ValueError):
        hazen_williams_headloss(Q_m3s=0.05, D_m=0.0, L_m=1000.0, C=130.0)


# ----------------------------------------------------------- Darcy-Weisbach / S-J

def test_reynolds_hand_calc():
    # Re = V·D/ν = 0,70736·0,3 / 1e-6 = 212207
    assert reynolds(0.70736, 0.3) == pytest.approx(212207.0, rel=1e-4)


def test_swamee_jain_friction_hand_calc():
    # Re=212207, ε=0,0001 m, D=0,3 m
    # ε/(3,7D)=9,009e-5 ; 5,74/Re^0,9=9,222e-5 ; soma=1,8231e-4
    # f = 0,25/[log10(1,8231e-4)]² = 0,25/13,982 = 0,01788
    f = swamee_jain_friction(Re=212207.0, eps_m=0.0001, D_m=0.3)
    assert f == pytest.approx(0.01788, abs=2e-4)


def test_darcy_weisbach_headloss_hand_calc():
    # f=0,01788, L=1000, D=0,3, V=0,70736
    # hf = 0,01788·(1000/0,3)·0,70736²/(2·9,81) = 1,519 m
    hf = darcy_weisbach_headloss(V_ms=0.70736, D_m=0.3, L_m=1000.0, f=0.01788)
    assert hf == pytest.approx(1.519, abs=0.01)


def test_pipe_flow_darcy_weisbach_result():
    r = pipe_flow_darcy_weisbach(Q_m3s=0.05, D_m=0.3, L_m=1000.0, eps_m=0.0001)
    assert r.metodo.startswith("Darcy-Weisbach")
    assert r.reynolds == pytest.approx(212207.0, rel=1e-3)
    assert r.f == pytest.approx(0.01788, abs=3e-4)
    assert r.hf_m == pytest.approx(1.519, abs=0.02)
    assert r.eps_m == 0.0001
    assert r.coef_C is None


# ------------------------------------------------------------------- validação

def test_validate_pipe_flow_ok():
    r = pipe_flow_hazen_williams(Q_m3s=0.05, D_m=0.3, L_m=1000.0, C=130.0)
    rep = validate_pipe_flow(r)
    assert rep.passed is True


def test_validate_pipe_flow_bad_C_fails():
    # C=200 fora da faixa física [80, 150] -> reprova
    r = pipe_flow_hazen_williams(Q_m3s=0.05, D_m=0.3, L_m=1000.0, C=200.0)
    rep = validate_pipe_flow(r)
    assert rep.passed is False


def test_validate_pipe_flow_high_velocity_warns():
    # V alta (> 3 m/s) gera alerta, mas não reprova
    r = pipe_flow_hazen_williams(Q_m3s=0.3, D_m=0.3, L_m=1000.0, C=130.0)
    rep = validate_pipe_flow(r)
    assert r.V_ms > 3.0
    assert rep.warnings  # alerta de velocidade
