"""Exportação do memorial (Markdown) para um PDF simples (reportlab).

Camada de saída determinística: recebe o texto do memorial e o desenha em A4, linha a
linha, com quebra de página automática. Não interpreta Markdown nem recalcula nada — é
um despejo legível do memorial já gerado pela engine.
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

_MARGEM = 2 * cm
_FONTE = "Helvetica"
_TAMANHO = 9
_LEADING = 12
_MAX_CHARS = 110


def _sanitizar(texto: str) -> str:
    """Mantém o PDF robusto: substitui glifos fora do Latin-1 (✓, ≥, ×…) por '?'."""
    return texto.encode("latin-1", "replace").decode("latin-1")


def _quebrar(linha: str, largura: int = _MAX_CHARS) -> list[str]:
    if len(linha) <= largura:
        return [linha]
    pedacos: list[str] = []
    while len(linha) > largura:
        pedacos.append(linha[:largura])
        linha = linha[largura:]
    pedacos.append(linha)
    return pedacos


def export_memorial_to_pdf(memorial_md: str, caminho: str) -> str:
    """Grava ``memorial_md`` num PDF A4 simples e devolve o caminho do arquivo."""
    c = canvas.Canvas(caminho, pagesize=A4)
    _, altura = A4
    y = altura - _MARGEM
    c.setFont(_FONTE, _TAMANHO)

    for linha_bruta in memorial_md.split("\n"):
        for linha in _quebrar(_sanitizar(linha_bruta.rstrip())):
            if y < _MARGEM:
                c.showPage()
                c.setFont(_FONTE, _TAMANHO)
                y = altura - _MARGEM
            c.drawString(_MARGEM, y, linha)
            y -= _LEADING

    c.save()
    return caminho
