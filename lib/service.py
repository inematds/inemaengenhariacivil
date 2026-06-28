"""Orquestrador de alto nível: dimensiona, valida e gera o memorial num só passo.

É o ponto de entrada que o MCP server expõe ao agente. Mantém toda a lógica testável
fora da camada de transporte (o server é só um adaptador fino).
"""

from __future__ import annotations

from lib.budget.estimate import montar_orcamento
from lib.budget.sinapi import load_sinapi
from lib.concrete.beams import design_rectangular_beam
from lib.concrete.columns import design_rectangular_column
from lib.concrete.footings import design_square_footing
from lib.concrete.slabs import design_one_way_slab, design_two_way_slab
from lib.geotechnical.bearing_capacity import design_bearing_capacity
from lib.geotechnical.earth_pressure import (
    coulomb_earth_pressure,
    rankine_earth_pressure,
)
from lib.geotechnical.piles import SoilLayer, comparar_metodos_estaca
from lib.geotechnical.settlement import (
    consolidation_settlement,
    elastic_settlement,
)
from lib.hydraulic.head_loss import total_head_loss
from lib.hydraulic.open_channel import (
    manning_circular,
    manning_rectangular,
    manning_trapezoidal,
)
from lib.hydraulic.pipe_flow import (
    pipe_flow_darcy_weisbach,
    pipe_flow_hazen_williams,
)
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.memorial import (
    render_bearing_capacity_memorial,
    render_beam_memorial,
    render_bolted_memorial,
    render_column_memorial,
    render_compression_memorial,
    render_consolidation_settlement_memorial,
    render_earth_pressure_memorial,
    render_elastic_settlement_memorial,
    render_footing_memorial,
    render_head_loss_memorial,
    render_open_channel_memorial,
    render_orcamento_memorial,
    render_pile_comparison_memorial,
    render_pipe_flow_memorial,
    render_slab_memorial,
    render_weld_memorial,
)
from lib.steel.connections import design_bolted_connection, design_fillet_weld
from lib.steel.profiles import DEFAULT_TABLE, load_profiles
from lib.steel.stability import design_compression
from lib.validators.budget_check import validate_orcamento
from lib.validators.geotech_check import (
    validate_bearing,
    validate_earth_pressure,
    validate_pile,
    validate_settlement,
)
from lib.validators.hydraulic_check import (
    validate_head_loss,
    validate_open_channel,
    validate_pipe_flow,
)
from lib.validators.report import Check, ValidationReport
from lib.validators.steel_check import validate_compression
from lib.validators.steel_connections_check import validate_bolted, validate_weld
from lib.validators.validate import (
    validate_beam,
    validate_column,
    validate_footing,
    validate_slab,
)


def solve_rectangular_beam(
    b_cm: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    vao_m: float,
    g_knm: float,
    q_knm: float,
    cobrimento_cm: float = 3.0,
    d_cm: float | None = None,
) -> dict:
    """Resolve uma viga retangular e devolve o pacote completo (dados serializáveis)."""
    r = design_rectangular_beam(
        b_cm=b_cm, h_cm=h_cm, fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        vao_m=vao_m, g_knm=g_knm, q_knm=q_knm,
        cobrimento_cm=cobrimento_cm, d_cm=d_cm,
    )
    rep = validate_beam(r)
    memorial = render_beam_memorial(r, rep)
    return _bundle(r, rep, memorial)


def _bundle(r, rep, memorial: str) -> dict:
    """Empacota resultado + validação + memorial + aviso obrigatório (formato único)."""
    return {
        "resultado": r.model_dump(),
        "validacao": rep.model_dump(),
        "memorial_markdown": memorial,
        "aviso": DISCLAIMER,
        "aprovado": rep.passed,
    }


