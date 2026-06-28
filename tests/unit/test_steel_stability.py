"""Testes — barra comprimida (NBR 8800:2008 §5.3), assumindo Q=1 (sem flambagem local).

Valores de referência calculados à mão. Conversões de unidade:
- E em kN/cm² = E[MPa]·0,1  (200000 MPa -> 20000 kN/cm²)
- fy em kN/cm² = fy[MPa]·0,1 (250 MPa -> 25 kN/cm²)
- Ne = π²·E·I/(KL)²  [kN]; λ0 = √(Q·A·fy/Ne); Nc,Rd = χ·Q·A·fy/γa1.
"""

import math

import pytest

from lib.steel.profiles import DEFAULT_TABLE, load_profiles
from lib.steel.stability import (
    chi_factor,
    design_compression,
    euler_load,
    lambda_0,
)
from lib.validators.steel_check import validate_compression


# --------------------------------------------------------------------- euler_load

def test_euler_load_hand_calc():
    # E=200000 MPa -> 20000 kN/cm²; I=1000 cm⁴; KL=200 cm
    # Ne = π²·20000·1000/200² = π²·20000000/40000 = π²·500 = 4934,80 kN
    ne = euler_load(e_mpa=200000.0, i_cm4=1000.0, kl_cm=200.0)
    assert ne == pytest.approx(math.pi**2 * 500.0, rel=1e-9)
    assert ne == pytest.approx(4934.80, abs=0.1)


def test_euler_load_scales_inverse_square_with_length():
    ne1 = euler_load(200000.0, 1000.0, 200.0)
    ne2 = euler_load(200000.0, 1000.0, 400.0)
    assert ne1 / ne2 == pytest.approx(4.0, rel=1e-9)   # dobrar KL -> Ne/4


# ----------------------------------------------------------------------- lambda_0

def test_lambda_0_hand_calc_unity():
    # A=25 cm²; fy=250 MPa -> 25 kN/cm²; A·fy=625 kN; Ne=625 kN -> λ0 = √1 = 1,0
    lam = lambda_0(q=1.0, area_cm2=25.0, fy_mpa=250.0, ne_kn=625.0)
    assert lam == pytest.approx(1.0, abs=1e-9)


def test_lambda_0_grows_with_slenderness():
    # menor Ne (barra mais esbelta) -> maior λ0
    lam_low = lambda_0(1.0, 25.0, 250.0, 2500.0)
    lam_high = lambda_0(1.0, 25.0, 250.0, 625.0)
    assert lam_high > lam_low


# ---------------------------------------------------------------------- chi_factor

def test_chi_factor_lambda0_zero_is_one():
    # âncora: χ(0) = 0,658^0 = 1,0
    assert chi_factor(0.0) == pytest.approx(1.0, abs=1e-12)


def test_chi_factor_lambda0_one_is_0658():
    # âncora: χ(1,0) = 0,658^(1²) = 0,658
    assert chi_factor(1.0) == pytest.approx(0.658, abs=1e-9)


def test_chi_factor_slender_branch():
    # λ0 = 2,0 > 1,5 -> χ = 0,877/λ0² = 0,877/4 = 0,21925
    assert chi_factor(2.0) == pytest.approx(0.877 / 4.0, abs=1e-9)


def test_chi_factor_continuous_at_transition():
    # χ deve ser monotônico decrescente e contínuo perto de λ0=1,5
    assert chi_factor(1.49) > chi_factor(1.51)


# --------------------------------------------------------------- design_compression

def test_design_compression_slender_weak_axis():
    # W250x22,3 (A=28,4; Iy=122), KL=300 cm, fy=250, E=200000, Q=1, γa1=1,1
    # Ne = π²·20000·122/300² = π²·27,1111 = 267,59 kN
    # A·fy = 28,4·25 = 710 kN ; λ0 = √(710/267,59) = 1,629 (>1,5)
    # χ = 0,877/1,629² = 0,3305 ; Nc,Rd = 0,3305·710/1,1 = 213,3 kN
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x22,3", base, kl_cm=300.0)
    assert r.ne_kn == pytest.approx(267.59, abs=0.2)
    assert r.lambda_0 == pytest.approx(1.629, abs=0.005)
    assert r.chi == pytest.approx(0.3305, abs=0.002)
    assert r.nc_rd_kn == pytest.approx(213.3, abs=0.5)
    assert r.norma == "NBR 8800:2008"


def test_design_compression_stocky_uses_0658_branch():
    # W250x22,3, KL=100 cm -> Ne = π²·20000·122/100² = π²·244 = 2408,2 kN
    # λ0 = √(710/2408,2) = 0,5430 (≤1,5) -> χ = 0,658^(0,5430²) = 0,8839
    # Nc,Rd = 0,8839·710/1,1 = 570,5 kN
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x22,3", base, kl_cm=100.0)
    assert r.lambda_0 == pytest.approx(0.5430, abs=0.003)
    assert r.chi == pytest.approx(0.8839, abs=0.002)
    assert r.nc_rd_kn == pytest.approx(570.5, abs=1.0)


def test_design_compression_uses_minimum_inertia():
    # a barra comprimida flamba no eixo de menor inércia -> Ne usa Iy
    base = load_profiles(DEFAULT_TABLE)
    p = base["W250x22,3"]
    r = design_compression("W250x22,3", base, kl_cm=300.0)
    ne_y = euler_load(r.e_mpa, p.iy_cm4, 300.0)
    assert r.ne_kn == pytest.approx(ne_y, rel=1e-9)
    assert r.i_cm4 == pytest.approx(p.iy_cm4, abs=1e-9)


def test_design_compression_missing_profile_raises():
    # abstenção: perfil inexistente propaga KeyError
    base = load_profiles(DEFAULT_TABLE)
    with pytest.raises(KeyError):
        design_compression("W999x99,9", base, kl_cm=300.0)


# ---------------------------------------------------------- validate_compression

def test_validate_compression_ok():
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x22,3", base, kl_cm=300.0)
    rep = validate_compression(r)
    assert rep.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep.checks)


def test_validate_compression_fy_out_of_range_fails():
    # fy=600 MPa fora de [250,450] (aços estruturais comuns) -> fail
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x22,3", base, kl_cm=300.0, fy_mpa=600.0)
    rep = validate_compression(r)
    assert rep.passed is False


def test_validate_compression_very_slender_warns():
    # W250x17,9 (Iy=91), KL=600 cm -> λ0 ≈ 3,4 (>3) gera alerta, mas Nc,Rd>0
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x17,9", base, kl_cm=600.0)
    rep = validate_compression(r)
    assert r.lambda_0 > 3.0
    assert r.nc_rd_kn > 0.0
    assert rep.passed is True
    assert len(rep.warnings) >= 1
