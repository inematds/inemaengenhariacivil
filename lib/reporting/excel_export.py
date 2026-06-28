"""Exportação de um pacote de cálculo (bundle do service) para planilha .xlsx.

Camada de saída determinística: recebe o dict devolvido por ``lib.service`` e grava
uma planilha com os campos do resultado e o status da validação. Não recalcula nada.
"""

from __future__ import annotations

from openpyxl import Workbook


def export_bundle_to_xlsx(bundle: dict, caminho: str) -> str:
    """Grava o ``bundle`` (resultado + validação) num arquivo .xlsx e devolve o caminho.

    Uma única planilha "Memorial" com colunas (Campo, Valor): primeiro os campos
    escalares de ``bundle["resultado"]`` (campos compostos são serializados como texto),
    depois o status global e cada verificação de ``bundle["validacao"]``.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Memorial"
    ws.append(["Campo", "Valor"])

    resultado = bundle.get("resultado", {})
    for campo, valor in resultado.items():
        if isinstance(valor, bool) or valor is None or isinstance(valor, (int, float, str)):
            ws.append([campo, valor])
        else:
            ws.append([campo, str(valor)])

    ws.append([])
    ws.append(["aprovado", "APROVADO" if bundle.get("aprovado") else "REPROVADO"])

    validacao = bundle.get("validacao", {})
    for check in validacao.get("checks", []):
        ws.append([f"validacao:{check['name']}", check["status"]])

    wb.save(caminho)
    return caminho
