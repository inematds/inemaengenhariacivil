"""Camada de unidades — registry `pint` compartilhado e verificação dimensional.

Regra do projeto: unidades são sempre verificadas antes de qualquer operação.
Todo o resto do código deve importar `ureg` / `Q_` DAQUI (pint só opera entre
quantidades do mesmo registry).
"""

from __future__ import annotations

import pint

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity


def ensure(value, unit: str) -> float:
    """Valida a dimensão de ``value`` e devolve a magnitude na unidade ``unit``.

    - Se ``value`` for um :class:`pint.Quantity`, converte para ``unit`` e devolve a
      magnitude. Dimensão incompatível levanta ``pint.DimensionalityError``.
    - Se ``value`` for um número puro, assume-se que já está em ``unit``.
    """
    if isinstance(value, ureg.Quantity):
        return float(value.to(unit).magnitude)
    return float(value)
