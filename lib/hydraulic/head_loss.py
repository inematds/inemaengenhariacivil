"""Perdas de carga localizadas (singularidades) — método dos coeficientes K.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Perda localizada de cada peça:
    h_loc = K · V²/(2g)
e a perda total de um trecho é a soma da perda distribuída (de ``pipe_flow``) com as
localizadas:
    hf_total = hf_distribuída + Σ K_i · V²/(2g).

Coeficientes K (adimensionais) — valores usuais de projeto (Azevedo Netto,
"Manual de Hidráulica", 8ª ed.; tabela de perdas localizadas). São valores médios
de referência; o projetista pode substituí-los conforme o fabricante da peça.
g = 9,81 m/s².
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel

GRAVIDADE = 9.81   # m/s²

# --- coeficientes de perda localizada K (adimensional) ------------------------
K_SINGULARIDADES: dict[str, float] = {
    "entrada": 0.5,                  # entrada normal/borda viva de reservatório
    "entrada_reentrante": 1.0,       # entrada de borda reentrante (Borda)
    "saida": 1.0,                    # saída de canalização para reservatório
    "curva_90": 0.9,                 # cotovelo/curva de 90°
    "curva_45": 0.4,                 # curva de 45°
    "curva_22": 0.2,                 # curva de 22,5°
    "te_passagem_direta": 0.6,       # tê — fluxo em linha (passagem direta)
    "te_saida_lateral": 1.3,         # tê — saída de lado (derivação)
    "te_saida_bilateral": 1.8,       # tê — saída bilateral
    "juncao": 0.4,                   # junção
    "ampliacao_gradual": 0.3,        # ampliação gradual (difusor)
    "reducao_gradual": 0.15,         # redução gradual
    "registro_gaveta_aberto": 0.2,   # registro de gaveta totalmente aberto
    "registro_globo_aberto": 10.0,   # registro de globo totalmente aberto
    "registro_angulo_aberto": 5.0,   # registro de ângulo totalmente aberto
    "valvula_pe_crivo": 2.5,         # válvula de pé com crivo
    "valvula_retencao": 2.5,         # válvula de retenção
    "medidor_venturi": 2.5,          # medidor Venturi
}


class HeadLossItem(BaseModel):
    """Perda localizada de uma singularidade (já multiplicada pela quantidade)."""
    tipo: str
    K: float
    quantidade: int
    h_m: float


class HeadLossResult(BaseModel):
    """Resultado da composição de perdas distribuída + localizadas de um trecho."""
    metodo: str
    V_ms: float
    g: float
    hf_distribuida_m: float
    hf_localizada_m: float
    hf_total_m: float
    itens: list[HeadLossItem]


def local_loss(K: float, V_ms: float, g: float = GRAVIDADE) -> float:
    """Perda de carga localizada de uma singularidade: h = K·V²/(2g) [m]."""
    if K < 0:
        raise ValueError(f"Coeficiente K={K} não pode ser negativo.")
    if g <= 0:
        raise ValueError(f"Gravidade g={g} m/s² deve ser positiva.")
    return K * V_ms**2 / (2.0 * g)


def singularity_K(tipo: str) -> float:
    """Coeficiente K da singularidade ``tipo`` (abstém-se se não estiver na tabela)."""
    try:
        return K_SINGULARIDADES[tipo]
    except KeyError:
        disponiveis = ", ".join(sorted(K_SINGULARIDADES))
        raise ValueError(
            f"Singularidade '{tipo}' não está na tabela de coeficientes K. "
            f"Tipos disponíveis: {disponiveis}."
        ) from None


def total_head_loss(
    hf_distribuida_m: float,
    singularidades: Mapping[str, int],
    V_ms: float,
    g: float = GRAVIDADE,
) -> HeadLossResult:
    """Perda total = distribuída + Σ localizadas, dado o mapa {tipo: quantidade}.

    ``singularidades`` mapeia cada tipo (chave de :data:`K_SINGULARIDADES`) à sua
    quantidade. Tipo fora da tabela levanta ``ValueError`` (princípio da abstenção).
    """
    if hf_distribuida_m < 0:
        raise ValueError(f"Perda distribuída hf={hf_distribuida_m} m não pode ser negativa.")

    itens: list[HeadLossItem] = []
    hf_loc = 0.0
    for tipo, qtd in singularidades.items():
        if qtd < 0:
            raise ValueError(f"Quantidade da singularidade '{tipo}' não pode ser negativa.")
        K = singularity_K(tipo)
        h = qtd * local_loss(K, V_ms, g)
        hf_loc += h
        itens.append(HeadLossItem(tipo=tipo, K=K, quantidade=qtd, h_m=h))

    return HeadLossResult(
        metodo="Coeficientes K (perdas localizadas)",
        V_ms=V_ms, g=g,
        hf_distribuida_m=hf_distribuida_m,
        hf_localizada_m=hf_loc,
        hf_total_m=hf_distribuida_m + hf_loc,
        itens=itens,
    )
