"""Validação obrigatória do domínio de hidráulica.

Todo cálculo hidráulico passa por aqui antes de ser apresentado: faixas físicas dos
coeficientes, geometria positiva, plausibilidade de velocidade e verificação
dimensional (``pint``). Determinístico, sem LLM.

Arquivo próprio do domínio de hidráulica — não toca nos validadores compartilhados.
Importa apenas ``Check`` / ``ValidationReport`` (estáveis) de :mod:`lib.validators.report`.

Faixas e limites adotados:
- Coeficiente de Hazen-Williams C ∈ [80, 150] (tubos comerciais usuais).
- Coeficiente de Manning n ∈ [0,009 ; 0,1] (do metal liso ao canal natural vegetado).
- Diâmetro/geometria estritamente positivos; declividade S > 0.
- Velocidade "razoável": alerta se V > 3 m/s (risco de erosão/transiente hidráulico)
  ou se V < 0,5 m/s (risco de sedimentação — crítico em redes de esgoto).
"""

from __future__ import annotations

import math

from lib.hydraulic.head_loss import HeadLossResult
from lib.hydraulic.open_channel import OpenChannelResult
from lib.hydraulic.pipe_flow import PipeFlowResult
from lib.units.registry import Q_, ensure
from lib.validators.report import Check, ValidationReport

# --- faixas físicas / limites de plausibilidade -------------------------------
C_HW_MIN, C_HW_MAX = 80.0, 150.0
N_MANNING_MIN, N_MANNING_MAX = 0.009, 0.1
V_MAX_RAZOAVEL = 3.0     # m/s — acima: erosão/golpe de aríete
V_MIN_AUTOLIMP = 0.5     # m/s — abaixo: sedimentação (esgoto)


def _fold(name: str, subs: list[Check]) -> Check:
    status = "ok"
    for c in subs:
        if c.status == "fail":
            status = "fail"
            break
        if c.status == "warning":
            status = "warning"
    detail = "; ".join(f"{c.name}={c.status}" for c in subs)
    return Check(name=name, status=status, detail=detail)


def _velocity_checks(v_ms: float) -> tuple[Check, list[str]]:
    warnings: list[str] = []
    if v_ms > V_MAX_RAZOAVEL:
        st = "warning"
        warnings.append(f"Velocidade V={v_ms:.2f} m/s > {V_MAX_RAZOAVEL:.1f} m/s "
                        "(risco de erosão/transiente hidráulico).")
    elif v_ms < V_MIN_AUTOLIMP:
        st = "warning"
        warnings.append(f"Velocidade V={v_ms:.2f} m/s < {V_MIN_AUTOLIMP:.1f} m/s "
                        "(risco de sedimentação — verificar autolimpeza em esgoto).")
    else:
        st = "ok"
    return (Check(name="velocidade", status=st,
                  detail=f"V={v_ms:.2f} m/s (faixa {V_MIN_AUTOLIMP}–{V_MAX_RAZOAVEL})"),
            warnings)


# --------------------------------------------------------------------- pipe flow

def validate_pipe_flow(r: PipeFlowResult) -> ValidationReport:
    """Valida um escoamento em conduto forçado (Hazen-Williams ou Darcy-Weisbach)."""
    phys: list[Check] = []

    ok = r.D_m > 0
    phys.append(Check(name="diametro", status="ok" if ok else "fail",
                      detail=f"D={r.D_m:.3f} m"))

    ok = r.L_m >= 0
    phys.append(Check(name="comprimento", status="ok" if ok else "fail",
                      detail=f"L={r.L_m:.1f} m"))

    ok = r.hf_m >= 0
    phys.append(Check(name="perda_carga", status="ok" if ok else "fail",
                      detail=f"hf={r.hf_m:.3f} m"))

    if r.coef_C is not None:
        ok = C_HW_MIN <= r.coef_C <= C_HW_MAX
        phys.append(Check(name="coef_C", status="ok" if ok else "fail",
                          detail=f"C={r.coef_C:.0f} (faixa {C_HW_MIN:.0f}–{C_HW_MAX:.0f})"))

    if r.f is not None:
        ok = 0.0 < r.f < 0.1
        phys.append(Check(name="fator_atrito", status="ok" if ok else "fail",
                          detail=f"f={r.f:.4f}"))

    vel, vel_warn = _velocity_checks(r.V_ms)

    # dimensional: Q = A·V = (π/4)·D²·V  [m³/s]
    q_q = (math.pi / 4.0) * Q_(r.D_m, "meter") ** 2 * Q_(r.V_ms, "meter/second")
    q_val = ensure(q_q, "meter**3/second")
    ref = max(abs(r.Q_m3s), 1e-9)
    ok = abs(q_val - r.Q_m3s) <= 1e-6 * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"Q={q_val:.4f} m³/s = A·V (dimensional ✓)")

    checks = [units, _fold("physical", phys), vel]
    passed = not any(c.status == "fail" for c in checks)
    return ValidationReport(passed=passed, checks=checks, warnings=vel_warn)


