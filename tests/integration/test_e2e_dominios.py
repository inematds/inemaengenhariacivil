"""Testes E2E (Fase 6) — pilha completa de cada domínio: service → cálculo → validação → memorial.

Cada caso exercita um orquestrador ``solve_*`` de :mod:`lib.service` de ponta a ponta
(é E2E de código: não sobe o processo do MCP, mas percorre a mesma engine que o server
expõe). As entradas são idênticas às dos testes unitários de ``test_service_phase*.py``,
ou seja, casos comprovadamente APROVADOS na camada de validação.

Para cada domínio asserta-se:
- o bundle tem as 5 chaves do contrato (``resultado``, ``validacao``, ``memorial_markdown``,
  ``aviso``, ``aprovado``);
- ``aprovado is True`` (e coerente com ``validacao.passed``);
- o memorial carrega o aviso obrigatório: ``RESPONSABILIDADE TÉCNICA`` e a ``Lei 6.496/77``.

Há ainda um teste do ciclo de memória de projeto (criar → registrar bundle real →
relatório consolidado) usando ``tmp_path``.
"""

from __future__ import annotations

import pathlib

import pytest

from lib.projects.store import (
    ProjectRecord,
    add_calculo,
    load_project,
    save_project,
)
from lib.reporting.report import build_project_report
from lib.service import (
    solve_bearing_capacity,
    solve_bolted_connection,
    solve_compression,
    solve_consolidation_settlement,
    solve_earth_pressure_coulomb,
    solve_earth_pressure_rankine,
    solve_earthwork,
    solve_elastic_settlement,
    solve_fellenius,
    solve_flexible_pavement,
    solve_head_loss,
    solve_infinite_slope,
    solve_one_way_slab,
    solve_open_channel,
    solve_orcamento,
    solve_pile_comparison,
    solve_pipe_flow,
    solve_rectangular_beam,
    solve_rectangular_column,
    solve_square_footing,
    solve_two_way_slab,
    solve_weld,
)

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}
_CSV = str(pathlib.Path(__file__).resolve().parents[2] / "data" / "sinapi_amostra.csv")

# Perfil de solo reaproveitado nas estacas (mesmo de test_service_phase3).
_LAYERS = [
    {"n_spt": 8, "soil_type": "argila siltosa", "thickness_m": 4.0},
    {"n_spt": 20, "soil_type": "areia siltosa", "thickness_m": 6.0},
]

# Fatias reaproveitadas no Fellenius (mesmo de test_service_phase6).
_SLICES = [
    {"w_kn": 50.0, "alpha_deg": -10.0, "dl_m": 2.0},
    {"w_kn": 120.0, "alpha_deg": 10.0, "dl_m": 2.1},
    {"w_kn": 150.0, "alpha_deg": 30.0, "dl_m": 2.6},
]

