"""MCP server `calc-server` — expõe a engine de cálculo determinística ao agente.

Princípio do projeto: resultados numéricos SÓ vêm destas ferramentas. Se uma ferramenta
não existir para o que foi pedido, o agente deve abster-se (nunca inventar números).

Execução:
    python mcp/calc-server/server.py            # inicia o server (stdio)
    python mcp/calc-server/server.py --selftest # autoteste rápido (não inicia stdio)
"""

from __future__ import annotations

import pathlib
import sys

# Importa o SDK `mcp` ANTES de pôr a raiz do repo no path (a raiz contém um diretório
# chamado `mcp/`, que sombrearia o pacote instalado).
from mcp.server.fastmcp import FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from lib.reporting.disclaimer import DISCLAIMER  # noqa: E402
from lib.service import (  # noqa: E402
    solve_one_way_slab,
    solve_rectangular_beam,
    solve_rectangular_column,
    solve_square_footing,
    solve_two_way_slab,
)
from lib.structural.combinations import combinar_elu_normal  # noqa: E402
from lib.structural.loads import (  # noqa: E402
    carga_acidental_uso,
    peso_especifico_material,
)
from lib.units.registry import Q_, ensure  # noqa: E402

mcp = FastMCP("inema-calc-server")


@mcp.tool()
def dimensionar_viga_retangular(
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
    """Dimensiona uma viga retangular biapoiada de concreto armado à flexão (NBR 6118, ELU).

    Cargas em kN/m: g (permanente, exclui peso próprio) e q (variável). Devolve o
    resultado, o relatório de validação, o memorial em Markdown e o aviso de
    responsabilidade técnica obrigatório.
    """
    return solve_rectangular_beam(
        b_cm=b_cm, h_cm=h_cm, fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        vao_m=vao_m, g_knm=g_knm, q_knm=q_knm,
        cobrimento_cm=cobrimento_cm, d_cm=d_cm,
    )


@mcp.tool()
def dimensionar_pilar(
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
    """Dimensiona um pilar retangular de concreto à compressão com 2ª ordem (NBR 6118).

    ``h_cm`` é a dimensão na direção analisada (a do momento e da flambagem). λ > 90 é
    recusado (fora do método simplificado). Devolve resultado, validação, memorial e aviso.
    """
    return solve_rectangular_column(
        nk_kn=nk_kn, mk_topo_knm=mk_topo_knm, b_cm=b_cm, h_cm=h_cm, le_cm=le_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm,
        phi_estribo_mm=phi_estribo_mm, phi_long_mm=phi_long_mm,
        d_linha_cm=d_linha_cm, alpha_b=alpha_b,
    )


@mcp.tool()
def dimensionar_sapata(
    nk_kn: float,
    sigma_adm_kpa: float,
    pilar_a_cm: float,
    pilar_b_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 5.0,
    phi_long_mm: float = 12.5,
) -> dict:
    """Dimensiona uma sapata isolada quadrada rígida sob carga centrada (NBR 6122/6118).

    Método das bielas. Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_square_footing(
        nk_kn=nk_kn, sigma_adm_kpa=sigma_adm_kpa,
        pilar_a_cm=pilar_a_cm, pilar_b_cm=pilar_b_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        cobrimento_cm=cobrimento_cm, phi_long_mm=phi_long_mm,
    )


@mcp.tool()
def dimensionar_laje_uma_direcao(
    lx_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
) -> dict:
    """Dimensiona uma laje maciça armada em UMA direção à flexão (NBR 6118, ELU).

    Cargas em kN/m². Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_one_way_slab(
        lx_m=lx_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )


@mcp.tool()
def dimensionar_laje_duas_direcoes(
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
    """Dimensiona uma laje maciça armada em DUAS direções, apoiada nos 4 lados (NBR 6118).

    ``lx_m`` é o MENOR vão (λ = ly/lx ≥ 1). Método das faixas (Grashof-Rankine).
    Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_two_way_slab(
        lx_m=lx_m, ly_m=ly_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )


@mcp.tool()
def combinar_acoes_elu(
    gk: float,
    qk_principal: float,
    qk_secundarias: list[float] | None = None,
    gamma_g: float = 1.4,
    gamma_q: float = 1.4,
    psi0: float = 0.5,
) -> dict:
    """Combinação última normal (ELU): Fd = γg·Gk + γq·(Qk_princ + Σ ψ0·Qk_sec).

    NBR 8681:2003 / NBR 6118:2014. Devolve a combinação e o aviso de responsabilidade.
    """
    cr = combinar_elu_normal(
        gk=gk, qk_principal=qk_principal, qk_secundarias=qk_secundarias,
        gamma_g=gamma_g, gamma_q=gamma_q, psi0=psi0,
    )
    return {"resultado": cr.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def consultar_peso_material(nome: str) -> dict:
    """Peso específico (kN/m³) de um material da NBR 6120:2019 Tab.2 (ex.: 'concreto armado').

    Material fora da tabela => erro com a lista de opções (o agente deve abster-se).
    """
    lv = peso_especifico_material(nome)
    return {"resultado": lv.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def consultar_carga_uso(uso: str) -> dict:
    """Carga acidental de piso (kN/m²) por uso do ambiente (NBR 6120:2019).

    Uso fora da tabela => erro com a lista de opções (o agente deve abster-se).
    """
    lv = carga_acidental_uso(uso)
    return {"resultado": lv.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def verificar_unidades(valor: float, unidade_origem: str, unidade_destino: str) -> dict:
    """Converte/valida uma grandeza entre unidades (pint). Falha se as dimensões diferem."""
    valor_convertido = ensure(Q_(valor, unidade_origem), unidade_destino)
    return {"valor": valor_convertido, "unidade": unidade_destino}


@mcp.tool()
def listar_capacidades() -> dict:
    """Lista os cálculos disponíveis. Se o pedido não estiver aqui, o agente deve abster-se."""
    return {
        "calculos": [
            "dimensionar_viga_retangular — flexão simples, seção retangular (NBR 6118:2014)",
            "dimensionar_pilar — flexão composta normal com 2ª ordem, λ≤90 (NBR 6118:2014)",
            "dimensionar_sapata — sapata isolada quadrada rígida, bielas (NBR 6122/6118)",
            "dimensionar_laje_uma_direcao — laje maciça armada em uma direção (NBR 6118)",
            "dimensionar_laje_duas_direcoes — laje maciça apoiada nos 4 lados (NBR 6118)",
            "combinar_acoes_elu — combinação última normal de ações (NBR 8681/6118)",
            "consultar_peso_material — peso específico de material (NBR 6120:2019 Tab.2)",
            "consultar_carga_uso — carga acidental por uso do ambiente (NBR 6120:2019)",
            "verificar_unidades — conversão/validação dimensional (pint)",
        ],
        "nota": (
            "Resultados numéricos só vêm destas ferramentas. Para cálculos não listados, "
            "informe que não há ferramenta disponível — não invente valores."
        ),
    }


def _selftest() -> int:
    viga = solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    pilar = solve_rectangular_column(
        nk_kn=500.0, mk_topo_knm=20.0, b_cm=40.0, h_cm=30.0, le_cm=300.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    )
    sapata = solve_square_footing(
        nk_kn=500.0, sigma_adm_kpa=200.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    bundles = [viga, pilar, sapata]
    ok = all(b["aprovado"] and "6.496/77" in b["aviso"] for b in bundles)
    print("SELFTEST OK" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    mcp.run()
