"""Estabilidade de taludes — talude infinito e método de Fellenius.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado. O disclaimer de
responsabilidade técnica é adicionado na camada de integração, não aqui.

Métodos e hipóteses
-------------------
Talude infinito (Das, "Fundamentos de Engenharia Geotécnica") — superfície de
ruptura plana e paralela à face, profundidade ``z`` muito menor que a extensão do
talude (efeitos de borda desprezados). Para solo c-φ, com poro-pressão ``u`` na
base da fatia:

    FS = [ c + (γ·z·cos²β − u)·tanφ ] / (γ·z·sinβ·cosβ)

Casos-limite:
  - solo friccional puro (c=0) e sem percolação (u=0): FS = tanφ/tanβ;
  - percolação paralela ao talude com lençol na superfície: u = γ_w·z·cos²β
    (informe ``u`` calculado pelo engenheiro; aqui ``u`` entra direto).

Fellenius (1936) — método ordinário (sueco) das fatias, superfície de ruptura
circular. Despreza as forças entre fatias; o equilíbrio é tomado normal à base:

    FS = Σ[ c·ΔL + (W·cosα − u·ΔL)·tanφ ] / Σ( W·sinα )

onde, por fatia, ``W`` é o peso por metro de talude (kN/m), ``α`` o ângulo da base
com a horizontal, ``ΔL`` o comprimento da base e ``u`` a poro-pressão na base.
É conservador frente a Bishop simplificado.

Bishop simplificado: FORA DE ESCOPO nesta fase (exige iteração de FS porque o termo
``mα = cosα + sinα·tanφ/FS`` depende do próprio FS). Abstém-se em favor de Fellenius,
que é o limite inferior usual e não requer iteração.

Classificação do fator de segurança (FS,mín usual ≈ 1,5, NBR 11682):
  - instável: FS < 1,0
  - crítico:  1,0 ≤ FS < 1,5
  - estável:  FS ≥ 1,5

Abstenção: entradas fora de faixa física (φ∉[0,50]°, γ∉[10,25] kN/m³, c<0, z≤0,
β∉(0,90)°) ou geometria inválida (sem fatias, ΔL≤0, W≤0, esforço atuante não
positivo) levantam ``ValueError``.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- faixas físicas (próprias do módulo, mantém o domínio isolado) -----------
PHI_MIN, PHI_MAX = 0.0, 50.0
GAMMA_MIN, GAMMA_MAX = 10.0, 25.0
C_MIN = 0.0
FS_SLOPE_MIN = 1.5  # fator de segurança mínimo usual (NBR 11682)


class Slice(BaseModel):
    """Fatia do método das fatias (ruptura circular).

    w_kn: peso da fatia por metro de talude (kN/m).
    alpha_deg: ângulo da base com a horizontal (graus; negativo perto do pé).
    dl_m: comprimento da base da fatia (m).
    u_kpa: poro-pressão na base da fatia (kPa).
    """

    w_kn: float
    alpha_deg: float
    dl_m: float
    u_kpa: float = 0.0


class InfiniteSlopeResult(BaseModel):
    """Fator de segurança de talude infinito (com ou sem percolação)."""

    # entrada (eco)
    c_kpa: float
    phi_deg: float
    gamma_kn_m3: float
    z_m: float
    beta_deg: float
    u_kpa: float
    # resultado
    fs: float
    resisting_kpa: float       # numerador (tensão cisalhante resistente, kPa)
    driving_kpa: float         # denominador (tensão cisalhante atuante, kPa)
    classification: str
    fs_min_usual: float = FS_SLOPE_MIN
    # metadados
    metodo: str = "Talude infinito (Das)"
    norma: str = "NBR 11682 / Das, Fundamentos de Engenharia Geotécnica"
    warnings: list[str] = []


class FelleniusResult(BaseModel):
    """Fator de segurança por Fellenius (método ordinário das fatias)."""

    # entrada (eco)
    c_kpa: float
    phi_deg: float
    n_slices: int
    # resultado
    fs: float
    resisting_kn_m: float      # numerador Σ resistente (kN/m de talude)
    driving_kn_m: float        # denominador Σ atuante (kN/m de talude)
    classification: str
    fs_min_usual: float = FS_SLOPE_MIN
    # metadados
    metodo: str = "Fellenius (método ordinário das fatias)"
    norma: str = "NBR 11682 / Fellenius (1936)"
    warnings: list[str] = []


def classify_fs(fs: float) -> str:
    """Classifica o talude pelo FS (FS,mín usual ≈ 1,5, NBR 11682)."""
    if fs < 1.0:
        return "instável"
    if fs < FS_SLOPE_MIN:
        return "crítico"
    return "estável"


def infinite_slope_fs(
    c_kpa: float,
    phi_deg: float,
    gamma_kn_m3: float,
    z_m: float,
    beta_deg: float,
    u_kpa: float = 0.0,
) -> InfiniteSlopeResult:
    """Talude infinito: FS = [c + (γ·z·cos²β − u)·tanφ] / (γ·z·sinβ·cosβ).

    Fonte: Das, "Fundamentos de Engenharia Geotécnica". Para solo friccional puro
    sem água, reduz a FS = tanφ/tanβ. Entradas fora de faixa física levantam
    ``ValueError`` (abstenção).
    """
    if not (PHI_MIN <= phi_deg <= PHI_MAX):
        raise ValueError(f"φ={phi_deg}° fora da faixa física [{PHI_MIN}, {PHI_MAX}].")
    if not (GAMMA_MIN <= gamma_kn_m3 <= GAMMA_MAX):
        raise ValueError(f"γ={gamma_kn_m3} kN/m³ fora da faixa física "
                         f"[{GAMMA_MIN}, {GAMMA_MAX}].")
    if c_kpa < C_MIN:
        raise ValueError(f"c={c_kpa} kPa deve ser ≥ 0.")
    if z_m <= 0.0:
        raise ValueError(f"z={z_m} m deve ser positivo.")
    if not (0.0 < beta_deg < 90.0):
        raise ValueError(f"β={beta_deg}° deve estar em (0, 90).")
    if u_kpa < 0.0:
        raise ValueError(f"u={u_kpa} kPa deve ser ≥ 0.")

    phi = math.radians(phi_deg)
    beta = math.radians(beta_deg)
    cos_b = math.cos(beta)
    sin_b = math.sin(beta)

    sigma = gamma_kn_m3 * z_m * cos_b**2          # tensão normal total (kPa)
    resisting = c_kpa + (sigma - u_kpa) * math.tan(phi)
    driving = gamma_kn_m3 * z_m * sin_b * cos_b
    fs = resisting / driving
    return InfiniteSlopeResult(
        c_kpa=c_kpa, phi_deg=phi_deg, gamma_kn_m3=gamma_kn_m3, z_m=z_m,
        beta_deg=beta_deg, u_kpa=u_kpa,
        fs=fs, resisting_kpa=resisting, driving_kpa=driving,
        classification=classify_fs(fs),
        warnings=[],
    )


def fellenius_fs(
    slices: list[Slice],
    c_kpa: float,
    phi_deg: float,
) -> FelleniusResult:
    """Fellenius (método ordinário das fatias), ruptura circular.

    FS = Σ[c·ΔL + (W·cosα − u·ΔL)·tanφ] / Σ(W·sinα). Fonte: Fellenius (1936).
    Despreza forças entre fatias (conservador). Entradas inválidas levantam
    ``ValueError`` (abstenção).
    """
    if not (PHI_MIN <= phi_deg <= PHI_MAX):
        raise ValueError(f"φ={phi_deg}° fora da faixa física [{PHI_MIN}, {PHI_MAX}].")
    if c_kpa < C_MIN:
        raise ValueError(f"c={c_kpa} kPa deve ser ≥ 0.")
    if not slices:
        raise ValueError("Lista de fatias vazia: forneça ao menos uma fatia.")

    tan_phi = math.tan(math.radians(phi_deg))
    resisting = 0.0
    driving = 0.0
    for i, s in enumerate(slices):
        if s.dl_m <= 0.0:
            raise ValueError(f"Fatia {i}: ΔL={s.dl_m} m deve ser positivo.")
        if s.w_kn <= 0.0:
            raise ValueError(f"Fatia {i}: W={s.w_kn} kN deve ser positivo.")
        if s.u_kpa < 0.0:
            raise ValueError(f"Fatia {i}: u={s.u_kpa} kPa deve ser ≥ 0.")
        alpha = math.radians(s.alpha_deg)
        normal_eff = s.w_kn * math.cos(alpha) - s.u_kpa * s.dl_m
        resisting += c_kpa * s.dl_m + normal_eff * tan_phi
        driving += s.w_kn * math.sin(alpha)

    if driving <= 0.0:
        raise ValueError(
            f"Σ(W·sinα)={driving:.3f} ≤ 0: esforço atuante não positivo, FS "
            "indefinido (geometria/superfície inválida)."
        )

    fs = resisting / driving
    return FelleniusResult(
        c_kpa=c_kpa, phi_deg=phi_deg, n_slices=len(slices),
        fs=fs, resisting_kn_m=resisting, driving_kn_m=driving,
        classification=classify_fs(fs),
        warnings=[],
    )
