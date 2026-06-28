"""Empuxo de terra sobre estruturas de contenção — Rankine e Coulomb.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Métodos e hipóteses
-------------------
Rankine (1857) — tardoz vertical liso, terrapleno horizontal, solo não coesivo:
    Ka = tan²(45 − φ/2)        Kp = tan²(45 + φ/2)
    E  = 0,5·γ·H²·K            (empuxo por metro de muro, kN/m)
    Ponto de aplicação a H/3 da base (distribuição triangular).

Coulomb (1776) — atrito solo-muro δ, inclinação do tardoz β (da vertical) e do
terrapleno α (da horizontal). Coeficiente ativo:

    Ka = cos²(φ−β) / [ cos²β · cos(δ+β) ·
         (1 + √( sin(φ+δ)·sin(φ−α) / (cos(δ+β)·cos(β−α)) ))² ]

Coeficiente passivo:

    Kp = cos²(φ+β) / [ cos²β · cos(δ−β) ·
         (1 − √( sin(φ+δ)·sin(φ+α) / (cos(δ−β)·cos(β−α)) ))² ]

Cross-check: com δ=β=α=0, Coulomb reduz a Rankine (Ka=cos²φ/(1+sinφ)²).
Âncora φ=30°: Ka=1/3, Kp=3.

Abstenção: entradas fora de faixa física (φ∉[0,50]°, γ∉[10,25] kN/m³, H≤0, δ∉[0,φ],
α≥φ) levantam ``ValueError``. Empuxo de água, sobrecargas e coesão são tratados à
parte pelo engenheiro.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- faixas físicas ----------------------------------------------------------
PHI_MIN, PHI_MAX = 0.0, 50.0
GAMMA_MIN, GAMMA_MAX = 10.0, 25.0


class RankineEarthPressureResult(BaseModel):
    """Empuxo de Rankine (ativo e passivo) por metro de muro."""

    # entrada (eco)
    gamma_kn_m3: float
    h_m: float
    phi_deg: float
    # coeficientes
    ka: float
    kp: float
    # empuxos (kN/m)
    ea_active_kn_m: float
    ep_passive_kn_m: float
    # ponto de aplicação (m da base)
    point_of_application_m: float
    # metadados
    metodo: str = "Rankine"
    norma: str = "NBR 11682 / Teoria de Rankine"
    warnings: list[str] = []


class CoulombEarthPressureResult(BaseModel):
    """Empuxo de Coulomb (ativo e passivo) por metro de muro."""

    # entrada (eco)
    gamma_kn_m3: float
    h_m: float
    phi_deg: float
    delta_deg: float
    beta_deg: float
    alpha_deg: float
    # coeficientes
    ka: float
    kp: float
    # empuxos (kN/m)
    ea_active_kn_m: float
    ep_passive_kn_m: float
    # ponto de aplicação (m da base)
    point_of_application_m: float
    # metadados
    metodo: str = "Coulomb"
    norma: str = "NBR 11682 / Teoria de Coulomb"
    warnings: list[str] = []


def _check_common(gamma_kn_m3: float, h_m: float, phi_deg: float) -> None:
    if not (PHI_MIN <= phi_deg <= PHI_MAX):
        raise ValueError(f"φ={phi_deg}° fora da faixa física [{PHI_MIN}, {PHI_MAX}].")
    if not (GAMMA_MIN <= gamma_kn_m3 <= GAMMA_MAX):
        raise ValueError(f"γ={gamma_kn_m3} kN/m³ fora da faixa física "
                         f"[{GAMMA_MIN}, {GAMMA_MAX}].")
    if h_m <= 0.0:
        raise ValueError(f"H={h_m} m deve ser positivo.")


def rankine_earth_pressure(
    gamma_kn_m3: float,
    h_m: float,
    phi_deg: float,
) -> RankineEarthPressureResult:
    """Empuxo de Rankine: Ka=tan²(45−φ/2), Kp=tan²(45+φ/2), E=0,5·γ·H²·K.

    Entradas fora de faixa física levantam ``ValueError`` (abstenção).
    """
    _check_common(gamma_kn_m3, h_m, phi_deg)
    phi = math.radians(phi_deg)
    ka = math.tan(math.pi / 4.0 - phi / 2.0) ** 2
    kp = math.tan(math.pi / 4.0 + phi / 2.0) ** 2
    ea = 0.5 * gamma_kn_m3 * h_m**2 * ka
    ep = 0.5 * gamma_kn_m3 * h_m**2 * kp
    return RankineEarthPressureResult(
        gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg,
        ka=ka, kp=kp, ea_active_kn_m=ea, ep_passive_kn_m=ep,
        point_of_application_m=h_m / 3.0,
        warnings=[],
    )


def coulomb_earth_pressure(
    gamma_kn_m3: float,
    h_m: float,
    phi_deg: float,
    delta_deg: float = 0.0,
    beta_deg: float = 0.0,
    alpha_deg: float = 0.0,
) -> CoulombEarthPressureResult:
    """Empuxo de Coulomb com atrito do muro δ, tardoz β e terrapleno α.

    Convenção: β = inclinação do tardoz em relação à vertical; α = inclinação do
    terrapleno em relação à horizontal; δ = ângulo de atrito solo-muro.
    Entradas fora de faixa física levantam ``ValueError`` (abstenção).
    """
    _check_common(gamma_kn_m3, h_m, phi_deg)
    if not (0.0 <= delta_deg <= phi_deg):
        raise ValueError(f"δ={delta_deg}° deve estar em [0, φ={phi_deg}].")
    if alpha_deg >= phi_deg:
        raise ValueError(f"α={alpha_deg}° ≥ φ={phi_deg}° torna o talude instável "
                         "para a teoria de Coulomb (raiz negativa).")

    phi = math.radians(phi_deg)
    delta = math.radians(delta_deg)
    beta = math.radians(beta_deg)
    alpha = math.radians(alpha_deg)

    # --- coeficiente ativo ---------------------------------------------------
    num_a = math.cos(phi - beta) ** 2
    root_a = math.sqrt(
        (math.sin(phi + delta) * math.sin(phi - alpha))
        / (math.cos(delta + beta) * math.cos(beta - alpha))
    )
    den_a = (math.cos(beta) ** 2 * math.cos(delta + beta) * (1.0 + root_a) ** 2)
    ka = num_a / den_a

    # --- coeficiente passivo -------------------------------------------------
    num_p = math.cos(phi + beta) ** 2
    root_p = math.sqrt(
        (math.sin(phi + delta) * math.sin(phi + alpha))
        / (math.cos(delta - beta) * math.cos(beta - alpha))
    )
    den_p = (math.cos(beta) ** 2 * math.cos(delta - beta) * (1.0 - root_p) ** 2)
    kp = num_p / den_p

    ea = 0.5 * gamma_kn_m3 * h_m**2 * ka
    ep = 0.5 * gamma_kn_m3 * h_m**2 * kp
    return CoulombEarthPressureResult(
        gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg,
        delta_deg=delta_deg, beta_deg=beta_deg, alpha_deg=alpha_deg,
        ka=ka, kp=kp, ea_active_kn_m=ea, ep_passive_kn_m=ep,
        point_of_application_m=h_m / 3.0,
        warnings=[],
    )
