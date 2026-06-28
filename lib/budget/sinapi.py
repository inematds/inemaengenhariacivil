"""Base local de preços de insumos/serviços tipo SINAPI — tabela consultável.

Camada de dados determinística: lê um CSV local (amostra) e devolve preços unitários
para que o agente nunca invente um custo (princípio da abstenção). Um código que não
existe na base levanta ``KeyError`` — o agente deve então abster-se.

ATENÇÃO: os valores do CSV de amostra (``data/sinapi_amostra.csv``) são ILUSTRATIVOS,
apenas para demonstração/teste. Em uso real, substitua pela tabela SINAPI vigente e
regional (desonerada/não desonerada, mês de referência e UF aplicáveis ao projeto).

Colunas esperadas no CSV: ``codigo,descricao,unidade,preco_unitario``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import BaseModel

COLUNAS_OBRIGATORIAS = ("codigo", "descricao", "unidade", "preco_unitario")


class SinapiItem(BaseModel):
    """Item de preço da base: código, descrição, unidade e preço unitário (R$)."""

    codigo: str
    descricao: str
    unidade: str
    preco_unitario: float


def load_sinapi(csv_path: str | Path) -> dict[str, SinapiItem]:
    """Carrega a base de preços de um CSV e indexa por ``codigo`` (string).

    Usa pandas para ler o arquivo. O código é sempre tratado como string (chave
    estável, evita perder zeros à esquerda). Levanta ``FileNotFoundError`` se o
    arquivo não existir, ``ValueError`` se faltar coluna ou se houver código duplicado.
    """
    caminho = Path(csv_path)
    if not caminho.exists():
        raise FileNotFoundError(f"Base de preços não encontrada: {caminho}")

    df = pd.read_csv(caminho, dtype={"codigo": str})
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(
            f"CSV {caminho} sem as colunas obrigatórias: {', '.join(faltando)}."
        )

    base: dict[str, SinapiItem] = {}
    for _, row in df.iterrows():
        codigo = str(row["codigo"]).strip()
        if codigo in base:
            raise ValueError(f"Código duplicado na base de preços: {codigo!r}.")
        base[codigo] = SinapiItem(
            codigo=codigo,
            descricao=str(row["descricao"]).strip(),
            unidade=str(row["unidade"]).strip(),
            preco_unitario=float(row["preco_unitario"]),
        )
    return base


def lookup(codigo: str, base: dict[str, SinapiItem]) -> SinapiItem:
    """Consulta um item por ``codigo`` na ``base`` carregada.

    Levanta ``KeyError`` (com dica) se o código não estiver tabelado — o agente deve
    abster-se em vez de inventar um preço.
    """
    chave = str(codigo).strip()
    if chave not in base:
        raise KeyError(
            f"Código '{codigo}' não consta na base de preços (amostra com "
            f"{len(base)} itens). Verifique a tabela SINAPI vigente/regional."
        )
    return base[chave]
