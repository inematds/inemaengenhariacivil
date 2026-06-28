"""Escoamento em canal aberto (superfície livre) — fórmula de Manning.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Fórmula de Manning (SI):
    Q = (1/n) · A · R^(2/3) · S^(1/2),   R = A/P
com Q em m³/s, A área molhada [m²], P perímetro molhado [m], R raio hidráulico [m],
S declividade de fundo (m/m) e n coeficiente de rugosidade de Manning (s/m^(1/3)).
Fonte: Chow, "Open-Channel Hydraulics" (1959); Azevedo Netto, "Manual de Hidráulica".

Geometrias suportadas:
- Retangular: largura de fundo ``b`` e tirante ``y``.
- Trapezoidal: fundo ``b``, tirante ``y`` e talude ``z`` (z = horizontal/vertical).
- Circular (seção parcialmente cheia): diâmetro ``D`` e tirante ``y``,
  com ângulo θ = 2·arccos(1 − 2y/D), A = (D²/8)(θ − sen θ), P = (D/2)·θ.

O tirante normal (dado Q) é resolvido numericamente por bisseção (scipy.optimize.brentq).
"""

from __future__ import annotations

import math

from pydantic import BaseModel
from scipy.optimize import brentq

GRAVIDADE = 9.81   # m/s²


class OpenChannelResult(BaseModel):
    """Resultado do escoamento uniforme (Manning) em canal aberto.

    ``b_m`` e ``z`` valem para seções retangular/trapezoidal; ``diametro_m`` para a
    circular. Os demais campos são sempre preenchidos.
    """
    geometria: str
    n: float
    S: float
    y_m: float
    area_m2: float
    perimetro_m: float
    raio_hidraulico_m: float
    V_ms: float
    Q_m3s: float
    b_m: float | None = None
    z: float | None = None
    diametro_m: float | None = None


def _check_manning(n: float, S: float) -> None:
    if n <= 0:
        raise ValueError(f"Coeficiente de Manning n={n} deve ser positivo.")
    if S <= 0:
        raise ValueError(f"Declividade S={S} m/m deve ser positiva (escoamento por gravidade).")


def manning_discharge(A_m2: float, P_m: float, n: float, S: float) -> float:
    """Vazão de Manning Q = (1/n)·A·R^(2/3)·S^(1/2) [m³/s], com R = A/P."""
    _check_manning(n, S)
    if A_m2 <= 0 or P_m <= 0:
        raise ValueError(f"Área A={A_m2} e perímetro P={P_m} devem ser positivos.")
    R = A_m2 / P_m
    return (1.0 / n) * A_m2 * R ** (2.0 / 3.0) * math.sqrt(S)


# ----------------------------------------------------- geometrias (A, P) molhadas

def _rect_area_perimeter(b_m: float, y_m: float) -> tuple[float, float]:
    if b_m <= 0:
        raise ValueError(f"Largura de fundo b={b_m} m deve ser positiva.")
    if y_m <= 0:
        raise ValueError(f"Tirante y={y_m} m deve ser positivo.")
    return b_m * y_m, b_m + 2.0 * y_m


def _trap_area_perimeter(b_m: float, y_m: float, z: float) -> tuple[float, float]:
    if b_m <= 0:
        raise ValueError(f"Largura de fundo b={b_m} m deve ser positiva.")
    if y_m <= 0:
        raise ValueError(f"Tirante y={y_m} m deve ser positivo.")
    if z < 0:
        raise ValueError(f"Talude z={z} (H:V) não pode ser negativo.")
    area = (b_m + z * y_m) * y_m
    perim = b_m + 2.0 * y_m * math.sqrt(1.0 + z**2)
    return area, perim


def _circ_area_perimeter(D_m: float, y_m: float) -> tuple[float, float]:
    if D_m <= 0:
        raise ValueError(f"Diâmetro D={D_m} m deve ser positivo.")
    if not (0.0 < y_m <= D_m):
        raise ValueError(f"Tirante y={y_m} m deve estar em (0, D={D_m}].")
    theta = 2.0 * math.acos(1.0 - 2.0 * y_m / D_m)   # ângulo central [rad]
    area = (D_m**2 / 8.0) * (theta - math.sin(theta))
    perim = (D_m / 2.0) * theta
    return area, perim


