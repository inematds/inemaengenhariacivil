"""Verificação dimensional com `pint` — recomputa Md a partir das cargas."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.units.registry import Q_, ensure
from lib.validators.report import Check


def check_units_beam(r: BeamFlexureResult) -> Check:
    # Md = p_d * L^2 / 8, com unidades explícitas (kN/m * m^2 = kN.m)
    md_q = Q_(r.pd_knm, "kilonewton/meter") * Q_(r.vao_m, "meter") ** 2 / 8.0
    md_val = ensure(md_q, "kilonewton * meter")
    ref = max(abs(r.md_knm), 1.0)
    ok = abs(md_val - r.md_knm) <= 1e-3 * ref
    return Check(name="units", status="ok" if ok else "fail",
                 detail=f"Md={md_val:.2f} kN·m (dimensional ✓)")