# ------------------------------------------------------------------ open channel

def validate_open_channel(r: OpenChannelResult) -> ValidationReport:
    """Valida um escoamento uniforme em canal aberto (Manning)."""
    phys: list[Check] = []

    ok = N_MANNING_MIN <= r.n <= N_MANNING_MAX
    phys.append(Check(name="coef_n", status="ok" if ok else "fail",
                      detail=f"n={r.n:.3f} (faixa {N_MANNING_MIN}–{N_MANNING_MAX})"))

    ok = r.S > 0
    phys.append(Check(name="declividade", status="ok" if ok else "fail",
                      detail=f"S={r.S:.5f} m/m"))

    ok = (r.y_m > 0 and r.area_m2 > 0 and r.perimetro_m > 0
          and r.raio_hidraulico_m > 0)
    phys.append(Check(name="geometria", status="ok" if ok else "fail",
                      detail=f"y={r.y_m:.3f} A={r.area_m2:.3f} P={r.perimetro_m:.3f} "
                             f"R={r.raio_hidraulico_m:.3f}"))

    ok = r.Q_m3s > 0
    phys.append(Check(name="vazao", status="ok" if ok else "fail",
                      detail=f"Q={r.Q_m3s:.3f} m³/s"))

    vel, vel_warn = _velocity_checks(r.V_ms)

    # dimensional: Q = A·V  [m³/s]
    q_q = Q_(r.area_m2, "meter**2") * Q_(r.V_ms, "meter/second")
    q_val = ensure(q_q, "meter**3/second")
    ref = max(abs(r.Q_m3s), 1e-9)
    ok = abs(q_val - r.Q_m3s) <= 1e-6 * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"Q={q_val:.4f} m³/s = A·V (dimensional ✓)")

    checks = [units, _fold("physical", phys), vel]
    passed = not any(c.status == "fail" for c in checks)
    return ValidationReport(passed=passed, checks=checks, warnings=vel_warn)


# --------------------------------------------------------------------- head loss

def validate_head_loss(r: HeadLossResult) -> ValidationReport:
    """Valida a composição de perdas distribuída + localizadas."""
    phys: list[Check] = []

    ok = r.hf_distribuida_m >= 0 and r.hf_localizada_m >= 0 and r.hf_total_m >= 0
    phys.append(Check(name="perdas_nao_negativas", status="ok" if ok else "fail",
                      detail=f"hf_dist={r.hf_distribuida_m:.3f} "
                             f"hf_loc={r.hf_localizada_m:.3f} hf_tot={r.hf_total_m:.3f} m"))

    ok = r.g > 0
    phys.append(Check(name="gravidade", status="ok" if ok else "fail",
                      detail=f"g={r.g:.2f} m/s²"))

    ok = all(it.h_m >= 0 and it.K >= 0 and it.quantidade >= 0 for it in r.itens)
    phys.append(Check(name="itens", status="ok" if ok else "fail",
                      detail=f"{len(r.itens)} singularidade(s)"))

    # dimensional: hf_total = hf_distribuída + hf_localizada  [m]
    tot_q = Q_(r.hf_distribuida_m, "meter") + Q_(r.hf_localizada_m, "meter")
    tot_val = ensure(tot_q, "meter")
    ref = max(abs(r.hf_total_m), 1e-9)
    ok = abs(tot_val - r.hf_total_m) <= 1e-6 * ref
    units = Check(name="units", status="ok" if ok else "fail",
                  detail=f"hf_total={tot_val:.3f} m = hf_dist + hf_loc (dimensional ✓)")

    checks = [units, _fold("physical", phys)]
    passed = not any(c.status == "fail" for c in checks)
    return ValidationReport(passed=passed, checks=checks, warnings=[])
