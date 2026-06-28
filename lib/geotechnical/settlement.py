"""Recalques de fundação — elástico imediato e adensamento primário.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Métodos e hipóteses
-------------------
(a) Recalque elástico imediato (teoria da elasticidade, Boussinesq/Timoshenko):

        s = q·B·(1−ν²)·Iw / Es

    q = pressão aplicada (kPa); B = largura (m); ν = coeficiente de Poisson;
    Iw = fator de influência (forma/rigidez da fundação); Es = módulo de
    elasticidade do solo (kPa). Resultado em metros.

(b) Recalque por adensamento primário (Terzaghi, argila normalmente adensada):

        s = Cc/(1+e0)·H·log10((σ0+Δσ)/σ0)

    Cc = índice de compressão; e0 = índice de vazios inicial; H = espessura da
    camada compressível (m); σ0 = tensão efetiva inicial (kPa); Δσ = acréscimo
    de tensão (kPa). Resultado em metros.

Abstenção: entradas fora de faixa física (ν∉[0,0.5], e0∉[0,3], Es≤0, q≤0, σ0≤0,
Cc≤0, H≤0, B≤0, Δσ<0) levantam ``ValueError``. A hipótese de argila normalmente
adensada (sem trecho de recompressão Cs) é do engenheiro.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- faixas físicas ----------------------------------------------------------
NU_MIN, NU_MAX = 0.0, 0.5     # coeficiente de Poisson
E0_MIN, E0_MAX = 0.0, 3.0     # índice de vazios inicial


class ElasticSettlementResult(BaseModel):
    """Recalque elástico imediato de fundação."""

    # entrada (eco)
    q_kpa: float
    b_m: float
    poisson_nu: float
    iw: float
    es_kpa: float
    # resultado
    settlement_m: float
    settlement_mm: float
    # metadados
    metodo: str = "Recalque elástico (teoria da elasticidade)"
    norma: str = "NBR 6122 (ELS)"
    warnings: list[str] = []


class ConsolidationSettlementResult(BaseModel):
    """Recalque por adensamento primário (Terzaghi)."""

    # entrada (eco)
    cc: float
    e0: float
    h_m: float
    sigma0_kpa: float
    delta_sigma_kpa: float
    # resultado
    settlement_m: float
    settlement_mm: float
    # metadados
    metodo: str = "Adensamento primário (Terzaghi, NA)"
    norma: str = "NBR 6122 (ELS)"
    warnings: list[str] = []


def elastic_settlement(
    q_kpa: float,
    b_m: float,
    poisson_nu: float,
    iw: float,
    es_kpa: float,
) -> ElasticSettlementResult:
    """Recalque elástico imediato ``s = q·B·(1−ν²)·Iw / Es`` (metros).

    Entradas fora de faixa física levantam ``ValueError`` (abstenção).
    """
    if q_kpa <= 0.0:
        raise ValueError(f"q={q_kpa} kPa deve ser positivo.")
    if b_m <= 0.0:
        raise ValueError(f"B={b_m} m deve ser positivo.")
    if not (NU_MIN <= poisson_nu <= NU_MAX):
        raise ValueError(f"ν={poisson_nu} fora da faixa física [{NU_MIN}, {NU_MAX}].")
    if iw <= 0.0:
        raise ValueError(f"Iw={iw} deve ser positivo.")
    if es_kpa <= 0.0:
        raise ValueError(f"Es={es_kpa} kPa deve ser positivo.")

    s_m = q_kpa * b_m * (1.0 - poisson_nu**2) * iw / es_kpa
    return ElasticSettlementResult(
        q_kpa=q_kpa, b_m=b_m, poisson_nu=poisson_nu, iw=iw, es_kpa=es_kpa,
        settlement_m=s_m, settlement_mm=s_m * 1000.0,
        warnings=[],
    )


def consolidation_settlement(
    cc: float,
    e0: float,
    h_m: float,
    sigma0_kpa: float,
    delta_sigma_kpa: float,
) -> ConsolidationSettlementResult:
    """Recalque por adensamento primário ``s = Cc/(1+e0)·H·log10((σ0+Δσ)/σ0)`` (m).

    Hipótese: argila normalmente adensada (σ0 ≥ σ'pré-adensamento). Entradas fora de
    faixa física levantam ``ValueError`` (abstenção).
    """
    if cc <= 0.0:
        raise ValueError(f"Cc={cc} deve ser positivo.")
    if not (E0_MIN <= e0 <= E0_MAX):
        raise ValueError(f"e0={e0} fora da faixa física [{E0_MIN}, {E0_MAX}].")
    if h_m <= 0.0:
        raise ValueError(f"H={h_m} m deve ser positivo.")
    if sigma0_kpa <= 0.0:
        raise ValueError(f"σ0={sigma0_kpa} kPa deve ser positivo.")
    if delta_sigma_kpa < 0.0:
        raise ValueError(f"Δσ={delta_sigma_kpa} kPa deve ser ≥ 0.")

    s_m = (cc / (1.0 + e0)) * h_m * math.log10((sigma0_kpa + delta_sigma_kpa) / sigma0_kpa)
    return ConsolidationSettlementResult(
        cc=cc, e0=e0, h_m=h_m, sigma0_kpa=sigma0_kpa, delta_sigma_kpa=delta_sigma_kpa,
        settlement_m=s_m, settlement_mm=s_m * 1000.0,
        warnings=[],
    )
