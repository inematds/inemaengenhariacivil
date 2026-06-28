"""Geração do memorial de cálculo (Markdown) para elementos de concreto armado."""

from __future__ import annotations

from lib.budget.estimate import OrcamentoResult
from lib.concrete.beams import BeamFlexureResult
from lib.concrete.columns import ColumnResult
from lib.concrete.footings import FootingResult
from lib.concrete.slabs import SlabResult
from lib.geotechnical.bearing_capacity import BearingCapacityResult
from lib.geotechnical.earth_pressure import (
    CoulombEarthPressureResult,
    RankineEarthPressureResult,
)
from lib.geotechnical.piles import PileComparisonResult
from lib.geotechnical.settlement import (
    ConsolidationSettlementResult,
    ElasticSettlementResult,
)
from lib.hydraulic.head_loss import HeadLossResult
from lib.hydraulic.open_channel import OpenChannelResult
from lib.hydraulic.pipe_flow import PipeFlowResult
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


# ====================================================================== GEOTECNIA


def render_bearing_capacity_memorial(
    r: BearingCapacityResult, rep: ValidationReport
) -> str:
    """Memorial da capacidade de carga de fundação rasa (Vesic, NBR 6122)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Capacidade de Carga de Fundação Rasa")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add(f"**Método:** {r.metodo} — fundação {r.shape} (estado-limite último GEO)")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Coesão c | {r.c_kpa:.1f} kPa |")
    add(f"| Ângulo de atrito φ | {r.phi_deg:.1f}° |")
    add(f"| Peso específico γ | {r.gamma_kn_m3:.1f} kN/m³ |")
    add(f"| Largura/diâmetro B | {r.b_m:.2f} m |")
    if r.l_m is not None:
        add(f"| Comprimento L | {r.l_m:.2f} m |")
    add(f"| Profundidade de assentamento Df | {r.depth_df_m:.2f} m |")
    add(f"| Forma da base | {r.shape} |")
    add(f"| Fator de segurança global FS | {r.fs:.1f} |")
    add("")

    add("## 2. Fatores de capacidade de carga e de forma (Vesic)")
    add("")
    add(f"- Nc = {r.nc:.2f} · Nq = {r.nq:.2f} · Nγ = {r.ngamma:.2f}")
    add(f"- Fatores de forma: sc = {r.sc:.3f} · sq = {r.sq:.3f} · sγ = {r.sgamma:.3f}")
    add(f"- Sobrecarga no nível da base: q = γ·Df = {r.q_surcharge_kpa:.1f} kPa")
    add("")

    add("## 3. Capacidade de carga (q_ult = c·Nc·sc + q·Nq·sq + 0,5·γ·B·Nγ·sγ)")
    add("")
    add(f"- Parcela de coesão: c·Nc·sc = {r.term_cohesion_kpa:.1f} kPa")
    add(f"- Parcela de sobrecarga: q·Nq·sq = {r.term_surcharge_kpa:.1f} kPa")
    add(f"- Parcela de peso: 0,5·γ·B·Nγ·sγ = {r.term_weight_kpa:.1f} kPa")
    add(f"- **Capacidade última: q_ult = {r.q_ult_kpa:.1f} kPa**")
    add(f"- **Tensão admissível: q_adm = q_ult/FS = {r.q_adm_kpa:.1f} kPa**")
    add("")

    linhas += _validation_section(rep, 4)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_elastic_settlement_memorial(
    r: ElasticSettlementResult, rep: ValidationReport
) -> str:
    """Memorial do recalque elástico imediato (teoria da elasticidade, NBR 6122 ELS)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Recalque Elástico Imediato")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add(f"**Método:** {r.metodo}")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Pressão aplicada q | {r.q_kpa:.1f} kPa |")
    add(f"| Largura B | {r.b_m:.2f} m |")
    add(f"| Coeficiente de Poisson ν | {r.poisson_nu:.2f} |")
    add(f"| Fator de influência Iw | {r.iw:.3f} |")
    add(f"| Módulo de elasticidade Es | {r.es_kpa:.0f} kPa |")
    add("")

    add("## 2. Recalque (s = q·B·(1−ν²)·Iw / Es)")
    add("")
    add(f"- **Recalque imediato: s = {r.settlement_mm:.2f} mm "
        f"({r.settlement_m:.5f} m)**")
    add("")

    linhas += _validation_section(rep, 3)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_consolidation_settlement_memorial(
    r: ConsolidationSettlementResult, rep: ValidationReport
) -> str:
    """Memorial do recalque por adensamento primário (Terzaghi, NBR 6122 ELS)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Recalque por Adensamento Primário")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add(f"**Método:** {r.metodo}")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Índice de compressão Cc | {r.cc:.3f} |")
    add(f"| Índice de vazios inicial e0 | {r.e0:.2f} |")
    add(f"| Espessura da camada H | {r.h_m:.2f} m |")
    add(f"| Tensão efetiva inicial σ0 | {r.sigma0_kpa:.1f} kPa |")
    add(f"| Acréscimo de tensão Δσ | {r.delta_sigma_kpa:.1f} kPa |")
    add("")

    add("## 2. Recalque (s = Cc/(1+e0)·H·log10((σ0+Δσ)/σ0))")
    add("")
    add(f"- **Recalque por adensamento: s = {r.settlement_mm:.2f} mm "
        f"({r.settlement_m:.5f} m)**")
    add("")

    linhas += _validation_section(rep, 3)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_earth_pressure_memorial(
    r: RankineEarthPressureResult | CoulombEarthPressureResult,
    rep: ValidationReport,
) -> str:
    """Memorial do empuxo de terra (Rankine ou Coulomb) sobre estrutura de contenção."""
    coulomb = isinstance(r, CoulombEarthPressureResult)
    linhas: list[str] = []
    add = linhas.append

    add(f"# Memorial de Cálculo — Empuxo de Terra ({r.metodo})")
    add("")
    add(f"**Norma:** {r.norma}  ")
    add(f"**Método:** {r.metodo} — empuxo por metro de muro")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Peso específico γ | {r.gamma_kn_m3:.1f} kN/m³ |")
    add(f"| Altura do muro H | {r.h_m:.2f} m |")
    add(f"| Ângulo de atrito φ | {r.phi_deg:.1f}° |")
    if coulomb:
        add(f"| Atrito solo-muro δ | {r.delta_deg:.1f}° |")
        add(f"| Inclinação do tardoz β | {r.beta_deg:.1f}° |")
        add(f"| Inclinação do terrapleno α | {r.alpha_deg:.1f}° |")
    add("")

    add("## 2. Coeficientes de empuxo")
    add("")
    add(f"- Coeficiente ativo: Ka = {r.ka:.4f}")
    add(f"- Coeficiente passivo: Kp = {r.kp:.4f}")
    add("")

    add("## 3. Empuxos (E = 0,5·γ·H²·K)")
    add("")
    add(f"- **Empuxo ativo: Ea = {r.ea_active_kn_m:.2f} kN/m**")
    add(f"- Empuxo passivo: Ep = {r.ep_passive_kn_m:.2f} kN/m")
    add(f"- Ponto de aplicação: z = H/3 = {r.point_of_application_m:.3f} m da base "
        "(distribuição triangular)")
    add("")

    linhas += _validation_section(rep, 4)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_pile_comparison_memorial(
    r: PileComparisonResult, rep: ValidationReport
) -> str:
    """Memorial comparativo da capacidade de estaca (Aoki-Velloso × Décourt-Quaresma)."""
    a, d = r.aoki, r.decourt
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Capacidade de Carga de Estaca "
        "(Aoki-Velloso × Décourt-Quaresma)")
    add("")
    add(f"**Norma:** {a.norma}  ")
    add("**Método:** dois métodos semiempíricos por SPT, com validação por divergência")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Tipo de estaca | {a.pile_type} |")
    add(f"| Diâmetro D | {a.diameter_m:.2f} m |")
    add(f"| Comprimento L | {a.length_m:.2f} m |")
    add(f"| Área de ponta Ap | {a.ap_m2:.4f} m² |")
    add(f"| Perímetro U | {a.u_m:.3f} m |")
    add(f"| Fator de segurança global FS | {a.fs:.1f} |")
    add(f"| Faixa de SPT do perfil | N ∈ [{a.n_spt_min}, {a.n_spt_max}] |")
    add("")

    add("## 2. Resistências por método")
    add("")
    add("| Método | Rp (kN) | Rl (kN) | Rult (kN) | Radm (kN) |")
    add("|--------|---------|---------|-----------|-----------|")
    add(f"| Aoki-Velloso | {a.rp_kn:.1f} | {a.rl_kn:.1f} | "
        f"{a.rult_kn:.1f} | {a.radm_kn:.1f} |")
    add(f"| Décourt-Quaresma | {d.rp_kn:.1f} | {d.rl_kn:.1f} | "
        f"{d.rult_kn:.1f} | {d.radm_kn:.1f} |")
    add("")

    add("## 3. Comparação entre métodos")
    add("")
    add(f"- Rult (Aoki-Velloso) = {r.rult_aoki_kn:.1f} kN")
    add(f"- Rult (Décourt-Quaresma) = {r.rult_decourt_kn:.1f} kN")
    add(f"- **Divergência relativa = {r.divergencia_pct:.1f}% (limite 20%)**")
    add(f"- Métodos convergem: {'sim' if r.convergem else 'NÃO — revisão recomendada'}")
    add("")

    linhas += _validation_section(rep, 4)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


# ====================================================================== HIDRÁULICA


def render_pipe_flow_memorial(r: PipeFlowResult, rep: ValidationReport) -> str:
    """Memorial do escoamento em conduto forçado (Hazen-Williams ou Darcy-Weisbach)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Escoamento em Conduto Forçado")
    add("")
    add(f"**Método:** {r.metodo}  ")
    add("**Referência:** Azevedo Netto, *Manual de Hidráulica*, 8ª ed.")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Vazão Q | {r.Q_m3s:.4f} m³/s |")
    add(f"| Diâmetro D | {r.D_m:.3f} m |")
    add(f"| Comprimento L | {r.L_m:.1f} m |")
    if r.coef_C is not None:
        add(f"| Coeficiente de Hazen-Williams C | {r.coef_C:.0f} |")
    if r.eps_m is not None:
        add(f"| Rugosidade absoluta ε | {r.eps_m:.2e} m |")
    add("")

    add("## 2. Resultados")
    add("")
    add(f"- Velocidade média: V = Q/A = {r.V_ms:.3f} m/s")
    if r.reynolds is not None:
        add(f"- Número de Reynolds: Re = {r.reynolds:.0f}")
    if r.f is not None:
        add(f"- Fator de atrito (Swamee-Jain): f = {r.f:.4f}")
    add(f"- **Perda de carga distribuída: hf = {r.hf_m:.3f} m**")
    add("")

    linhas += _validation_section(rep, 3)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_open_channel_memorial(r: OpenChannelResult, rep: ValidationReport) -> str:
    """Memorial do escoamento uniforme em canal aberto (fórmula de Manning)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Escoamento em Canal Aberto (Manning)")
    add("")
    add(f"**Método:** Fórmula de Manning — seção {r.geometria}  ")
    add("**Referência:** Chow, *Open-Channel Hydraulics* (1959).")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    if r.b_m is not None:
        add(f"| Largura de fundo b | {r.b_m:.2f} m |")
    if r.z is not None:
        add(f"| Talude z (H:V) | {r.z:.2f} |")
    if r.diametro_m is not None:
        add(f"| Diâmetro D | {r.diametro_m:.3f} m |")
    add(f"| Tirante y | {r.y_m:.3f} m |")
    add(f"| Coeficiente de Manning n | {r.n:.4f} |")
    add(f"| Declividade de fundo S | {r.S:.5f} m/m |")
    add("")

    add("## 2. Resultados (Q = (1/n)·A·R^(2/3)·S^(1/2))")
    add("")
    add(f"- Área molhada: A = {r.area_m2:.4f} m²")
    add(f"- Perímetro molhado: P = {r.perimetro_m:.4f} m")
    add(f"- Raio hidráulico: R = A/P = {r.raio_hidraulico_m:.4f} m")
    add(f"- Velocidade média: V = {r.V_ms:.3f} m/s")
    add(f"- **Vazão: Q = {r.Q_m3s:.4f} m³/s**")
    add("")

    linhas += _validation_section(rep, 3)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


def render_head_loss_memorial(r: HeadLossResult, rep: ValidationReport) -> str:
    """Memorial da perda de carga total (distribuída + localizadas, coeficientes K)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Cálculo — Perda de Carga (distribuída + localizadas)")
    add("")
    add(f"**Método:** {r.metodo}  ")
    add("**Referência:** Azevedo Netto, *Manual de Hidráulica*, 8ª ed.")
    add("")

    add("## 1. Dados de entrada")
    add("")
    add("| Parâmetro | Valor |")
    add("|-----------|-------|")
    add(f"| Velocidade média V | {r.V_ms:.3f} m/s |")
    add(f"| Gravidade g | {r.g:.2f} m/s² |")
    add(f"| Perda distribuída hf,dist | {r.hf_distribuida_m:.3f} m |")
    add("")

    add("## 2. Perdas localizadas (h = K·V²/(2g))")
    add("")
    add("| Singularidade | K | Quantidade | h (m) |")
    add("|---------------|---|------------|-------|")
    for it in r.itens:
        add(f"| {it.tipo} | {it.K:.2f} | {it.quantidade} | {it.h_m:.4f} |")
    add("")

    add("## 3. Composição")
    add("")
    add(f"- Perda distribuída: hf,dist = {r.hf_distribuida_m:.3f} m")
    add(f"- Perda localizada total: hf,loc = {r.hf_localizada_m:.3f} m")
    add(f"- **Perda de carga total: hf,total = {r.hf_total_m:.3f} m**")
    add("")

    linhas += _validation_section(rep, 4)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)


