"""Validação obrigatória do domínio de GEOTECNIA.

Arquivo próprio do domínio (não toca nos validadores compartilhados). Cada cálculo
passa por unidades (pint), física (faixas razoáveis) e normativa (consistência /
limites) antes de ser apresentado. Determinístico, sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report`
(estável) e ``Q_``/``ensure`` de :mod:`lib.units.registry`.
"""

from __future__ import annotations

import math

from lib.geotechnical.bearing_capacity import (
    GAMMA_MAX,
    GAMMA_MIN,
    PHI_MAX,
    PHI_MIN,
    BearingCapacityResult,
)
from lib.geotechnical.earth_pressure import (
    CoulombEarthPressureResult,
    RankineEarthPressureResult,
)
from lib.geotechnical.piles import (
    N_SPT_MAX,
    N_SPT_MIN,
    PileCapacityResult,
)
from lib.geotechnical.settlement import (
    E0_MAX,
    E0_MIN,
    NU_MAX,
    NU_MIN,
    ConsolidationSettlementResult,
    ElasticSettlementResult,
)
from lib.units.registry import Q_, ensure
from lib.validators.report import Check, ValidationReport

# faixas físicas adicionais
C_MIN = 0.0                 # coesão ≥ 0
FS_BEARING_MIN = 3.0        # FS analítico usual de fundação rasa (NBR 6122)
FS_PILE_MIN = 2.0           # FS global usual de estaca (NBR 6122)
SETTLEMENT_WARN_MM = 25.0   # recalque que costuma exigir atenção (NBR 6122)
TOL = 1e-3                  # tolerância relativa das reconstruções


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


# --- capacidade de carga (Vesic) --------------------------------------------
def validate_bearing(r: BearingCapacityResult) -> ValidationReport:
    """Valida capacidade de carga de fundação rasa (unidades, física, normativa)."""
    # unidades: reconstrói q_ult = c·Nc·sc + q·Nq·sq + 0,5·γ·B·Nγ·sγ (kPa)
    term_c = Q_(r.c_kpa, "kilopascal") * r.nc * r.sc
    term_q = Q_(r.q_surcharge_kpa, "kilopascal") * r.nq * r.sq
    term_g = (0.5 * Q_(r.gamma_kn_m3, "kilonewton/meter**3")
              * Q_(r.b_m, "meter") * r.ngamma * r.sgamma)
    q_ult_val = ensure(term_c + term_q + term_g, "kilopascal")
    ref = max(abs(r.q_ult_kpa), 1.0)
    ok = abs(q_ult_val - r.q_ult_kpa) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"q_ult={q_ult_val:.1f} kPa (dimensional ✓)")

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
    ok = r.b_m > 0 and r.depth_df_m >= 0 and r.q_ult_kpa > 0 and r.q_adm_kpa > 0
    phys.append(Check(name="geometria", status="ok" if ok else "fail",
                      detail=f"B={r.b_m:.2f} m Df={r.depth_df_m:.2f} m "
                             f"q_adm={r.q_adm_kpa:.1f} kPa"))

    norm: list[Check] = []
    ok = abs(r.q_adm_kpa * r.fs - r.q_ult_kpa) <= TOL * ref
    norm.append(Check(name="FS_consistencia", status="ok" if ok else "fail",
                      detail=f"q_adm·FS={r.q_adm_kpa * r.fs:.1f} ≈ q_ult={r.q_ult_kpa:.1f} kPa"))
    st = "ok" if r.fs >= FS_BEARING_MIN - 1e-9 else "warning"
    norm.append(Check(name="FS_minimo", status=st,
                      detail=f"FS={r.fs:.1f} (recomendado ≥ {FS_BEARING_MIN:.0f}, NBR 6122)"))

    return _assemble(units, phys, norm, r.warnings)


