"""Geração do memorial de cálculo (Markdown) para elementos de concreto armado."""

from __future__ import annotations

from lib.concrete.beams import BeamFlexureResult
from lib.concrete.columns import ColumnResult
from lib.concrete.footings import FootingResult
from lib.concrete.slabs import SlabResult
from lib.reporting.disclaimer import DISCLAIMER
from lib.validators.report import ValidationReport

_STATUS_ICON = {"ok": "✓", "warning": "⚠", "fail": "✗"}


def _validation_section(rep: ValidationReport, numero: int) -> list[str]:
    """Tabela de validação automática + avisos (mesmo formato em todos os memoriais)."""
    linhas: list[str] = []
    add = linhas.append
    add(f"## {numero}. Validação automática")
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
    return linhas


def _disclaimer_footer() -> list[str]:
    return ["---", "", DISCLAIMER]


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


def render_column_memorial(r: ColumnResult, rep: ValidationReport) -> str:
    classe_c = f"C{int(round(r.fck_mpa))}"
    classe_aco = f"CA-{int(round(r.fyk_mpa / 10))}"
    if r.bitolas is not None:
        bitola = (f"{r.bitolas.n_bars} Ø {r.bitolas.phi_mm:.1f} mm "
                  f"(As,ef = {r.bitolas.as_ef_cm2:.2f} cm²)")
    else:
        bitola = "detalhar manualmente (sem combinação comercial disponível)"

    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Pilar de Concreto Armado")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add("**Elemento:** Pilar retangular — flexão composta normal com 2ª ordem (ELU)")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Seção (b × h) | {r.b_cm:.0f} × {r.h_cm:.0f} cm |")
    add(f"| Comprimento de flambagem le | {r.le_cm:.0f} cm |")
    add(f"| Concreto | {classe_c} (fck = {r.fck_mpa:.0f} MPa) |")
    add(f"| Aço | {classe_aco} (fyk = {r.fyk_mpa:.0f} MPa) |")
    add(f"| Distância d' (eixo da armadura) | {r.d_linha_cm:.1f} cm |")
    add(f"| Carga normal característica Nk | {r.nk_kn:.2f} kN |")
    add(f"| Momento de topo característico Mk | {r.mk_topo_knm:.2f} kN·m |")
    add("")

    add("## 2. Esforços de cálculo")
    add("")
    add(f"- Força normal: Nd = γf·Nk = **{r.nd_kn:.2f} kN**")
    add(f"- Momento de 1ª ordem: M1d,A = γf·Mk = {r.m1d_a_knm:.2f} kN·m")
    add(f"- fcd = fck/1,4 = {r.fcd_mpa:.2f} MPa · fyd = fyk/1,15 = {r.fyd_mpa:.2f} MPa")
    add("")

    add("## 3. Esbeltez (NBR 6118 15.8.2)")
    add("")
    add(f"- Raio de giração: i = {r.i_cm:.2f} cm")
    add(f"- **Índice de esbeltez: λ = le/i = {r.esbeltez:.1f}**")
    add(f"- Esbeltez-limite: λ1 = {r.lambda1:.1f}")
    add(f"- Classificação: **{r.classe}**")
    add("")

    add("## 4. Efeitos de 2ª ordem (pilar-padrão, curvatura aproximada)")
    add("")
    add(f"- Força normal adimensional: ν = {r.nu:.3f}")
    add(f"- Curvatura: 1/r = {r.one_over_r:.5f} 1/m")
    add(f"- Momento de 2ª ordem: M2d = {r.m2d_knm:.2f} kN·m")
    add(f"- Momento mínimo: M1d,mín = {r.m1d_min_knm:.2f} kN·m")
    add(f"- **Momento total de cálculo: Md,tot = {r.md_tot_knm:.2f} kN·m**")
    add("")

    add("## 5. Armadura longitudinal (simétrica)")
    add("")
    add(f"- As,cálculo = {r.as_calc_cm2:.2f} cm²")
    add(f"- As,mín = {r.as_min_cm2:.2f} cm² · As,máx = {r.as_max_cm2:.2f} cm²")
    add(f"- **As,adotada = {r.as_adopted_cm2:.2f} cm²** (governado por: {r.governed_by})")
    add(f"- Detalhamento: **{bitola}**")
    add("")

    linhas += _validation_section(rep, 6)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_footing_memorial(r: FootingResult, rep: ValidationReport) -> str:
    classe_c = f"C{int(round(r.fck_mpa))}"
    classe_aco = f"CA-{int(round(r.fyk_mpa / 10))}"
    bitola_x = f"{r.bars_x.n_bars} Ø {r.bars_x.phi_mm:.1f} mm (As,ef = {r.bars_x.as_ef_cm2:.2f} cm²)"
    bitola_y = f"{r.bars_y.n_bars} Ø {r.bars_y.phi_mm:.1f} mm (As,ef = {r.bars_y.as_ef_cm2:.2f} cm²)"

    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Sapata Isolada Quadrada Rígida")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add("**Elemento:** Sapata isolada quadrada rígida — carga centrada (método das bielas)")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Carga normal característica Nk | {r.nk_kn:.2f} kN |")
    add(f"| Tensão admissível do solo σ_adm | {r.sigma_adm_kpa:.1f} kPa |")
    add(f"| Pilar (a × b) | {r.pilar_a_cm:.0f} × {r.pilar_b_cm:.0f} cm |")
    add(f"| Concreto | {classe_c} (fck = {r.fck_mpa:.0f} MPa) |")
    add(f"| Aço | {classe_aco} (fyk = {r.fyk_mpa:.0f} MPa) |")
    add("")

    add("## 2. Geometria")
    add("")
    add(f"- Área necessária: A_nec = {r.area_nec_m2:.3f} m²")
    add(f"- **Lado adotado: L = {r.lado_cm:.0f} cm** (área efetiva = {r.area_efetiva_m2:.3f} m²)")
    add(f"- Altura: h = {r.altura_h_cm:.0f} cm · altura útil d = {r.d_cm:.1f} cm")
    add(f"- Sapata rígida (NBR 6118 22.6.1): {'sim' if r.rigida else 'NÃO'}")
    add("")

    add("## 3. Tensão no solo")
    add("")
    add(f"- Peso próprio da sapata: pp = {r.pp_sapata_kn:.2f} kN")
    add(f"- **Tensão no solo: σ_solo = {r.sigma_solo_kpa:.1f} kPa** "
        f"(σ_adm = {r.sigma_adm_kpa:.1f} kPa)")
    add("")

    add("## 4. Armadura de flexão (método das bielas, NBR 6118 22.6.4.1)")
    add("")
    add(f"- Força normal de cálculo: Nd = γf·Nk = {r.nd_kn:.2f} kN")
    add(f"- fyd = fyk/1,15 = {r.fyd_mpa:.2f} MPa")
    add(f"- As (direção x) = {r.as_x_cm2:.2f} cm² → **{bitola_x}**")
    add(f"- As (direção y) = {r.as_y_cm2:.2f} cm² → **{bitola_y}**")
    add("")

    linhas += _validation_section(rep, 5)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_slab_memorial(r: SlabResult, rep: ValidationReport) -> str:
    classe_c = f"C{int(round(r.fck_mpa))}"
    classe_aco = f"CA-{int(round(r.fyk_mpa / 10))}"
    duas = r.tipo == "duas_direcoes"
    titulo = "duas direções (apoiada nos 4 lados)" if duas else "uma direção"

    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Laje Maciça de Concreto Armado")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add(f"**Elemento:** Laje maciça armada em {titulo} — flexão (ELU)")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Vão lx (menor) | {r.lx_m:.2f} m |")
    if duas and r.ly_m is not None:
        add(f"| Vão ly (maior) | {r.ly_m:.2f} m |")
        add(f"| Relação λ = ly/lx | {r.ly_m / r.lx_m:.2f} |")
    add(f"| Espessura h | {r.h_cm:.1f} cm |")
    add(f"| Altura útil d | {r.d_cm:.1f} cm |")
    add(f"| Concreto | {classe_c} (fck = {r.fck_mpa:.0f} MPa) |")
    add(f"| Aço | {classe_aco} (fyk = {r.fyk_mpa:.0f} MPa) |")
    add(f"| Carga permanente g (excl. PP) | {r.g_knm2:.2f} kN/m² |")
    add(f"| Carga variável q | {r.q_knm2:.2f} kN/m² |")
    add("")

    add("## 2. Cargas e esforços (por metro de largura)")
    add("")
    add(f"- Peso próprio: pp = {r.pp_knm2:.3f} kN/m²")
    add(f"- Carga de cálculo: p_d = {r.pd_knm2:.2f} kN/m²")
    if duas and r.py_knm2 is not None and r.my_knm is not None:
        add(f"- Quinhão de carga: px = {r.px_knm2:.2f} kN/m² · py = {r.py_knm2:.2f} kN/m²")
        add(f"- **Mx = {r.mx_knm:.2f} kN·m/m** · **My = {r.my_knm:.2f} kN·m/m**")
    else:
        add(f"- **Momento de cálculo: Mx = {r.mx_knm:.2f} kN·m/m**")
    add("")

    add("## 3. Armadura (por metro)")
    add("")
    add(f"- As (direção x) = {r.as_x_cm2_m:.2f} cm²/m (As,mín = {r.as_min_x_cm2_m:.2f} cm²/m)")
    rotulo_y = "direção y" if duas else "distribuição"
    add(f"- As ({rotulo_y}) = {r.as_y_cm2_m:.2f} cm²/m (As,mín = {r.as_min_y_cm2_m:.2f} cm²/m)")
    add(f"- x/d (x) = {r.x_over_d_x:.3f}"
        + (f" · x/d (y) = {r.x_over_d_y:.3f}" if r.x_over_d_y is not None else ""))
    add("")

    linhas += _validation_section(rep, 4)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)
