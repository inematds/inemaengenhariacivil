"""Validação obrigatória do domínio de PAVIMENTAÇÃO (pavimento flexível DNER/DNIT).

Validador próprio do domínio (não toca nos validadores compartilhados). Cada
cálculo passa por reconstrução (unidades/fórmula), física (faixas razoáveis) e
normativa (inequações de equivalência estrutural) antes de ser apresentado.
Determinístico, sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report`.
"""

from __future__ import annotations

from lib.pavement.flexible import (
    CBR_MAX,
    CBR_MIN,
    MIN_BASE_CM,
    MIN_REFORCO_CM,
    MIN_SUBBASE_CM,
    N_MAX,
    N_MIN,
    PavementResult,
    espessura_total,
)
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


def validate_pavement(r: PavementResult) -> ValidationReport:
    """Valida o dimensionamento de pavimento flexível (DNER/DNIT)."""
    if not isinstance(r, PavementResult):
        raise TypeError(f"Tipo não suportado: {type(r).__name__}")

    # --- unidades / reconstrução: Hm = 77,67·N^0,0482·CBR^-0,598 -------------
    cbr_ok = CBR_MIN <= r.cbr_subleito <= CBR_MAX
    n_ok = N_MIN <= r.n_trafego <= N_MAX
    if cbr_ok and n_ok:
        hm_rec = espessura_total(r.cbr_subleito, r.n_trafego)
        ref = max(abs(r.hm_cm), 1.0)
        ok = abs(hm_rec - r.hm_cm) <= TOL * ref
        units = Check(name="units", status="ok" if ok else "fail",
                      detail=f"Hm={hm_rec:.2f} cm (reconstrução da equação DNER ✓)")
    else:
        # entradas fora de faixa: não há reconstrução confiável
        units = Check(name="units", status="fail",
                      detail="entradas fora de faixa: reconstrução não aplicável")

    # --- física --------------------------------------------------------------
    phys: list[Check] = []
    phys.append(Check(name="cbr_subleito", status="ok" if cbr_ok else "fail",
                      detail=f"CBR={r.cbr_subleito:.1f}% "
                             f"(faixa {CBR_MIN:.0f}–{CBR_MAX:.0f})"))
    phys.append(Check(name="numero_N", status="ok" if n_ok else "fail",
                      detail=f"N={r.n_trafego:.3g} "
                             f"(faixa {N_MIN:.0g}–{N_MAX:.0g})"))
    if r.cbr_reforco is not None:
        ok = CBR_MIN <= r.cbr_reforco <= CBR_MAX
        phys.append(Check(name="cbr_reforco", status="ok" if ok else "fail",
                          detail=f"CBR_reforço={r.cbr_reforco:.1f}%"))
    ok = (r.r_cm > 0 and r.b_cm >= MIN_BASE_CM and r.s_cm >= MIN_SUBBASE_CM
          and (r.reforco_cm is None or r.reforco_cm >= MIN_REFORCO_CM))
    phys.append(Check(name="espessuras_minimas", status="ok" if ok else "fail",
                      detail=f"R={r.r_cm:.1f} B={r.b_cm:.1f} S={r.s_cm:.1f} cm "
                             f"(min B/S={MIN_BASE_CM:.0f}/{MIN_SUBBASE_CM:.0f})"))
    ok = all(k > 0 for k in (r.k_rev, r.k_base, r.k_subbase, r.k_reforco))
    phys.append(Check(name="coeficientes_K", status="ok" if ok else "fail",
                      detail=f"K_R={r.k_rev} K_B={r.k_base} K_S={r.k_subbase}"))
    ok = abs((r.r_cm + r.b_cm + r.s_cm + (r.reforco_cm or 0.0))
             - r.espessura_total_cm) <= TOL * max(r.espessura_total_cm, 1.0)
    phys.append(Check(name="soma_espessuras", status="ok" if ok else "fail",
                      detail=f"H_total={r.espessura_total_cm:.1f} cm (= Σ camadas)"))

    # --- normativa: inequações de equivalência estrutural (recomputadas) -----
    norm: list[Check] = []
    lhs1 = r.r_cm * r.k_rev + r.b_cm * r.k_base
    ok = lhs1 + TOL >= r.h20_cm
    norm.append(Check(name="sobre_subbase", status="ok" if ok else "fail",
                      detail=f"R·K_R+B·K_B={lhs1:.1f} ≥ H20={r.h20_cm:.1f} cm"))
    lhs2 = lhs1 + r.s_cm * r.k_subbase
    if r.cbr_reforco is not None and r.hn_cm is not None:
        ok = lhs2 + TOL >= r.hn_cm
        norm.append(Check(name="sobre_reforco", status="ok" if ok else "fail",
                          detail=f"+S·K_S={lhs2:.1f} ≥ Hn={r.hn_cm:.1f} cm"))
        lhs3 = lhs2 + (r.reforco_cm or 0.0) * r.k_reforco
        ok = lhs3 + TOL >= r.hm_cm
        norm.append(Check(name="sobre_subleito", status="ok" if ok else "fail",
                          detail=f"+Ref·K_ref={lhs3:.1f} ≥ Hm={r.hm_cm:.1f} cm"))
    else:
        ok = lhs2 + TOL >= r.hm_cm
        norm.append(Check(name="sobre_subleito", status="ok" if ok else "fail",
                          detail=f"+S·K_S={lhs2:.1f} ≥ Hm={r.hm_cm:.1f} cm"))
    st = "ok" if r.r_cm + TOL >= r.r_min_cm else "warning"
    norm.append(Check(name="revestimento_minimo", status=st,
                      detail=f"R={r.r_cm:.1f} cm (mín. DNER {r.r_min_cm:.1f} cm)"))

    return _assemble(units, phys, norm, r.warnings)
