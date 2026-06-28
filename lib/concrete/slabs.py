"""Laje maciça de concreto armado (NBR 6118:2014, ELU à flexão).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Método e hipóteses:

- Laje em UMA direção (``design_one_way_slab``): faixa de 1 m tratada como viga
  biapoiada. Md = p_d·lx²/8 por metro; reusa ``flexure_design`` (b = 100 cm).
  Carga de cálculo p_d = γg·(g + pp) + γq·q, γg = γq = 1.4, peso próprio pp = 25·h.

- Laje em DUAS direções (``design_two_way_slab``), caso apoiado nos 4 lados
  (simplesmente apoiado): MÉTODO DAS FAIXAS DE GRASHOF-RANKINE — distribui a carga
  entre as duas direções por igualdade das flechas centrais de faixas ortogonais
  simplesmente apoiadas (5·p·L⁴/384EI):
      px = p·ly⁴/(lx⁴ + ly⁴)   (faixas que vencem lx, vão menor — carregam mais)
      py = p·lx⁴/(lx⁴ + ly⁴)
      Mx = px·lx²/8    My = py·ly²/8     (por metro)
  Coeficiente equivalente μ (M = μ·p·lx²) tabelado a partir da fórmula, λ = ly/lx ≥ 1:
      λ=1.0 -> μx=μy=0.1250 ; λ=1.25 -> μx=0.0709, μy_lx²=... (ver fórmula acima);
      λ=2.0 -> μx=0.1176 (px≈0.941p). É um método conservador: despreza a rigidez à
      torção dos cantos (a favor da segurança). Fonte: método clássico das faixas
      (Grashof/Rankine), p. ex. ARAÚJO, "Curso de Concreto Armado".
  LIMITAÇÃO (abstenção): só o caso APOIADO-APOIADO nos 4 lados está implementado;
  bordas engastadas exigem tabelas específicas (Bares/Czerny) e não são tratadas aqui.

As,mín de laje (NBR 6118 19.3.3.2 / Tabela 19.1), ρmin da Tabela 17.3 (``rho_min_pct``):
  - armadura principal (positiva) de laje em UMA direção: ρs ≥ ρmin;
  - armadura de distribuição (secundária): As ≥ 0,2·As,principal, ≥ 0,9 cm²/m e
    ρs ≥ 0,5·ρmin;
  - armaduras positivas de laje em DUAS direções: ρs ≥ 0,67·ρmin.

Espessura mínima (NBR 6118 13.2.4.1): default h_min = 8 cm (laje de piso); abaixo disso,
aviso (o engenheiro deve confirmar a classe da laje).
"""

from __future__ import annotations

from pydantic import BaseModel

from lib.concrete.beams import flexure_design, rho_min_pct

# --- constantes normativas ---------------------------------------------------
GAMMA_G = 1.4            # ponderação de ações permanentes (desfavorável)
GAMMA_Q = 1.4            # ponderação de ações variáveis (desfavorável)
PESO_CONCRETO = 25.0     # kN/m³ (NBR 6120:2019) — peso próprio da laje
H_MIN_PISO_CM = 8.0      # espessura mínima de laje de piso (NBR 6118 13.2.4.1)
LAMBDA_TWO_WAY_MAX = 2.0  # λ=ly/lx acima disto -> comporta-se como uma direção
AS_DIST_FRAC = 0.20      # distribuição ≥ 20% da principal
AS_DIST_MIN_CM2_M = 0.90  # distribuição ≥ 0,9 cm²/m
RHO_DIST_FRAC = 0.50     # distribuição ≥ 0,5·ρmin
RHO_TWO_WAY_FRAC = 0.67  # positivas de laje em duas direções ≥ 0,67·ρmin