# Um caso APROVADO por domínio. Cada valor é um callable que devolve o bundle do service.
# Cobre as variantes pedidas: laje 1/2 direções, recalque elástico/adensamento, empuxo
# Rankine/Coulomb, conduto Hazen-Williams/Darcy-Weisbach e talude infinito/Fellenius.
_CASOS_APROVADOS = {
    # --- estrutural (concreto) -------------------------------------------------
    "viga_concreto": lambda: solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    ),
    "pilar_concreto": lambda: solve_rectangular_column(
        nk_kn=500.0, mk_topo_knm=20.0, b_cm=40.0, h_cm=30.0, le_cm=300.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    ),
    "sapata_isolada": lambda: solve_square_footing(
        nk_kn=500.0, sigma_adm_kpa=200.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    ),
    "laje_uma_direcao": lambda: solve_one_way_slab(
        lx_m=4.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0, fck_mpa=25.0, fyk_mpa=500.0,
    ),
    "laje_duas_direcoes": lambda: solve_two_way_slab(
        lx_m=4.0, ly_m=5.0, g_knm2=1.0, q_knm2=2.0, h_cm=12.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    ),
    # --- geotecnia -------------------------------------------------------------
    "capacidade_carga": lambda: solve_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0, b_m=2.0, depth_df_m=1.5,
    ),
    "recalque_elastico": lambda: solve_elastic_settlement(
        q_kpa=150.0, b_m=2.0, poisson_nu=0.3, iw=0.95, es_kpa=20000.0,
    ),
    "recalque_adensamento": lambda: solve_consolidation_settlement(
        cc=0.3, e0=0.8, h_m=4.0, sigma0_kpa=80.0, delta_sigma_kpa=60.0,
    ),
    "empuxo_rankine": lambda: solve_earth_pressure_rankine(
        gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0,
    ),
    "empuxo_coulomb": lambda: solve_earth_pressure_coulomb(
        gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0, delta_deg=20.0,
    ),
    "estaca_comparacao": lambda: solve_pile_comparison(_LAYERS, "pre-moldada", 0.30),
    # --- hidráulica ------------------------------------------------------------
    "conduto_hazen_williams": lambda: solve_pipe_flow(
        Q_m3s=0.05, D_m=0.30, L_m=1000.0, metodo="hazen-williams", C=130.0,
    ),
    "conduto_darcy_weisbach": lambda: solve_pipe_flow(
        Q_m3s=0.05, D_m=0.30, L_m=1000.0, metodo="darcy-weisbach", eps_m=1.5e-4,
    ),
    "canal_manning": lambda: solve_open_channel(
        geometria="retangular", n=0.013, S=0.001, y_m=0.5, b_m=1.0,
    ),
    "perda_de_carga": lambda: solve_head_loss(
        hf_distribuida_m=2.0,
        singularidades={"curva_90": 2, "registro_gaveta_aberto": 1},
        V_ms=1.5,
    ),
    # --- orçamento -------------------------------------------------------------
    "orcamento": lambda: solve_orcamento(
        itens=[
            {"codigo": "92873", "quantidade": 1.5},
            {"codigo": "92915", "quantidade": 180.0},
            {"codigo": "92438", "quantidade": 18.0},
        ],
        bdi_pct=25.0,
        csv_path=_CSV,
    ),
    # --- metálicas -------------------------------------------------------------
    "compressao_aco": lambda: solve_compression(
        designacao="W250x22,3", kl_cm=300.0, fy_mpa=250.0,
    ),
    "ligacao_parafusada": lambda: solve_bolted_connection(
        forca_kn=200.0, db_mm=20.0, fub_mpa=800.0, t_mm=9.5, fu_mpa=400.0,
    ),
    "solda_filete": lambda: solve_weld(forca_kn=200.0, perna_mm=6.0),
    # --- pavimento / terraplenagem / taludes -----------------------------------
    "pavimento_flexivel": lambda: solve_flexible_pavement(
        cbr_subleito=10.0, n_trafego=1.0e6,
    ),
    "terraplenagem": lambda: solve_earthwork(
        volume_corte_m3=5000.0, volume_aterro_m3=3000.0, fator_empolamento=1.25,
    ),
    "talude_infinito": lambda: solve_infinite_slope(
        c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0, z_m=3.0, beta_deg=20.0,
    ),
    "talude_fellenius": lambda: solve_fellenius(_SLICES, c_kpa=15.0, phi_deg=20.0),
}


@pytest.mark.parametrize("dominio", sorted(_CASOS_APROVADOS))
def test_e2e_dominio_aprovado(dominio: str) -> None:
    """Pilha completa de um caso aprovado por domínio: contrato + aprovação + aviso."""
    bundle = _CASOS_APROVADOS[dominio]()

    # contrato: o bundle tem as 5 chaves padrão
    assert set(bundle) >= _KEYS

    # o caso escolhido passa na validação e o flag é coerente com o relatório embutido
    assert bundle["aprovado"] is True
    assert bundle["aprovado"] == bundle["validacao"]["passed"]

    # o memorial carrega o aviso obrigatório (responsabilidade técnica + Lei 6.496/77)
    memorial = bundle["memorial_markdown"]
    assert "RESPONSABILIDADE TÉCNICA" in memorial
    assert "6.496/77" in memorial

    # o aviso também aparece no campo dedicado do bundle
    assert "6.496/77" in bundle["aviso"]


def test_e2e_cobre_todos_os_dominios() -> None:
    """Sanidade: a suíte cobre todos os orquestradores de domínio do service."""
    # 22 domínios da Fase 1-6 + variantes HW/DW de conduto = 23 casos aprovados.
    assert len(_CASOS_APROVADOS) >= 22


def test_e2e_ciclo_memoria_projeto(tmp_path) -> None:
    """Ciclo de memória: criar projeto → registrar bundle real → relatório consolidado.

    Usa ``tmp_path`` (não toca em ``memory/projects/`` real). O relatório consolidado
    deve embutir o memorial do cálculo, o cabeçalho do projeto e o aviso obrigatório.
    """
    bundle = solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    assert bundle["aprovado"] is True

    rec = ProjectRecord(
        project_id="e2e-edificio",
        nome="Edifício E2E",
        responsavel="Eng. Responsável",
        criado_em="2026-01-01T00:00:00",
    )
    save_project(rec, base_dir=str(tmp_path))
    add_calculo(
        "e2e-edificio", bundle, base_dir=str(tmp_path),
        timestamp="2026-01-01T00:00:00",
    )

    # roundtrip em disco preservou o bundle e o carimbo de tempo do chamador
    reloaded = load_project("e2e-edificio", base_dir=str(tmp_path))
    assert len(reloaded.calculos) == 1
    assert reloaded.calculos[0]["registrado_em"] == "2026-01-01T00:00:00"

    relatorio = build_project_report(reloaded)
    # o relatório consolidado embute o memorial REAL do cálculo...
    assert bundle["memorial_markdown"] in relatorio
    # ...sob o cabeçalho do projeto e com o aviso obrigatório
    assert "Edifício E2E" in relatorio
    assert "RESPONSABILIDADE TÉCNICA" in relatorio
    assert "6.496/77" in relatorio
