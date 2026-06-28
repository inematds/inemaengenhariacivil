"""Interpolação de tabelas de norma (Fase 5).

Funções puras e sem estado para consultar tabelas normativas (ex.: coeficientes
tabelados em função de um ou dois parâmetros). Toda a aritmética vive aqui; o LLM
apenas chama estas funções via MCP e interpreta o resultado.

Princípio da abstenção
-----------------------
Não se extrapola fora do domínio tabelado: um ponto fora dos limites levanta
``ValueError`` em vez de devolver um número possivelmente inseguro. ``nearest`` é a
exceção consciente — devolve sempre um valor já existente na tabela (o nó mais
próximo), nunca um valor calculado por extrapolação.

Convenções
----------
- ``xs`` (e ``ys`` na grade bilinear) devem ser estritamente crescentes.
- Na grade bilinear ``grid[i][j]`` corresponde ao nó ``(xs[i], ys[j])``.
"""

from __future__ import annotations

import bisect
from collections.abc import Sequence


def _check_axis(xs: Sequence[float], nome: str = "xs") -> None:
    """Valida que ``xs`` tem >=2 pontos e é estritamente crescente."""
    if len(xs) < 2:
        raise ValueError(f"{nome} precisa de pelo menos 2 pontos (recebido {len(xs)}).")
    for a, b in zip(xs, xs[1:]):
        if not (b > a):
            raise ValueError(
                f"{nome} deve ser estritamente crescente; "
                f"violação em {a!r} -> {b!r}."
            )


def linear_interp(x: float, xs: Sequence[float], ys: Sequence[float]) -> float:
    """Interpolação linear de ``y(x)`` numa tabela 1D.

    ``xs`` deve ser estritamente crescente e ``ys`` ter o mesmo comprimento.
    Um ``x`` exatamente igual a um nó devolve o próprio ``y``. Fora do intervalo
    ``[xs[0], xs[-1]]`` levanta ``ValueError`` (sem extrapolação — princípio da
    abstenção).

    Raises:
        ValueError: comprimentos diferentes, ``xs`` não monotônico/curto, ou ``x``
            fora do domínio tabelado.
    """
    if len(xs) != len(ys):
        raise ValueError(
            f"xs e ys têm comprimentos diferentes ({len(xs)} != {len(ys)})."
        )
    _check_axis(xs, "xs")

    if x < xs[0] or x > xs[-1]:
        raise ValueError(
            f"x={x} fora do domínio tabelado [{xs[0]}, {xs[-1]}]; "
            "extrapolação proibida (princípio da abstenção)."
        )

    # localiza o intervalo [xs[i], xs[i+1]] que contém x
    i = bisect.bisect_right(xs, x) - 1
    if i >= len(xs) - 1:        # x == xs[-1]
        return float(ys[-1])
    if i < 0:                   # x == xs[0] (guardado pelo bisect, defensivo)
        return float(ys[0])

    x0, x1 = xs[i], xs[i + 1]
    y0, y1 = ys[i], ys[i + 1]
    t = (x - x0) / (x1 - x0)
    return float(y0 + t * (y1 - y0))


def bilinear_interp(
    x: float,
    y: float,
    xs: Sequence[float],
    ys: Sequence[float],
    grid: Sequence[Sequence[float]],
) -> float:
    """Interpolação bilinear de ``z(x, y)`` numa grade tabelada.

    ``grid[i][j]`` é o valor no nó ``(xs[i], ys[j])``; ``xs`` e ``ys`` devem ser
    estritamente crescentes. No centro de uma célula o resultado é a média dos
    quatro cantos; nos nós devolve o próprio valor. Fora dos limites em ``x`` ou
    ``y`` levanta ``ValueError`` (sem extrapolação).

    Raises:
        ValueError: ``xs``/``ys`` inválidos, ``grid`` com dimensões incompatíveis,
            ou ``(x, y)`` fora do domínio tabelado.
    """
    _check_axis(xs, "xs")
    _check_axis(ys, "ys")

    if len(grid) != len(xs):
        raise ValueError(
            f"grid tem {len(grid)} linhas, mas xs tem {len(xs)} pontos."
        )
    for idx, linha in enumerate(grid):
        if len(linha) != len(ys):
            raise ValueError(
                f"grid[{idx}] tem {len(linha)} colunas, mas ys tem {len(ys)} pontos."
            )

    if x < xs[0] or x > xs[-1]:
        raise ValueError(
            f"x={x} fora do domínio tabelado [{xs[0]}, {xs[-1]}]; "
            "extrapolação proibida (princípio da abstenção)."
        )
    if y < ys[0] or y > ys[-1]:
        raise ValueError(
            f"y={y} fora do domínio tabelado [{ys[0]}, {ys[-1]}]; "
            "extrapolação proibida (princípio da abstenção)."
        )

    i = min(bisect.bisect_right(xs, x) - 1, len(xs) - 2)
    i = max(i, 0)
    j = min(bisect.bisect_right(ys, y) - 1, len(ys) - 2)
    j = max(j, 0)

    x0, x1 = xs[i], xs[i + 1]
    y0, y1 = ys[j], ys[j + 1]
    tx = (x - x0) / (x1 - x0)
    ty = (y - y0) / (y1 - y0)

    q00 = grid[i][j]
    q10 = grid[i + 1][j]
    q01 = grid[i][j + 1]
    q11 = grid[i + 1][j + 1]

    # interpola em x nas duas bordas e depois em y
    a = q00 + tx * (q10 - q00)
    b = q01 + tx * (q11 - q01)
    return float(a + ty * (b - a))


def nearest(x: float, xs: Sequence[float], ys: Sequence[float]) -> float:
    """Vizinho mais próximo: devolve o ``y`` do nó cujo ``xs`` está mais perto de ``x``.

    Não interpola nem extrapola — devolve sempre um valor já tabelado, o que o
    torna seguro mesmo para ``x`` fora do intervalo (clampa ao nó extremo). Em
    caso de empate, escolhe o menor índice.

    Raises:
        ValueError: comprimentos diferentes ou ``xs`` vazio.
    """
    if len(xs) != len(ys):
        raise ValueError(
            f"xs e ys têm comprimentos diferentes ({len(xs)} != {len(ys)})."
        )
    if len(xs) == 0:
        raise ValueError("xs vazio.")

    best_i = min(range(len(xs)), key=lambda i: abs(xs[i] - x))
    return float(ys[best_i])