# --- recalques --------------------------------------------------------------
def _validate_elastic(r: ElasticSettlementResult) -> ValidationReport:
    s_q = (Q_(r.q_kpa, "kilopascal") * Q_(r.b_m, "meter")
           * (1.0 - r.poisson_nu**2) * r.iw / Q_(r.es_kpa, "kilopascal"))
    s_val = ensure(s_q, "meter")
    ref = max(abs(r.settlement_m), 1e-6)
    ok = abs(s_val - r.settlement_m) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"s={s_val * 1000.0:.2f} mm (dimensional ✓)")

    phys: list[Check] = []
    ok = NU_MIN <= r.poisson_nu <= NU_MAX
    phys.append(Check(name="poisson", status="ok" if ok else "fail",
                      detail=f"ν={r.poisson_nu:.2f} (faixa {NU_MIN}–{NU_MAX})"))
    ok = r.es_kpa > 0 and r.q_kpa > 0 and r.b_m > 0 and r.iw > 0
    phys.append(Check(name="parametros", status="ok" if ok else "fail",
                      detail=f"Es={r.es_kpa:.0f} kPa q={r.q_kpa:.0f} kPa B={r.b_m:.2f} m"))
    ok = r.settlement_m >= 0
    phys.append(Check(name="recalque_positivo", status="ok" if ok else "fail",
                      detail=f"s={r.settlement_mm:.2f} mm (≥0)"))

    norm: list[Check] = []
    st = "ok" if r.settlement_mm <= SETTLEMENT_WARN_MM else "warning"
    norm.append(Check(name="recalque_admissivel", status=st,
                      detail=f"s={r.settlement_mm:.1f} mm "
                             f"(referência {SETTLEMENT_WARN_MM:.0f} mm, NBR 6122 ELS)"))
    return _assemble(units, phys, norm, r.warnings)


def _validate_consolidation(r: ConsolidationSettlementResult) -> ValidationReport:
    factor = (r.cc / (1.0 + r.e0)) * math.log10(
        (r.sigma0_kpa + r.delta_sigma_kpa) / r.sigma0_kpa)
    s_val = ensure(Q_(r.h_m, "meter") * factor, "meter")
    ref = max(abs(r.settlement_m), 1e-6)
    ok = abs(s_val - r.settlement_m) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"s={s_val * 1000.0:.2f} mm (dimensional ✓)")

    phys: list[Check] = []
    ok = E0_MIN <= r.e0 <= E0_MAX
    phys.append(Check(name="e0", status="ok" if ok else "fail",
                      detail=f"e0={r.e0:.2f} (faixa {E0_MIN}–{E0_MAX})"))
    ok = r.cc > 0 and r.sigma0_kpa > 0 and r.delta_sigma_kpa >= 0 and r.h_m > 0
    phys.append(Check(name="parametros", status="ok" if ok else "fail",
                      detail=f"Cc={r.cc:.2f} σ0={r.sigma0_kpa:.0f} "
                             f"Δσ={r.delta_sigma_kpa:.0f} kPa H={r.h_m:.2f} m"))
    ok = r.settlement_m >= 0
    phys.append(Check(name="recalque_positivo", status="ok" if ok else "fail",
                      detail=f"s={r.settlement_mm:.2f} mm (≥0)"))

    norm: list[Check] = []
    st = "ok" if r.settlement_mm <= SETTLEMENT_WARN_MM else "warning"
    norm.append(Check(name="recalque_admissivel", status=st,
                      detail=f"s={r.settlement_mm:.1f} mm "
                             f"(referência {SETTLEMENT_WARN_MM:.0f} mm, NBR 6122 ELS)"))
    return _assemble(units, phys, norm, r.warnings)


def validate_settlement(
    r: ElasticSettlementResult | ConsolidationSettlementResult,
) -> ValidationReport:
    """Valida recalque elástico ou por adensamento (despacha pelo tipo do resultado)."""
    if isinstance(r, ElasticSettlementResult):
        return _validate_elastic(r)
    if isinstance(r, ConsolidationSettlementResult):
        return _validate_consolidation(r)
    raise TypeError(f"Tipo de recalque não suportado: {type(r).__name__}")


