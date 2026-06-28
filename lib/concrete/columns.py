"""Pilar retangular de concreto armado com efeitos de 2ª ordem (NBR 6118:2014, cap.15).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Método e hipóteses (flexão composta normal, momentos atuando na direção de ``h``):

1. Esforços de cálculo: Nd = γf·Nk, M1d,A = γf·Mk,topo (γf = 1.4).

2. Esbeltez (NBR 6118 15.8.2):
   - raio de giração i = h/√12 (seção retangular, direção analisada);
   - λ = le/i;
   - excentricidade de 1ª ordem e1 = M1d,A/Nd;
   - λ1 = (25 + 12,5·e1/h)/αb, com αb = 1,0 (pilar com momentos nas extremidades, sem
     cargas transversais — caso usual, documentado e fixado); λ1 é limitado a
     35 ≤ λ1 ≤ 90 (NBR 6118 15.8.2).
   Classificação: λ ≤ λ1 → "curto" (2ª ordem desprezível); λ1 < λ ≤ 90 → "medio"
   (método do pilar-padrão com curvatura aproximada); λ > 90 → RECUSA (fora do escopo
   deste núcleo — princípio da abstenção; exige métodos mais refinados, item 15.8.3.2).

3. 2ª ordem por curvatura aproximada (NBR 6118 15.8.3.3.2):
   - força normal adimensional ν = Nd/(Ac·fcd), Ac = b·h;
   - curvatura 1/r = 0,005/[h·(ν+0,5)] ≤ 0,005/h, com h EM METROS;
   - M2d = Nd·le²/10·(1/r), com le em metros;
   - Md,tot = αb·M1d,A + M2d ≥ M1d,mín, com M1d,mín = Nd·(0,015 + 0,03·h[m]).
   Para pilar curto, M2d = 0 e Md,tot = max(αb·M1d,A, M1d,mín).

4. Armadura longitudinal SIMÉTRICA (duas camadas iguais As/2): dimensionada por
   compatibilidade de deformações no ELU (bloco retangular de tensões, λ=0,8,
   αc=0,85; εcu=3,5‰, εc2=2,0‰, εsu=10‰; Es=210 GPa). Itera-se As até a capacidade
   da seção em flexão composta, MRd avaliado para N = Nd, alcançar Md,tot. Limites:
   As,mín = max(0,4%·Ac, 0,15·Nd/fyd) (NBR 6118 17.3.5.3.1); As,máx = 8%·Ac (com
   emendas) e 4%·Ac fora de emendas (alerta).

Limitações (abstenção): só flexão composta NORMAL (1 direção); fck ≤ 50 MPa; λ ≤ 90;
detalhamento (espaçamento, estribos, emendas, flambagem de barras) é do engenheiro.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel

from lib.concrete.beams import (
    ALPHA_C,
    GAMMA_C,
    GAMMA_S,
    LAMBDA,
    BarChoice,
    select_bars,
)

# --- constantes normativas (NBR 6118:2014) ----------------------------------
GAMMA_F = 1.4            # ponderação da carga do pilar (Nd = γf·Nk)
ES_KNCM2 = 21000.0       # módulo de elasticidade do aço (210 GPa) em kN/cm²
EPS_CU = 0.0035          # encurtamento último do concreto (fck ≤ 50 MPa)
EPS_C2 = 0.0020          # encurtamento no início do patamar (fck ≤ 50 MPa)
EPS_SU = 0.010           # alongamento máximo da armadura tracionada
ALPHA_B = 1.0            # αb (momentos nas extremidades, sem cargas transversais)
LAMBDA1_MIN = 35.0       # limite inferior de λ1 (NBR 6118 15.8.2)
LAMBDA1_MAX = 90.0       # limite superior de λ1 (NBR 6118 15.8.2)
LAMBDA_MAX = 90.0        # acima disto, pilar-padrão + curvatura aprox. não se aplica
AS_MIN_FRAC = 0.004      # 0,4%·Ac (NBR 6118 17.3.5.3.1)
AS_MAX_FRAC = 0.08       # 8%·Ac (com emendas) — limite absoluto
AS_LAP_WARN_FRAC = 0.04  # 4%·Ac (fora de emendas) — alerta de detalhamento


class ColumnResult(BaseModel):
    """Resultado completo do dimensionamento de um pilar retangular à compressão."""

    # entrada (eco)
    nk_kn: float
    mk_topo_knm: float
    b_cm: float
    h_cm: float
    le_cm: float
    fck_mpa: float
    fyk_mpa: float
    d_linha_cm: float
    # esforços de cálculo
    nd_kn: float
    m1d_a_knm: float
    fcd_mpa: float
    fyd_mpa: float
    # esbeltez
    i_cm: float
    esbeltez: float          # λ
    lambda1: float           # λ1
    classe: Literal["curto", "medio"]
    # 2ª ordem
    nu: float                # ν
    one_over_r: float        # 1/r (1/m)
    m2d_knm: float
    m1d_min_knm: float
    md_tot_knm: float
    # armadura
    as_calc_cm2: float
    as_min_cm2: float
    as_max_cm2: float
    as_adopted_cm2: float
    governed_by: str
    bitolas: BarChoice | None
    # metadados
    norma: str = "NBR 6118:2014"
    warnings: list[str] = []


def _check_inputs(nk_kn: float, b_cm: float, h_cm: float, le_cm: float,
                  fck_mpa: float, fyk_mpa: float) -> None:
    if nk_kn <= 0:
        raise ValueError(f"Nk={nk_kn} kN deve ser positivo (compressão do pilar).")
    if b_cm <= 0 or h_cm <= 0:
        raise ValueError(f"Dimensões do pilar devem ser positivas (b={b_cm}, h={h_cm}).")
    if le_cm <= 0:
        raise ValueError(f"le={le_cm} cm (comprimento de flambagem) deve ser positivo.")
    if not (10.0 <= fck_mpa <= 100.0):
        raise ValueError(f"fck={fck_mpa} MPa fora da faixa física [10, 100].")
    if fck_mpa > 50.0:
        raise ValueError("fck > 50 MPa (Grupo II) ainda não implementado para pilares.")
    if not (250.0 <= fyk_mpa <= 600.0):
        raise ValueError(f"fyk={fyk_mpa} MPa fora da faixa de aços comerciais [250, 600].")


def _strain_at(z: float, x: float, h: float, d_linha: float) -> float:
    """Deformação (compressão positiva) à profundidade ``z`` (a partir da borda
    mais comprimida) para a linha neutra ``x``. Pivôs do ELU (NBR 6118 17.2.2)."""
    if x <= h:
        d2 = h - d_linha  # camada tracionada (inferior)
        if x < d2:
            eps_bot = EPS_CU * (x - d2) / x  # < 0 (tração) com pivô no topo
            if -eps_bot > EPS_SU:
                # Domínio 2: pivô na armadura inferior em εsu (tração)
                return -EPS_SU * (z - x) / (d2 - x)
        # Pivô no topo em εcu (domínios 3/4/4a)
        return EPS_CU * (x - z) / x
    # x > h: pivô C em εc2, à profundidade (1 - εc2/εcu)·h (domínio 5)
    z_c = (1.0 - EPS_C2 / EPS_CU) * h
    return EPS_C2 * (x - z) / (x - z_c)


def _section_nm(x: float, as_total: float, b: float, h: float, d_linha: float,
                fcd_k: float, fyd_k: float) -> tuple[float, float]:
    """Esforços resistentes (N em kN, M em kN·cm) da seção com armadura simétrica,
    para a posição de linha neutra ``x`` (cm). Momento tomado no centro geométrico."""
    y = min(LAMBDA * x, h)
    rcc = ALPHA_C * fcd_k * b * y               # resultante de compressão (kN)
    center = h / 2.0
    n = rcc
    m = rcc * (center - y / 2.0)
    as_layer = as_total / 2.0
    for di in (d_linha, h - d_linha):
        sigma = ES_KNCM2 * _strain_at(di, x, h, d_linha)
        sigma = max(-fyd_k, min(fyd_k, sigma))
        f = sigma * as_layer
        n += f
        m += f * (center - di)
    return n, m


def _x_for_n(nd: float, as_total: float, b: float, h: float, d_linha: float,
             fcd_k: float, fyd_k: float) -> float | None:
    """Linha neutra ``x`` que equilibra a força normal ``nd`` (None se inviável)."""
    lo, hi = 1e-4, 10.0 * h
    n_hi, _ = _section_nm(hi, as_total, b, h, d_linha, fcd_k, fyd_k)
    if n_hi < nd:
        return None  # nem a compressão quase uniforme resiste a Nd
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        n_mid, _ = _section_nm(mid, as_total, b, h, d_linha, fcd_k, fyd_k)
        if n_mid < nd:
            lo = mid
        else:
            hi = mid
    return hi


def column_moment_capacity(nd_kn: float, as_total_cm2: float, b_cm: float, h_cm: float,
                           d_linha_cm: float, fck_mpa: float, fyk_mpa: float) -> float:
    """Momento resistente (kN·m) da seção em flexão composta normal para N = ``nd_kn``.

    Devolve 0.0 se a seção não resiste à força normal (sem capacidade de momento).
    """
    fcd_k = (fck_mpa / GAMMA_C) * 0.1
    fyd_k = (fyk_mpa / GAMMA_S) * 0.1
    x = _x_for_n(nd_kn, as_total_cm2, b_cm, h_cm, d_linha_cm, fcd_k, fyd_k)
    if x is None:
        return 0.0
    _, m_kncm = _section_nm(x, as_total_cm2, b_cm, h_cm, d_linha_cm, fcd_k, fyd_k)
    return m_kncm / 100.0  # kN·cm -> kN·m


def _required_as(nd_kn: float, md_tot_knm: float, b_cm: float, h_cm: float,
                 d_linha_cm: float, fck_mpa: float, fyk_mpa: float,
                 as_max_hard: float) -> tuple[float, bool]:
    """Menor As (cm²) cuja capacidade ≥ ``md_tot_knm`` para N = ``nd_kn``.

    Retorna (As, viável). Se nem ``as_max_hard`` for suficiente, devolve
    (as_max_hard, False) — abstenção: a seção precisa ser ampliada.
    """
    def cap(as_total: float) -> float:
        return column_moment_capacity(nd_kn, as_total, b_cm, h_cm, d_linha_cm,
                                      fck_mpa, fyk_mpa)

    if cap(as_max_hard) < md_tot_knm:
        return as_max_hard, False
    lo, hi = 0.0, as_max_hard
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if cap(mid) >= md_tot_knm:
            hi = mid
        else:
            lo = mid
    return hi, True


def design_rectangular_column(
    nk_kn: float,
    mk_topo_knm: float,
    b_cm: float,
    h_cm: float,
    le_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 3.0,
    phi_estribo_mm: float = 5.0,
    phi_long_mm: float = 20.0,
    d_linha_cm: float | None = None,
    alpha_b: float = ALPHA_B,
) -> ColumnResult:
    """Dimensiona um pilar retangular de concreto à compressão com 2ª ordem.

    ``h_cm`` é a dimensão na direção analisada (a do momento e da flambagem).
    Recusa (``ValueError``) entradas inválidas e λ > 90 (princípio da abstenção).
    """
    _check_inputs(nk_kn, b_cm, h_cm, le_cm, fck_mpa, fyk_mpa)
    if mk_topo_knm < 0:
        raise ValueError(f"Mk_topo={mk_topo_knm} kN·m deve ser não negativo.")

    if d_linha_cm is None:
        d_linha_cm = cobrimento_cm + (phi_estribo_mm / 10.0) + (phi_long_mm / 10.0) / 2.0

    # 1) esforços de cálculo ------------------------------------------------
    nd = GAMMA_F * nk_kn
    m1d_a = GAMMA_F * mk_topo_knm
    fcd_mpa = fck_mpa / GAMMA_C
    fyd_mpa = fyk_mpa / GAMMA_S
    fcd_k = fcd_mpa * 0.1   # MPa -> kN/cm²
    fyd_k = fyd_mpa * 0.1

    # 2) esbeltez -----------------------------------------------------------
    i_cm = h_cm / math.sqrt(12.0)
    lam = le_cm / i_cm
    e1_cm = m1d_a / nd * 100.0           # M1d,A[kN·m]/Nd[kN] = m -> cm
    lambda1_raw = (25.0 + 12.5 * e1_cm / h_cm) / alpha_b
    lambda1 = min(LAMBDA1_MAX, max(LAMBDA1_MIN, lambda1_raw))

    if lam > LAMBDA_MAX + 1e-9:
        raise ValueError(
            f"λ={lam:.1f} > {LAMBDA_MAX:.0f}: fora do escopo do pilar-padrão com "
            "curvatura aproximada (NBR 6118 15.8.3.1) — exige método mais refinado."
        )
    classe: Literal["curto", "medio"] = "curto" if lam <= lambda1 else "medio"

    # 3) 2ª ordem por curvatura aproximada ----------------------------------
    ac = b_cm * h_cm
    nu = nd / (ac * fcd_k)
    h_m = h_cm / 100.0
    le_m = le_cm / 100.0
    one_over_r = min(0.005 / (h_m * (nu + 0.5)), 0.005 / h_m)
    m2d = 0.0 if classe == "curto" else nd * le_m**2 / 10.0 * one_over_r
    m1d_min = nd * (0.015 + 0.03 * h_m)
    md_tot = max(alpha_b * m1d_a + m2d, m1d_min)

    # 4) armadura longitudinal simétrica ------------------------------------
    as_max = AS_MAX_FRAC * ac
    as_calc, feasible = _required_as(nd, md_tot, b_cm, h_cm, d_linha_cm,
                                     fck_mpa, fyk_mpa, as_max)
    as_min = max(AS_MIN_FRAC * ac, 0.15 * nd / fyd_k)

    if not feasible:
        as_adopted = as_max
        governed_by = "As_max (insuficiente)"
    elif as_calc >= as_min:
        as_adopted = as_calc
        governed_by = "ELU"
    else:
        as_adopted = as_min
        governed_by = "As_min"

    warnings: list[str] = []
    if not feasible:
        warnings.append(
            f"As necessário > As_máx={as_max:.2f} cm² (8%·Ac): a seção não resiste a "
            f"(Nd={nd:.0f} kN, Md,tot={md_tot:.1f} kN·m) — ampliar o pilar."
        )
    if as_adopted > AS_LAP_WARN_FRAC * ac + 1e-9:
        warnings.append(
            f"As={as_adopted:.2f} cm² > 4%·Ac={AS_LAP_WARN_FRAC * ac:.2f} cm² "
            "(limite fora de regiões de emenda, NBR 6118 17.3.5.3.4)."
        )

    bitolas: BarChoice | None
    try:
        bitolas = select_bars(as_adopted, n_min=4, n_max=20)
    except ValueError:
        bitolas = None
        warnings.append(
            f"Nenhuma combinação comercial cobre As={as_adopted:.2f} cm² (detalhar à mão)."
        )

    return ColumnResult(
        nk_kn=nk_kn, mk_topo_knm=mk_topo_knm, b_cm=b_cm, h_cm=h_cm, le_cm=le_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, d_linha_cm=d_linha_cm,
        nd_kn=nd, m1d_a_knm=m1d_a, fcd_mpa=fcd_mpa, fyd_mpa=fyd_mpa,
        i_cm=i_cm, esbeltez=lam, lambda1=lambda1, classe=classe,
        nu=nu, one_over_r=one_over_r, m2d_knm=m2d, m1d_min_knm=m1d_min, md_tot_knm=md_tot,
        as_calc_cm2=as_calc, as_min_cm2=as_min, as_max_cm2=as_max,
        as_adopted_cm2=as_adopted, governed_by=governed_by, bitolas=bitolas,
        warnings=warnings,
    )
