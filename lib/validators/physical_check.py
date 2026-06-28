"""Verificação física — limites razoáveis de cada grandeza."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.validators.report import Check

X_D_DOMAIN_MAX = 0.628   # limite domínio 3/4 (acima => ruptura frágil)


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
