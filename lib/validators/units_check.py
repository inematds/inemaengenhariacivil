"""Verificação dimensional com `pint` — recomputa Md a partir das cargas."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.concrete.columns import ColumnResult
from lib.concrete.footings import FootingResult
from lib.concrete.slabs import SlabResult
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


def check_units_footing(r: FootingResult) -> Check:
    # σ_solo = (Nk + pp) / A, com unidades explícitas (kN / m² = kPa)
    sigma_q = Q_(r.nk_kn + r.pp_sapata_kn, "kilonewton") / Q_(r.area_efetiva_m2, "meter**2")
    sigma_val = ensure(sigma_q, "kilopascal")
    ref = max(abs(r.sigma_solo_kpa), 1.0)
    ok = abs(sigma_val - r.sigma_solo_kpa) <= 1e-3 * ref
    return Check(name="units", status="ok" if ok else "fail",
                 detail=f"σ_solo={sigma_val:.1f} kPa (dimensional ✓)")


def check_units_column(r: ColumnResult) -> Check:
    # ν = Nd / (Ac · fcd), adimensional (pint reduz kN/(cm²·MPa) a número puro)
    nu_q = (Q_(r.nd_kn, "kilonewton")
            / (Q_(r.b_cm * r.h_cm, "centimeter**2") * Q_(r.fcd_mpa, "megapascal")))
    nu_val = ensure(nu_q, "dimensionless")
    ref = max(abs(r.nu), 1e-3)
    ok = abs(nu_val - r.nu) <= 1e-3 * ref
    return Check(name="units", status="ok" if ok else "fail",
                 detail=f"ν={nu_val:.3f} (dimensional ✓)")


def check_units_slab(r: SlabResult) -> Check:
    # Mx = px · lx² / 8 (faixa de 1 m: px em kN/m² ≡ kN/m -> kN·m/m)
    mx_q = Q_(r.px_knm2, "kilonewton/meter") * Q_(r.lx_m, "meter") ** 2 / 8.0
    mx_val = ensure(mx_q, "kilonewton * meter")
    ref = max(abs(r.mx_knm), 1.0)
    ok = abs(mx_val - r.mx_knm) <= 1e-3 * ref
    return Check(name="units", status="ok" if ok else "fail",
                 detail=f"Mx={mx_val:.2f} kN·m/m (dimensional ✓)")
