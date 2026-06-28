"""Escoamento em conduto forçado (tubulações sob pressão).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Métodos:
- **Hazen-Williams** (empírico, água a temperatura ambiente), forma SI:
  hf = 10,67 · Q^1,852 · L / (C^1,852 · D^4,87)
  com Q em m³/s, D em m, L em m, hf em m e C o coeficiente de rugosidade (adimensional).
  Fonte: Azevedo Netto, "Manual de Hidráulica", 8ª ed. (forma SI usual).
- **Darcy-Weisbach** (racional, válido para qualquer fluido/regime):
  hf = f · (L/D) · V²/(2g)
  com o fator de atrito f obtido pela aproximação explícita de **Swamee-Jain (1976)**
  para o diagrama de Moody:
  f = 0,25 / [log10(ε/(3,7·D) + 5,74/Re^0,9)]²   (válida p/ 5e3 ≤ Re ≤ 1e8,
  1e-6 ≤ ε/D ≤ 1e-2), com Re = V·D/ν.

Hipóteses:
- Água a ~20 °C: viscosidade cinemática ν ≈ 1,0e-6 m²/s.
- Aceleração da gravidade g = 9,81 m/s².
- Seção circular plena; V = Q/A, A = π·D²/4.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- constantes físicas -------------------------------------------------------
GRAVIDADE = 9.81          # m/s²
NU_AGUA_20C = 1.0e-6      # viscosidade cinemática da água a ~20 °C (m²/s)


class PipeFlowResult(BaseModel):
    """Resultado do escoamento em conduto forçado.

    ``reynolds`` e ``f`` só são preenchidos no método de Darcy-Weisbach; ``coef_C``
    só no de Hazen-Williams.
    """
    metodo: str
    Q_m3s: float
    V_ms: float
    D_m: float
    L_m: float
    hf_m: float
    coef_C: float | None = None
    eps_m: float | None = None
    nu_m2s: float | None = None
    reynolds: float | None = None
    f: float | None = None


def _check_geometry(D_m: float, L_m: float) -> None:
    if D_m <= 0:
        raise ValueError(f"Diâmetro D={D_m} m deve ser positivo.")
    if L_m < 0:
        raise ValueError(f"Comprimento L={L_m} m não pode ser negativo.")


def pipe_area(D_m: float) -> float:
    """Área da seção circular plena: A = π·D²/4 [m²]."""
    if D_m <= 0:
        raise ValueError(f"Diâmetro D={D_m} m deve ser positivo.")
    return math.pi * D_m**2 / 4.0


def velocity_from_flow(Q_m3s: float, D_m: float) -> float:
    """Velocidade média V = Q/A [m/s]."""
    return Q_m3s / pipe_area(D_m)


def flow_from_velocity(V_ms: float, D_m: float) -> float:
    """Vazão Q = V·A [m³/s]."""
    return V_ms * pipe_area(D_m)


# ------------------------------------------------------------------ Hazen-Williams

def hazen_williams_headloss(Q_m3s: float, D_m: float, L_m: float, C: float) -> float:
    """Perda de carga distribuída por Hazen-Williams (SI) [m].

    hf = 10,67 · Q^1,852 · L / (C^1,852 · D^4,87).
    """
    _check_geometry(D_m, L_m)
    if C <= 0:
        raise ValueError(f"Coeficiente C={C} de Hazen-Williams deve ser positivo.")
    if Q_m3s < 0:
        raise ValueError(f"Vazão Q={Q_m3s} m³/s não pode ser negativa.")
    return 10.67 * Q_m3s**1.852 * L_m / (C**1.852 * D_m**4.87)


def pipe_flow_hazen_williams(Q_m3s: float, D_m: float, L_m: float, C: float) -> PipeFlowResult:
    """Escoamento forçado por Hazen-Williams: monta o resultado completo."""
    hf = hazen_williams_headloss(Q_m3s, D_m, L_m, C)
    v = velocity_from_flow(Q_m3s, D_m)
    return PipeFlowResult(
        metodo="Hazen-Williams (SI)",
        Q_m3s=Q_m3s, V_ms=v, D_m=D_m, L_m=L_m, hf_m=hf, coef_C=C,
    )


# ----------------------------------------------------------- Darcy-Weisbach / S-J

def reynolds(V_ms: float, D_m: float, nu_m2s: float = NU_AGUA_20C) -> float:
    """Número de Reynolds Re = V·D/ν (adimensional)."""
    if nu_m2s <= 0:
        raise ValueError(f"Viscosidade cinemática ν={nu_m2s} m²/s deve ser positiva.")
    if D_m <= 0:
        raise ValueError(f"Diâmetro D={D_m} m deve ser positivo.")
    return V_ms * D_m / nu_m2s


def swamee_jain_friction(Re: float, eps_m: float, D_m: float) -> float:
    """Fator de atrito de Darcy por Swamee-Jain (1976) [adimensional].

    f = 0,25 / [log10(ε/(3,7·D) + 5,74/Re^0,9)]².
    Válida no regime turbulento (5e3 ≤ Re ≤ 1e8); fora dela a aproximação degrada.
    """
    if D_m <= 0:
        raise ValueError(f"Diâmetro D={D_m} m deve ser positivo.")
    if eps_m < 0:
        raise ValueError(f"Rugosidade ε={eps_m} m não pode ser negativa.")
    if Re <= 0:
        raise ValueError(f"Reynolds Re={Re} deve ser positivo.")
    termo = math.log10(eps_m / (3.7 * D_m) + 5.74 / Re**0.9)
    return 0.25 / termo**2


def darcy_weisbach_headloss(V_ms: float, D_m: float, L_m: float, f: float) -> float:
    """Perda de carga distribuída por Darcy-Weisbach [m].

    hf = f · (L/D) · V²/(2g).
    """
    _check_geometry(D_m, L_m)
    if f <= 0:
        raise ValueError(f"Fator de atrito f={f} deve ser positivo.")
    return f * (L_m / D_m) * V_ms**2 / (2.0 * GRAVIDADE)


def pipe_flow_darcy_weisbach(
    Q_m3s: float, D_m: float, L_m: float, eps_m: float, nu_m2s: float = NU_AGUA_20C
) -> PipeFlowResult:
    """Escoamento forçado por Darcy-Weisbach com f de Swamee-Jain: resultado completo."""
    v = velocity_from_flow(Q_m3s, D_m)
    re = reynolds(v, D_m, nu_m2s)
    f = swamee_jain_friction(re, eps_m, D_m)
    hf = darcy_weisbach_headloss(v, D_m, L_m, f)
    return PipeFlowResult(
        metodo="Darcy-Weisbach (Swamee-Jain)",
        Q_m3s=Q_m3s, V_ms=v, D_m=D_m, L_m=L_m, hf_m=hf,
        eps_m=eps_m, nu_m2s=nu_m2s, reynolds=re, f=f,
    )