# ====================================================================== ORÇAMENTO


def render_orcamento_memorial(r: OrcamentoResult, rep: ValidationReport) -> str:
    """Memorial de orçamento (custo direto + BDI), preços tipo SINAPI (amostra)."""
    linhas: list[str] = []
    add = linhas.append

    add("# Memorial de Orçamento — Custo Direto + BDI")
    add("")
    add(f"**Referência:** {r.norma}  ")
    add("**Base de preços:** tabela tipo SINAPI (amostra ILUSTRATIVA — substituir pela "
        "SINAPI vigente/regional, com desoneração, mês de referência e UF do projeto)")
    add("")

    add("## 1. Itens orçados")
    add("")
    add("| Código | Descrição | Unid. | Qtd. | Preço unit. (R$) | Custo (R$) |")
    add("|--------|-----------|-------|------|------------------|------------|")
    for it in r.itens:
        add(f"| {it.codigo} | {it.descricao} | {it.unidade} | "
            f"{it.quantidade:.2f} | {it.preco_unitario:.2f} | {it.custo:.2f} |")
    add("")

    add("## 2. Composição do custo")
    add("")
    add(f"- Subtotal (custo direto): R$ {r.subtotal:.2f}")
    add(f"- BDI aplicado: {r.bdi_pct:.2f}% → R$ {r.valor_bdi:.2f}")
    add(f"- **Total (custo direto + BDI): R$ {r.total:.2f}**")
    add("")

    linhas += _validation_section(rep, 3)
    linhas += _disclaimer_footer()
    return "\n".join(linhas)
