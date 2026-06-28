"""Testes da geração de memorial de cálculo e do aviso de responsabilidade."""

from lib.concrete.beams import design_rectangular_beam
from lib.concrete.columns import design_rectangular_column
from lib.concrete.footings import design_square_footing
from lib.concrete.slabs import design_one_way_slab, design_two_way_slab
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.memorial import (
    render_beam_memorial,
    render_column_memorial,
    render_footing_memorial,
    render_slab_memorial,
)
from lib.validators.validate import (
    validate_beam,
    validate_column,
    validate_footing,
    validate_slab,
)


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


def test_column_memorial_has_key_sections_and_values():
    r = design_rectangular_column(
        nk_kn=500.0, mk_topo_knm=20.0, b_cm=40.0, h_cm=30.0, le_cm=300.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    )
    rep = validate_column(r)
    md = render_column_memorial(r, rep)

    assert "Pilar" in md
    assert "NBR 6118" in md
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    assert f"λ = le/i = {r.esbeltez:.1f}" in md      # esbeltez
    assert f"Md,tot = {r.md_tot_knm:.2f}" in md      # momento total
    assert f"As,adotada = {r.as_adopted_cm2:.2f}" in md


def test_footing_memorial_has_key_sections_and_values():
    r = design_square_footing(
        nk_kn=500.0, sigma_adm_kpa=200.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    rep = validate_footing(r)
    md = render_footing_memorial(r, rep)

    assert "Sapata" in md
    assert "NBR 6122" in md
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    assert f"L = {r.lado_cm:.0f} cm" in md           # lado da sapata
    assert f"σ_solo = {r.sigma_solo_kpa:.1f} kPa" in md
    assert f"{r.as_x_cm2:.2f}" in md                 # armadura direção x


def test_one_way_slab_memorial_has_key_sections_and_values():
    r = design_one_way_slab(
        lx_m=4.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0, fck_mpa=25.0, fyk_mpa=500.0,
    )
    rep = validate_slab(r)
    md = render_slab_memorial(r, rep)

    assert "Laje" in md
    assert "NBR 6118" in md
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    assert "uma direção" in md
    assert f"Mx = {r.mx_knm:.2f}" in md
    assert f"{r.as_x_cm2_m:.2f}" in md


def test_two_way_slab_memorial_has_key_sections_and_values():
    r = design_two_way_slab(
        lx_m=4.0, ly_m=5.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    rep = validate_slab(r)
    md = render_slab_memorial(r, rep)

    assert "duas direções" in md
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    assert f"Mx = {r.mx_knm:.2f}" in md
    assert r.my_knm is not None and f"My = {r.my_knm:.2f}" in md
