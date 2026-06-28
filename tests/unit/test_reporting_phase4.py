"""Testes da camada de documentação da Fase 4: memorial de orçamento + relatório.

- ``render_orcamento_memorial``: tabela de itens, subtotal/BDI/total e o aviso de
  responsabilidade técnica (RESPONSABILIDADE TÉCNICA + Lei 6.496/77).
- ``build_project_report``: relatório consolidado de um projeto com vários cálculos,
  contendo cada memorial e o disclaimer ao final.
"""

import pathlib

from lib.budget.estimate import montar_orcamento
from lib.budget.sinapi import load_sinapi
from lib.projects.store import ProjectRecord
from lib.reporting.report import build_project_report
from lib.service import solve_orcamento
from lib.validators.budget_check import validate_orcamento

_CSV = pathlib.Path(__file__).resolve().parents[2] / "data" / "sinapi_amostra.csv"


def _orcamento_bundle():
    return solve_orcamento(
        itens=[
            {"codigo": "92873", "quantidade": 1.5},
            {"codigo": "92915", "quantidade": 180.0},
        ],
        bdi_pct=25.0,
        csv_path=str(_CSV),
    )


# --- memorial de orçamento -------------------------------------------------
def test_orcamento_memorial_has_disclaimer_and_total():
    from lib.reporting.memorial import render_orcamento_memorial

    base = load_sinapi(_CSV)
    r = montar_orcamento(
        [{"codigo": "92873", "quantidade": 1.5}, {"codigo": "92915", "quantidade": 180.0}],
        base,
        bdi_pct=25.0,
    )
    rep = validate_orcamento(r)
    md = render_orcamento_memorial(r, rep)

    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    # subtotal = 1.5*520 + 180*12.5 = 780 + 2250 = 3030; total = 3030*1.25 = 3787.50
    assert f"R$ {r.total:.2f}" in md
    assert "R$ 3787.50" in md
    # itens aparecem na tabela com código e custo
    assert "92873" in md and "92915" in md
    assert "Memorial de Orçamento" in md


def test_orcamento_memorial_shows_bdi_and_subtotal():
    bundle = _orcamento_bundle()
    md = bundle["memorial_markdown"]
    assert "BDI aplicado: 25.00%" in md
    assert "Subtotal (custo direto): R$ 3030.00" in md


# --- relatório consolidado do projeto --------------------------------------
def test_build_project_report_includes_two_calculos_and_disclaimer():
    # dois cálculos no histórico, cada um com seu memorial
    c1 = _orcamento_bundle()
    c2 = solve_orcamento(
        itens=[{"codigo": "92438", "quantidade": 18.0}],
        bdi_pct=20.0,
        csv_path=str(_CSV),
    )
    record = ProjectRecord(
        project_id="edificio-beta",
        nome="Edifício Beta",
        responsavel="Eng. Ciclana",
        calculos=[c1, c2],
    )
    md = build_project_report(record)

    # cabeçalho do projeto
    assert "Edifício Beta" in md
    assert "Eng. Ciclana" in md
    # ambos os memoriais presentes
    assert c1["memorial_markdown"] in md
    assert c2["memorial_markdown"] in md
    # índice cita os dois cálculos
    assert "## Índice de cálculos" in md
    assert "1." in md and "2." in md
    # disclaimer ao final
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md


def test_build_project_report_empty_history():
    record = ProjectRecord(project_id="vazio", nome="Sem Cálculos")
    md = build_project_report(record)
    assert "Sem Cálculos" in md
    assert "nenhum cálculo registrado" in md
    assert "6.496/77" in md
