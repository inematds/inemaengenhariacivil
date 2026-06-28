"""Geração do memorial de cálculo (Markdown) para viga de concreto armado."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.reporting.disclaimer import DISCLAIMER
from lib.validators.report import ValidationReport

_STATUS_ICON = {"ok": "✓", "warning": "⚠", "fail": "✗"}


def render_beam_memorial(r: BeamFlexureResult, rep: ValidationReport) -> str:
    classe_c = f"C{int(round(r.fck_mpa))}"
    classe_aco = f"CA-{int(round(r.fyk_mpa / 10))}"
    bitola = f"{r.bars.n_bars} Ø {r.bars.phi_mm:.1f} mm"

    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Viga de Concreto Armado")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add("**Elemento:** Viga retangular biapoiada — flexão simples (ELU)")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Seção (b × h) | {r.b_cm:.0f} × {r.h_cm:.0f} cm |")
    add(f"| Altura útil d | {r.d_cm:.1f} cm |")
    add(f"| Concreto | {classe_c} (fck = {r.fck_mpa:.0f} MPa) |")
    add(f"| Aço | {classe_aco} (fyk = {r.fyk_mpa:.0f} MPa) |")
    add(f"| Vão | {r.vao_m:.2f} m |")
    add(f"| Carga permanente g (excl. PP) | {r.g_knm:.2f} kN/m |")
    add(f"| Carga variável q | {r.q_knm:.2f} kN/m |")
    add("")

    add("## 2. Esforços")
    add("")
    add(f"- Peso próprio: pp = {r.pp_knm:.3f} kN/m")
    add(f"- Carga de cálculo: p_d = 1,4·(g + pp) + 1,4·q = {r.pd_knm:.2f} kN/m")
    add(f"- Momento de cálculo: **Md = p_d·L²/8 = {r.md_knm:.2f} kN·m**")
    add("")

    add("## 3. Materiais")
    add("")
    add(f"- fcd = fck/1,4 = {r.fcd_mpa:.2f} MPa")
    add(f"- fyd = fyk/1,15 = {r.fyd_mpa:.2f} MPa")
    add("")

    add("## 4. Flexão (estado-limite último)")
    add("")
    add(f"- Linha neutra: x = {r.x_cm:.2f} cm")
    add(f"- x/d = {r.x_over_d:.3f} ({'dúctil' if r.ductile else 'verificar ductilidade'})")
    add(f"- Braço de alavanca: z = {r.z_cm:.2f} cm")
    add("")

    add("## 5. Armadura longitudinal")
    add("")
    add(f"- As,cálculo = {r.as_calc_cm2:.2f} cm²")
    add(f"- As,mín = {r.as_min_cm2:.2f} cm² · As,máx = {r.as_max_cm2:.2f} cm²")
    add(f"- **As,adotada = {r.as_adopted_cm2:.2f} cm²** (governado por: {r.governed_by})")
    add(f"- Detalhamento: **{bitola}** (As,ef = {r.bars.as_ef_cm2:.2f} cm²)")
    add("")

    add("## 6. Validação automática")
    add("")
    add("| Verificação | Status | Detalhe |")
    add("|-------------|--------|---------|")
    for c in rep.checks:
        add(f"| {c.name} | {_STATUS_ICON.get(c.status, c.status)} | {c.detail} |")
    add("")
    add(f"**Resultado da validação:** {'APROVADO' if rep.passed else 'REPROVADO'}")
    add("")

    if rep.warnings:
        add("### Avisos")
        add("")
        for w in rep.warnings:
            add(f"- ⚠ {w}")
        add("")

    add("---")
    add("")
    add(DISCLAIMER)

    return "\n".join(linhas)
