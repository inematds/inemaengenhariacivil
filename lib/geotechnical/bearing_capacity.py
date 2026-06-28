"""Capacidade de carga de fundação rasa — método de Vesic (NBR 6122).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Método e hipóteses
-------------------
Equação geral de capacidade de carga (Terzaghi/Vesic):

    q_ult = c·Nc·sc + q·Nq·sq + 0,5·γ·B·Nγ·sγ

com a sobrecarga efetiva no nível da base ``q = γ·Df`` (Df = profundidade de
assentamento). A tensão admissível é ``q_adm = q_ult / FS`` (FS = 3 por padrão,
faixa usual da NBR 6122 para fundações superficiais).

Fatores de capacidade de carga — forma fechada de Vesic (1973):
    Nq = e^(π·tanφ)·tan²(45+φ/2)
    Nc = (Nq−1)·cotφ            (φ=0 → Nc = π+2 ≈ 5,14, valor de Prandtl)
    Nγ = 2·(Nq+1)·tanφ

Âncora φ=30°: Nq≈18,40 ; Nc≈30,14 ; Nγ≈22,40.

Fatores de forma de Vesic (função da razão B/L):
    sc = 1 + (Nq/Nc)·(B/L)
    sq = 1 + (B/L)·tanφ
    sγ = 1 − 0,4·(B/L)
Por forma de sapata:
    - corrida   : B/L = 0 → sc = sq = sγ = 1
    - quadrada  : B/L = 1 → sc = 1+Nq/Nc ; sq = 1+tanφ ; sγ = 0,6
    - circular  : B/L = 1 (B = diâmetro), idem quadrada
    - retangular: B/L = b/l (0 < b ≤ l), informado pelo usuário

Abstenção: entradas fora de faixa física (φ∉[0,50]°, γ∉[10,25] kN/m³, c<0, B≤0,
Df<0, FS<1, forma não tabelada) levantam ``ValueError``. O fator de segurança e a
verificação de recalques (ELS) são de responsabilidade do engenheiro.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- constantes --------------------------------------------------------------
NC_PHI_ZERO = math.pi + 2.0   # Nc para φ=0 (Prandtl) ≈ 5,14
FS_DEFAULT = 3.0              # fator de segurança global usual (NBR 6122)
PHI_MIN, PHI_MAX = 0.0, 50.0          # faixa física do ângulo de atrito (°)
GAMMA_MIN, GAMMA_MAX = 10.0, 25.0     # faixa física do peso específico (kN/m³)
FORMAS = ("corrida", "quadrada", "retangular", "circular")


class BearingCapacityResult(BaseModel):
    """Resultado da capacidade de carga de uma fundação rasa (método de Vesic)."""

    # entrada (eco)
    c_kpa: float
    phi_deg: float
    gamma_kn_m3: float
    b_m: float
    l_m: float | None
    depth_df_m: float
    shape: str
    fs: float
    # sobrecarga
    q_surcharge_kpa: float
    # fatores de capacidade de carga
    nc: float
    nq: float
    ngamma: float
    # fatores de forma
    sc: float
    sq: float
    sgamma: float
    # parcelas (kPa) — transparência e verificação dimensional
    term_cohesion_kpa: float
    term_surcharge_kpa: float
    term_weight_kpa: float
    # resultados
    q_ult_kpa: float
    q_adm_kpa: float
    # metadados
    metodo: str = "Vesic (forma fechada)"
    norma: str = "NBR 6122"
    warnings: list[str] = []


def vesic_bearing_factors(phi_deg: float) -> tuple[float, float, float]:
    """Fatores de capacidade de carga (Nc, Nq, Nγ) de Vesic para ``phi_deg`` graus.

    Devolve a tupla ``(Nc, Nq, Nγ)``. Para φ=0 usa Nc=π+2 (≈5,14), Nq=1, Nγ=0.
    """
    if not (PHI_MIN <= phi_deg <= PHI_MAX):
        raise ValueError(f"φ={phi_deg}° fora da faixa física [{PHI_MIN}, {PHI_MAX}].")
    phi = math.radians(phi_deg)
    nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4.0 + phi / 2.0) ** 2
    if phi_deg == 0.0:
        nc = NC_PHI_ZERO
        ng = 0.0
    else:
        nc = (nq - 1.0) / math.tan(phi)
        ng = 2.0 * (nq + 1.0) * math.tan(phi)
    return nc, nq, ng


def _shape_factors(shape: str, b_over_l: float, nc: float, nq: float,
                   phi_deg: float) -> tuple[float, float, float]:
    """Fatores de forma de Vesic ``(sc, sq, sγ)`` a partir da razão B/L."""
    phi = math.radians(phi_deg)
    sc = 1.0 + (nq / nc) * b_over_l
    sq = 1.0 + b_over_l * math.tan(phi)
    sgamma = 1.0 - 0.4 * b_over_l
    return sc, sq, sgamma


def _b_over_l(shape: str, b_m: float, l_m: float | None) -> tuple[float, float | None]:
    """Razão B/L e comprimento efetivo conforme a forma da sapata."""
    if shape == "corrida":
        return 0.0, None
    if shape in ("quadrada", "circular"):
        return 1.0, b_m
    # retangular
    if l_m is None or l_m <= 0.0:
        raise ValueError("Sapata retangular exige comprimento l_m > 0.")
    if l_m < b_m:
        raise ValueError(f"Para sapata retangular use B ≤ L (B={b_m}, L={l_m}).")
    return b_m / l_m, l_m


def design_bearing_capacity(
    c_kpa: float,
    phi_deg: float,
    gamma_kn_m3: float,
    b_m: float,
    depth_df_m: float,
    shape: str = "quadrada",
    l_m: float | None = None,
    fs: float = FS_DEFAULT,
) -> BearingCapacityResult:
    """Capacidade de carga de fundação rasa pelo método de Vesic.

    Parâmetros
    ----------
    c_kpa: coesão do solo (kPa).
    phi_deg: ângulo de atrito interno (graus).
    gamma_kn_m3: peso específico do solo (kN/m³).
    b_m: menor dimensão da base (largura) ou diâmetro, em metros.
    depth_df_m: profundidade de assentamento Df (m) → sobrecarga q = γ·Df.
    shape: "corrida" | "quadrada" | "retangular" | "circular".
    l_m: comprimento da base (m), obrigatório para "retangular".
    fs: fator de segurança global (≥1), default 3.

    Entradas fora de faixa física levantam ``ValueError`` (abstenção).
    """
    if c_kpa < 0.0:
        raise ValueError(f"c={c_kpa} kPa deve ser ≥ 0.")
    if not (PHI_MIN <= phi_deg <= PHI_MAX):
        raise ValueError(f"φ={phi_deg}° fora da faixa física [{PHI_MIN}, {PHI_MAX}].")
    if not (GAMMA_MIN <= gamma_kn_m3 <= GAMMA_MAX):
        raise ValueError(f"γ={gamma_kn_m3} kN/m³ fora da faixa física "
                         f"[{GAMMA_MIN}, {GAMMA_MAX}].")
    if b_m <= 0.0:
        raise ValueError(f"B={b_m} m deve ser positivo.")
    if depth_df_m < 0.0:
        raise ValueError(f"Df={depth_df_m} m deve ser ≥ 0.")
    if fs < 1.0:
        raise ValueError(f"FS={fs} deve ser ≥ 1.")
    if shape not in FORMAS:
        raise ValueError(f"Forma '{shape}' não tabelada; use uma de {FORMAS}.")

    b_over_l, l_eff = _b_over_l(shape, b_m, l_m)
    nc, nq, ng = vesic_bearing_factors(phi_deg)
    sc, sq, sgamma = _shape_factors(shape, b_over_l, nc, nq, phi_deg)

    q_surcharge = gamma_kn_m3 * depth_df_m                     # kPa

    term_c = c_kpa * nc * sc                                   # kPa
    term_q = q_surcharge * nq * sq                             # kPa
    term_g = 0.5 * gamma_kn_m3 * b_m * ng * sgamma             # kPa
    q_ult = term_c + term_q + term_g
    q_adm = q_ult / fs

    return BearingCapacityResult(
        c_kpa=c_kpa, phi_deg=phi_deg, gamma_kn_m3=gamma_kn_m3,
        b_m=b_m, l_m=l_eff, depth_df_m=depth_df_m, shape=shape, fs=fs,
        q_surcharge_kpa=q_surcharge,
        nc=nc, nq=nq, ngamma=ng,
        sc=sc, sq=sq, sgamma=sgamma,
        term_cohesion_kpa=term_c, term_surcharge_kpa=term_q, term_weight_kpa=term_g,
        q_ult_kpa=q_ult, q_adm_kpa=q_adm,
        warnings=[],
    )
