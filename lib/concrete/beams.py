"""Flexão simples — viga retangular de concreto armado (NBR 6118:2014, ELU).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta o
problema, chama estas funções via MCP e explica o resultado.

Hipóteses:
- Bloco retangular de tensões; concreto fck <= 50 MPa -> lambda = 0.8, alpha_c = 0.85.
- Coeficientes de ponderação: gamma_c = 1.4, gamma_s = 1.15.
- Combinação última normal com gamma_g = gamma_q = 1.4 (ações desfavoráveis).
- Viga biapoiada com carga uniformemente distribuída: Md = p_d * L^2 / 8.
- Seção retangular, armadura simples (sem armadura de compressão).
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- constantes normativas (NBR 6118:2014) ----------------------------------
LAMBDA = 0.8          # altura do bloco retangular / linha neutra (fck <= 50 MPa)
ALPHA_C = 0.85        # redução de resistência do concreto à compressão
GAMMA_C = 1.4         # ponderação do concreto
GAMMA_S = 1.15        # ponderação do aço
GAMMA_G = 1.4         # ponderação de ações permanentes (desfavorável)
GAMMA_Q = 1.4         # ponderação de ações variáveis (desfavorável)
PESO_CONCRETO_ARMADO = 25.0   # kN/m^3 (NBR 6120)
X_D_DUCTIL_MAX = 0.45         # limite de ductilidade x/d (sem redistribuição, fck<=50)

# Diâmetros comerciais de barras (mm)
DIAMETROS_MM = (6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0)

# Taxa de armadura mínima rho_min (%) — NBR 6118:2014 Tabela 17.3 (seção retangular)
_RHO_MIN_PCT = {20: 0.150, 25: 0.150, 30: 0.150, 35: 0.164,
                40: 0.179, 45: 0.194, 50: 0.208}


class FlexureCore(BaseModel):
    """Resultado do núcleo de flexão (momento dado)."""
    as_calc_cm2: float
    x_cm: float
    x_over_d: float
    z_cm: float
    fcd_mpa: float
    fyd_mpa: float


class BarChoice(BaseModel):
    """Detalhamento da armadura escolhida."""
    n_bars: int
    phi_mm: float
    as_ef_cm2: float


class BeamFlexureResult(BaseModel):
    """Resultado completo do dimensionamento à flexão de viga retangular."""
    # entrada (eco)
    b_cm: float
    h_cm: float
    d_cm: float
    fck_mpa: float
    fyk_mpa: float
    vao_m: float
    g_knm: float
    q_knm: float
    # esforços
    pp_knm: float
    pd_knm: float
    md_knm: float
    # materiais
    fcd_mpa: float
    fyd_mpa: float
    # flexão
    x_cm: float
    x_over_d: float
    z_cm: float
    ductile: bool
    # armadura
    as_calc_cm2: float
    as_min_cm2: float
    as_max_cm2: float
    as_adopted_cm2: float
    governed_by: str
    bars: BarChoice
    # metadados
    norma: str = "NBR 6118:2014"
    warnings: list[str] = []


def _check_material(fck_mpa: float, fyk_mpa: float) -> None:
    if not (10.0 <= fck_mpa <= 100.0):
        raise ValueError(f"fck={fck_mpa} MPa fora da faixa física [10, 100].")
    if fck_mpa > 50.0:
        raise ValueError("fck > 50 MPa exige o domínio de concretos do Grupo II "
                         "(lambda/alpha_c variáveis), ainda não implementado.")
    if not (250.0 <= fyk_mpa <= 600.0):
        raise ValueError(f"fyk={fyk_mpa} MPa fora da faixa de aços comerciais [250, 600].")


def rho_min_pct(fck_mpa: float) -> float:
    """Taxa de armadura mínima (%) por interpolação linear da Tabela 17.3."""
    if fck_mpa <= 30.0:
        return _RHO_MIN_PCT[30]
    if fck_mpa >= 50.0:
        return _RHO_MIN_PCT[50]
    chaves = sorted(_RHO_MIN_PCT)
    for lo, hi in zip(chaves, chaves[1:]):
        if lo <= fck_mpa <= hi:
            t = (fck_mpa - lo) / (hi - lo)
            return _RHO_MIN_PCT[lo] + t * (_RHO_MIN_PCT[hi] - _RHO_MIN_PCT[lo])
    return _RHO_MIN_PCT[50]


def _area_barra_cm2(phi_mm: float) -> float:
    return math.pi / 4.0 * (phi_mm / 10.0) ** 2


def flexure_design(md_knm: float, b_cm: float, d_cm: float,
                   fck_mpa: float, fyk_mpa: float) -> FlexureCore:
    """Dimensiona a armadura de tração para o momento de cálculo ``md_knm``.

    Resolve o equilíbrio da seção (bloco retangular) e devolve As de cálculo, a
    posição da linha neutra ``x`` e o braço de alavanca ``z``. Não aplica As_min.
    """
    _check_material(fck_mpa, fyk_mpa)

    fcd_k = (fck_mpa / GAMMA_C) * 0.1   # MPa -> kN/cm^2
    fyd_k = (fyk_mpa / GAMMA_S) * 0.1
    md_kncm = md_knm * 100.0            # kN.m -> kN.cm

    k1 = ALPHA_C * LAMBDA * fcd_k * b_cm          # resultante de compressão por cm de x
    a = k1 * (LAMBDA / 2.0)
    disc = (k1 * d_cm) ** 2 - 4.0 * a * md_kncm
    if disc < 0:
        raise ValueError("Momento excede a capacidade da seção com armadura simples; "
                         "requer armadura dupla ou seção maior (fora do escopo da Fase 1).")
    x = (k1 * d_cm - math.sqrt(disc)) / (2.0 * a)
    z = d_cm - (LAMBDA / 2.0) * x
    as_calc = (k1 * x) / fyd_k

    return FlexureCore(
        as_calc_cm2=as_calc,
        x_cm=x,
        x_over_d=x / d_cm,
        z_cm=z,
        fcd_mpa=fck_mpa / GAMMA_C,
        fyd_mpa=fyk_mpa / GAMMA_S,
    )


def select_bars(as_req_cm2: float, n_min: int = 2, n_max: int = 8) -> BarChoice:
    """Escolhe (n, phi) comercial que cobre ``as_req_cm2`` com o menor excesso de área.

    Desempate: menor número de barras e, depois, menor diâmetro.
    """
    best: BarChoice | None = None
    best_key: tuple[float, int, float] | None = None
    for phi in DIAMETROS_MM:
        area = _area_barra_cm2(phi)
        for n in range(n_min, n_max + 1):
            as_ef = n * area
            if as_ef + 1e-9 < as_req_cm2:
                continue
            key = (as_ef - as_req_cm2, n, phi)
            if best_key is None or key < best_key:
                best_key = key
                best = BarChoice(n_bars=n, phi_mm=phi, as_ef_cm2=as_ef)
    if best is None:
        raise ValueError(f"Nenhuma combinação até {n_max} barras cobre As={as_req_cm2:.2f} cm².")
    return best


def design_rectangular_beam(
    b_cm: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    vao_m: float,
    g_knm: float,
    q_knm: float,
    cobrimento_cm: float = 3.0,
    phi_estribo_mm: float = 5.0,
    phi_long_mm: float = 16.0,
    peso_concreto: float = PESO_CONCRETO_ARMADO,
    d_cm: float | None = None,
) -> BeamFlexureResult:
    """Dimensionamento completo de viga retangular biapoiada à flexão (ELU).

    Cargas ``g_knm`` (permanente, exclui peso próprio) e ``q_knm`` (variável) em kN/m.
    Se ``d_cm`` não for informado, é estimado a partir do cobrimento e dos diâmetros.
    """
    _check_material(fck_mpa, fyk_mpa)

    if d_cm is None:
        d_linha = cobrimento_cm + (phi_estribo_mm / 10.0) + (phi_long_mm / 10.0) / 2.0
        d_cm = h_cm - d_linha

    pp = peso_concreto * (b_cm / 100.0) * (h_cm / 100.0)          # kN/m
    pd = GAMMA_G * (g_knm + pp) + GAMMA_Q * q_knm                 # kN/m
    md = pd * vao_m**2 / 8.0                                      # kN.m

    core = flexure_design(md, b_cm, d_cm, fck_mpa, fyk_mpa)

    as_min = rho_min_pct(fck_mpa) / 100.0 * b_cm * h_cm
    as_max = 0.04 * b_cm * h_cm

    if core.as_calc_cm2 >= as_min:
        as_adopted = core.as_calc_cm2
        governed_by = "ELU"
    else:
        as_adopted = as_min
        governed_by = "As_min"

    warnings: list[str] = []
    if core.x_over_d > X_D_DUCTIL_MAX:
        warnings.append(
            f"x/d = {core.x_over_d:.3f} > {X_D_DUCTIL_MAX} (ductilidade): "
            "considerar armadura dupla ou aumentar a seção (NBR 6118 14.6.4.3)."
        )
    if as_adopted > as_max:
        warnings.append(
            f"As = {as_adopted:.2f} cm² > As_max = {as_max:.2f} cm² "
            "(4% da seção, NBR 6118 17.3.5.2.4)."
        )

    bars = select_bars(as_adopted)

    return BeamFlexureResult(
        b_cm=b_cm, h_cm=h_cm, d_cm=d_cm, fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        vao_m=vao_m, g_knm=g_knm, q_knm=q_knm,
        pp_knm=pp, pd_knm=pd, md_knm=md,
        fcd_mpa=core.fcd_mpa, fyd_mpa=core.fyd_mpa,
        x_cm=core.x_cm, x_over_d=core.x_over_d, z_cm=core.z_cm,
        ductile=core.x_over_d <= X_D_DUCTIL_MAX,
        as_calc_cm2=core.as_calc_cm2, as_min_cm2=as_min, as_max_cm2=as_max,
        as_adopted_cm2=as_adopted, governed_by=governed_by, bars=bars,
        warnings=warnings,
    )
