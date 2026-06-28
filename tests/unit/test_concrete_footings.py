"""Testes de sapata isolada quadrada rígida (NBR 6122 + NBR 6118:2014 22.6).

Valores de referência calculados à mão (a conta está nos comentários).
Método das bielas (NBR 6118 22.6.4.1): As = Nd·(L − a_pilar) / (8·d·fyd), Nd = 1.4·Nk.
"""

import pytest

from lib.concrete.footings import FootingResult, design_square_footing


def test_design_square_footing_known_case():
    # Nk=800 kN, σ_adm=300 kPa, pilar 30x30, C25, CA-50
    # A_nec = 1.05*800/300 = 2.80 m²;  L = √2.80 = 1.6733 m -> 170 cm
    # A_ef  = 1.70² = 2.89 m²
    # h_min rígida = (170-30)/3 = 46.67 cm -> adota 50 cm; d = 50-5-1.25 = 43.75 cm
    # pp    = 25*2.89*0.50 = 36.125 kN
    # σ_solo = (800+36.125)/2.89 = 289.32 kPa <= 300  OK
    # Nd = 1.4*800 = 1120 kN; fyd = 500/1.15 = 434.78 MPa = 43.478 kN/cm²
    # As = 1120*140 / (8*43.75*43.478) = 156800 / 15217.4 = 10.30 cm²
    r = design_square_footing(
        nk_kn=800.0, sigma_adm_kpa=300.0,
        pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert isinstance(r, FootingResult)
    assert r.area_nec_m2 == pytest.approx(2.80, abs=0.005)
    assert r.lado_cm == pytest.approx(170.0, abs=1e-6)
    assert r.area_efetiva_m2 == pytest.approx(2.89, abs=1e-3)
    assert r.altura_h_cm == pytest.approx(50.0, abs=1e-6)
    assert r.d_cm == pytest.approx(43.75, abs=1e-6)
    assert r.pp_sapata_kn == pytest.approx(36.125, abs=0.01)
    assert r.sigma_solo_kpa == pytest.approx(289.32, abs=0.1)
    assert r.rigida is True
    assert r.nd_kn == pytest.approx(1120.0, abs=1e-6)
    assert r.as_x_cm2 == pytest.approx(10.30, abs=0.05)
    assert r.as_y_cm2 == pytest.approx(10.30, abs=0.05)
    assert r.bars_x.as_ef_cm2 >= r.as_x_cm2
    assert r.bars_y.as_ef_cm2 >= r.as_y_cm2


def test_design_square_footing_rounds_side_and_respects_pilar():
    # A_nec = 1.05*500/250 = 2.10 m²; L = √2.10 = 1.4491 m = 144.91 -> 145 cm
    r = design_square_footing(
        nk_kn=500.0, sigma_adm_kpa=250.0,
        pilar_a_cm=20.0, pilar_b_cm=20.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert r.lado_cm == pytest.approx(145.0, abs=1e-6)
    assert r.lado_cm >= max(r.pilar_a_cm, r.pilar_b_cm)
    assert r.lado_cm % 5 == pytest.approx(0.0, abs=1e-9)


def test_design_square_footing_soil_overstress_warns():
    # Nk=1000, σ_adm=200: footing alta (h=70) + solo fraco -> pp > 5%·Nk
    # A_nec=5.25 -> L=230 cm; A_ef=5.29; h_min=(230-30)/3=66.67 -> 70 cm
    # pp=25*5.29*0.70=92.575; σ_solo=(1000+92.575)/5.29=206.5 kPa > 200
    r = design_square_footing(
        nk_kn=1000.0, sigma_adm_kpa=200.0,
        pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert r.sigma_solo_kpa > r.sigma_adm_kpa
    assert any("solo" in w.lower() for w in r.warnings)


def test_design_square_footing_rectangular_column_differs_per_direction():
    # pilar 50x20: As maior na direção do menor lado do pilar (maior balanço)
    r = design_square_footing(
        nk_kn=800.0, sigma_adm_kpa=300.0,
        pilar_a_cm=50.0, pilar_b_cm=20.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert r.as_y_cm2 > r.as_x_cm2  # (L - 20) > (L - 50)


def test_design_square_footing_rejects_invalid():
    with pytest.raises(ValueError):
        design_square_footing(nk_kn=-1.0, sigma_adm_kpa=200.0,
                              pilar_a_cm=30.0, pilar_b_cm=30.0,
                              fck_mpa=25.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_square_footing(nk_kn=500.0, sigma_adm_kpa=0.0,
                              pilar_a_cm=30.0, pilar_b_cm=30.0,
                              fck_mpa=25.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_square_footing(nk_kn=500.0, sigma_adm_kpa=200.0,
                              pilar_a_cm=-30.0, pilar_b_cm=30.0,
                              fck_mpa=25.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_square_footing(nk_kn=500.0, sigma_adm_kpa=200.0,
                              pilar_a_cm=30.0, pilar_b_cm=30.0,
                              fck_mpa=60.0, fyk_mpa=500.0)  # fck>50 fora de escopo
