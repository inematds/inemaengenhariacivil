"""Relatório técnico consolidado de um projeto (Markdown) — Fase 4.

Monta um único documento a partir do histórico de cálculos de um
:class:`~lib.projects.store.ProjectRecord`: cabeçalho do projeto, índice dos
cálculos e os memoriais já gerados pela engine, concatenados, com o aviso de
responsabilidade técnica obrigatório ao final.

Camada de saída determinística: não recalcula nada — apenas costura os
``memorial_markdown`` que o service produziu. O PDF é oferecido reusando
:func:`lib.reporting.pdf_export.export_memorial_to_pdf`.
"""

from __future__ import annotations

from lib.projects.store import ProjectRecord
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.pdf_export import export_memorial_to_pdf


def _titulo_calculo(calc: dict, i: int) -> str:
    """Extrai o título do cálculo a partir do primeiro heading do memorial."""
    memorial = calc.get("memorial_markdown", "") or ""
    for linha in memorial.splitlines():
        s = linha.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return f"Cálculo {i}"


def build_project_report(record: ProjectRecord) -> str:
    """Monta o relatório técnico consolidado (Markdown) de um projeto.

    Inclui o cabeçalho (nome, responsável), o índice dos cálculos do histórico
    (``record.calculos``, cada um um bundle do service com ``memorial_markdown``)
    e os memoriais na íntegra. Termina sempre com o ``DISCLAIMER``.
    """
    linhas: list[str] = []
    add = linhas.append

    add(f"# Relatório Técnico Consolidado — {record.nome}")
    add("")
    add(f"**Projeto (id):** {record.project_id}  ")
    add(f"**Responsável técnico:** {record.responsavel or '— (a definir)'}  ")
    if record.criado_em:
        add(f"**Criado em:** {record.criado_em}  ")
    add(f"**Cálculos no histórico:** {len(record.calculos)}")
    add("")

    add("## Índice de cálculos")
    add("")
    if record.calculos:
        for i, calc in enumerate(record.calculos, start=1):
            add(f"{i}. {_titulo_calculo(calc, i)}")
    else:
        add("_(nenhum cálculo registrado neste projeto)_")
    add("")

    for i, calc in enumerate(record.calculos, start=1):
        add("---")
        add("")
        add(f"## Cálculo {i}")
        add("")
        memorial = calc.get("memorial_markdown")
        if memorial:
            add(memorial)
        else:
            add("_(cálculo sem memorial registrado)_")
        add("")

    add("---")
    add("")
    add(DISCLAIMER)
    return "\n".join(linhas)


def export_project_report_to_pdf(record: ProjectRecord, caminho: str) -> str:
    """Gera o relatório consolidado e o exporta para PDF (reusa o exportador do memorial)."""
    return export_memorial_to_pdf(build_project_report(record), caminho)
