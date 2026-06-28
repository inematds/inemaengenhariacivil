"""Orquestrador de alto nível: dimensiona, valida e gera o memorial num só passo.

É o ponto de entrada que o MCP server expõe ao agente. Mantém toda a lógica testável
fora da camada de transporte (o server é só um adaptador fino).
"""

from __future__ import annotations

from lib.concrete.beams import design_rectangular_beam
from lib.reporting.disclaimer import DISCLAIMER
from lib.reporting.memorial import render_beam_memorial
from lib.validators.validate import validate_beam


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
    return {
        "resultado": r.model_dump(),
        "validacao": rep.model_dump(),
        "memorial_markdown": memorial,
        "aviso": DISCLAIMER,
        "aprovado": rep.passed,
    }
