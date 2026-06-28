"""Validação obrigatória de ESTABILIDADE DE TALUDES.

Arquivo próprio do domínio (não toca nos validadores compartilhados). Cada cálculo
passa por unidades (pint), física (faixas razoáveis) e normativa (FS,mín ≈ 1,5,
NBR 11682) antes de ser apresentado. Determinístico, sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report`
(estável), ``Q_``/``ensure`` de :mod:`lib.units.registry` e as constantes/modelos
do próprio módulo :mod:`lib.geotechnical.slope_stability`.
"""

from __future__ import annotations

import math

from lib.geotechnical.slope_stability import (
    C_MIN,
    FS_SLOPE_MIN,
    GAMMA_MAX,
    GAMMA_MIN,
    PHI_MAX,
    PHI_MIN,
    FelleniusResult,
    InfiniteSlopeResult,
)
from lib.units.registry import Q_, ensure
from lib.validators.report import Check, ValidationReport

TOL = 1e-3  # tolerância relativa das reconstruções


def _fold(name: str, subs: list[Check]) -> Check:
    """Resume uma lista de checagens em uma só (fail > warning > ok)."""
    status = "ok"
    for c in subs:
        if c.status == "fail":
            status = "fail"
            break
        if c.status == "warning":
            status = "warning"
    detail = "; ".join(f"{c.name}={c.status}" for c in subs)
    return Check(name=name, status=status, detail=detail)


def _assemble(units: Check, phys: list[Check], norm: list[Check],
              extra_warnings: list[str]) -> ValidationReport:
    checks = [units, _fold("physical", phys), _fold("normative", norm)]
    passed = not any(c.status == "fail" for c in checks)
    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(extra_warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def _normative_fs(fs: float) -> Check:
    """Alerta/falha normativa pelo FS (FS,mín usual ≈ 1,5, NBR 11682)."""
    if fs < 1.0:
        st = "fail"
    elif fs < FS_SLOPE_MIN:
        st = "warning"
    else:
        st = "ok"
    return Check(name="FS_minimo", status=st,
                 detail=f"FS={fs:.3f} (mínimo usual ≥ {FS_SLOPE_MIN:.1f}, NBR 11682)")


def _validate_infinite(r: InfiniteSlopeResult) -> ValidationReport:
    # unidades: reconstrói num/den em kPa e o FS adimensional via pint
    beta = math.radians(r.beta_deg)
    phi = math.radians(r.phi_deg)
    sigma_q = (Q_(r.gamma_kn_m3, "kilonewton/meter**3") * Q_(r.z_m, "meter")
               * math.cos(beta) ** 2)
    num_q = Q_(r.c_kpa, "kilopascal") + (sigma_q - Q_(r.u_kpa, "kilopascal")) * math.tan(phi)
    den_q = (Q_(r.gamma_kn_m3, "kilonewton/meter**3") * Q_(r.z_m, "meter")
             * math.sin(beta) * math.cos(beta))
    num_val = ensure(num_q, "kilopascal")
    den_val = ensure(den_q, "kilopascal")
    fs_val = num_val / den_val
    ok = abs(fs_val - r.fs) <= TOL * max(abs(r.fs), 1.0)
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"FS={fs_val:.3f} (num/den em kPa, dimensional ✓)")

    phys: list[Check] = []
    ok = PHI_MIN <= r.phi_deg <= PHI_MAX
    phys.append(Check(name="phi", status="ok" if ok else "fail",
                      detail=f"φ={r.phi_deg:.1f}° (faixa {PHI_MIN:.0f}–{PHI_MAX:.0f})"))
    ok = GAMMA_MIN <= r.gamma_kn_m3 <= GAMMA_MAX
    phys.append(Check(name="gamma", status="ok" if ok else "fail",
                      detail=f"γ={r.gamma_kn_m3:.1f} kN/m³ "
                             f"(faixa {GAMMA_MIN:.0f}–{GAMMA_MAX:.0f})"))
    ok = r.c_kpa >= C_MIN
    phys.append(Check(name="coesao", status="ok" if ok else "fail",
                      detail=f"c={r.c_kpa:.1f} kPa (≥0)"))
    ok = 0.0 < r.beta_deg < 90.0 and r.z_m > 0.0 and r.u_kpa >= 0.0
    phys.append(Check(name="geometria", status="ok" if ok else "fail",
                      detail=f"β={r.beta_deg:.1f}° (0–90) z={r.z_m:.2f} m "
                             f"u={r.u_kpa:.1f} kPa"))
    ok = r.fs > 0.0 and r.driving_kpa > 0.0
    phys.append(Check(name="FS_positivo", status="ok" if ok else "fail",
                      detail=f"FS={r.fs:.3f} (>0) τ_atuante={r.driving_kpa:.2f} kPa"))

    norm: list[Check] = []
    norm.append(Check(name="classificacao", status="ok",
                      detail=f"FS={r.fs:.3f} -> {r.classification}"))
    norm.append(_normative_fs(r.fs))
    return _assemble(units, phys, norm, r.warnings)


def _validate_fellenius(r: FelleniusResult) -> ValidationReport:
    # unidades: c·ΔL (1 m) deve ter dimensão de força/comprimento (kN/m); FS = res/drv
    cdl_q = Q_(r.c_kpa, "kilopascal") * Q_(1.0, "meter")
    cdl_val = ensure(cdl_q, "kilonewton/meter")
    fs_val = r.resisting_kn_m / r.driving_kn_m
    ok = abs(fs_val - r.fs) <= TOL * max(abs(r.fs), 1.0) and cdl_val >= 0.0
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"FS=res/drv={fs_val:.3f} (c·ΔL em kN/m, dimensional ✓)")

    phys: list[Check] = []
    ok = PHI_MIN <= r.phi_deg <= PHI_MAX
    phys.append(Check(name="phi", status="ok" if ok else "fail",
                      detail=f"φ={r.phi_deg:.1f}° (faixa {PHI_MIN:.0f}–{PHI_MAX:.0f})"))
    ok = r.c_kpa >= C_MIN
    phys.append(Check(name="coesao", status="ok" if ok else "fail",
                      detail=f"c={r.c_kpa:.1f} kPa (≥0)"))
    ok = r.n_slices >= 1 and r.driving_kn_m > 0.0
    phys.append(Check(name="geometria", status="ok" if ok else "fail",
                      detail=f"n_fatias={r.n_slices} Σatuante={r.driving_kn_m:.2f} kN/m"))
    ok = r.fs > 0.0
    phys.append(Check(name="FS_positivo", status="ok" if ok else "fail",
                      detail=f"FS={r.fs:.3f} (>0)"))

    norm: list[Check] = []
    norm.append(Check(name="classificacao", status="ok",
                      detail=f"FS={r.fs:.3f} -> {r.classification}"))
    norm.append(_normative_fs(r.fs))
    return _assemble(units, phys, norm, r.warnings)


def validate_slope(
    r: InfiniteSlopeResult | FelleniusResult,
) -> ValidationReport:
    """Valida estabilidade de talude (talude infinito ou Fellenius).

    Despacha pelo tipo do resultado: unidades (pint), física (faixas) e normativa
    (FS,mín ≈ 1,5, NBR 11682).
    """
    if isinstance(r, InfiniteSlopeResult):
        return _validate_infinite(r)
    if isinstance(r, FelleniusResult):
        return _validate_fellenius(r)
    raise TypeError(f"Tipo de resultado de talude não suportado: {type(r).__name__}")
