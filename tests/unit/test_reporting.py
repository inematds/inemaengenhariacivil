"""Testes da geração de memorial de cálculo e do aviso de responsabilidade."""

from lib.concrete.beams import design_rectangular_beam
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.memorial import render_beam_memorial
from lib.validators.validate import validate_beam


def test_disclaimer_cites_correct_laws():
    assert "6.496/77" in DISCLAIMER
    assert "5.194/66" in DISCLAIMER
    assert "ART" in DISCLAIMER


def test_memorial_has_key_sections_and_values():
    r = design_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    rep = validate_beam(r)
    md = render_beam_memorial(r, rep)

    assert "NBR 6118" in md
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md                         # aviso obrigatório embutido
    assert f"Ø {r.bars.phi_mm:.1f}" in md           # detalhamento da armadura
    assert f"{r.as_adopted_cm2:.2f}" in md          # As adotada
    assert "Md" in md                               # momento de cálculo
