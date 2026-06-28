"""Testes dos orquestradores de alto nível da Fase 2 (pilar, sapata, lajes).

Cada ``solve_*`` deve devolver o mesmo pacote serializável da viga: resultado,
validação, memorial, aviso (com a Lei 6.496/77) e o flag ``aprovado`` coerente.
"""

from lib.service import (
    solve_one_way_slab,
    solve_rectangular_column,
    solve_square_footing,
    solve_two_way_slab,
)

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}


def _assert_bundle(bundle: dict) -> None:
    assert set(bundle) >= _KEYS
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    # coerência: aprovado reflete a validação embutida
    assert bundle["aprovado"] == bundle["validacao"]["passed"]


def test_solve_column_bundle_approved():
    bundle = solve_rectangular_column(
        nk_kn=500.0, mk_topo_knm=20.0, b_cm=40.0, h_cm=30.0, le_cm=300.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["as_adopted_cm2"] > 0
    assert bundle["resultado"]["esbeltez"] > 0


def test_solve_footing_bundle_approved():
    bundle = solve_square_footing(
        nk_kn=500.0, sigma_adm_kpa=200.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["sigma_solo_kpa"] <= bundle["resultado"]["sigma_adm_kpa"]


def test_solve_footing_bundle_overstressed_rejected():
    # σ_solo ligeiramente acima de σ_adm => a validação deve reprovar (coerência).
    bundle = solve_square_footing(
        nk_kn=600.0, sigma_adm_kpa=150.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is False


def test_solve_one_way_slab_bundle_approved():
    bundle = solve_one_way_slab(
        lx_m=4.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0, fck_mpa=25.0, fyk_mpa=500.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["tipo"] == "uma_direcao"
    assert bundle["resultado"]["as_x_cm2_m"] > 0


def test_solve_two_way_slab_bundle_approved():
    bundle = solve_two_way_slab(
        lx_m=4.0, ly_m=5.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["tipo"] == "duas_direcoes"
    assert bundle["resultado"]["my_knm"] is not None
