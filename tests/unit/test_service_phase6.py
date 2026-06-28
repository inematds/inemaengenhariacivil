"""Testes do orquestrador da Fase 6 — pavimento, terraplenagem, taludes.

Cada ``solve_*`` devolve o pacote serializável padrão: resultado, validação,
memorial (com aviso embutido), aviso (Lei 6.496/77) e o flag ``aprovado`` coerente.
Abstenção: entradas fora de faixa física propagam ``ValueError``.
"""

import pytest

from lib.geotechnical.slope_stability import Slice
from lib.service import (
    solve_earthwork,
    solve_fellenius,
    solve_flexible_pavement,
    solve_infinite_slope,
)

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}


def _assert_bundle(bundle: dict) -> None:
    assert set(bundle) >= _KEYS
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    assert bundle["aprovado"] == bundle["validacao"]["passed"]


# --- pavimento flexível ----------------------------------------------------
def test_solve_pavement_bundle_approved():
    bundle = solve_flexible_pavement(cbr_subleito=10.0, n_trafego=1.0e6)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["cbr_subleito"] == 10.0
    assert r["espessura_total_cm"] == pytest.approx(39.0)
    assert all(ineq["atende"] for ineq in r["inequacoes"])


def test_solve_pavement_out_of_range_aborts():
    with pytest.raises(ValueError):
        solve_flexible_pavement(cbr_subleito=1.0, n_trafego=1.0e6)


# --- terraplenagem ---------------------------------------------------------
def test_solve_earthwork_bundle_excess():
    bundle = solve_earthwork(volume_corte_m3=5000.0, volume_aterro_m3=3000.0,
                             fator_empolamento=1.25)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["balanco_m3"] == pytest.approx(2000.0)
    assert r["situacao"] == "excesso"
    assert r["volume_corte_solto_m3"] == pytest.approx(6250.0)
    assert r["volume_bota_fora_m3"] == pytest.approx(2000.0)


def test_solve_earthwork_bad_factor_aborts():
    with pytest.raises(ValueError):
        solve_earthwork(volume_corte_m3=100.0, volume_aterro_m3=50.0,
                        fator_empolamento=2.0)


# --- talude infinito -------------------------------------------------------
def test_solve_infinite_slope_bundle_stable():
    bundle = solve_infinite_slope(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                                  z_m=3.0, beta_deg=20.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["fs"] == pytest.approx(1.857, abs=0.01)
    assert r["classification"] == "estável"


def test_solve_infinite_slope_out_of_range_aborts():
    with pytest.raises(ValueError):
        solve_infinite_slope(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                             z_m=3.0, beta_deg=95.0)


# --- Fellenius -------------------------------------------------------------
def test_solve_fellenius_accepts_dicts():
    slices = [
        {"w_kn": 50.0, "alpha_deg": -10.0, "dl_m": 2.0},
        {"w_kn": 120.0, "alpha_deg": 10.0, "dl_m": 2.1},
        {"w_kn": 150.0, "alpha_deg": 30.0, "dl_m": 2.6},
    ]
    bundle = solve_fellenius(slices, c_kpa=15.0, phi_deg=20.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    r = bundle["resultado"]
    assert r["n_slices"] == 3
    assert r["fs"] == pytest.approx(2.395, abs=0.01)
    assert r["classification"] == "estável"


def test_solve_fellenius_accepts_slice_objects():
    slices = [
        Slice(w_kn=50.0, alpha_deg=-10.0, dl_m=2.0),
        Slice(w_kn=120.0, alpha_deg=10.0, dl_m=2.1),
        Slice(w_kn=150.0, alpha_deg=30.0, dl_m=2.6),
    ]
    bundle = solve_fellenius(slices, c_kpa=15.0, phi_deg=20.0)
    _assert_bundle(bundle)
    assert bundle["resultado"]["n_slices"] == 3


def test_solve_fellenius_empty_aborts():
    with pytest.raises(ValueError):
        solve_fellenius([], c_kpa=15.0, phi_deg=20.0)
