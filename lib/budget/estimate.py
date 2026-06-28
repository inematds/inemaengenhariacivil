"""Montagem de orçamento — custo por item, subtotal, BDI e total.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
pedido, chama estas funções via MCP e explica o resultado.

Modelo:
- custo do item = quantidade × preço unitário (preço vindo da base tipo SINAPI).
- subtotal = Σ custos dos itens (custo direto).
- valor do BDI = subtotal × (bdi_pct / 100).
- total = subtotal × (1 + bdi_pct / 100) = subtotal + valor do BDI.

O BDI (Benefícios e Despesas Indiretas) é aplicado de forma simplificada como um
percentual único sobre o custo direto. A faixa aceita é [0, 40] % (referência usual de
obras de edificação, Acórdão TCU 2622/2013). A composição detalhada do BDI e o
enquadramento da obra são responsabilidade do engenheiro/orçamentista.
"""

from __future__ import annotations

from pydantic import BaseModel

from lib.budget.sinapi import SinapiItem, lookup

BDI_MIN_PCT = 0.0     # BDI não negativo
BDI_MAX_PCT = 40.0    # teto da faixa aceita pelo método simplificado


class ItemOrcamento(BaseModel):
    """Linha detalhada do orçamento (insumo/serviço orçado)."""

    codigo: str
    descricao: str
    unidade: str
    quantidade: float
    preco_unitario: float
    custo: float


class OrcamentoResult(BaseModel):
    """Resultado completo do orçamento: itens, subtotal, BDI e total."""

    itens: list[ItemOrcamento]
    subtotal: float
    bdi_pct: float
    valor_bdi: float
    total: float
    norma: str = "Custo direto + BDI (referência TCU)"
    warnings: list[str] = []


def _check_bdi(bdi_pct: float) -> None:
    if not (BDI_MIN_PCT <= bdi_pct <= BDI_MAX_PCT):
        raise ValueError(
            f"BDI={bdi_pct}% fora da faixa aceita [{BDI_MIN_PCT:.0f}, {BDI_MAX_PCT:.0f}]%."
        )


def montar_orcamento(
    itens: list[dict],
    base: dict[str, SinapiItem],
    bdi_pct: float = 0.0,
) -> OrcamentoResult:
    """Monta o orçamento a partir de uma lista de itens ``{codigo, quantidade}``.

    Para cada item, consulta o preço na ``base`` (tipo SINAPI), calcula
    custo = quantidade × preço unitário, soma o subtotal e aplica o BDI.

    Abstenção / validação de entrada:
    - código inexistente na base -> ``KeyError`` (propagado de :func:`lookup`);
    - quantidade negativa -> ``ValueError``;
    - BDI fora de [0, 40] % -> ``ValueError``;
    - lista de itens vazia -> ``ValueError``.
    """
    _check_bdi(bdi_pct)
    if not itens:
        raise ValueError("Lista de itens vazia: nada a orçar.")

    detalhados: list[ItemOrcamento] = []
    subtotal = 0.0
    for i, entrada in enumerate(itens):
        if "codigo" not in entrada or "quantidade" not in entrada:
            raise ValueError(
                f"Item {i} inválido: requer chaves 'codigo' e 'quantidade'."
            )
        quantidade = float(entrada["quantidade"])
        if quantidade < 0:
            raise ValueError(
                f"Quantidade negativa no item {i} (codigo={entrada['codigo']!r}): "
                f"{quantidade}."
            )
        ref = lookup(str(entrada["codigo"]), base)
        custo = quantidade * ref.preco_unitario
        subtotal += custo
        detalhados.append(
            ItemOrcamento(
                codigo=ref.codigo,
                descricao=ref.descricao,
                unidade=ref.unidade,
                quantidade=quantidade,
                preco_unitario=ref.preco_unitario,
                custo=custo,
            )
        )

    valor_bdi = subtotal * (bdi_pct / 100.0)
    total = subtotal + valor_bdi

    return OrcamentoResult(
        itens=detalhados,
        subtotal=subtotal,
        bdi_pct=bdi_pct,
        valor_bdi=valor_bdi,
        total=total,
    )
