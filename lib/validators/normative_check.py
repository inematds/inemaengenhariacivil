"""Verificação normativa — limites prescritos na NBR 6118:2014."""

from __future__ import annotations

from lib.concrete.beams import X_D_DUCTIL_MAX, BeamFlexureResult
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
