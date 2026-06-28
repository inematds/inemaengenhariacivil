"""Testes de empuxo de terra — Rankine e Coulomb.

Valores de referência calculados à mão (a conta está nos comentários).
Fontes: Rankine (1857) e Coulomb (1776), formulações clássicas de empuxo.

Âncoras φ=30°: Ka=tan²(45−15)=tan²30=1/3 ; Kp=tan²(45+15)=tan²60=3.
Coulomb reduz a Rankine quando δ=β=α=0 (cross-check).
"""

import pytest

from lib.geotechnical.earth_pressure import (
    CoulombEarthPressureResult,
    RankineEarthPressureResult,
    coulomb_earth_pressure,
    rankine_earth_pressure,
)
from lib.validators.geotech_check import validate_earth_pressure


def test_rankine_coefficients_phi_30():
    # Ka = tan²(30) = 1/3 ; Kp = tan²(60) = 3
    r = rankine_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0)
    assert isinstance(r, RankineEarthPressureResult)
    assert r.ka == pytest.approx(1.0 / 3.0, abs=1e-6)
    assert r.kp == pytest.approx(3.0, abs=1e-6)


def test_rankine_thrust_and_point():
    # γ=18, H=4, φ=30 -> Ka=1/3
    # Ea = 0.5·γ·H²·Ka = 0.5·18·16·(1/3) = 144·(1/3) = 48 kN/m
    # Ep = 0.5·18·16·3 = 432 kN/m ; ponto de aplicação = H/3 = 1.333 m
    r = rankine_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0)
    assert r.ea_active_kn_m == pytest.approx(48.0, abs=1e-6)
    assert r.ep_passive_kn_m == pytest.approx(432.0, abs=1e-6)
    assert r.point_of_application_m == pytest.approx(4.0 / 3.0, abs=1e-6)


def test_coulomb_reduces_to_rankine():
    # δ=β=α=0 -> Ka_coulomb = cos²φ/(1+sinφ)² = 0.75/2.25 = 1/3 = Ka_rankine
    r = coulomb_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0,
                               delta_deg=0.0, beta_deg=0.0, alpha_deg=0.0)
    assert isinstance(r, CoulombEarthPressureResult)
    assert r.ka == pytest.approx(1.0 / 3.0, abs=1e-6)
    assert r.kp == pytest.approx(3.0, abs=1e-6)
    assert r.ea_active_kn_m == pytest.approx(48.0, abs=1e-6)


def test_coulomb_with_wall_friction():
    # φ=30, δ=20, β=0, α=0
    # Ka = cos²30 / [cos20·(1+√(sin50·sin30/cos20))²]
    #    = 0.75 / [0.93969·(1+√(0.76604·0.5/0.93969))²]
    #    = 0.75 / [0.93969·(1+√0.407602)²] = 0.75 / [0.93969·1.638437²]
    #    = 0.75 / 2.52262 = 0.29731
    r = coulomb_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0,
                               delta_deg=20.0, beta_deg=0.0, alpha_deg=0.0)
    assert r.ka == pytest.approx(0.29731, abs=1e-4)
    # Ea = 0.5·18·16·0.29731 = 144·0.29731 = 42.81 kN/m
    assert r.ea_active_kn_m == pytest.approx(42.81, abs=0.05)
    assert r.point_of_application_m == pytest.approx(4.0 / 3.0, abs=1e-6)


def test_validate_earth_pressure_rankine_and_coulomb():
    rr = rankine_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0)
    rep_r = validate_earth_pressure(rr)
    assert rep_r.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep_r.checks)

    rc = coulomb_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0, delta_deg=20.0)
    rep_c = validate_earth_pressure(rc)
    assert rep_c.passed is True


def test_earth_pressure_rejects_invalid():
    with pytest.raises(ValueError):
        rankine_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=55.0)  # φ>50
    with pytest.raises(ValueError):
        rankine_earth_pressure(gamma_kn_m3=5.0, h_m=4.0, phi_deg=30.0)  # γ<10
    with pytest.raises(ValueError):
        rankine_earth_pressure(gamma_kn_m3=18.0, h_m=0.0, phi_deg=30.0)  # H<=0
    with pytest.raises(ValueError):
        coulomb_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0,
                               delta_deg=40.0)  # δ>φ
    with pytest.raises(ValueError):
        coulomb_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0,
                               alpha_deg=35.0)  # α>=φ (talude instável p/ a fórmula)
