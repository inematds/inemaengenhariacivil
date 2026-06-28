"""Verificação normativa — limites prescritos na NBR 6118:2014 / NBR 6122."""

from __future__ import annotations

from lib.concrete.beams import X_D_DUCTIL_MAX, BeamFlexureResult
from lib.concrete.columns import AS_LAP_WARN_FRAC, LAMBDA_MAX, ColumnResult
from lib.concrete.footings import FootingResult
from lib.concrete.slabs import SlabResult
from lib.validators.report import Check


def check_normative_beam(r: BeamFlexureResult) -> list[Check]:
    checks: list[Check] = []

    ok = r.as_adopted_cm2 >= r.as_min_cm2 - 1e-6
    checks.append(Check(name="As_min", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} ≥ As_min={r.as_min_cm2:.2f} cm² "
                               "(NBR 6118 Tab.17.3)"))

    ok = r.as_adopted_cm2 <= r.as_max_cm2 + 1e-6
    checks.append(Check(name="As_max", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} ≤ As_max={r.as_max_cm2:.2f} cm² "
                               "(4% Ac, NBR 6118 17.3.5.2.4)"))

    if r.x_over_d <= X_D_DUCTIL_MAX:
        st = "ok"
    else:
        st = "warning"
    checks.append(Check(name="ductilidade", status=st,
                        detail=f"x/d={r.x_over_d:.3f} (limite dúctil {X_D_DUCTIL_MAX})"))

    return checks


def check_normative_footing(r: FootingResult) -> list[Check]:
    checks: list[Check] = []

    ok = r.sigma_solo_kpa <= r.sigma_adm_kpa + 1e-6
    checks.append(Check(name="tensao_solo", status="ok" if ok else "fail",
                        detail=f"σ_solo={r.sigma_solo_kpa:.1f} ≤ σ_adm={r.sigma_adm_kpa:.1f} kPa "
                               "(NBR 6122)"))

    checks.append(Check(name="rigidez", status="ok" if r.rigida else "fail",
                        detail=f"h={r.altura_h_cm:.0f} cm garante sapata rígida "
                               "(NBR 6118 22.6.1)" if r.rigida else
                               f"h={r.altura_h_cm:.0f} cm < (L−a)/3 (NBR 6118 22.6.1)"))

    return checks


def check_normative_column(r: ColumnResult) -> list[Check]:
    checks: list[Check] = []

    ok = r.as_adopted_cm2 >= r.as_min_cm2 - 1e-6
    checks.append(Check(name="As_min", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} ≥ As_min={r.as_min_cm2:.2f} cm² "
                               "(NBR 6118 17.3.5.3.1)"))

    ok = r.as_adopted_cm2 <= r.as_max_cm2 + 1e-6
    checks.append(Check(name="As_max", status="ok" if ok else "fail",
                        detail=f"As={r.as_adopted_cm2:.2f} ≤ As_max={r.as_max_cm2:.2f} cm² "
                               "(8% Ac, NBR 6118 17.3.5.3.4)"))

    lap = AS_LAP_WARN_FRAC * r.b_cm * r.h_cm
    st = "warning" if r.as_adopted_cm2 > lap + 1e-6 else "ok"
    checks.append(Check(name="emenda", status=st,
                        detail=f"As={r.as_adopted_cm2:.2f} vs 4%·Ac={lap:.2f} cm² "
                               "(fora de emendas)"))

    ok = r.esbeltez <= LAMBDA_MAX + 1e-9
    checks.append(Check(name="esbeltez", status="ok" if ok else "fail",
                        detail=f"λ={r.esbeltez:.1f} ≤ {LAMBDA_MAX:.0f} ({r.classe})"))

    return checks


def check_normative_slab(r: SlabResult) -> list[Check]:
    checks: list[Check] = []

    ok = r.as_x_cm2_m >= r.as_min_x_cm2_m - 1e-6
    checks.append(Check(name="As_min_x", status="ok" if ok else "fail",
                        detail=f"As_x={r.as_x_cm2_m:.2f} ≥ As_min={r.as_min_x_cm2_m:.2f} "
                               "cm²/m (NBR 6118 Tab.19.1)"))

    ok = r.as_y_cm2_m >= r.as_min_y_cm2_m - 1e-6
    checks.append(Check(name="As_min_y", status="ok" if ok else "fail",
                        detail=f"As_y={r.as_y_cm2_m:.2f} ≥ As_min={r.as_min_y_cm2_m:.2f} "
                               "cm²/m (NBR 6118 Tab.19.1)"))

    ok = r.h_cm >= r.h_min_cm - 1e-9
    st = "ok" if ok else "warning"
    checks.append(Check(name="h_min", status=st,
                        detail=f"h={r.h_cm:.1f} ≥ h_min={r.h_min_cm:.1f} cm "
                               "(NBR 6118 13.2.4.1)"))

    xods = [r.x_over_d_x] + ([r.x_over_d_y] if r.x_over_d_y is not None else [])
    st = "ok" if all(v <= X_D_DUCTIL_MAX for v in xods) else "warning"
    checks.append(Check(name="ductilidade", status=st,
                        detail=f"x/d={', '.join(f'{v:.3f}' for v in xods)} "
                               f"(limite dúctil {X_D_DUCTIL_MAX})"))

    return checks
