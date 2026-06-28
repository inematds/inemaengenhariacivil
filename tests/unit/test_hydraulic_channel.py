"""Testes de canal aberto (Manning).

Valores de referência calculados à mão.

Fonte: equação de Manning (SI), Q = (1/n)·A·R^(2/3)·S^(1/2), R = A/P
(Chow, "Open-Channel Hydraulics", 1959; Azevedo Netto, "Manual de Hidráulica").
"""

import pytest

from lib.hydraulic.open_channel import (
    OpenChannelResult,
    manning_circular,
    manning_discharge,
    manning_rectangular,
    manning_trapezoidal,
    normal_depth_circular,
    normal_depth_rectangular,
    normal_depth_trapezoidal,
)
from lib.validators.hydraulic_check import validate_open_channel


# ---------------------------------------------------------------- retangular

def test_manning_rectangular_hand_calc():
    # b=2 m, y=1 m, n=0,015, S=0,001
    # A=2, P=4, R=0,5
    # Q = (1/0,015)·2·0,5^(2/3)·0,001^0,5 = 66,667·2·0,62996·0,031623 = 2,656 m³/s
    r = manning_rectangular(b_m=2.0, y_m=1.0, n=0.015, S=0.001)
    assert isinstance(r, OpenChannelResult)
    assert r.geometria == "retangular"
    assert r.area_m2 == pytest.approx(2.0, abs=1e-6)
    assert r.perimetro_m == pytest.approx(4.0, abs=1e-6)
    assert r.raio_hidraulico_m == pytest.approx(0.5, abs=1e-6)
    assert r.Q_m3s == pytest.approx(2.656, abs=0.01)
    assert r.V_ms == pytest.approx(1.328, abs=0.01)


def test_manning_discharge_helper():
    # mesmos números do hand-calc acima
    q = manning_discharge(A_m2=2.0, P_m=4.0, n=0.015, S=0.001)
    assert q == pytest.approx(2.656, abs=0.01)


def test_normal_depth_rectangular_roundtrip():
    # Q=2,656, b=2, n=0,015, S=0,001 -> y ≈ 1,0 m
    y = normal_depth_rectangular(Q_m3s=2.656, b_m=2.0, n=0.015, S=0.001)
    assert y == pytest.approx(1.0, abs=0.01)


# --------------------------------------------------------------- trapezoidal

def test_manning_trapezoidal_hand_calc():
    # b=2, y=1, z=1 (talude 1:1), n=0,015, S=0,001
    # A=(2+1·1)·1=3 ; P=2+2·1·√2=4,82843 ; R=3/4,82843=0,62132
    # Q=(1/0,015)·3·0,62132^(2/3)·0,031623 = 4,60 m³/s
    r = manning_trapezoidal(b_m=2.0, y_m=1.0, z=1.0, n=0.015, S=0.001)
    assert r.geometria == "trapezoidal"
    assert r.area_m2 == pytest.approx(3.0, abs=1e-6)
    assert r.perimetro_m == pytest.approx(4.828427, abs=1e-5)
    assert r.raio_hidraulico_m == pytest.approx(0.621320, abs=1e-5)
    assert r.Q_m3s == pytest.approx(4.604, abs=0.02)


def test_normal_depth_trapezoidal_roundtrip():
    y = normal_depth_trapezoidal(Q_m3s=4.604, b_m=2.0, z=1.0, n=0.015, S=0.001)
    assert y == pytest.approx(1.0, abs=0.01)


# ------------------------------------------------------------------ circular

def test_manning_circular_half_full_hand_calc():
    # D=1,0 m, y=0,5 m (meia seção), n=0,013, S=0,001
    # θ=π ; A=π/8=0,39270 ; P=π/2=1,57080 ; R=0,25
    # Q=(1/0,013)·0,39270·0,25^(2/3)·0,031623 = 0,3791 m³/s
    r = manning_circular(D_m=1.0, y_m=0.5, n=0.013, S=0.001)
    assert r.geometria == "circular"
    assert r.area_m2 == pytest.approx(0.392699, abs=1e-5)
    assert r.perimetro_m == pytest.approx(1.570796, abs=1e-5)
    assert r.raio_hidraulico_m == pytest.approx(0.25, abs=1e-5)
    assert r.Q_m3s == pytest.approx(0.3791, abs=0.002)


def test_normal_depth_circular_roundtrip():
    y = normal_depth_circular(Q_m3s=0.3791, D_m=1.0, n=0.013, S=0.001)
    assert y == pytest.approx(0.5, abs=0.01)


# ----------------------------------------------------------------- abstenção

def test_manning_rectangular_rejects_nonpositive_depth():
    with pytest.raises(ValueError):
        manning_rectangular(b_m=2.0, y_m=0.0, n=0.015, S=0.001)


def test_manning_circular_rejects_depth_above_diameter():
    with pytest.raises(ValueError):
        manning_circular(D_m=1.0, y_m=1.5, n=0.013, S=0.001)


# ------------------------------------------------------------------- validação

def test_validate_open_channel_ok():
    r = manning_rectangular(b_m=2.0, y_m=1.0, n=0.015, S=0.001)
    rep = validate_open_channel(r)
    assert rep.passed is True


def test_validate_open_channel_bad_n_fails():
    # n=0,5 fora da faixa [0,009 ; 0,1] -> reprova
    r = manning_rectangular(b_m=2.0, y_m=1.0, n=0.5, S=0.001)
    rep = validate_open_channel(r)
    assert rep.passed is False
