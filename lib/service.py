"""Orquestrador de alto nível: dimensiona, valida e gera o memorial num só passo.

É o ponto de entrada que o MCP server expõe ao agente. Mantém toda a lógica testável
fora da camada de transporte (o server é só um adaptador fino).
"""

from __future__ import annotations

from lib.concrete.beams import design_rectangular_beam
from lib.concrete.columns import design_rectangular_column
from lib.concrete.footings import design_square_footing
from lib.concrete.slabs import design_one_way_slab, design_two_way_slab
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.memorial import (
    render_beam_memorial,
    render_column_memorial,
    render_footing_memorial,
    render_slab_memorial,
)
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
