"""Testes do orquestrador de alto nível (cálculo + validação + memorial)."""

from lib.service import solve_rectangular_beam


def test_solve_returns_full_bundle():
    bundle = solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    assert set(bundle) >= {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}
    assert bundle["aprovado"] is True
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    assert bundle["resultado"]["as_adopted_cm2"] > 0
