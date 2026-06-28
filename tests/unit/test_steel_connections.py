"""Testes de ligações metálicas — parafusos e solda de filete (NBR 8800:2008 §6).

Valores de referência calculados à mão (a conta está nos comentários).
Unidades internas: cm, kN, kN/cm² (1 MPa = 0,1 kN/cm²); db/t/perna entram em mm.
"""

import math

import pytest

from lib.steel.connections import (
    BoltedConnectionResult,
    WeldResult,
    bolt_bearing_resistance,
    bolt_shear_resistance,
    design_bolted_connection,
    design_fillet_weld,
    fillet_weld_resistance,
)
from lib.validators.report import ValidationReport
from lib.validators.steel_connections_check import validate_bolted, validate_weld


# --- parafusos: cortante (NBR 8800:2008 §6.3.3.2) ----------------------------
def test_bolt_shear_M20_threads_in_plane():
    # M20: db=20 mm -> 2 cm; Ab = pi*2^2/4 = 3.14159 cm²; fub=800 MPa = 80 kN/cm²
    # rosca no plano de corte -> coef 0.4; 1 plano; gamma_a2 = 1.35
    # Fv,Rd = 0.4 * 3.14159 * 80 / 1.35 = 100.531 / 1.35 = 74.467 kN
    assert bolt_shear_resistance(20.0, 800.0) == pytest.approx(74.467, abs=0.01)


def test_bolt_shear_no_threads_in_plane_uses_0_5():
    # plano de corte fora da rosca -> coef 0.5
    # Fv,Rd = 0.5 * 3.14159 * 80 / 1.35 = 125.664 / 1.35 = 93.084 kN
    assert bolt_shear_resistance(20.0, 800.0, rosca_no_plano=False) == pytest.approx(
        93.084, abs=0.01
    )


def test_bolt_shear_two_planes_doubles():
    # dois planos de corte (corte duplo) -> 2 * 74.467 = 148.93 kN
    assert bolt_shear_resistance(20.0, 800.0, planos=2) == pytest.approx(148.934, abs=0.02)


def test_bolt_shear_area_matches_circle():
    # checagem direta de Ab via campo do resultado de projeto
    r = design_bolted_connection(300.0, 20.0, 800.0, 10.0, 400.0)
    assert r.ab_cm2 == pytest.approx(math.pi * (2.0**2) / 4.0, abs=1e-6)


# --- parafusos: pressão de contato / esmagamento (NBR 8800:2008 §6.3.3.3) -----
def test_bolt_bearing_resistance_upper_limit():
    # Fc,Rd = 2.4 * db * t * fu / gamma_a2 (limite superior)
    # db=2 cm, t=1 cm, fu=400 MPa=40 kN/cm²: 2.4*2*1*40/1.35 = 192/1.35 = 142.222 kN
    assert bolt_bearing_resistance(20.0, 10.0, 400.0) == pytest.approx(142.222, abs=0.01)


def test_bolt_bearing_thin_plate():
    # t=3 mm=0.3 cm: 2.4*2*0.3*40/1.35 = 57.6/1.35 = 42.667 kN
    assert bolt_bearing_resistance(20.0, 3.0, 400.0) == pytest.approx(42.667, abs=0.01)


# --- dimensionamento da ligação parafusada ------------------------------------
def test_design_bolted_shear_governs():
    # Fv=74.467, Fc=142.222 -> governa cortante; min=74.467
    # n = ceil(300 / 74.467) = ceil(4.029) = 5; cap = 5*74.467 = 372.34 kN
    r = design_bolted_connection(300.0, 20.0, 800.0, 10.0, 400.0)
    assert isinstance(r, BoltedConnectionResult)
    assert r.fv_rd_kn == pytest.approx(74.467, abs=0.01)
    assert r.fc_rd_kn == pytest.approx(142.222, abs=0.01)
    assert r.rd_bolt_kn == pytest.approx(74.467, abs=0.01)
    assert r.governante == "cortante"
    assert r.n_parafusos == 5
    assert r.capacidade_total_kn == pytest.approx(372.34, abs=0.05)
    assert r.capacidade_total_kn >= r.forca_kn


