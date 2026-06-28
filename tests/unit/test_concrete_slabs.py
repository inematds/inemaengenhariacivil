"""Testes de laje maciça de concreto armado (NBR 6118:2014).

Valores de referência calculados à mão (a conta está nos comentários).
- Laje 1 direção: faixa de 1 m como viga, Md = p_d*lx^2/8 por metro.
- Laje 2 direções (apoiada nos 4 lados): método das faixas de Grashof-Rankine
  (igualdade de flechas centrais), px = p*ly^4/(lx^4+ly^4), py = p*lx^4/(lx^4+ly^4),
  Mx = px*lx^2/8, My = py*ly^2/8.
Coeficientes: gamma_g=gamma_q=1.4; peso próprio = 25*h.
"""

import pytest

from lib.concrete.slabs import (
    SlabResult,
    design_one_way_slab,
    design_two_way_slab,
)


# ----------------------------------------------------------- laje em 1 direção

def test_one_way_slab_known_case():
    # lx=4, g=1.5, q=2.0, h=10, C25, CA-50
    # pp=25*0.10=2.5; g_tot=4.0; p_d=1.4*4.0+1.4*2.0=8.4 kN/m²
    # Md=8.4*4²/8=16.8 kN·m/m; d=10-2.5-0.5=7.0
    # As≈6.344 cm²/m (flexure_design); As,mín=0.15%*100*10=1.5 cm²/m
    r = design_one_way_slab(lx_m=4.0, g_knm2=1.5, q_knm2=2.0, h_cm=10.0,
                            fck_mpa=25.0, fyk_mpa=500.0)
    assert isinstance(r, SlabResult)
    assert r.tipo == "uma_direcao"
    assert r.pp_knm2 == pytest.approx(2.5, abs=1e-6)
    assert r.pd_knm2 == pytest.approx(8.4, abs=1e-3)
    assert r.mx_knm == pytest.approx(16.8, abs=0.01)
    assert r.as_x_cm2_m == pytest.approx(6.344, abs=0.02)
    assert r.as_min_x_cm2_m == pytest.approx(1.5, abs=1e-3)
    assert r.as_x_cm2_m >= r.as_min_x_cm2_m
    assert r.as_y_cm2_m > 0  # armadura de distribuição
    assert r.ly_m is None and r.my_knm is None


def test_one_way_slab_min_thickness_warns():
    # h=6 cm < h_min (8 cm, laje de piso) -> aviso
    r = design_one_way_slab(lx_m=3.0, g_knm2=1.0, q_knm2=1.5, h_cm=6.0,
                            fck_mpa=25.0, fyk_mpa=500.0)
    assert any("mínim" in w.lower() or "minim" in w.lower() for w in r.warnings)


# --------------------------------------------------------- laje em 2 direções

def test_two_way_slab_known_case():
    # lx=4, ly=5, g=2, q=3, h=12, C25, CA-50
    # pp=3.0; g_tot=5.0; p_d=1.4*5+1.4*3=11.2 kN/m²; λ=ly/lx=1.25
    # px=11.2*5⁴/(4⁴+5⁴)=11.2*625/881=7.9455; py=11.2*256/881=3.2545
    # Mx=7.9455*4²/8=15.891; My=3.2545*5²/8=10.170
    r = design_two_way_slab(lx_m=4.0, ly_m=5.0, g_knm2=2.0, q_knm2=3.0, h_cm=12.0,
                            fck_mpa=25.0, fyk_mpa=500.0)
    assert isinstance(r, SlabResult)
    assert r.tipo == "duas_direcoes"
    assert r.pd_knm2 == pytest.approx(11.2, abs=1e-3)
    assert r.px_knm2 == pytest.approx(7.9455, abs=0.01)
    assert r.py_knm2 == pytest.approx(3.2545, abs=0.01)
    assert r.mx_knm == pytest.approx(15.891, abs=0.02)
    assert r.my_knm == pytest.approx(10.170, abs=0.02)
    assert r.as_x_cm2_m == pytest.approx(4.364, abs=0.02)
    assert r.as_y_cm2_m == pytest.approx(3.096, abs=0.02)
    assert r.mx_knm > r.my_knm  # direção curta carrega mais


def test_two_way_slab_warns_when_ratio_above_two():
    # λ=ly/lx=2.5 > 2 -> recomendar laje em uma direção
    r = design_two_way_slab(lx_m=2.0, ly_m=5.0, g_knm2=2.0, q_knm2=2.0, h_cm=10.0,
                            fck_mpa=25.0, fyk_mpa=500.0)
    assert any("uma dire" in w.lower() or "λ" in w or "2" in w for w in r.warnings)


def test_two_way_slab_rejects_ly_less_than_lx():
    with pytest.raises(ValueError):
        design_two_way_slab(lx_m=5.0, ly_m=4.0, g_knm2=2.0, q_knm2=3.0, h_cm=12.0,
                            fck_mpa=25.0, fyk_mpa=500.0)


def test_slab_rejects_invalid_material():
    with pytest.raises(ValueError):
        design_one_way_slab(lx_m=4.0, g_knm2=1.0, q_knm2=1.0, h_cm=10.0,
                            fck_mpa=60.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_two_way_slab(lx_m=4.0, ly_m=5.0, g_knm2=1.0, q_knm2=1.0, h_cm=12.0,
                            fck_mpa=25.0, fyk_mpa=200.0)
