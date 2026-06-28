"""Testes de capacidade de carga de fundação rasa — método de Vesic (forma fechada).

Valores de referência calculados à mão (a conta está nos comentários).
Fonte: Vesic (1973/1975), "Bearing Capacity of Shallow Foundations".

Fatores (forma fechada):
  Nq = e^(π·tanφ)·tan²(45+φ/2);  Nc = (Nq−1)·cotφ (φ=0 → Nc≈5,14);
  Nγ = 2·(Nq+1)·tanφ.
Âncora φ=30°: Nq≈18,40 ; Nc≈30,14 ; Nγ≈22,40.
"""

import pytest

from lib.geotechnical.bearing_capacity import (
    BearingCapacityResult,
    design_bearing_capacity,
    vesic_bearing_factors,
)
from lib.validators.geotech_check import validate_bearing


def test_vesic_factors_phi_30():
    # tan30=0.57735; π·tan30=1.81380; e^1.81380=6.13372
    # Nq = 6.13372·tan²60 = 6.13372·3 = 18.401
    # Nc = (18.401−1)·cot30 = 17.401·1.73205 = 30.140
    # Nγ = 2·(18.401+1)·tan30 = 2·19.401·0.57735 = 22.402
    nc, nq, ng = vesic_bearing_factors(30.0)
    assert nq == pytest.approx(18.40, abs=0.05)
    assert nc == pytest.approx(30.14, abs=0.05)
    assert ng == pytest.approx(22.40, abs=0.05)


def test_vesic_factors_phi_zero():
    # φ=0 (caso não drenado): Nq=1, Nc=π+2≈5.14, Nγ=0
    nc, nq, ng = vesic_bearing_factors(0.0)
    assert nq == pytest.approx(1.0, abs=1e-9)
    assert nc == pytest.approx(5.14, abs=0.01)
    assert ng == pytest.approx(0.0, abs=1e-9)


def test_design_square_footing_full():
    # c=10 kPa, φ=30°, γ=18 kN/m³, B=2 m, Df=1 m, sapata quadrada, FS=3
    # q_surcharge = γ·Df = 18 kPa
    # sc = 1 + Nq/Nc = 1 + 18.401/30.140 = 1.61052
    # sq = 1 + tan30 = 1.57735 ; sγ = 1 − 0.4 = 0.60
    # T1 = c·Nc·sc = 10·30.140·1.61052 = 485.41
    # T2 = q·Nq·sq = 18·18.401·1.57735 = 522.45
    # T3 = 0.5·γ·B·Nγ·sγ = 0.5·18·2·22.402·0.6 = 241.94
    # q_ult = 1249.81 kPa ; q_adm = 1249.81/3 = 416.60 kPa
    r = design_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
        b_m=2.0, depth_df_m=1.0, shape="quadrada", fs=3.0,
    )
    assert isinstance(r, BearingCapacityResult)
    assert r.nc == pytest.approx(30.14, abs=0.05)
    assert r.nq == pytest.approx(18.40, abs=0.05)
    assert r.ngamma == pytest.approx(22.40, abs=0.05)
    assert r.sc == pytest.approx(1.6105, abs=0.001)
    assert r.sq == pytest.approx(1.5774, abs=0.001)
    assert r.sgamma == pytest.approx(0.60, abs=1e-6)
    assert r.q_surcharge_kpa == pytest.approx(18.0, abs=1e-9)
    assert r.q_ult_kpa == pytest.approx(1249.81, abs=2.0)
    assert r.q_adm_kpa == pytest.approx(416.60, abs=1.0)
    assert r.fs == 3.0


def test_design_strip_footing_shape_factors_unity():
    # Mesma entrada, sapata corrida -> sc=sq=sγ=1
    # q_ult = c·Nc + q·Nq + 0.5·γ·B·Nγ
    #       = 10·30.140 + 18·18.401 + 0.5·18·2·22.402
    #       = 301.40 + 331.22 + 403.24 = 1035.86 kPa
    r = design_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
        b_m=2.0, depth_df_m=1.0, shape="corrida", fs=3.0,
    )
    assert r.sc == pytest.approx(1.0, abs=1e-9)
    assert r.sq == pytest.approx(1.0, abs=1e-9)
    assert r.sgamma == pytest.approx(1.0, abs=1e-9)
    assert r.q_ult_kpa == pytest.approx(1035.86, abs=2.0)


def test_design_undrained_phi_zero_strip():
    # c=50 kPa, φ=0, γ=18, B=2, Df=1, corrida
    # q_ult = c·Nc + q·Nq = 50·5.14159 + 18·1 = 257.08 + 18 = 275.08 kPa
    r = design_bearing_capacity(
        c_kpa=50.0, phi_deg=0.0, gamma_kn_m3=18.0,
        b_m=2.0, depth_df_m=1.0, shape="corrida", fs=3.0,
    )
    assert r.ngamma == pytest.approx(0.0, abs=1e-9)
    assert r.q_ult_kpa == pytest.approx(275.08, abs=0.5)


def test_validate_bearing_passes():
    r = design_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
        b_m=2.0, depth_df_m=1.0, shape="quadrada", fs=3.0,
    )
    rep = validate_bearing(r)
    assert rep.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep.checks)


def test_validate_bearing_low_fs_warns():
    # FS=2 < 3 -> normativa em warning, mas ainda passa (não é fail)
    r = design_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
        b_m=2.0, depth_df_m=1.0, shape="quadrada", fs=2.0,
    )
    rep = validate_bearing(r)
    assert rep.passed is True
    assert any("FS" in w for w in rep.warnings)


def test_design_bearing_rejects_invalid():
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=10.0, phi_deg=60.0, gamma_kn_m3=18.0,
                                b_m=2.0, depth_df_m=1.0)  # φ>50
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=5.0,
                                b_m=2.0, depth_df_m=1.0)  # γ<10
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=-1.0, phi_deg=30.0, gamma_kn_m3=18.0,
                                b_m=2.0, depth_df_m=1.0)  # c<0
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
                                b_m=0.0, depth_df_m=1.0)  # B<=0
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
                                b_m=2.0, depth_df_m=1.0, shape="trapezio")  # forma inválida
    with pytest.raises(ValueError):
        design_bearing_capacity(c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0,
                                b_m=2.0, depth_df_m=1.0, fs=0.5)  # FS<1
