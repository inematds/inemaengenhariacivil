"""Orquestrador da validação obrigatória de um dimensionamento de viga.

Todo cálculo passa por aqui antes de ser apresentado: unidades, física, normativa e
equilíbrio. Determinístico, sem LLM.
"""

from __future__ import annotations

from lib.concrete.beams import ALPHA_C, LAMBDA, BeamFlexureResult
from lib.validators.normative_check import check_normative_beam
from lib.validators.physical_check import check_physical_beam
from lib.validators.report import Check, ValidationReport
from lib.validators.units_check import check_units_beam


def check_equilibrium_beam(r: BeamFlexureResult) -> Check:
    """Equilíbrio da seção: resultante de compressão ≈ tração na armadura de cálculo."""
    fcd_k = (r.fcd_mpa) * 0.1            # MPa -> kN/cm^2
    fyd_k = (r.fyd_mpa) * 0.1
    rcc = ALPHA_C * LAMBDA * fcd_k * r.b_cm * r.x_cm     # kN
    rst = r.as_calc_cm2 * fyd_k                          # kN
    ref = max(abs(rcc), 1.0)
    ok = abs(rcc - rst) <= 1e-2 * ref
    return Check(name="equilibrium", status="ok" if ok else "fail",
                 detail=f"Rcc={rcc:.1f} kN ≈ Rst={rst:.1f} kN (ΣF≈0)")


def _fold(name: str, subs: list[Check]) -> Check:
    status = "ok"
    for c in subs:
        if c.status == "fail":
            status = "fail"
            break
        if c.status == "warning":
            status = "warning"
    detail = "; ".join(f"{c.name}={c.status}" for c in subs)
    return Check(name=name, status=status, detail=detail)


def validate_beam(r: BeamFlexureResult) -> ValidationReport:
    phys = check_physical_beam(r)
    norm = check_normative_beam(r)
    units = check_units_beam(r)
    equi = check_equilibrium_beam(r)

    checks = [units, _fold("physical", phys), _fold("normative", norm), equi]
    passed = not any(c.status == "fail" for c in checks)

    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(r.warnings)

    return ValidationReport(passed=passed, checks=checks, warnings=warnings)