class SlabResult(BaseModel):
    """Resultado completo do dimensionamento de uma laje maciça à flexão (por metro)."""

    # tipo e geometria
    tipo: str                 # "uma_direcao" | "duas_direcoes"
    lx_m: float
    ly_m: float | None
    h_cm: float
    d_cm: float               # altura útil da direção x (principal/menor vão)
    fck_mpa: float
    fyk_mpa: float
    # cargas
    g_knm2: float
    q_knm2: float
    pp_knm2: float
    pd_knm2: float
    px_knm2: float
    py_knm2: float | None
    # esforços (por metro)
    mx_knm: float
    my_knm: float | None
    x_over_d_x: float
    x_over_d_y: float | None
    # armadura (por metro)
    as_x_cm2_m: float
    as_y_cm2_m: float
    as_min_x_cm2_m: float
    as_min_y_cm2_m: float
    # limites
    h_min_cm: float
    # metadados
    norma: str = "NBR 6118:2014"
    warnings: list[str] = []


def _check_inputs(lx_m: float, g_knm2: float, q_knm2: float, h_cm: float,
                  fck_mpa: float, fyk_mpa: float) -> None:
    if lx_m <= 0:
        raise ValueError(f"lx={lx_m} m deve ser positivo.")
    if g_knm2 < 0 or q_knm2 < 0:
        raise ValueError(f"Cargas devem ser não negativas (g={g_knm2}, q={q_knm2}).")
    if h_cm <= 0:
        raise ValueError(f"h={h_cm} cm deve ser positivo.")
    if not (10.0 <= fck_mpa <= 100.0):
        raise ValueError(f"fck={fck_mpa} MPa fora da faixa física [10, 100].")
    if fck_mpa > 50.0:
        raise ValueError("fck > 50 MPa (Grupo II) ainda não implementado para lajes.")
    if not (250.0 <= fyk_mpa <= 600.0):
        raise ValueError(f"fyk={fyk_mpa} MPa fora da faixa de aços comerciais [250, 600].")


def _pd(g_knm2: float, q_knm2: float, h_cm: float,
        peso_concreto: float) -> tuple[float, float]:
    """Peso próprio (kN/m²) e carga de cálculo p_d (kN/m²)."""
    pp = peso_concreto * (h_cm / 100.0)
    pd = GAMMA_G * (g_knm2 + pp) + GAMMA_Q * q_knm2
    return pp, pd


def design_one_way_slab(
    lx_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
    peso_concreto: float = PESO_CONCRETO,
    h_min_cm: float = H_MIN_PISO_CM,
) -> SlabResult:
    """Dimensiona uma laje maciça armada em UMA direção (faixa de 1 m como viga)."""
    _check_inputs(lx_m, g_knm2, q_knm2, h_cm, fck_mpa, fyk_mpa)

    pp, pd = _pd(g_knm2, q_knm2, h_cm, peso_concreto)
    mx = pd * lx_m**2 / 8.0                          # kN·m/m
    d_cm = h_cm - cobrimento_cm - (phi_mm / 10.0) / 2.0

    core = flexure_design(mx, 100.0, d_cm, fck_mpa, fyk_mpa)

    ac = 100.0 * h_cm
    as_min_x = rho_min_pct(fck_mpa) / 100.0 * ac     # principal: ρmin
    as_x = max(core.as_calc_cm2, as_min_x)
    # distribuição (secundária)
    as_min_y = max(AS_DIST_FRAC * as_x, AS_DIST_MIN_CM2_M,
                   RHO_DIST_FRAC * rho_min_pct(fck_mpa) / 100.0 * ac)
    as_y = as_min_y

    warnings = _thickness_warnings(h_cm, h_min_cm)
    if core.x_over_d > 0.45:
        warnings.append(
            f"x/d={core.x_over_d:.3f} > 0.45: ductilidade — aumentar h da laje "
            "(NBR 6118 14.6.4.3)."
        )

    return SlabResult(
        tipo="uma_direcao", lx_m=lx_m, ly_m=None, h_cm=h_cm, d_cm=d_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        g_knm2=g_knm2, q_knm2=q_knm2, pp_knm2=pp, pd_knm2=pd, px_knm2=pd, py_knm2=None,
        mx_knm=mx, my_knm=None, x_over_d_x=core.x_over_d, x_over_d_y=None,
        as_x_cm2_m=as_x, as_y_cm2_m=as_y, as_min_x_cm2_m=as_min_x, as_min_y_cm2_m=as_min_y,
        h_min_cm=h_min_cm, warnings=warnings,
    )


