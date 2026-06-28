"""Testes do orquestrador da Fase 5 (metálicas): bundles de compressão e ligações.

Cada ``solve_*`` devolve o pacote serializável padrão: resultado, validação,
memorial (com aviso embutido), aviso (Lei 6.496/77) e o flag ``aprovado`` coerente.
Abstenção: perfil inexistente propaga ``KeyError``; entradas inválidas, ``ValueError``.
"""

import pytest

from lib.service import solve_bolted_connection, solve_compression, solve_weld

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}


def _assert_bundle(bundle: dict) -> None:
    assert set(bundle) >= _KEYS
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    assert "NBR 8800" in bundle["memorial_markdown"]
    assert bundle["aprovado"] == bundle["validacao"]["passed"]


# --- compressão ------------------------------------------------------------
def test_solve_compression_bundle_approved():
    bundle = solve_compression(designacao="W250x22,3", kl_cm=300.0, fy_mpa=250.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["designacao"] == "W250x22,3"
    # Nc,Rd ≈ 213,33 kN (calculado à mão a partir do catálogo)
    assert r["nc_rd_kn"] == pytest.approx(213.33, abs=0.1)
    assert r["i_cm4"] == pytest.approx(122.0)  # eixo fraco (Iy) governa


def test_solve_compression_unknown_profile_aborts():
    with pytest.raises(KeyError):
        solve_compression(designacao="W999x99,9", kl_cm=300.0)


# --- ligação parafusada ----------------------------------------------------
def test_solve_bolted_bundle_approved():
    bundle = solve_bolted_connection(
        forca_kn=200.0, db_mm=20.0, fub_mpa=800.0, t_mm=9.5, fu_mpa=400.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["n_parafusos"] == 3
    assert r["governante"] == "cortante"
    assert r["capacidade_total_kn"] >= r["forca_kn"]


def test_solve_bolted_invalid_force_aborts():
    with pytest.raises(ValueError):
        solve_bolted_connection(
            forca_kn=-5.0, db_mm=20.0, fub_mpa=800.0, t_mm=9.5, fu_mpa=400.0,
        )


# --- solda de filete -------------------------------------------------------
def test_solve_weld_bundle_approved():
    bundle = solve_weld(forca_kn=200.0, perna_mm=6.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    # L = força / Rd, com Rd ≈ 9,0533 kN/cm -> L ≈ 22,09 cm
    assert r["comprimento_nec_cm"] == pytest.approx(22.09, abs=0.1)


def test_solve_weld_below_min_leg_reproved():
    # perna < 3 mm: a validação reprova (mínimo prático de filete)
    bundle = solve_weld(forca_kn=50.0, perna_mm=2.0)
    assert bundle["aprovado"] is False
