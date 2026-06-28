"""Ações para o cálculo de estruturas — tabela consultável (NBR 6120:2019).

Camada de dados determinística: pesos específicos de materiais (Tab.2) e cargas
acidentais (variáveis) por uso dos ambientes. NÃO calcula esforços; apenas devolve os
valores normativos para que o agente nunca invente uma carga (princípio da abstenção).

Os valores reproduzem a tabela em ``normas/NBR6120/README.md`` (fonte interna do repo).
"""

from __future__ import annotations

import unicodedata

from pydantic import BaseModel

PESO_CONCRETO_ARMADO = 25.0  # kN/m³ (NBR 6120:2019 Tab.2) — atalho usado por outros módulos

# --- pesos específicos de materiais (kN/m³) — NBR 6120:2019 Tab.2 -------------
PESOS_ESPECIFICOS: dict[str, float] = {
    "concreto armado": 25.0,
    "concreto simples": 24.0,
    "alvenaria de tijolo": 13.0,
    "alvenaria de tijolo macico": 18.0,
    "argamassa de cimento": 21.0,
    "aco": 78.5,
    "madeira (pinus)": 5.5,
    "agua": 10.0,
}

# --- cargas acidentais por uso (kN/m²) — NBR 6120:2019 (uso dos ambientes) ----
CARGAS_ACIDENTAIS: dict[str, float] = {
    "dormitorio": 1.5,
    "sala": 1.5,
    "cozinha": 1.5,
    "banheiro": 1.5,
    "corredor": 3.0,
    "escada": 3.0,
    "garagem": 3.0,
    "escritorio": 2.0,
    "biblioteca": 4.0,
    "loja": 4.0,
}


class LoadValue(BaseModel):
    """Valor tabelado de uma ação, com unidade e norma de referência."""
    categoria: str
    descricao: str
    valor: float
    unidade: str
    norma: str = "NBR 6120:2019"


def _normalize(chave: str) -> str:
    """Minúsculas + remoção de acentos para casar chaves de forma robusta."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", chave) if not unicodedata.combining(c)
    )
    return sem_acento.strip().lower()


def peso_especifico_material(nome: str) -> LoadValue:
    """Peso específico (kN/m³) de um material da NBR 6120:2019 Tab.2.

    Levanta ``KeyError`` (com a lista de opções) se o material não estiver tabelado —
    o agente deve então abster-se em vez de inventar um valor.
    """
    chave = _normalize(nome)
    if chave not in PESOS_ESPECIFICOS:
        raise KeyError(
            f"Material '{nome}' não consta na NBR 6120:2019 Tab.2. "
            f"Disponíveis: {', '.join(listar_materiais())}."
        )
    return LoadValue(
        categoria="peso_especifico", descricao=nome,
        valor=PESOS_ESPECIFICOS[chave], unidade="kN/m³",
    )


def carga_acidental_uso(uso: str) -> LoadValue:
    """Carga acidental (variável) de piso, em kN/m², por uso do ambiente (NBR 6120:2019).

    Levanta ``KeyError`` se o uso não estiver tabelado (princípio da abstenção).
    """
    chave = _normalize(uso)
    if chave not in CARGAS_ACIDENTAIS:
        raise KeyError(
            f"Uso '{uso}' não consta na NBR 6120:2019. "
            f"Disponíveis: {', '.join(listar_usos())}."
        )
    return LoadValue(
        categoria="carga_acidental", descricao=uso,
        valor=CARGAS_ACIDENTAIS[chave], unidade="kN/m²",
    )


def peso_proprio_laje_macica(h_cm: float, peso_concreto: float = PESO_CONCRETO_ARMADO) -> float:
    """Peso próprio (kN/m²) de uma laje maciça de espessura ``h_cm`` (g = γ·h)."""
    if h_cm <= 0:
        raise ValueError("Espessura da laje deve ser positiva.")
    return peso_concreto * (h_cm / 100.0)


def listar_materiais() -> list[str]:
    """Nomes (sem acento, minúsculos) dos materiais tabelados."""
    return sorted(PESOS_ESPECIFICOS)


def listar_usos() -> list[str]:
    """Nomes (sem acento, minúsculos) dos usos tabelados."""
    return sorted(CARGAS_ACIDENTAIS)