def test_design_bolted_bearing_governs():
    # chapa fina t=3 mm: Fc=42.667 < Fv=74.467 -> governa pressão de contato
    # n = ceil(200 / 42.667) = ceil(4.687) = 5
    r = design_bolted_connection(200.0, 20.0, 800.0, 3.0, 400.0)
    assert r.governante == "pressão de contato"
    assert r.rd_bolt_kn == pytest.approx(42.667, abs=0.01)
    assert r.n_parafusos == 5


def test_design_bolted_exact_multiple_no_extra_bolt():
    # se a força é múltiplo exato da resistência por parafuso, não soma parafuso extra
    fv = bolt_shear_resistance(20.0, 800.0)
    r = design_bolted_connection(fv * 3.0, 20.0, 800.0, 10.0, 400.0)
    assert r.n_parafusos == 3


# --- solda de filete (NBR 8800:2008 §6.2.6) -----------------------------------
def test_fillet_weld_resistance_per_cm():
    # aw = 0.7*perna; Rd = 0.6*fw*aw / gamma_a2
    # perna=5 mm=0.5 cm -> aw=0.35 cm; fw=485 MPa=48.5 kN/cm²
    # Rd = 0.6*48.5*0.35/1.35 = 10.185/1.35 = 7.5444 kN/cm
    assert fillet_weld_resistance(5.0) == pytest.approx(7.5444, abs=0.001)


def test_fillet_weld_resistance_default_electrode_e70():
    # fw padrão = 485 MPa (eletrodo E70) -> mesmo valor do teste anterior
    assert fillet_weld_resistance(5.0, fw_mpa=485.0) == pytest.approx(7.5444, abs=0.001)


def test_design_fillet_weld_length():
    # força=150 kN, perna=5 mm -> L = 150 / 7.5444 = 19.882 cm
    r = design_fillet_weld(150.0, 5.0)
    assert isinstance(r, WeldResult)
    assert r.rd_kn_cm == pytest.approx(7.5444, abs=0.001)
    assert r.comprimento_nec_cm == pytest.approx(19.882, abs=0.01)
    assert r.aw_cm == pytest.approx(0.35, abs=1e-6)


# --- abstenção: entradas física/dimensionalmente inválidas --------------------
def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        bolt_shear_resistance(-20.0, 800.0)
    with pytest.raises(ValueError):
        bolt_shear_resistance(20.0, 0.0)
    with pytest.raises(ValueError):
        bolt_shear_resistance(20.0, 800.0, planos=0)
    with pytest.raises(ValueError):
        bolt_bearing_resistance(20.0, -1.0, 400.0)
    with pytest.raises(ValueError):
        design_bolted_connection(-300.0, 20.0, 800.0, 10.0, 400.0)
    with pytest.raises(ValueError):
        design_fillet_weld(150.0, 0.0)
    with pytest.raises(ValueError):
        fillet_weld_resistance(5.0, fw_mpa=-1.0)


# --- validação determinística (lib/validators/steel_connections_check.py) ------
def test_validate_bolted_ok():
    r = design_bolted_connection(300.0, 20.0, 800.0, 10.0, 400.0)
    rep = validate_bolted(r)
    assert isinstance(rep, ValidationReport)
    assert rep.passed is True


def test_validate_bolted_warns_unusual_bitola():
    # db=30 mm fora da faixa usual [12.5, 25] -> alerta (warning), mas não falha
    r = design_bolted_connection(300.0, 30.0, 800.0, 10.0, 400.0)
    rep = validate_bolted(r)
    assert rep.passed is True
    assert any("bitola" in w.lower() for w in rep.warnings)


def test_validate_weld_ok():
    r = design_fillet_weld(150.0, 5.0)
    rep = validate_weld(r)
    assert rep.passed is True


def test_validate_weld_fails_small_leg():
    # perna = 2 mm < 3 mm (mínimo) -> reprova na validação dimensional
    r = design_fillet_weld(150.0, 2.0)
    rep = validate_weld(r)
    assert rep.passed is False
    assert any(c.status == "fail" for c in rep.checks)