def solve_rectangular_column(
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
    alpha_b: float = 1.0,
) -> dict:
    """Resolve um pilar retangular (2ª ordem) e devolve o pacote completo."""
    r = design_rectangular_column(
        nk_kn=nk_kn, mk_topo_knm=mk_topo_knm, b_cm=b_cm, h_cm=h_cm, le_cm=le_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm,
        phi_estribo_mm=phi_estribo_mm, phi_long_mm=phi_long_mm,
        d_linha_cm=d_linha_cm, alpha_b=alpha_b,
    )
    rep = validate_column(r)
    memorial = render_column_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_square_footing(
    nk_kn: float,
    sigma_adm_kpa: float,
    pilar_a_cm: float,
    pilar_b_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 5.0,
    phi_long_mm: float = 12.5,
    fator_peso_proprio: float = 1.05,
    peso_concreto: float = 25.0,
    modulo_cm: float = 5.0,
) -> dict:
    """Resolve uma sapata isolada quadrada rígida e devolve o pacote completo."""
    r = design_square_footing(
        nk_kn=nk_kn, sigma_adm_kpa=sigma_adm_kpa,
        pilar_a_cm=pilar_a_cm, pilar_b_cm=pilar_b_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm,
        phi_long_mm=phi_long_mm, fator_peso_proprio=fator_peso_proprio,
        peso_concreto=peso_concreto, modulo_cm=modulo_cm,
    )
    rep = validate_footing(r)
    memorial = render_footing_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_one_way_slab(
    lx_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
) -> dict:
    """Resolve uma laje maciça armada em UMA direção e devolve o pacote completo."""
    r = design_one_way_slab(
        lx_m=lx_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )
    rep = validate_slab(r)
    memorial = render_slab_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_two_way_slab(
    lx_m: float,
    ly_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
) -> dict:
    """Resolve uma laje maciça armada em DUAS direções e devolve o pacote completo."""
    r = design_two_way_slab(
        lx_m=lx_m, ly_m=ly_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )
    rep = validate_slab(r)
    memorial = render_slab_memorial(r, rep)
    return _bundle(r, rep, memorial)


# ====================================================================== GEOTECNIA


def solve_bearing_capacity(
    c_kpa: float,
    phi_deg: float,
    gamma_kn_m3: float,
    b_m: float,
    depth_df_m: float,
    shape: str = "quadrada",
    l_m: float | None = None,
    fs: float = 3.0,
) -> dict:
    """Resolve a capacidade de carga de fundação rasa (Vesic) — pacote completo."""
    r = design_bearing_capacity(
        c_kpa=c_kpa, phi_deg=phi_deg, gamma_kn_m3=gamma_kn_m3, b_m=b_m,
        depth_df_m=depth_df_m, shape=shape, l_m=l_m, fs=fs,
    )
    rep = validate_bearing(r)
    memorial = render_bearing_capacity_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_elastic_settlement(
    q_kpa: float,
    b_m: float,
    poisson_nu: float,
    iw: float,
    es_kpa: float,
) -> dict:
    """Resolve o recalque elástico imediato — pacote completo."""
    r = elastic_settlement(q_kpa=q_kpa, b_m=b_m, poisson_nu=poisson_nu, iw=iw, es_kpa=es_kpa)
    rep = validate_settlement(r)
    memorial = render_elastic_settlement_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_consolidation_settlement(
    cc: float,
    e0: float,
    h_m: float,
    sigma0_kpa: float,
    delta_sigma_kpa: float,
) -> dict:
    """Resolve o recalque por adensamento primário (Terzaghi) — pacote completo."""
    r = consolidation_settlement(
        cc=cc, e0=e0, h_m=h_m, sigma0_kpa=sigma0_kpa, delta_sigma_kpa=delta_sigma_kpa,
    )
    rep = validate_settlement(r)
    memorial = render_consolidation_settlement_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_earth_pressure_rankine(
    gamma_kn_m3: float,
    h_m: float,
    phi_deg: float,
) -> dict:
    """Resolve o empuxo de terra de Rankine — pacote completo."""
    r = rankine_earth_pressure(gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg)
    rep = validate_earth_pressure(r)
    memorial = render_earth_pressure_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_earth_pressure_coulomb(
    gamma_kn_m3: float,
    h_m: float,
    phi_deg: float,
    delta_deg: float = 0.0,
    beta_deg: float = 0.0,
    alpha_deg: float = 0.0,
) -> dict:
    """Resolve o empuxo de terra de Coulomb (δ, β, α) — pacote completo."""
    r = coulomb_earth_pressure(
        gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg,
        delta_deg=delta_deg, beta_deg=beta_deg, alpha_deg=alpha_deg,
    )
    rep = validate_earth_pressure(r)
    memorial = render_earth_pressure_memorial(r, rep)
    return _bundle(r, rep, memorial)