# ----------------------------------------------------------- vazão dado o tirante

def manning_rectangular(b_m: float, y_m: float, n: float, S: float) -> OpenChannelResult:
    """Vazão em canal retangular pela fórmula de Manning."""
    _check_manning(n, S)
    A, P = _rect_area_perimeter(b_m, y_m)
    Q = manning_discharge(A, P, n, S)
    return OpenChannelResult(
        geometria="retangular", n=n, S=S, y_m=y_m, area_m2=A, perimetro_m=P,
        raio_hidraulico_m=A / P, V_ms=Q / A, Q_m3s=Q, b_m=b_m,
    )


def manning_trapezoidal(b_m: float, y_m: float, z: float, n: float, S: float) -> OpenChannelResult:
    """Vazão em canal trapezoidal pela fórmula de Manning (talude z = H:V)."""
    _check_manning(n, S)
    A, P = _trap_area_perimeter(b_m, y_m, z)
    Q = manning_discharge(A, P, n, S)
    return OpenChannelResult(
        geometria="trapezoidal", n=n, S=S, y_m=y_m, area_m2=A, perimetro_m=P,
        raio_hidraulico_m=A / P, V_ms=Q / A, Q_m3s=Q, b_m=b_m, z=z,
    )


def manning_circular(D_m: float, y_m: float, n: float, S: float) -> OpenChannelResult:
    """Vazão em conduto circular parcialmente cheio pela fórmula de Manning."""
    _check_manning(n, S)
    A, P = _circ_area_perimeter(D_m, y_m)
    Q = manning_discharge(A, P, n, S)
    return OpenChannelResult(
        geometria="circular", n=n, S=S, y_m=y_m, area_m2=A, perimetro_m=P,
        raio_hidraulico_m=A / P, V_ms=Q / A, Q_m3s=Q, diametro_m=D_m,
    )


# --------------------------------------------------------- tirante normal (dado Q)

def normal_depth_rectangular(Q_m3s: float, b_m: float, n: float, S: float) -> float:
    """Tirante normal y [m] num canal retangular para a vazão ``Q_m3s`` (brentq)."""
    _check_manning(n, S)
    if Q_m3s <= 0:
        raise ValueError(f"Vazão Q={Q_m3s} m³/s deve ser positiva.")

    def f(y: float) -> float:
        A, P = _rect_area_perimeter(b_m, y)
        return manning_discharge(A, P, n, S) - Q_m3s

    return brentq(f, 1e-6, 1e3)


def normal_depth_trapezoidal(Q_m3s: float, b_m: float, z: float, n: float, S: float) -> float:
    """Tirante normal y [m] num canal trapezoidal para a vazão ``Q_m3s`` (brentq)."""
    _check_manning(n, S)
    if Q_m3s <= 0:
        raise ValueError(f"Vazão Q={Q_m3s} m³/s deve ser positiva.")

    def f(y: float) -> float:
        A, P = _trap_area_perimeter(b_m, y, z)
        return manning_discharge(A, P, n, S) - Q_m3s

    return brentq(f, 1e-6, 1e3)


def normal_depth_circular(Q_m3s: float, D_m: float, n: float, S: float) -> float:
    """Tirante normal y [m] num conduto circular para a vazão ``Q_m3s`` (brentq).

    A busca fica no intervalo (0, D); se a vazão exceder a do conduto pleno, abstém-se.
    """
    _check_manning(n, S)
    if Q_m3s <= 0:
        raise ValueError(f"Vazão Q={Q_m3s} m³/s deve ser positiva.")

    def f(y: float) -> float:
        A, P = _circ_area_perimeter(D_m, y)
        return manning_discharge(A, P, n, S) - Q_m3s

    if f(D_m * (1.0 - 1e-9)) < 0:
        raise ValueError(
            f"Vazão Q={Q_m3s} m³/s excede a capacidade do conduto circular "
            f"D={D_m} m a plena seção (S={S}, n={n})."
        )
    return brentq(f, 1e-6, D_m * (1.0 - 1e-9))
