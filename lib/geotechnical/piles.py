"""Capacidade de carga de estaca por SPT — Aoki-Velloso e Décourt-Quaresma.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Métodos, hipóteses e tabelas
----------------------------
Capacidade última = resistência de ponta (Rp) + atrito lateral (Rl). A resistência
admissível é ``Radm = Rult / FS`` (FS = 2,0 por padrão, valor global usual da
NBR 6122 para métodos semiempíricos).

Geometria da estaca: Ap = π·D²/4 (área de ponta), U = π·D (perímetro).
O perfil é uma lista de camadas (N do SPT, tipo de solo, espessura); a ponta fica
na base da última camada e o comprimento L é a soma das espessuras.

— Aoki-Velloso (1975) —
    Ponta:   qp = K·Np / F1            Rp = qp·Ap
    Lateral: rl_i = α·K·Nl_i / F2      Rl = Σ rl_i·U·ΔL_i
  K (kPa) e α (—) por tipo de solo (Tabela de Aoki-Velloso, 1975).
  F1, F2 por tipo de estaca (F2 = 2·F1):
    pré-moldada/metálica F1=1,75 F2=3,5 ; Franki F1=2,5 F2=5,0 ;
    escavada F1=3,0 F2=6,0.

— Décourt-Quaresma (1978) —
    Ponta:   qp = C·Np                 Rp = qp·Ap
    Lateral: rl = 10·(Ns/3 + 1) [kPa]  Rl = rl·U·L
  C (kPa) por tipo de solo: argila=120 ; silte argiloso=200 ; silte arenoso=250 ;
  areia=400 (extrapolado às variações por predominância textural). Np = N na cota da
  ponta; Ns = média dos N ao longo do fuste (cada N limitado a [3,50]). Os fatores
  α,β de Décourt-Quaresma (1996) por tipo de estaca/solo são adotados =1,0 (estaca
  cravada/pré-moldada) — refinamento a cargo do engenheiro (abstenção).

Comparação (docs/08-validacao-calculos.md): roda os dois métodos e emite aviso se a
divergência relativa de Rult exceder 20%.

Abstenção: N fora de [0,50], tipo de solo ou de estaca não tabelado, D≤0, perfil
vazio → ``ValueError``.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- constantes --------------------------------------------------------------
FS_DEFAULT = 2.0           # fator de segurança global usual (NBR 6122)
DIVERGENCIA_LIMITE = 0.20  # aviso de divergência entre métodos (>20%)
N_SPT_MIN, N_SPT_MAX = 0, 50
NS_MIN_DECOURT, NS_MAX_DECOURT = 3.0, 50.0   # limites do N do fuste (Décourt)

# Aoki-Velloso (1975): K em kPa, α adimensional (fração) por tipo de solo.
AOKI_SOLO: dict[str, tuple[float, float]] = {
    "areia": (1000.0, 0.014),
    "areia siltosa": (800.0, 0.020),
    "areia silto-argilosa": (700.0, 0.024),
    "areia argilosa": (600.0, 0.030),
    "areia argilo-siltosa": (500.0, 0.028),
    "silte": (400.0, 0.030),
    "silte arenoso": (550.0, 0.022),
    "silte areno-argiloso": (450.0, 0.028),
    "silte argiloso": (230.0, 0.034),
    "silte argilo-arenoso": (250.0, 0.030),
    "argila": (200.0, 0.060),
    "argila arenosa": (350.0, 0.024),
    "argila areno-siltosa": (300.0, 0.028),
    "argila siltosa": (220.0, 0.040),
    "argila silto-arenosa": (330.0, 0.030),
}

# Aoki-Velloso: F1, F2 por tipo de estaca (F2 = 2·F1).
AOKI_F1F2: dict[str, tuple[float, float]] = {
    "pre-moldada": (1.75, 3.5),
    "metalica": (1.75, 3.5),
    "franki": (2.5, 5.0),
    "escavada": (3.0, 6.0),
}

# Décourt-Quaresma (1978): C em kPa por tipo de solo.
DECOURT_C: dict[str, float] = {
    "areia": 400.0,
    "areia siltosa": 400.0,
    "areia silto-argilosa": 400.0,
    "areia argilosa": 400.0,
    "areia argilo-siltosa": 400.0,
    "silte": 250.0,
    "silte arenoso": 250.0,
    "silte areno-argiloso": 250.0,
    "silte argiloso": 200.0,
    "silte argilo-arenoso": 200.0,
    "argila": 120.0,
    "argila arenosa": 120.0,
    "argila areno-siltosa": 120.0,
    "argila siltosa": 120.0,
    "argila silto-arenosa": 120.0,
}

PILE_TYPES = tuple(AOKI_F1F2.keys())


class SoilLayer(BaseModel):
    """Camada do perfil de sondagem SPT atravessada pela estaca."""

    n_spt: int
    soil_type: str
    thickness_m: float


class PileCapacityResult(BaseModel):
    """Capacidade de carga de estaca por um método semiempírico (SPT)."""

    # entrada (eco)
    metodo: str
    pile_type: str
    diameter_m: float
    length_m: float
    fs: float
    # geometria
    ap_m2: float
    u_m: float
    # resistências (kN)
    rp_kn: float
    rl_kn: float
    rult_kn: float
    radm_kn: float
    # transparência / verificação dimensional
    qp_kpa: float      # resistência unitária de ponta
    # faixa de SPT do perfil (verificação física)
    n_spt_min: int
    n_spt_max: int
    # metadados
    norma: str = "NBR 6122"
    warnings: list[str] = []


class PileComparisonResult(BaseModel):
    """Comparação Aoki-Velloso × Décourt-Quaresma (validação por 2º método)."""

    aoki: PileCapacityResult
    decourt: PileCapacityResult
    rult_aoki_kn: float
    rult_decourt_kn: float
    divergencia: float       # fração relativa |Δ|/max
    divergencia_pct: float
    convergem: bool
    warnings: list[str] = []


def _geometry(diameter_m: float) -> tuple[float, float]:
    if diameter_m <= 0.0:
        raise ValueError(f"Diâmetro D={diameter_m} m deve ser positivo.")
    ap = math.pi * diameter_m**2 / 4.0
    u = math.pi * diameter_m
    return ap, u


def _check_profile(layers: list[SoilLayer], pile_type: str,
                   c_table: dict[str, float] | None = None) -> None:
    if not layers:
        raise ValueError("Perfil de sondagem vazio.")
    if pile_type not in AOKI_F1F2:
        raise ValueError(f"Tipo de estaca '{pile_type}' não tabelado; "
                         f"use uma de {PILE_TYPES}.")
    for ly in layers:
        if not (N_SPT_MIN <= ly.n_spt <= N_SPT_MAX):
            raise ValueError(f"N_SPT={ly.n_spt} fora da faixa física "
                             f"[{N_SPT_MIN}, {N_SPT_MAX}] na camada '{ly.soil_type}'.")
        if ly.thickness_m <= 0.0:
            raise ValueError(f"Espessura={ly.thickness_m} m deve ser positiva.")
        if ly.soil_type not in AOKI_SOLO:
            raise ValueError(f"Solo '{ly.soil_type}' não tabelado (Aoki-Velloso).")
        if c_table is not None and ly.soil_type not in c_table:
            raise ValueError(f"Solo '{ly.soil_type}' não tabelado (Décourt-Quaresma).")


def _spt_range(layers: list[SoilLayer]) -> tuple[int, int]:
    ns = [ly.n_spt for ly in layers]
    return min(ns), max(ns)


def aoki_velloso(
    layers: list[SoilLayer],
    pile_type: str,
    diameter_m: float,
    fs: float = FS_DEFAULT,
) -> PileCapacityResult:
    """Capacidade de estaca pelo método de Aoki-Velloso (1975).

    Entradas inválidas (N∉[0,50], solo/estaca não tabelado, D≤0, perfil vazio)
    levantam ``ValueError`` (abstenção).
    """
    if fs < 1.0:
        raise ValueError(f"FS={fs} deve ser ≥ 1.")
    _check_profile(layers, pile_type)
    ap, u = _geometry(diameter_m)
    f1, f2 = AOKI_F1F2[pile_type]
    length = sum(ly.thickness_m for ly in layers)

    # ponta — camada da base
    tip = layers[-1]
    k_tip, _alpha_tip = AOKI_SOLO[tip.soil_type]
    qp = k_tip * tip.n_spt / f1                       # kPa
    rp = qp * ap                                      # kN

    # atrito lateral — soma das camadas
    rl = 0.0
    for ly in layers:
        k, alpha = AOKI_SOLO[ly.soil_type]
        rl_unit = alpha * k * ly.n_spt / f2           # kPa
        rl += rl_unit * u * ly.thickness_m            # kN

    rult = rp + rl
    n_min, n_max = _spt_range(layers)
    return PileCapacityResult(
        metodo="Aoki-Velloso", pile_type=pile_type, diameter_m=diameter_m,
        length_m=length, fs=fs, ap_m2=ap, u_m=u,
        rp_kn=rp, rl_kn=rl, rult_kn=rult, radm_kn=rult / fs,
        qp_kpa=qp, n_spt_min=n_min, n_spt_max=n_max,
        warnings=[],
    )


def decourt_quaresma(
    layers: list[SoilLayer],
    pile_type: str,
    diameter_m: float,
    fs: float = FS_DEFAULT,
) -> PileCapacityResult:
    """Capacidade de estaca pelo método de Décourt-Quaresma (1978).

    Entradas inválidas (N∉[0,50], solo/estaca não tabelado, D≤0, perfil vazio)
    levantam ``ValueError`` (abstenção).
    """
    if fs < 1.0:
        raise ValueError(f"FS={fs} deve ser ≥ 1.")
    _check_profile(layers, pile_type, c_table=DECOURT_C)
    ap, u = _geometry(diameter_m)
    length = sum(ly.thickness_m for ly in layers)

    # ponta — C·Np na cota da ponta
    tip = layers[-1]
    c_tip = DECOURT_C[tip.soil_type]
    qp = c_tip * tip.n_spt                            # kPa
    rp = qp * ap                                      # kN

    # atrito lateral — N médio do fuste (limitado a [3,50])
    ns_vals = [min(max(float(ly.n_spt), NS_MIN_DECOURT), NS_MAX_DECOURT) for ly in layers]
    ns_mean = sum(ns_vals) / len(ns_vals)
    rl_unit = 10.0 * (ns_mean / 3.0 + 1.0)            # kPa
    rl = rl_unit * u * length                         # kN

    rult = rp + rl
    n_min, n_max = _spt_range(layers)
    return PileCapacityResult(
        metodo="Décourt-Quaresma", pile_type=pile_type, diameter_m=diameter_m,
        length_m=length, fs=fs, ap_m2=ap, u_m=u,
        rp_kn=rp, rl_kn=rl, rult_kn=rult, radm_kn=rult / fs,
        qp_kpa=qp, n_spt_min=n_min, n_spt_max=n_max,
        warnings=[],
    )


def comparar_metodos_estaca(
    layers: list[SoilLayer],
    pile_type: str,
    diameter_m: float,
    fs: float = FS_DEFAULT,
    tol: float = DIVERGENCIA_LIMITE,
) -> PileComparisonResult:
    """Roda Aoki-Velloso e Décourt-Quaresma e compara Rult (validação por 2º método).

    Emite aviso (e ``convergem=False``) se a divergência relativa exceder ``tol``
    (20% por padrão, conforme docs/08-validacao-calculos.md).
    """
    aoki = aoki_velloso(layers, pile_type, diameter_m, fs)
    decourt = decourt_quaresma(layers, pile_type, diameter_m, fs)
    ra, rd = aoki.rult_kn, decourt.rult_kn
    divergencia = abs(ra - rd) / max(ra, rd)
    convergem = divergencia <= tol
    warnings: list[str] = []
    if not convergem:
        warnings.append(
            f"Divergência de {divergencia:.0%} entre Aoki-Velloso "
            f"(Rult={ra:.0f} kN) e Décourt-Quaresma (Rult={rd:.0f} kN) "
            f"> {tol:.0%}: revisão recomendada (docs/08-validacao-calculos.md)."
        )
    return PileComparisonResult(
        aoki=aoki, decourt=decourt,
        rult_aoki_kn=ra, rult_decourt_kn=rd,
        divergencia=divergencia, divergencia_pct=divergencia * 100.0,
        convergem=convergem, warnings=warnings,
    )