# --- empuxo de terra --------------------------------------------------------
def validate_earth_pressure(
    r: RankineEarthPressureResult | CoulombEarthPressureResult,
) -> ValidationReport:
    """Valida empuxo de terra (Rankine ou Coulomb): unidades, física, normativa."""
    if not isinstance(r, (RankineEarthPressureResult, CoulombEarthPressureResult)):
        raise TypeError(f"Tipo de empuxo não suportado: {type(r).__name__}")

    # unidades: E = 0,5·γ·H²·Ka -> kN/m
    ea_q = 0.5 * Q_(r.gamma_kn_m3, "kilonewton/meter**3") * Q_(r.h_m, "meter") ** 2 * r.ka
    ea_val = ensure(ea_q, "kilonewton/meter")
    ref = max(abs(r.ea_active_kn_m), 1.0)
    ok = abs(ea_val - r.ea_active_kn_m) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"Ea={ea_val:.2f} kN/m (dimensional ✓)")

    phys: list[Check] = []
    ok = PHI_MIN <= r.phi_deg <= PHI_MAX
    phys.append(Check(name="phi", status="ok" if ok else "fail",
                      detail=f"φ={r.phi_deg:.1f}° (faixa {PHI_MIN:.0f}–{PHI_MAX:.0f})"))
    ok = GAMMA_MIN <= r.gamma_kn_m3 <= GAMMA_MAX
    phys.append(Check(name="gamma", status="ok" if ok else "fail",
                      detail=f"γ={r.gamma_kn_m3:.1f} kN/m³ "
                             f"(faixa {GAMMA_MIN:.0f}–{GAMMA_MAX:.0f})"))
    ok = r.h_m > 0 and 0.0 < r.ka < 1.0 and r.kp > 1.0
    phys.append(Check(name="coeficientes", status="ok" if ok else "fail",
                      detail=f"H={r.h_m:.2f} m Ka={r.ka:.3f} (0–1) Kp={r.kp:.3f} (>1)"))

    norm: list[Check] = []
    ok = r.kp > r.ka
    norm.append(Check(name="Ka_lt_Kp", status="ok" if ok else "fail",
                      detail=f"Ka={r.ka:.3f} < Kp={r.kp:.3f}"))
    ok = abs(r.point_of_application_m - r.h_m / 3.0) <= TOL * max(r.h_m, 1.0)
    norm.append(Check(name="ponto_aplicacao", status="ok" if ok else "fail",
                      detail=f"z={r.point_of_application_m:.3f} m ≈ H/3 "
                             "(distribuição triangular)"))
    return _assemble(units, phys, norm, r.warnings)


# --- estacas ----------------------------------------------------------------
def validate_pile(r: PileCapacityResult) -> ValidationReport:
    """Valida capacidade de estaca (Aoki-Velloso / Décourt-Quaresma)."""
    # unidades: Rp = qp·Ap -> kN
    rp_q = Q_(r.qp_kpa, "kilopascal") * Q_(r.ap_m2, "meter**2")
    rp_val = ensure(rp_q, "kilonewton")
    ref = max(abs(r.rp_kn), 1.0)
    ok = abs(rp_val - r.rp_kn) <= TOL * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"Rp={rp_val:.1f} kN (dimensional ✓)")

    phys: list[Check] = []
    ok = N_SPT_MIN <= r.n_spt_min and r.n_spt_max <= N_SPT_MAX
    phys.append(Check(name="SPT", status="ok" if ok else "fail",
                      detail=f"N∈[{r.n_spt_min},{r.n_spt_max}] "
                             f"(faixa {N_SPT_MIN}–{N_SPT_MAX})"))
    ok = r.diameter_m > 0 and r.length_m > 0 and r.ap_m2 > 0 and r.u_m > 0
    phys.append(Check(name="geometria", status="ok" if ok else "fail",
                      detail=f"D={r.diameter_m:.2f} m L={r.length_m:.1f} m"))
    ok = r.rp_kn > 0 and r.rl_kn > 0 and r.rult_kn > 0 and r.radm_kn > 0
    phys.append(Check(name="resistencias", status="ok" if ok else "fail",
                      detail=f"Rp={r.rp_kn:.0f} Rl={r.rl_kn:.0f} Rult={r.rult_kn:.0f} kN"))

    norm: list[Check] = []
    ok = abs(r.rp_kn + r.rl_kn - r.rult_kn) <= TOL * max(abs(r.rult_kn), 1.0)
    norm.append(Check(name="Rult_consistencia", status="ok" if ok else "fail",
                      detail=f"Rp+Rl={r.rp_kn + r.rl_kn:.0f} ≈ Rult={r.rult_kn:.0f} kN"))
    ok = abs(r.radm_kn * r.fs - r.rult_kn) <= TOL * max(abs(r.rult_kn), 1.0)
    norm.append(Check(name="FS_consistencia", status="ok" if ok else "fail",
                      detail=f"Radm·FS={r.radm_kn * r.fs:.0f} ≈ Rult={r.rult_kn:.0f} kN"))
    st = "ok" if r.fs >= FS_PILE_MIN - 1e-9 else "warning"
    norm.append(Check(name="FS_minimo", status=st,
                      detail=f"FS={r.fs:.1f} (recomendado ≥ {FS_PILE_MIN:.0f}, NBR 6122)"))
    return _assemble(units, phys, norm, r.warnings)
