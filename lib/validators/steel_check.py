"""Validação obrigatória do domínio de AÇO — barras comprimidas (NBR 8800:2008).

Validador próprio da Fase 5 (não toca nos validadores compartilhados). Cada
resultado passa por unidades (pint), física (faixas razoáveis) e normativa
(consistência / limites) antes de ser apresentado. Determinístico, sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report`
(estável) e ``Q_``/``ensure`` de :mod:`lib.units.registry`.
"""

from __future__ import annotations

import math

from lib.steel.stability import FY_MAX_MPA, FY_MIN_MPA, CompressionResult
from lib.units.registry import Q_, ensure
from lib.validators.report import Check, ValidationReport

LAMBDA0_WARN = 3.0   # acima disso a barra é considerada muito esbelta
TOL = 1e-3           # tolerância relativa das reconstruções dimensionais


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


def _assemble(
    units: Check, phys: list[Check], norm: list[Check], extra_warnings: list[str]
) -> ValidationReport:
    checks = [units, _fold("physical", phys), _fold("normative", norm)]
    passed = not any(c.status == "fail" for c in checks)
    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(extra_warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def validate_compression(r: CompressionResult) -> ValidationReport:
    """Valida barra comprimida (NBR 8800:2008 §5.3): unidades, física, normativa.

    - unidades: reconstrói ``Ne = π²·E·I/(KL)²`` com pint e confere a dimensão (kN).
    - física: ``fy ∈ [250, 450]`` MPa (aços estruturais comuns); ``λ0 > 0``
      (alerta se ``λ0 > 3``, barra muito esbelta); ``Nc,Rd > 0``.
    - normativa: ``χ`` na faixa (0, 1]; consistência ``Nc,Rd = χ·Q·A·fy/γa1``.
    """
    if not isinstance(r, CompressionResult):
        raise TypeError(f"Tipo não suportado: {type(r).__name__}")

    # --- unidades: Ne dimensional (megapascal·cm⁴/cm² -> kilonewton) ---------
    ne_q = (
        math.pi**2
        * Q_(r.e_mpa, "megapascal")
        * Q_(r.i_cm4, "centimeter**4")
        / Q_(r.kl_cm, "centimeter") ** 2
    )
    ne_val = ensure(ne_q, "kilonewton")
    ref = max(abs(r.ne_kn), 1.0)
    ok = abs(ne_val - r.ne_kn) <= TOL * ref
    units = Check(
        name="units",
        status="ok" if ok else "fail",
        detail=f"Ne={ne_val:.1f} kN (dimensional ✓)",
    )

    # --- física -------------------------------------------------------------
    phys: list[Check] = []
    ok = FY_MIN_MPA <= r.fy_mpa <= FY_MAX_MPA
    phys.append(
        Check(
            name="fy",
            status="ok" if ok else "fail",
            detail=f"fy={r.fy_mpa:.0f} MPa (faixa {FY_MIN_MPA:.0f}–{FY_MAX_MPA:.0f})",
        )
    )
    if r.lambda_0 <= 0:
        phys.append(Check(name="lambda0", status="fail",
                          detail=f"λ0={r.lambda_0:.3f} (deve ser > 0)"))
    elif r.lambda_0 > LAMBDA0_WARN:
        phys.append(Check(name="lambda0", status="warning",
                          detail=f"λ0={r.lambda_0:.2f} > {LAMBDA0_WARN:.0f} "
                                 "(barra muito esbelta)"))
    else:
        phys.append(Check(name="lambda0", status="ok",
                          detail=f"λ0={r.lambda_0:.3f} (> 0)"))
    ok = r.nc_rd_kn > 0 and r.ne_kn > 0 and r.area_cm2 > 0 and r.kl_cm > 0
    phys.append(
        Check(
            name="resistencias",
            status="ok" if ok else "fail",
            detail=f"Nc,Rd={r.nc_rd_kn:.1f} kN Ne={r.ne_kn:.1f} kN",
        )
    )

    # --- normativa ----------------------------------------------------------
    norm: list[Check] = []
    ok = 0.0 < r.chi <= 1.0 + 1e-9
    norm.append(
        Check(
            name="chi_faixa",
            status="ok" if ok else "fail",
            detail=f"χ={r.chi:.4f} (0 < χ ≤ 1)",
        )
    )
    n_pl_kn = r.q * r.area_cm2 * (r.fy_mpa * 0.1)            # Q·A·fy em kN
    nc_rd_ref = r.chi * n_pl_kn / r.gamma_a1
    ok = abs(nc_rd_ref - r.nc_rd_kn) <= TOL * max(abs(r.nc_rd_kn), 1.0)
    norm.append(
        Check(
            name="NcRd_consistencia",
            status="ok" if ok else "fail",
            detail=f"χ·Q·A·fy/γa1={nc_rd_ref:.1f} ≈ Nc,Rd={r.nc_rd_kn:.1f} kN",
        )
    )

    return _assemble(units, phys, norm, r.warnings)
