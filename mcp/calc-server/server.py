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

from lib.service import solve_rectangular_beam  # noqa: E402
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
            "verificar_unidades — conversão/validação dimensional (pint)",
        ],
        "nota": (
            "Resultados numéricos só vêm destas ferramentas. Para cálculos não listados, "
            "informe que não há ferramenta disponível — não invente valores."
        ),
    }


def _selftest() -> int:
    bundle = solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    ok = bundle["aprovado"] and "6.496/77" in bundle["aviso"]
    print("SELFTEST OK" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    mcp.run()