def design_two_way_slab(
    lx_m: float,
    ly_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
    peso_concreto: float = PESO_CONCRETO,
    h_min_cm: float = H_MIN_PISO_CM,
) -> SlabResult:
    """Dimensiona uma laje maciça armada em DUAS direções, apoiada nos 4 lados.

    Exige ly ≥ lx (λ = ly/lx ≥ 1). Método das faixas de Grashof-Rankine.
    """
    _check_inputs(lx_m, g_knm2, q_knm2, h_cm, fck_mpa, fyk_mpa)
    if ly_m < lx_m - 1e-9:
        raise ValueError(
            f"ly={ly_m} m < lx={lx_m} m: passe lx como o MENOR vão (λ=ly/lx ≥ 1)."
        )

    pp, pd = _pd(g_knm2, q_knm2, h_cm, peso_concreto)
    lam = ly_m / lx_m

    # distribuição de carga (Grashof-Rankine)
    px = pd * ly_m**4 / (lx_m**4 + ly_m**4)
    py = pd * lx_m**4 / (lx_m**4 + ly_m**4)
    mx = px * lx_m**2 / 8.0
    my = py * ly_m**2 / 8.0

    phi_cm = phi_mm / 10.0
    d_x = h_cm - cobrimento_cm - phi_cm / 2.0          # camada externa (direção x)
    d_y = h_cm - cobrimento_cm - phi_cm - phi_cm / 2.0  # camada interna (direção y)

    core_x = flexure_design(mx, 100.0, d_x, fck_mpa, fyk_mpa)
    core_y = flexure_design(my, 100.0, d_y, fck_mpa, fyk_mpa)

    ac = 100.0 * h_cm
    as_min = max(RHO_TWO_WAY_FRAC * rho_min_pct(fck_mpa) / 100.0 * ac, AS_DIST_MIN_CM2_M)
    as_x = max(core_x.as_calc_cm2, as_min)
    as_y = max(core_y.as_calc_cm2, as_min)

    warnings = _thickness_warnings(h_cm, h_min_cm)
    if lam > LAMBDA_TWO_WAY_MAX + 1e-9:
        warnings.append(
            f"λ=ly/lx={lam:.2f} > {LAMBDA_TWO_WAY_MAX:.0f}: a laje trabalha "
            "praticamente em uma direção — considerar design_one_way_slab."
        )
    for nome, xod in (("x", core_x.x_over_d), ("y", core_y.x_over_d)):
        if xod > 0.45:
            warnings.append(
                f"x/d (dir. {nome})={xod:.3f} > 0.45: ductilidade — aumentar h "
                "(NBR 6118 14.6.4.3)."
            )

    return SlabResult(
        tipo="duas_direcoes", lx_m=lx_m, ly_m=ly_m, h_cm=h_cm, d_cm=d_x,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        g_knm2=g_knm2, q_knm2=q_knm2, pp_knm2=pp, pd_knm2=pd, px_knm2=px, py_knm2=py,
        mx_knm=mx, my_knm=my, x_over_d_x=core_x.x_over_d, x_over_d_y=core_y.x_over_d,
        as_x_cm2_m=as_x, as_y_cm2_m=as_y, as_min_x_cm2_m=as_min, as_min_y_cm2_m=as_min,
        h_min_cm=h_min_cm, warnings=warnings,
    )


def _thickness_warnings(h_cm: float, h_min_cm: float) -> list[str]:
    if h_cm < h_min_cm - 1e-9:
        return [
            f"h={h_cm:.1f} cm < h_mínima={h_min_cm:.1f} cm "
            "(NBR 6118 13.2.4.1) — confirmar a classe da laje."
        ]
    return []
