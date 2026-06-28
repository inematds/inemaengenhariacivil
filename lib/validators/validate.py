"""Orquestrador da validação obrigatória de um dimensionamento de viga.

Todo cálculo passa por aqui antes de ser apresentado: unidades, física, normativa e
equilíbrio. Determinístico, sem LLM.
"""

from __future__ import annotations

from lib.concrete.beams import ALPHA_C, LAMBDA, BeamFlexureResult
from lib.concrete.columns import ColumnResult, column_moment_capacity
from lib.concrete.footings import FootingResult
from lib.concrete.slabs import SlabResult
from lib.validators.normative_check import (
    check_normative_beam,
    check_normative_column,
    check_normative_footing,
    check_normative_slab,
)
from lib.validators.physical_check import (
    check_physical_beam,
    check_physical_column,
    check_physical_footing,
    check_physical_slab,
)
from lib.validators.report import Check, ValidationReport
from lib.validators.units_check import (
    check_units_beam,
    check_units_column,
    check_units_footing,
    check_units_slab,
)


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


def validate_footing(r: FootingResult) -> ValidationReport:
    """Validação obrigatória de uma sapata: unidades, física e normativa (NBR 6122/6118)."""
    phys = check_physical_footing(r)
    norm = check_normative_footing(r)
    units = check_units_footing(r)

    checks = [units, _fold("physical", phys), _fold("normative", norm)]
    passed = not any(c.status == "fail" for c in checks)

    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(r.warnings)

    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def check_capacity_column(r: ColumnResult) -> Check:
    """Capacidade da seção em flexão composta ≥ solicitação (Nd, Md,tot)."""
    mrd = column_moment_capacity(r.nd_kn, r.as_adopted_cm2, r.b_cm, r.h_cm,
                                 r.d_linha_cm, r.fck_mpa, r.fyk_mpa)
    ok = mrd >= r.md_tot_knm - 1e-2 * max(abs(r.md_tot_knm), 1.0)
    return Check(name="capacidade", status="ok" if ok else "fail",
                 detail=f"MRd={mrd:.1f} ≥ Md,tot={r.md_tot_knm:.1f} kN·m (N=Nd)")


def validate_column(r: ColumnResult) -> ValidationReport:
    """Validação obrigatória de um pilar: unidades, física, normativa e capacidade."""
    phys = check_physical_column(r)
    norm = check_normative_column(r)
    units = check_units_column(r)
    cap = check_capacity_column(r)

    checks = [units, _fold("physical", phys), _fold("normative", norm), cap]
    passed = not any(c.status == "fail" for c in checks)

    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(r.warnings)

    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def validate_slab(r: SlabResult) -> ValidationReport:
    """Validação obrigatória de uma laje: unidades, física e normativa (NBR 6118)."""
    phys = check_physical_slab(r)
    norm = check_normative_slab(r)
    units = check_units_slab(r)

    checks = [units, _fold("physical", phys), _fold("normative", norm)]
    passed = not any(c.status == "fail" for c in checks)

    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(r.warnings)

    return ValidationReport(passed=passed, checks=checks, warnings=warnings)
