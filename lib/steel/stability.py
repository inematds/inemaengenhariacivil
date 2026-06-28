"""Barra comprimida — flambagem por flexão (NBR 8800:2008 §5.3).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas
interpreta o problema, chama estas funções via MCP e explica o resultado.

Hipóteses:
- Flambagem global por flexão; ``Q = 1`` (seção compacta, sem flambagem local).
- A barra comprimida flamba no eixo de **menor inércia** -> ``Ne`` usa ``Iy``.
- Coeficiente de ponderação da resistência ``γa1 = 1,1`` (NBR 8800 Tabela 3).

Conversões de unidade (cuidado no contorno):
- ``E`` em kN/cm² = ``E[MPa]·0,1`` (200000 MPa -> 20000 kN/cm²).
- ``fy`` em kN/cm² = ``fy[MPa]·0,1``; assim ``A[cm²]·fy[kN/cm²]`` fica em kN.
- ``I`` em cm⁴, ``KL`` em cm -> ``Ne = π²·E·I/(KL)²`` em kN.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

from lib.steel.profiles import ProfileProperties, get_profile

# --- constantes normativas (NBR 8800:2008) ----------------------------------
GAMMA_A1 = 1.10          # ponderação da resistência ao escoamento (Tabela 3)
LAMBDA0_TRANSITION = 1.5  # fronteira das curvas de χ (§5.3.3)
MPA_TO_KN_CM2 = 0.1      # 1 MPa = 0,1 kN/cm²

# faixa de validade dos aços estruturais comuns (informativa)
FY_MIN_MPA = 250.0
FY_MAX_MPA = 450.0


class CompressionResult(BaseModel):
    """Resultado do dimensionamento de barra comprimida (NBR 8800 §5.3)."""

    # entrada (eco)
    designacao: str
    kl_cm: float
    fy_mpa: float
    e_mpa: float
    q: float
    gamma_a1: float
    area_cm2: float
    i_cm4: float          # inércia usada na flambagem (eixo fraco, Iy)
    # resultados intermediários
    ne_kn: float          # carga de flambagem elástica (Euler)
    lambda_0: float       # índice de esbeltez reduzido
    chi: float            # fator de redução por flambagem
    # capacidade resistente de cálculo
    nc_rd_kn: float       # Nc,Rd
    # metadados
    norma: str = "NBR 8800:2008"
    warnings: list[str] = []


def euler_load(e_mpa: float, i_cm4: float, kl_cm: float) -> float:
    """Carga de flambagem elástica de Euler ``Ne`` (kN).

    ``Ne = π²·E·I/(KL)²``, com ``E`` convertido de MPa para kN/cm².
    """
    if kl_cm <= 0:
        raise ValueError(f"KL={kl_cm} cm deve ser positivo.")
    e_kn_cm2 = e_mpa * MPA_TO_KN_CM2
    return math.pi**2 * e_kn_cm2 * i_cm4 / kl_cm**2


def lambda_0(q: float, area_cm2: float, fy_mpa: float, ne_kn: float) -> float:
    """Índice de esbeltez reduzido ``λ0 = √(Q·A·fy/Ne)`` (adimensional).

    ``A·fy`` é avaliado em kN (``fy`` convertido de MPa para kN/cm²).
    """
    if ne_kn <= 0:
        raise ValueError(f"Ne={ne_kn} kN deve ser positivo.")
    n_pl_kn = q * area_cm2 * (fy_mpa * MPA_TO_KN_CM2)   # Q·A·fy em kN
    return math.sqrt(n_pl_kn / ne_kn)


def chi_factor(lambda_0: float) -> float:
    """Fator de redução por flambagem ``χ`` (NBR 8800:2008 §5.3.3).

    - ``λ0 ≤ 1,5`` -> ``χ = 0,658^(λ0²)``
    - ``λ0 > 1,5`` -> ``χ = 0,877/λ0²``
    """
    if lambda_0 <= LAMBDA0_TRANSITION:
        return 0.658 ** (lambda_0**2)
    return 0.877 / lambda_0**2


def design_compression(
    designacao: str,
    base: dict[str, ProfileProperties],
    kl_cm: float,
    fy_mpa: float = 250.0,
    e_mpa: float = 200000.0,
    q: float = 1.0,
    gamma_a1: float = GAMMA_A1,
) -> CompressionResult:
    """Dimensiona barra comprimida a partir de um perfil da tabela (NBR 8800 §5.3).

    A flambagem por flexão governa no eixo de menor inércia, portanto ``Ne`` é
    calculado com ``Iy`` do perfil. ``Nc,Rd = χ·Q·A·fy/γa1``.

    Abstenção: perfil inexistente propaga ``KeyError`` (de :func:`get_profile`).
    """
    prof = get_profile(designacao, base)
    i_cm4 = prof.iy_cm4                      # eixo fraco governa a flambagem

    ne = euler_load(e_mpa, i_cm4, kl_cm)
    lam = lambda_0(q, prof.area_cm2, fy_mpa, ne)
    chi = chi_factor(lam)

    n_pl_kn = q * prof.area_cm2 * (fy_mpa * MPA_TO_KN_CM2)   # Q·A·fy em kN
    nc_rd = chi * n_pl_kn / gamma_a1

    warnings: list[str] = []
    if lam > 3.0:
        warnings.append(
            f"λ0 = {lam:.2f} > 3,0: barra muito esbelta — rever travamentos ou "
            "aumentar a seção (NBR 8800 §5.3)."
        )

    return CompressionResult(
        designacao=designacao,
        kl_cm=kl_cm,
        fy_mpa=fy_mpa,
        e_mpa=e_mpa,
        q=q,
        gamma_a1=gamma_a1,
        area_cm2=prof.area_cm2,
        i_cm4=i_cm4,
        ne_kn=ne,
        lambda_0=lam,
        chi=chi,
        nc_rd_kn=nc_rd,
        warnings=warnings,
    )
