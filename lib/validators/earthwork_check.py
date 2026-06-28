"""Validação obrigatória do domínio de TERRAPLENAGEM (balanço corte/aterro).

Validador próprio do domínio (não toca nos validadores compartilhados). Cada
cálculo passa por unidades (pint), física (faixas razoáveis) e normativa
(consistência do balanço) antes de ser apresentado. Determinístico, sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report`
e ``Q_``/``ensure`` de :mod:`lib.units.registry`.
"""

from __future__ import annotations

from lib.earthwork.volumes import FE_MAX, FE_MIN, EarthworkResult
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


def validate_earthwork(r: EarthworkResult) -> ValidationReport:
    """Valida o balanço de terraplenagem (unidades, física, normativa)."""
    if not isinstance(r, EarthworkResult):
        raise TypeError(f"Tipo não suportado: {type(r).__name__}")

    # --- unidades: volume solto = corte·Fe -> m³ (dimensional) ---------------
    solto_q = Q_(r.volume_corte_m3, "meter**3") * r.fator_empolamento
    solto_val = ensure(solto_q, "meter**3")
    ref = max(abs(r.volume_corte_solto_m3), 1.0)
    ok = abs(solto_val - r.volume_corte_solto_m3) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"V_solto={solto_val:.1f} m³ (dimensional ✓)")

    # --- física --------------------------------------------------------------
    phys: list[Check] = []
    ok = r.volume_corte_m3 >= 0 and r.volume_aterro_m3 >= 0
    phys.append(Check(name="volumes_positivos", status="ok" if ok else "fail",
                      detail=f"corte={r.volume_corte_m3:.1f} "
                             f"aterro={r.volume_aterro_m3:.1f} m³ (≥0)"))
    ok = FE_MIN <= r.fator_empolamento <= FE_MAX
    phys.append(Check(name="empolamento", status="ok" if ok else "fail",
                      detail=f"Fe={r.fator_empolamento:.2f} "
                             f"(faixa {FE_MIN:.1f}–{FE_MAX:.1f})"))
    ok = r.volume_emprestimo_m3 >= 0 and r.volume_bota_fora_m3 >= 0
    phys.append(Check(name="movimentos_positivos", status="ok" if ok else "fail",
                      detail=f"empréstimo={r.volume_emprestimo_m3:.1f} "
                             f"bota-fora={r.volume_bota_fora_m3:.1f} m³ (≥0)"))

    # --- normativa: consistência do balanço ----------------------------------
    norm: list[Check] = []
    balanco_rec = r.volume_corte_m3 - r.volume_aterro_m3
    ok = abs(balanco_rec - r.balanco_m3) <= TOL * max(abs(r.balanco_m3), 1.0)
    norm.append(Check(name="balanco_consistencia", status="ok" if ok else "fail",
                      detail=f"corte−aterro={balanco_rec:.1f} ≈ "
                             f"balanço={r.balanco_m3:.1f} m³"))
    esperado = ("excesso" if balanco_rec > 1e-9 else
                "deficit" if balanco_rec < -1e-9 else "equilibrio")
    ok = r.situacao == esperado
    norm.append(Check(name="situacao_consistente", status="ok" if ok else "fail",
                      detail=f"situação={r.situacao} (esperado {esperado})"))
    ok = (abs(r.volume_bota_fora_m3 - max(balanco_rec, 0.0)) <= TOL * ref
          and abs(r.volume_emprestimo_m3 - max(-balanco_rec, 0.0)) <= TOL * ref)
    norm.append(Check(name="bota_fora_emprestimo", status="ok" if ok else "fail",
                      detail=f"bota-fora={r.volume_bota_fora_m3:.1f} "
                             f"empréstimo={r.volume_emprestimo_m3:.1f} m³"))

    return _assemble(units, phys, norm, r.warnings)