def _combine_pile_reports(r, rep_a: ValidationReport, rep_d: ValidationReport) -> ValidationReport:
    """Junta as validações dos dois métodos + a checagem de convergência num só relatório."""
    checks: list[Check] = []
    for c in rep_a.checks:
        checks.append(Check(name=f"Aoki/{c.name}", status=c.status, detail=c.detail))
    for c in rep_d.checks:
        checks.append(Check(name=f"Décourt/{c.name}", status=c.status, detail=c.detail))
    checks.append(Check(
        name="convergencia",
        status="ok" if r.convergem else "warning",
        detail=f"divergência {r.divergencia_pct:.1f}% (limite 20%)",
    ))
    passed = rep_a.passed and rep_d.passed
    warnings = list(rep_a.warnings) + list(rep_d.warnings) + list(r.warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def solve_pile_comparison(
    layers: list[dict | SoilLayer],
    pile_type: str,
    diameter_m: float,
    fs: float = 2.0,
    tol: float = 0.20,
) -> dict:
    """Compara Aoki-Velloso × Décourt-Quaresma, valida ambos e gera memorial comparativo."""
    parsed = [ly if isinstance(ly, SoilLayer) else SoilLayer(**ly) for ly in layers]
    r = comparar_metodos_estaca(parsed, pile_type, diameter_m, fs=fs, tol=tol)
    rep_a = validate_pile(r.aoki)
    rep_d = validate_pile(r.decourt)
    rep = _combine_pile_reports(r, rep_a, rep_d)
    memorial = render_pile_comparison_memorial(r, rep)
    return _bundle(r, rep, memorial)


# ====================================================================== HIDRÁULICA


def solve_pipe_flow(
    Q_m3s: float,
    D_m: float,
    L_m: float,
    metodo: str = "hazen-williams",
    C: float = 130.0,
    eps_m: float | None = None,
    nu_m2s: float = 1.0e-6,
) -> dict:
    """Resolve o escoamento em conduto forçado (Hazen-Williams ou Darcy-Weisbach)."""
    m = metodo.strip().lower()
    if m in ("hw", "hazen-williams", "hazen_williams"):
        r = pipe_flow_hazen_williams(Q_m3s=Q_m3s, D_m=D_m, L_m=L_m, C=C)
    elif m in ("dw", "darcy-weisbach", "darcy_weisbach"):
        if eps_m is None:
            raise ValueError("Darcy-Weisbach exige a rugosidade absoluta eps_m (m).")
        r = pipe_flow_darcy_weisbach(Q_m3s=Q_m3s, D_m=D_m, L_m=L_m, eps_m=eps_m, nu_m2s=nu_m2s)
    else:
        raise ValueError(
            f"Método '{metodo}' não suportado; use 'hazen-williams' ou 'darcy-weisbach'."
        )
    rep = validate_pipe_flow(r)
    memorial = render_pipe_flow_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_open_channel(
    geometria: str,
    n: float,
    S: float,
    y_m: float,
    b_m: float | None = None,
    z: float | None = None,
    D_m: float | None = None,
) -> dict:
    """Resolve o escoamento uniforme em canal aberto (Manning) por geometria."""
    g = geometria.strip().lower()
    if g == "retangular":
        if b_m is None:
            raise ValueError("Canal retangular exige a largura de fundo b_m.")
        r = manning_rectangular(b_m=b_m, y_m=y_m, n=n, S=S)
    elif g == "trapezoidal":
        if b_m is None or z is None:
            raise ValueError("Canal trapezoidal exige b_m e talude z.")
        r = manning_trapezoidal(b_m=b_m, y_m=y_m, z=z, n=n, S=S)
    elif g == "circular":
        if D_m is None:
            raise ValueError("Conduto circular exige o diâmetro D_m.")
        r = manning_circular(D_m=D_m, y_m=y_m, n=n, S=S)
    else:
        raise ValueError(
            f"Geometria '{geometria}' não suportada; use "
            "'retangular', 'trapezoidal' ou 'circular'."
        )
    rep = validate_open_channel(r)
    memorial = render_open_channel_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_head_loss(
    hf_distribuida_m: float,
    singularidades: dict[str, int],
    V_ms: float,
) -> dict:
    """Resolve a perda de carga total (distribuída + localizadas) — pacote completo."""
    r = total_head_loss(
        hf_distribuida_m=hf_distribuida_m, singularidades=singularidades, V_ms=V_ms,
    )
    rep = validate_head_loss(r)
    memorial = render_head_loss_memorial(r, rep)
    return _bundle(r, rep, memorial)


# ====================================================================== ORÇAMENTO


def solve_orcamento(
    itens: list[dict],
    bdi_pct: float = 0.0,
    csv_path: str = "data/sinapi_amostra.csv",
) -> dict:
    """Monta um orçamento (custo direto + BDI) e devolve o pacote completo.

    ``itens`` é a lista de quantitativos ``{codigo, quantidade}``; os preços vêm da
    base tipo SINAPI em ``csv_path`` (amostra ILUSTRATIVA por padrão). Carrega a base,
    monta o orçamento, valida a aritmética e gera o memorial. Propaga as abstenções dos
    núcleos (código inexistente, BDI fora de [0,40] %, quantidade negativa, lista vazia).
    """
    base = load_sinapi(csv_path)
    r = montar_orcamento(itens, base, bdi_pct=bdi_pct)
    rep = validate_orcamento(r)
    memorial = render_orcamento_memorial(r, rep)
    return _bundle(r, rep, memorial)


# ====================================================================== METÁLICAS


def solve_compression(
    designacao: str,
    kl_cm: float,
    fy_mpa: float = 250.0,
    e_mpa: float = 200000.0,
    q: float = 1.0,
    gamma_a1: float = 1.1,
    json_path: str | None = None,
) -> dict:
    """Resolve uma barra comprimida de aço (NBR 8800 §5.3) — pacote completo.

    Carrega a tabela de perfis W (``DEFAULT_TABLE`` por padrão), dimensiona à flambagem
    por flexão, valida e gera o memorial. Abstenção: perfil inexistente propaga
    ``KeyError`` (de :func:`lib.steel.profiles.get_profile`).
    """
    base = load_profiles(json_path if json_path is not None else DEFAULT_TABLE)
    r = design_compression(
        designacao=designacao, base=base, kl_cm=kl_cm,
        fy_mpa=fy_mpa, e_mpa=e_mpa, q=q, gamma_a1=gamma_a1,
    )
    rep = validate_compression(r)
    memorial = render_compression_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_bolted_connection(
    forca_kn: float,
    db_mm: float,
    fub_mpa: float,
    t_mm: float,
    fu_mpa: float,
    planos: int = 1,
    rosca_no_plano: bool = True,
    gamma_a2: float = 1.35,
) -> dict:
    """Resolve uma ligação parafusada à cortante (NBR 8800 §6.3) — pacote completo."""
    r = design_bolted_connection(
        forca_kn=forca_kn, db_mm=db_mm, fub_mpa=fub_mpa, t_mm=t_mm, fu_mpa=fu_mpa,
        planos=planos, rosca_no_plano=rosca_no_plano, gamma_a2=gamma_a2,
    )
    rep = validate_bolted(r)
    memorial = render_bolted_memorial(r, rep)
    return _bundle(r, rep, memorial)


def solve_weld(
    forca_kn: float,
    perna_mm: float,
    fw_mpa: float = 485.0,
    gamma_a2: float = 1.35,
) -> dict:
    """Resolve uma solda de filete (NBR 8800 §6.2.6) — pacote completo."""
    r = design_fillet_weld(
        forca_kn=forca_kn, perna_mm=perna_mm, fw_mpa=fw_mpa, gamma_a2=gamma_a2,
    )
    rep = validate_weld(r)
    memorial = render_weld_memorial(r, rep)
    return _bundle(r, rep, memorial)
