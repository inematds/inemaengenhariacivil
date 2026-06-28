"""Verificação física — limites razoáveis de cada grandeza."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.concrete.columns import LAMBDA_MAX, ColumnResult
from lib.concrete.footings import (
    SIGMA_ADM_MAX,
    SIGMA_ADM_MIN,
    FootingResult,
)
from lib.concrete.slabs import SlabResult
from lib.validators.report import Check

X_D_DOMAIN_MAX = 0.628   # limite domínio 3/4 (acima => ruptura frágil)
NU_PHYS_MAX = 2.0        # ν fisicamente plausível para pilar


def check_physical_beam(r: BeamFlexureResult) -> list[Check]:
    checks: list[Check] = []

    ok = 10.0 <= r.fck_mpa <= 100.0
    checks.append(Check(name="fck", status="ok" if ok else "fail",
                        detail=f"fck={r.fck_mpa:.0f} MPa (faixa 10–100)"))

    ok = 250.0 <= r.fyk_mpa <= 600.0
    checks.append(Check(name="fyk", status="ok" if ok else "fail",
                        detail=f"fyk={r.fyk_mpa:.0f} MPa (faixa 250–600)"))

    ok = r.b_cm > 0 and r.h_cm > 0 and 0 < r.d_cm < r.h_cm
    checks.append(Check(name="geometria", status="ok" if ok else "fail",
                        detail=f"b={r.b_cm:.0f} h={r.h_cm:.0f} d={r.d_cm:.1f} cm"))

    ok = r.as_adopted_cm2 > 0
    checks.append(Check(name="As_positivo", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} cm²"))

    if r.x_over_d > X_D_DOMAIN_MAX:
        st = "fail"
    elif r.x_over_d < 0:
        st = "fail"
    else:
        st = "ok"
    checks.append(Check(name="dominio", status=st,
                        detail=f"x/d={r.x_over_d:.3f} (limite {X_D_DOMAIN_MAX})"))

    return checks


def check_physical_footing(r: FootingResult) -> list[Check]:
    checks: list[Check] = []

    ok = SIGMA_ADM_MIN <= r.sigma_adm_kpa <= SIGMA_ADM_MAX
    checks.append(Check(name="sigma_adm", status="ok" if ok else "fail",
                        detail=f"σ_adm={r.sigma_adm_kpa:.0f} kPa "
                               f"(faixa {SIGMA_ADM_MIN:.0f}–{SIGMA_ADM_MAX:.0f})"))

    ok = (10.0 <= r.fck_mpa <= 100.0) and (250.0 <= r.fyk_mpa <= 600.0)
    checks.append(Check(name="materiais", status="ok" if ok else "fail",
                        detail=f"fck={r.fck_mpa:.0f} MPa, fyk={r.fyk_mpa:.0f} MPa"))

    ok = (r.lado_cm > 0 and r.altura_h_cm > 0 and 0 < r.d_cm < r.altura_h_cm
          and r.lado_cm >= max(r.pilar_a_cm, r.pilar_b_cm))
    checks.append(Check(name="geometria", status="ok" if ok else "fail",
                        detail=f"L={r.lado_cm:.0f} h={r.altura_h_cm:.0f} d={r.d_cm:.1f} cm "
                               f"(pilar {r.pilar_a_cm:.0f}x{r.pilar_b_cm:.0f})"))

    ok = r.as_x_cm2 > 0 and r.as_y_cm2 > 0
    checks.append(Check(name="As_positivo", status="ok" if ok else "fail",
                        detail=f"As_x={r.as_x_cm2:.2f} As_y={r.as_y_cm2:.2f} cm²"))

    return checks


def check_physical_column(r: ColumnResult) -> list[Check]:
    checks: list[Check] = []

    ok = (10.0 <= r.fck_mpa <= 100.0) and (250.0 <= r.fyk_mpa <= 600.0)
    checks.append(Check(name="materiais", status="ok" if ok else "fail",
                        detail=f"fck={r.fck_mpa:.0f} MPa, fyk={r.fyk_mpa:.0f} MPa"))

    ok = r.b_cm > 0 and r.h_cm > 0 and 0 < r.d_linha_cm < r.h_cm / 2.0
    checks.append(Check(name="geometria", status="ok" if ok else "fail",
                        detail=f"b={r.b_cm:.0f} h={r.h_cm:.0f} d'={r.d_linha_cm:.1f} cm"))

    ok = r.as_adopted_cm2 > 0
    checks.append(Check(name="As_positivo", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} cm²"))

    ok = 0.0 < r.nu < NU_PHYS_MAX
    checks.append(Check(name="nu", status="ok" if ok else "fail",
                        detail=f"ν={r.nu:.3f} (faixa 0–{NU_PHYS_MAX:.1f})"))

    ok = 0.0 <= r.esbeltez <= LAMBDA_MAX
    checks.append(Check(name="esbeltez", status="ok" if ok else "fail",
                        detail=f"λ={r.esbeltez:.1f} ≤ {LAMBDA_MAX:.0f} ({r.classe})"))

    return checks


def check_physical_slab(r: SlabResult) -> list[Check]:
    checks: list[Check] = []

    ok = (10.0 <= r.fck_mpa <= 100.0) and (250.0 <= r.fyk_mpa <= 600.0)
    checks.append(Check(name="materiais", status="ok" if ok else "fail",
                        detail=f"fck={r.fck_mpa:.0f} MPa, fyk={r.fyk_mpa:.0f} MPa"))

    ok = r.h_cm > 0 and 0 < r.d_cm < r.h_cm and r.lx_m > 0
    checks.append(Check(name="geometria", status="ok" if ok else "fail",
                        detail=f"h={r.h_cm:.1f} d={r.d_cm:.1f} cm, lx={r.lx_m:.2f} m"))

    ok = r.as_x_cm2_m > 0 and r.as_y_cm2_m > 0
    checks.append(Check(name="As_positivo", status="ok" if ok else "fail",
                        detail=f"As_x={r.as_x_cm2_m:.2f} As_y={r.as_y_cm2_m:.2f} cm²/m"))

    xods = [r.x_over_d_x] + ([r.x_over_d_y] if r.x_over_d_y is not None else [])
    ok = all(0.0 <= v <= X_D_DOMAIN_MAX for v in xods)
    checks.append(Check(name="dominio", status="ok" if ok else "fail",
                        detail=f"x/d={', '.join(f'{v:.3f}' for v in xods)} "
                               f"(limite {X_D_DOMAIN_MAX})"))

    return checks
