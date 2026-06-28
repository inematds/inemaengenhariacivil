"""Testes dos orquestradores de alto nível da Fase 3 (geotecnia + hidráulica).

Cada ``solve_*`` devolve o pacote serializável padrão: resultado, validação,
memorial (com aviso embutido), aviso (Lei 6.496/77) e o flag ``aprovado`` coerente.
"""

import json
import pathlib

from lib.geotechnical.piles import AOKI_F1F2, AOKI_SOLO, DECOURT_C
from lib.service import (
    solve_bearing_capacity,
    solve_consolidation_settlement,
    solve_earth_pressure_coulomb,
    solve_earth_pressure_rankine,
    solve_elastic_settlement,
    solve_head_loss,
    solve_open_channel,
    solve_pile_comparison,
    solve_pipe_flow,
)

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}


def _assert_bundle(bundle: dict) -> None:
    assert set(bundle) >= _KEYS
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    assert bundle["aprovado"] == bundle["validacao"]["passed"]


def test_solve_bearing_capacity_bundle_approved():
    bundle = solve_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0, b_m=2.0, depth_df_m=1.5,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["q_adm_kpa"] > 0


def test_solve_elastic_settlement_bundle():
    bundle = solve_elastic_settlement(
        q_kpa=150.0, b_m=2.0, poisson_nu=0.3, iw=0.95, es_kpa=20000.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["settlement_mm"] > 0


def test_solve_consolidation_settlement_bundle():
    bundle = solve_consolidation_settlement(
        cc=0.3, e0=0.8, h_m=4.0, sigma0_kpa=80.0, delta_sigma_kpa=60.0,
    )
    _assert_bundle(bundle)
    assert bundle["resultado"]["settlement_mm"] > 0


def test_solve_earth_pressure_rankine_bundle_approved():
    bundle = solve_earth_pressure_rankine(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    # Ka = 1/3, Ea = 0,5·18·4²·(1/3) = 48 kN/m
    assert abs(bundle["resultado"]["ea_active_kn_m"] - 48.0) < 1e-6


def test_solve_earth_pressure_coulomb_bundle():
    bundle = solve_earth_pressure_coulomb(
        gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0, delta_deg=20.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["ka"] > 0


def test_solve_pile_comparison_bundle():
    layers = [
        {"n_spt": 8, "soil_type": "argila siltosa", "thickness_m": 4.0},
        {"n_spt": 20, "soil_type": "areia siltosa", "thickness_m": 6.0},
    ]
    bundle = solve_pile_comparison(layers, "pre-moldada", 0.30)
    _assert_bundle(bundle)
    # ambos os métodos válidos => aprovado True; a divergência é só um aviso
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["rult_aoki_kn"] > 0
    assert bundle["resultado"]["rult_decourt_kn"] > 0
    assert "divergencia_pct" in bundle["resultado"]


def test_solve_pile_comparison_divergence_warns():
    # perfil com ponta muito mais forte no atrito que na ponta amplifica divergência
    layers = [
        {"n_spt": 3, "soil_type": "argila", "thickness_m": 8.0},
        {"n_spt": 40, "soil_type": "areia", "thickness_m": 2.0},
    ]
    bundle = solve_pile_comparison(layers, "escavada", 0.40)
    _assert_bundle(bundle)
    if not bundle["resultado"]["convergem"]:
        assert any("Divergência" in w for w in bundle["validacao"]["warnings"])


def test_solve_pipe_flow_hazen_williams_bundle():
    bundle = solve_pipe_flow(Q_m3s=0.05, D_m=0.30, L_m=1000.0, metodo="hazen-williams", C=130.0)
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["hf_m"] > 0
    assert "Hazen-Williams" in bundle["resultado"]["metodo"]


def test_solve_pipe_flow_darcy_weisbach_bundle():
    bundle = solve_pipe_flow(
        Q_m3s=0.05, D_m=0.30, L_m=1000.0, metodo="darcy-weisbach", eps_m=1.5e-4,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["f"] > 0


def test_solve_open_channel_rectangular_bundle():
    bundle = solve_open_channel(
        geometria="retangular", n=0.013, S=0.001, y_m=0.5, b_m=1.0,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["Q_m3s"] > 0


def test_solve_head_loss_bundle():
    bundle = solve_head_loss(
        hf_distribuida_m=2.0,
        singularidades={"curva_90": 2, "registro_gaveta_aberto": 1},
        V_ms=1.5,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    assert bundle["resultado"]["hf_total_m"] > 2.0


# --- consistência das tabelas JSON da NBR 6122 com os valores hardcoded -------

_TABLES = pathlib.Path(__file__).resolve().parents[2] / "normas" / "NBR6122" / "tables"


def test_json_aoki_k_alpha_matches_code():
    data = json.loads((_TABLES / "aoki_velloso_k_alpha.json").read_text(encoding="utf-8"))
    solos = data["solos"]
    assert set(solos) == set(AOKI_SOLO)
    for solo, (k, alpha) in AOKI_SOLO.items():
        assert solos[solo]["K_kpa"] == k
        assert solos[solo]["alpha"] == alpha


def test_json_aoki_f1_f2_matches_code():
    data = json.loads((_TABLES / "aoki_velloso_f1_f2.json").read_text(encoding="utf-8"))
    estacas = data["estacas"]
    assert set(estacas) == set(AOKI_F1F2)
    for tipo, (f1, f2) in AOKI_F1F2.items():
        assert estacas[tipo]["F1"] == f1
        assert estacas[tipo]["F2"] == f2


def test_json_decourt_c_matches_code():
    data = json.loads((_TABLES / "decourt_c.json").read_text(encoding="utf-8"))
    solos = data["solos"]
    assert set(solos) == set(DECOURT_C)
    for solo, c in DECOURT_C.items():
        assert solos[solo]["C_kpa"] == c
