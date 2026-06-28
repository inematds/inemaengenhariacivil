"""Validação obrigatória do domínio de LIGAÇÕES METÁLICAS (NBR 8800:2008 §6).

Arquivo próprio do domínio (não toca nos validadores compartilhados). Reverifica de
forma determinística, sem LLM, a coerência dimensional e aritmética de uma ligação
parafusada ou soldada antes de ela ser apresentada:

- Parafusos: resistências por modo > 0; resistência governante = mínimo entre cortante
  e contato; capacidade total = n·Rd ≥ força solicitante; nº de parafusos ≥ 1; fub/fu
  positivos; bitola na faixa usual [12,5; 25] mm (alerta — warning — quando fora).
- Solda: garganta aw = 0,7·perna; Rd = força/comprimento (reconstrução); fw > 0;
  perna ≥ 3 mm (mínimo prático — reprova quando abaixo).

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report` (estável).
"""

from __future__ import annotations

from lib.steel.connections import (
    COEF_GARGANTA,
    DB_MAX_MM,
    DB_MIN_MM,
    PERNA_MIN_MM,
    BoltedConnectionResult,
    WeldResult,
)
from lib.validators.report import Check, ValidationReport

TOL = 1e-6  # tolerância absoluta das reconstruções aritméticas


def _rel_ok(a: float, b: float) -> bool:
    return abs(a - b) <= TOL * max(abs(a), abs(b), 1.0)


def validate_bolted(r: BoltedConnectionResult) -> ValidationReport:
    """Valida uma :class:`BoltedConnectionResult` (NBR 8800:2008 §6.3).

    Devolve um :class:`ValidationReport` (``passed=False`` se qualquer checagem
    falhar). Determinístico e independente do LLM.
    """
    checks: list[Check] = []
    warnings: list[str] = []

    # --- material / física -------------------------------------------------
    mat_ok = r.fub_mpa > 0 and r.fu_mpa > 0
    checks.append(Check(
        name="materiais_positivos",
        status="ok" if mat_ok else "fail",
        detail=f"fub={r.fub_mpa:g} MPa, fu={r.fu_mpa:g} MPa (devem ser > 0)",
    ))

    res_ok = r.fv_rd_kn > 0 and r.fc_rd_kn > 0
    checks.append(Check(
        name="resistencias_positivas",
        status="ok" if res_ok else "fail",
        detail=f"Fv,Rd={r.fv_rd_kn:.2f} kN, Fc,Rd={r.fc_rd_kn:.2f} kN (> 0)",
    ))

    # --- governante = mínimo -----------------------------------------------
    rd_min = min(r.fv_rd_kn, r.fc_rd_kn)
    gov_ok = _rel_ok(r.rd_bolt_kn, rd_min)
    checks.append(Check(
        name="governante_minimo",
        status="ok" if gov_ok else "fail",
        detail=f"Rd_parafuso={r.rd_bolt_kn:.2f} ≈ min(Fv,Rd, Fc,Rd)={rd_min:.2f} kN "
               f"({r.governante})",
    ))

    # --- nº de parafusos >= 1 ----------------------------------------------
    n_ok = r.n_parafusos >= 1
    checks.append(Check(
        name="numero_parafusos",
        status="ok" if n_ok else "fail",
        detail=f"n={r.n_parafusos} parafuso(s) (>= 1)",
    ))

    # --- capacidade total coerente e suficiente ----------------------------
    cap_calc = r.n_parafusos * r.rd_bolt_kn
    cap_arit_ok = _rel_ok(cap_calc, r.capacidade_total_kn)
    cap_suf_ok = r.capacidade_total_kn + TOL >= r.forca_kn
    checks.append(Check(
        name="capacidade_total",
        status="ok" if (cap_arit_ok and cap_suf_ok) else "fail",
        detail=f"n·Rd={cap_calc:.2f} ≈ capacidade={r.capacidade_total_kn:.2f} kN "
               f"e ≥ força={r.forca_kn:.2f} kN",
    ))

    # --- bitola na faixa usual (alerta) ------------------------------------
    bitola_ok = DB_MIN_MM <= r.db_mm <= DB_MAX_MM
    checks.append(Check(
        name="bitola_usual",
        status="ok" if bitola_ok else "warning",
        detail=f"db={r.db_mm:g} mm (faixa usual [{DB_MIN_MM:g}, {DB_MAX_MM:g}] mm)",
    ))
    if not bitola_ok:
        warnings.append(
            f"bitola db={r.db_mm:g} mm fora da faixa usual "
            f"[{DB_MIN_MM:g}, {DB_MAX_MM:g}] mm."
        )

    passed = not any(c.status == "fail" for c in checks)
    warnings += list(r.warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)


def validate_weld(r: WeldResult) -> ValidationReport:
    """Valida uma :class:`WeldResult` (NBR 8800:2008 §6.2.6).

    Devolve um :class:`ValidationReport` (``passed=False`` se qualquer checagem
    falhar). Determinístico e independente do LLM.
    """
    checks: list[Check] = []
    warnings: list[str] = []

    # --- material / física -------------------------------------------------
    fw_ok = r.fw_mpa > 0
    checks.append(Check(
        name="fw_positivo",
        status="ok" if fw_ok else "fail",
        detail=f"fw={r.fw_mpa:g} MPa (deve ser > 0)",
    ))

    rd_ok = r.rd_kn_cm > 0
    checks.append(Check(
        name="resistencia_positiva",
        status="ok" if rd_ok else "fail",
        detail=f"Rd={r.rd_kn_cm:.4f} kN/cm (> 0)",
    ))

    # --- garganta efetiva aw = 0,7·perna -----------------------------------
    aw_calc = COEF_GARGANTA * (r.perna_mm / 10.0)
    aw_ok = _rel_ok(r.aw_cm, aw_calc)
    checks.append(Check(
        name="garganta_efetiva",
        status="ok" if aw_ok else "fail",
        detail=f"aw={r.aw_cm:.4f} ≈ 0,7·perna={aw_calc:.4f} cm",
    ))

    # --- comprimento coerente: força = Rd·L --------------------------------
    forca_calc = r.rd_kn_cm * r.comprimento_nec_cm
    comp_ok = _rel_ok(forca_calc, r.forca_kn)
    checks.append(Check(
        name="comprimento_coerente",
        status="ok" if comp_ok else "fail",
        detail=f"Rd·L={forca_calc:.2f} ≈ força={r.forca_kn:.2f} kN "
               f"(L={r.comprimento_nec_cm:.2f} cm)",
    ))

    # --- perna mínima de filete (reprova abaixo) ---------------------------
    perna_ok = r.perna_mm >= PERNA_MIN_MM
    checks.append(Check(
        name="perna_minima",
        status="ok" if perna_ok else "fail",
        detail=f"perna={r.perna_mm:g} mm (mínimo {PERNA_MIN_MM:g} mm)",
    ))

    passed = not any(c.status == "fail" for c in checks)
    warnings += list(r.warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)
