"""Testes de flexão simples — viga retangular de concreto armado (NBR 6118:2014, ELU).

Valores de referência calculados à mão (bloco retangular de tensões, fck <= 50 MPa:
lambda=0.8, alpha_c=0.85; gamma_c=1.4, gamma_s=1.15).
"""

import pytest

from lib.concrete.beams import design_rectangular_beam, flexure_design, select_bars


# ---------------------------------------------------------------- flexure_design

def test_flexure_design_known_section():
    # Md=150 kN.m, b=20, d=45, C25, CA-50  ->  x~16.0 cm, As~8.94 cm2
    r = flexure_design(md_knm=150.0, b_cm=20.0, d_cm=45.0, fck_mpa=25.0, fyk_mpa=500.0)
    assert r.x_cm == pytest.approx(16.00, abs=0.05)
    assert r.x_over_d == pytest.approx(0.356, abs=0.005)
    assert r.z_cm == pytest.approx(38.60, abs=0.05)
    assert r.as_calc_cm2 == pytest.approx(8.94, abs=0.05)


def test_flexure_design_low_moment_gives_small_steel():
    # Md baixo -> As_calc pequeno (As_min é aplicado só no dimensionamento completo)
    r = flexure_design(md_knm=10.0, b_cm=20.0, d_cm=45.0, fck_mpa=25.0, fyk_mpa=500.0)
    assert r.as_calc_cm2 == pytest.approx(0.516, abs=0.02)


# ------------------------------------------------------------------- select_bars

def test_select_bars_minimizes_excess_area():
    # As=8.94 cm2 -> 3 phi 20mm (As_ef = 9.42 cm2) é a opção de menor excesso
    choice = select_bars(8.94)
    assert choice.n_bars == 3
    assert choice.phi_mm == 20.0
    assert choice.as_ef_cm2 == pytest.approx(9.42, abs=0.02)


def test_select_bars_always_meets_demand():
    choice = select_bars(5.40)
    assert choice.as_ef_cm2 >= 5.40


# --------------------------------------------------- design_rectangular_beam (full)

def test_design_beam_load_chain():
    # viga 25x50, C30, vao 5m, g=10 q=10 (excl. PP). PP=25*0.25*0.50=3.125 kN/m
    r = design_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    assert r.pp_knm == pytest.approx(3.125, abs=0.001)
    assert r.pd_knm == pytest.approx(32.375, abs=0.01)      # 1.4*(10+3.125)+1.4*10
    assert r.md_knm == pytest.approx(101.17, abs=0.1)        # pd*L^2/8
    assert r.as_adopted_cm2 >= r.as_min_cm2
    assert r.bars.as_ef_cm2 >= r.as_adopted_cm2
    assert r.x_over_d < 0.45                                  # dúctil
    assert r.ductile is True


def test_design_beam_minimum_steel_governs():
    # cargas pequenas -> As_min governa
    r = design_rectangular_beam(
        b_cm=20.0, h_cm=40.0, fck_mpa=25.0, fyk_mpa=500.0,
        vao_m=3.0, g_knm=1.0, q_knm=1.0, d_cm=36.0,
    )
    assert r.as_min_cm2 == pytest.approx(1.20, abs=0.001)     # 0.15% * 20 * 40
    assert r.as_adopted_cm2 == pytest.approx(1.20, abs=0.001)
    assert r.governed_by == "As_min"


def test_design_beam_rejects_invalid_fck():
    with pytest.raises(Exception):
        design_rectangular_beam(
            b_cm=20.0, h_cm=40.0, fck_mpa=5.0, fyk_mpa=500.0,
            vao_m=3.0, g_knm=1.0, q_knm=1.0,
        )
