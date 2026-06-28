"""MCP server `calc-server` — expõe a engine de cálculo determinística ao agente.

Princípio do projeto: resultados numéricos SÓ vêm destas ferramentas. Se uma ferramenta
não existir para o que foi pedido, o agente deve abster-se (nunca inventar números).

Execução:
    python mcp/calc-server/server.py            # inicia o server (stdio)
    python mcp/calc-server/server.py --selftest # autoteste rápido (não inicia stdio)
"""

from __future__ import annotations

import pathlib
import sys

# Importa o SDK `mcp` ANTES de pôr a raiz do repo no path (a raiz contém um diretório
# chamado `mcp/`, que sombrearia o pacote instalado).
from mcp.server.fastmcp import FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from lib.budget.sinapi import load_sinapi, lookup  # noqa: E402
from lib.math.interpolation import linear_interp  # noqa: E402
from lib.norms.search import buscar_tabela  # noqa: E402
from lib.projects.store import (  # noqa: E402
    ProjectRecord,
    add_calculo,
    list_projects,
    load_project,
    save_project,
)
from lib.reporting.disclaimer import DISCLAIMER  # noqa: E402
from lib.reporting.report import build_project_report  # noqa: E402
from lib.service import (  # noqa: E402
    solve_bearing_capacity,
    solve_bolted_connection,
    solve_compression,
    solve_consolidation_settlement,
    solve_earth_pressure_coulomb,
    solve_earth_pressure_rankine,
    solve_earthwork,
    solve_elastic_settlement,
    solve_fellenius,
    solve_flexible_pavement,
    solve_head_loss,
    solve_infinite_slope,
    solve_one_way_slab,
    solve_open_channel,
    solve_orcamento,
    solve_pile_comparison,
    solve_pipe_flow,
    solve_rectangular_beam,
    solve_rectangular_column,
    solve_square_footing,
    solve_two_way_slab,
    solve_weld,
)
from lib.steel.profiles import get_profile, load_profiles  # noqa: E402
from lib.structural.combinations import combinar_elu_normal  # noqa: E402
from lib.structural.loads import (  # noqa: E402
    carga_acidental_uso,
    peso_especifico_material,
)
from lib.units.registry import Q_, ensure  # noqa: E402

mcp = FastMCP("inema-calc-server")


@mcp.tool()
def dimensionar_viga_retangular(
    b_cm: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    vao_m: float,
    g_knm: float,
    q_knm: float,
    cobrimento_cm: float = 3.0,
    d_cm: float | None = None,
) -> dict:
    """Dimensiona uma viga retangular biapoiada de concreto armado à flexão (NBR 6118, ELU).

    Cargas em kN/m: g (permanente, exclui peso próprio) e q (variável). Devolve o
    resultado, o relatório de validação, o memorial em Markdown e o aviso de
    responsabilidade técnica obrigatório.
    """
    return solve_rectangular_beam(
        b_cm=b_cm, h_cm=h_cm, fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        vao_m=vao_m, g_knm=g_knm, q_knm=q_knm,
        cobrimento_cm=cobrimento_cm, d_cm=d_cm,
    )


@mcp.tool()
def dimensionar_pilar(
    nk_kn: float,
    mk_topo_knm: float,
    b_cm: float,
    h_cm: float,
    le_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 3.0,
    phi_estribo_mm: float = 5.0,
    phi_long_mm: float = 20.0,
    d_linha_cm: float | None = None,
    alpha_b: float = 1.0,
) -> dict:
    """Dimensiona um pilar retangular de concreto à compressão com 2ª ordem (NBR 6118).

    ``h_cm`` é a dimensão na direção analisada (a do momento e da flambagem). λ > 90 é
    recusado (fora do método simplificado). Devolve resultado, validação, memorial e aviso.
    """
    return solve_rectangular_column(
        nk_kn=nk_kn, mk_topo_knm=mk_topo_knm, b_cm=b_cm, h_cm=h_cm, le_cm=le_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm,
        phi_estribo_mm=phi_estribo_mm, phi_long_mm=phi_long_mm,
        d_linha_cm=d_linha_cm, alpha_b=alpha_b,
    )


@mcp.tool()
def dimensionar_sapata(
    nk_kn: float,
    sigma_adm_kpa: float,
    pilar_a_cm: float,
    pilar_b_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 5.0,
    phi_long_mm: float = 12.5,
) -> dict:
    """Dimensiona uma sapata isolada quadrada rígida sob carga centrada (NBR 6122/6118).

    Método das bielas. Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_square_footing(
        nk_kn=nk_kn, sigma_adm_kpa=sigma_adm_kpa,
        pilar_a_cm=pilar_a_cm, pilar_b_cm=pilar_b_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        cobrimento_cm=cobrimento_cm, phi_long_mm=phi_long_mm,
    )


@mcp.tool()
def dimensionar_laje_uma_direcao(
    lx_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
) -> dict:
    """Dimensiona uma laje maciça armada em UMA direção à flexão (NBR 6118, ELU).

    Cargas em kN/m². Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_one_way_slab(
        lx_m=lx_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )


@mcp.tool()
def dimensionar_laje_duas_direcoes(
    lx_m: float,
    ly_m: float,
    g_knm2: float,
    q_knm2: float,
    h_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 2.5,
    phi_mm: float = 10.0,
) -> dict:
    """Dimensiona uma laje maciça armada em DUAS direções, apoiada nos 4 lados (NBR 6118).

    ``lx_m`` é o MENOR vão (λ = ly/lx ≥ 1). Método das faixas (Grashof-Rankine).
    Devolve resultado, validação, memorial e o aviso obrigatório.
    """
    return solve_two_way_slab(
        lx_m=lx_m, ly_m=ly_m, g_knm2=g_knm2, q_knm2=q_knm2, h_cm=h_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa, cobrimento_cm=cobrimento_cm, phi_mm=phi_mm,
    )


@mcp.tool()
def combinar_acoes_elu(
    gk: float,
    qk_principal: float,
    qk_secundarias: list[float] | None = None,
    gamma_g: float = 1.4,
    gamma_q: float = 1.4,
    psi0: float = 0.5,
) -> dict:
    """Combinação última normal (ELU): Fd = γg·Gk + γq·(Qk_princ + Σ ψ0·Qk_sec).

    NBR 8681:2003 / NBR 6118:2014. Devolve a combinação e o aviso de responsabilidade.
    """
    cr = combinar_elu_normal(
        gk=gk, qk_principal=qk_principal, qk_secundarias=qk_secundarias,
        gamma_g=gamma_g, gamma_q=gamma_q, psi0=psi0,
    )
    return {"resultado": cr.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def consultar_peso_material(nome: str) -> dict:
    """Peso específico (kN/m³) de um material da NBR 6120:2019 Tab.2 (ex.: 'concreto armado').

    Material fora da tabela => erro com a lista de opções (o agente deve abster-se).
    """
    lv = peso_especifico_material(nome)
    return {"resultado": lv.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def consultar_carga_uso(uso: str) -> dict:
    """Carga acidental de piso (kN/m²) por uso do ambiente (NBR 6120:2019).

    Uso fora da tabela => erro com a lista de opções (o agente deve abster-se).
    """
    lv = carga_acidental_uso(uso)
    return {"resultado": lv.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def verificar_unidades(valor: float, unidade_origem: str, unidade_destino: str) -> dict:
    """Converte/valida uma grandeza entre unidades (pint). Falha se as dimensões diferem."""
    valor_convertido = ensure(Q_(valor, unidade_origem), unidade_destino)
    return {"valor": valor_convertido, "unidade": unidade_destino}


# ============================================================== GEOTECNIA


@mcp.tool()
def capacidade_carga_fundacao(
    c_kpa: float,
    phi_deg: float,
    gamma_kn_m3: float,
    b_m: float,
    depth_df_m: float,
    shape: str = "quadrada",
    l_m: float | None = None,
    fs: float = 3.0,
) -> dict:
    """Capacidade de carga de fundação rasa pelo método de Vesic (NBR 6122).

    ``shape`` ∈ {corrida, quadrada, retangular, circular} (retangular exige ``l_m``).
    Devolve q_ult, q_adm, validação, memorial e o aviso de responsabilidade técnica.
    """
    return solve_bearing_capacity(
        c_kpa=c_kpa, phi_deg=phi_deg, gamma_kn_m3=gamma_kn_m3, b_m=b_m,
        depth_df_m=depth_df_m, shape=shape, l_m=l_m, fs=fs,
    )


@mcp.tool()
def recalque_elastico(
    q_kpa: float,
    b_m: float,
    poisson_nu: float,
    iw: float,
    es_kpa: float,
) -> dict:
    """Recalque elástico imediato s = q·B·(1−ν²)·Iw/Es (NBR 6122 ELS).

    Devolve o recalque (m e mm), a validação, o memorial e o aviso obrigatório.
    """
    return solve_elastic_settlement(
        q_kpa=q_kpa, b_m=b_m, poisson_nu=poisson_nu, iw=iw, es_kpa=es_kpa,
    )


@mcp.tool()
def recalque_adensamento(
    cc: float,
    e0: float,
    h_m: float,
    sigma0_kpa: float,
    delta_sigma_kpa: float,
) -> dict:
    """Recalque por adensamento primário (Terzaghi, argila NA) — NBR 6122 ELS.

    s = Cc/(1+e0)·H·log10((σ0+Δσ)/σ0). Devolve recalque, validação, memorial e aviso.
    """
    return solve_consolidation_settlement(
        cc=cc, e0=e0, h_m=h_m, sigma0_kpa=sigma0_kpa, delta_sigma_kpa=delta_sigma_kpa,
    )


@mcp.tool()
def empuxo_rankine(gamma_kn_m3: float, h_m: float, phi_deg: float) -> dict:
    """Empuxo de terra de Rankine (ativo e passivo) por metro de muro.

    Ka=tan²(45−φ/2), Kp=tan²(45+φ/2), E=0,5·γ·H²·K. Devolve coeficientes, empuxos,
    ponto de aplicação (H/3), validação, memorial e o aviso obrigatório.
    """
    return solve_earth_pressure_rankine(gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg)


@mcp.tool()
def empuxo_coulomb(
    gamma_kn_m3: float,
    h_m: float,
    phi_deg: float,
    delta_deg: float = 0.0,
    beta_deg: float = 0.0,
    alpha_deg: float = 0.0,
) -> dict:
    """Empuxo de terra de Coulomb com atrito do muro δ, tardoz β e terrapleno α.

    δ ∈ [0, φ]; α < φ. Devolve coeficientes, empuxos, validação, memorial e o aviso.
    """
    return solve_earth_pressure_coulomb(
        gamma_kn_m3=gamma_kn_m3, h_m=h_m, phi_deg=phi_deg,
        delta_deg=delta_deg, beta_deg=beta_deg, alpha_deg=alpha_deg,
    )


@mcp.tool()
def capacidade_estaca(
    layers: list[dict],
    pile_type: str,
    diameter_m: float,
    fs: float = 2.0,
    tol: float = 0.20,
) -> dict:
    """Capacidade de carga de estaca por SPT, comparando Aoki-Velloso × Décourt-Quaresma.

    ``layers`` é o perfil de sondagem: lista de objetos
    ``{"n_spt": int, "soil_type": str, "thickness_m": float}`` (do topo até a ponta).
    ``pile_type`` ∈ {pre-moldada, metalica, franki, escavada}. Roda os dois métodos,
    valida ambos e emite aviso se a divergência de Rult exceder ``tol`` (20%).
    Devolve Rult/Radm dos dois métodos, divergência, validação, memorial e o aviso.
    """
    return solve_pile_comparison(
        layers=layers, pile_type=pile_type, diameter_m=diameter_m, fs=fs, tol=tol,
    )


# ============================================================== HIDRÁULICA


@mcp.tool()
def escoamento_conduto(
    Q_m3s: float,
    D_m: float,
    L_m: float,
    metodo: str = "hazen-williams",
    C: float = 130.0,
    eps_m: float | None = None,
    nu_m2s: float = 1.0e-6,
) -> dict:
    """Escoamento em conduto forçado (tubulação sob pressão).

    ``metodo`` = "hazen-williams" (usa ``C``) ou "darcy-weisbach" (usa ``eps_m`` e o
    fator de atrito de Swamee-Jain). Devolve velocidade, perda de carga distribuída,
    validação (alerta de velocidade), memorial e o aviso de responsabilidade.
    """
    return solve_pipe_flow(
        Q_m3s=Q_m3s, D_m=D_m, L_m=L_m, metodo=metodo, C=C, eps_m=eps_m, nu_m2s=nu_m2s,
    )


@mcp.tool()
def canal_aberto_manning(
    geometria: str,
    n: float,
    S: float,
    y_m: float,
    b_m: float | None = None,
    z: float | None = None,
    D_m: float | None = None,
) -> dict:
    """Escoamento uniforme em canal aberto pela fórmula de Manning.

    ``geometria`` ∈ {retangular (usa ``b_m``), trapezoidal (usa ``b_m`` e ``z``),
    circular (usa ``D_m``)}. Devolve A, P, R, velocidade, vazão, validação (autolimpeza
    V≥0,5 m/s e erosão V≤3 m/s), memorial e o aviso obrigatório.
    """
    return solve_open_channel(
        geometria=geometria, n=n, S=S, y_m=y_m, b_m=b_m, z=z, D_m=D_m,
    )


@mcp.tool()
def perda_de_carga(
    hf_distribuida_m: float,
    singularidades: dict[str, int],
    V_ms: float,
) -> dict:
    """Perda de carga total = distribuída + Σ localizadas (coeficientes K).

    ``singularidades`` mapeia cada peça (ex.: "curva_90", "registro_gaveta_aberto") à
    sua quantidade. Tipo fora da tabela => erro (o agente deve abster-se). Devolve a
    composição das perdas, a validação, o memorial e o aviso obrigatório.
    """
    return solve_head_loss(
        hf_distribuida_m=hf_distribuida_m, singularidades=singularidades, V_ms=V_ms,
    )


# ============================================================== METÁLICAS (NBR 8800)


@mcp.tool()
def dimensionar_compressao_aco(
    designacao: str,
    kl_cm: float,
    fy_mpa: float = 250.0,
    e_mpa: float = 200000.0,
    q: float = 1.0,
    gamma_a1: float = 1.1,
) -> dict:
    """Dimensiona barra comprimida de aço à flambagem por flexão (NBR 8800:2008 §5.3).

    ``designacao`` é um perfil W do catálogo (ver ``consultar_perfil_w``). ``kl_cm`` é o
    comprimento de flambagem (KL); a flambagem governa no eixo de menor inércia (Iy).
    Hipótese: ``Q = 1`` (seção compacta, sem flambagem local) — se houver flambagem
    local (Q≠1), FLT, ou outro estado-limite, abstenha-se. Perfil inexistente => erro
    listando os disponíveis. Devolve Nc,Rd, validação, memorial e o aviso obrigatório.
    """
    return solve_compression(
        designacao=designacao, kl_cm=kl_cm, fy_mpa=fy_mpa, e_mpa=e_mpa,
        q=q, gamma_a1=gamma_a1,
    )


@mcp.tool()
def consultar_perfil_w(designacao: str) -> dict:
    """Consulta as propriedades geométricas de um perfil laminado W (catálogo NBR 8800).

    Devolve d, bf, tw, tf, área, inércias (Ix/Iy), módulos (Wx/Wy/Zx), raios (rx/ry) e
    massa linear. Perfil inexistente => erro listando os disponíveis (o agente deve
    abster-se em vez de inventar propriedades).
    """
    prof = get_profile(designacao, load_profiles())
    return {"resultado": prof.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def ligacao_parafusada(
    forca_kn: float,
    db_mm: float,
    fub_mpa: float,
    t_mm: float,
    fu_mpa: float,
    planos: int = 1,
    rosca_no_plano: bool = True,
    gamma_a2: float = 1.35,
) -> dict:
    """Dimensiona uma ligação parafusada solicitada ao cortante (NBR 8800:2008 §6.3).

    Calcula a resistência por parafuso como o mínimo entre cortante (§6.3.3.2) e pressão
    de contato (§6.3.3.3, limite 2,4·db·t·fu/γa2) e adota n = ⌈força/Rd⌉.
    ``rosca_no_plano=True`` usa coef. 0,4 (rosca no plano de corte); ``False`` usa 0,5.
    Hipótese: espaçamentos/distâncias às bordas mínimos atendidos — confirmar no
    detalhamento. Devolve resistências, nº de parafusos, validação, memorial e o aviso.
    """
    return solve_bolted_connection(
        forca_kn=forca_kn, db_mm=db_mm, fub_mpa=fub_mpa, t_mm=t_mm, fu_mpa=fu_mpa,
        planos=planos, rosca_no_plano=rosca_no_plano, gamma_a2=gamma_a2,
    )


@mcp.tool()
def solda_filete(
    forca_kn: float,
    perna_mm: float,
    fw_mpa: float = 485.0,
    gamma_a2: float = 1.35,
) -> dict:
    """Dimensiona o comprimento de solda de filete para uma força (NBR 8800:2008 §6.2.6).

    Rd = 0,6·fw·aw/γa2, com garganta aw = 0,7·perna; ``fw`` é a resistência do metal da
    solda (eletrodo E70 => 485 MPa). Considera o metal da solda governante e esforço
    paralelo ao eixo do filete. Devolve a resistência por cm, o comprimento necessário,
    a validação, o memorial e o aviso de responsabilidade técnica.
    """
    return solve_weld(forca_kn=forca_kn, perna_mm=perna_mm, fw_mpa=fw_mpa, gamma_a2=gamma_a2)


# ================================== PAVIMENTO / TERRAPLENAGEM / TALUDES


@mcp.tool()
def dimensionar_pavimento_flexivel(
    cbr_subleito: float,
    n_trafego: float,
    cbr_reforco: float | None = None,
    k_rev: float = 2.0,
    k_base: float = 1.0,
    k_subbase: float = 1.0,
    k_reforco: float = 1.0,
    r_cm: float | None = None,
) -> dict:
    """Dimensiona pavimento flexível pelo método empírico do DNER/DNIT (CBR / número N).

    ``n_trafego`` é o número N de solicitações do eixo padrão. ``cbr_reforco`` ativa a
    camada de reforço do subleito (opcional). ``r_cm`` fixa o revestimento (senão usa o
    mínimo DNER). Válido para CBR ∈ [2, 20]% e N ∈ [1e4, 1e8] — fora disso abstém-se.
    NÃO trata pavimento rígido nem método mecanístico-empírico. Devolve as espessuras
    por camada, a verificação das inequações, validação, memorial e o aviso obrigatório.
    """
    return solve_flexible_pavement(
        cbr_subleito=cbr_subleito, n_trafego=n_trafego, cbr_reforco=cbr_reforco,
        k_rev=k_rev, k_base=k_base, k_subbase=k_subbase, k_reforco=k_reforco, r_cm=r_cm,
    )


@mcp.tool()
def terraplenagem_balanco(
    volume_corte_m3: float,
    volume_aterro_m3: float,
    fator_empolamento: float = 1.0,
) -> dict:
    """Balanço de terraplenagem corte × aterro (volumes geométricos, áreas médias).

    ``balanco = corte − aterro``: positivo => excesso (bota-fora); negativo => déficit
    (empréstimo). ``fator_empolamento`` ∈ [1,0; 1,5] reporta o volume solto a
    transportar. Volumes negativos ou Fe fora da faixa => erro (o agente deve abster-se).
    Devolve volumes derivados, situação, validação, memorial e o aviso obrigatório.
    """
    return solve_earthwork(
        volume_corte_m3=volume_corte_m3, volume_aterro_m3=volume_aterro_m3,
        fator_empolamento=fator_empolamento,
    )


@mcp.tool()
def talude_infinito(
    c_kpa: float,
    phi_deg: float,
    gamma_kn_m3: float,
    z_m: float,
    beta_deg: float,
    u_kpa: float = 0.0,
) -> dict:
    """Fator de segurança de talude infinito (ruptura plana paralela à face).

    FS = [c + (γ·z·cos²β − u)·tanφ] / (γ·z·sinβ·cosβ). ``u`` é a poro-pressão na base
    (informe o valor calculado para percolação). Faixas físicas: φ∈[0,50]°,
    γ∈[10,25] kN/m³, β∈(0,90)°, c≥0, z>0 — fora delas abstém-se. FS,mín usual ≥ 1,5
    (NBR 11682). Devolve FS, classificação, validação, memorial e o aviso obrigatório.
    """
    return solve_infinite_slope(
        c_kpa=c_kpa, phi_deg=phi_deg, gamma_kn_m3=gamma_kn_m3, z_m=z_m,
        beta_deg=beta_deg, u_kpa=u_kpa,
    )


@mcp.tool()
def talude_fellenius(
    slices: list[dict],
    c_kpa: float,
    phi_deg: float,
) -> dict:
    """Estabilidade de talude por Fellenius (método ordinário das fatias, circular).

    ``slices`` é a lista de fatias ``{"w_kn": float, "alpha_deg": float, "dl_m": float,
    "u_kpa": float?}`` (W = peso por metro de talude; α = ângulo da base; ΔL = comprimento
    da base; u = poro-pressão). FS = Σ[c·ΔL + (W·cosα − u·ΔL)·tanφ] / Σ(W·sinα). Conservador
    frente a Bishop simplificado (FORA DE ESCOPO — exige iteração). Lista vazia, ΔL≤0 ou W≤0
    => erro (abster-se). Devolve FS, classificação, validação, memorial e o aviso obrigatório.
    """
    return solve_fellenius(slices=slices, c_kpa=c_kpa, phi_deg=phi_deg)


# ============================================================== NORMAS (consulta)


@mcp.tool()
def consultar_tabela_norma(termo: str, base_dir: str = "normas") -> dict:
    """Busca LÉXICA por ``termo`` nas tabelas normativas (``normas/<NORMA>/tables/*.json``).

    Casamento por substring, sem acento e case-insensitive — NÃO usa embeddings/semântica.
    Devolve SÓ o que está tabelado (chave + dados de cada entrada que casa); termo sem
    correspondência => lista vazia (o agente deve abster-se, nunca inventar valor de norma).
    """
    base = base_dir if pathlib.Path(base_dir).is_absolute() else str(_ROOT / base_dir)
    resultados = buscar_tabela(termo, base_dir=base)
    return {"termo": termo, "resultados": resultados, "n": len(resultados), "aviso": DISCLAIMER}


@mcp.tool()
def interpolar_tabela(x: float, xs: list[float], ys: list[float]) -> dict:
    """Interpolação LINEAR de y(x) numa tabela 1D (NBR — coeficientes tabelados).

    ``xs`` deve ser estritamente crescente e ``ys`` ter o mesmo comprimento. Sem
    extrapolação: ``x`` fora de ``[xs[0], xs[-1]]`` => erro (princípio da abstenção). Use
    sobre valores obtidos de ``consultar_tabela_norma`` — não invente os nós da tabela.
    """
    y = linear_interp(x, xs, ys)
    return {"resultado": {"x": x, "y": y}, "aviso": DISCLAIMER}


# ============================================================== ORÇAMENTO


@mcp.tool()
def montar_orcamento(
    itens: list[dict],
    bdi_pct: float = 0.0,
    csv_path: str = "data/sinapi_amostra.csv",
) -> dict:
    """Monta um orçamento (custo direto + BDI) a partir de quantitativos.

    ``itens`` é a lista ``[{"codigo": str, "quantidade": float}, ...]``; os preços vêm
    da base tipo SINAPI em ``csv_path``. ATENÇÃO: a base de amostra é ILUSTRATIVA —
    substitua pela SINAPI vigente/regional (desoneração, mês de referência e UF). BDI ∈
    [0, 40] %. Código inexistente => erro (o agente deve abster-se). Devolve itens,
    subtotal, BDI, total, validação aritmética, memorial e o aviso obrigatório.
    """
    return solve_orcamento(itens=itens, bdi_pct=bdi_pct, csv_path=csv_path)


@mcp.tool()
def consultar_preco_sinapi(
    codigo: str,
    csv_path: str = "data/sinapi_amostra.csv",
) -> dict:
    """Consulta o preço unitário de um código na base tipo SINAPI (amostra ilustrativa).

    Código fora da base => erro (o agente deve abster-se em vez de inventar preço).
    Devolve o item (código, descrição, unidade, preço unitário) e o aviso obrigatório.
    """
    item = lookup(codigo, load_sinapi(csv_path))
    return {"resultado": item.model_dump(), "aviso": DISCLAIMER}


# ============================================================== PROJETOS / DOCUMENTAÇÃO


@mcp.tool()
def salvar_projeto(
    project_id: str,
    nome: str,
    responsavel: str | None = None,
    criado_em: str | None = None,
    metadados: dict | None = None,
    base_dir: str = "memory/projects",
) -> dict:
    """Cria/sobrescreve o registro de um projeto na memória persistente (JSON por projeto).

    ``project_id`` deve ser um nome de arquivo seguro (letras, dígitos, '_', '-', '.');
    id inseguro => erro. Devolve o registro salvo, o caminho do arquivo e o aviso.
    """
    record = ProjectRecord(
        project_id=project_id,
        nome=nome,
        responsavel=responsavel,
        criado_em=criado_em,
        metadados=metadados or {},
    )
    caminho = save_project(record, base_dir=base_dir)
    return {"resultado": record.model_dump(), "caminho": caminho, "aviso": DISCLAIMER}


@mcp.tool()
def carregar_projeto(project_id: str, base_dir: str = "memory/projects") -> dict:
    """Carrega o registro completo de um projeto (com o histórico de cálculos).

    Projeto inexistente ou id inseguro => erro (o agente deve abster-se). Devolve o
    registro e o aviso obrigatório.
    """
    record = load_project(project_id, base_dir=base_dir)
    return {"resultado": record.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def listar_projetos(base_dir: str = "memory/projects") -> dict:
    """Lista os ``project_id`` existentes na memória persistente (ordenados)."""
    return {"projetos": list_projects(base_dir=base_dir)}


@mcp.tool()
def registrar_calculo_no_projeto(
    project_id: str,
    bundle: dict,
    base_dir: str = "memory/projects",
    timestamp: str | None = None,
) -> dict:
    """Anexa um cálculo (bundle do service) ao histórico de um projeto e regrava o arquivo.

    Idempotente para bundles idênticos. ``timestamp`` (ISO, fornecido pelo chamador) é
    registrado em ``registrado_em``. Devolve o registro atualizado e o aviso.
    """
    record = add_calculo(project_id, bundle, base_dir=base_dir, timestamp=timestamp)
    return {"resultado": record.model_dump(), "aviso": DISCLAIMER}


@mcp.tool()
def gerar_relatorio_projeto(project_id: str, base_dir: str = "memory/projects") -> dict:
    """Gera o relatório técnico consolidado (Markdown) com todos os cálculos do projeto.

    Costura os memoriais do histórico sob um cabeçalho do projeto e o índice de cálculos,
    terminando com o aviso de responsabilidade técnica. Devolve o Markdown e o aviso.
    """
    record = load_project(project_id, base_dir=base_dir)
    return {"relatorio_markdown": build_project_report(record), "aviso": DISCLAIMER}


@mcp.tool()
def listar_capacidades() -> dict:
    """Lista os cálculos disponíveis. Se o pedido não estiver aqui, o agente deve abster-se."""
    return {
        "calculos": [
            "dimensionar_viga_retangular — flexão simples, seção retangular (NBR 6118:2014)",
            "dimensionar_pilar — flexão composta normal com 2ª ordem, λ≤90 (NBR 6118:2014)",
            "dimensionar_sapata — sapata isolada quadrada rígida, bielas (NBR 6122/6118)",
            "dimensionar_laje_uma_direcao — laje maciça armada em uma direção (NBR 6118)",
            "dimensionar_laje_duas_direcoes — laje maciça apoiada nos 4 lados (NBR 6118)",
            "capacidade_carga_fundacao — capacidade de carga de fundação rasa, Vesic (NBR 6122)",
            "recalque_elastico — recalque elástico imediato (NBR 6122 ELS)",
            "recalque_adensamento — recalque por adensamento primário, Terzaghi (NBR 6122 ELS)",
            "empuxo_rankine — empuxo de terra de Rankine (contenção)",
            "empuxo_coulomb — empuxo de terra de Coulomb com δ/β/α (contenção)",
            "capacidade_estaca — estaca por SPT, Aoki-Velloso × Décourt-Quaresma (NBR 6122)",
            "dimensionar_compressao_aco — barra comprimida, flambagem por flexão (NBR 8800:2008)",
            "consultar_perfil_w — propriedades geométricas de perfil laminado W (NBR 8800)",
            "ligacao_parafusada — ligação parafusada à cortante, nº de parafusos (NBR 8800 §6.3)",
            "solda_filete — comprimento de solda de filete (NBR 8800 §6.2.6)",
            "consultar_tabela_norma — busca léxica nas tabelas das normas (só o tabelado)",
            "interpolar_tabela — interpolação linear de coeficientes tabelados (sem extrapolar)",
            "escoamento_conduto — conduto forçado, Hazen-Williams ou Darcy-Weisbach",
            "canal_aberto_manning — escoamento uniforme em canal aberto (Manning)",
            "perda_de_carga — perda distribuída + localizadas (coeficientes K)",
            "dimensionar_pavimento_flexivel — pavimento flexível, método empírico (DNER/DNIT)",
            "terraplenagem_balanco — balanço corte/aterro, empolamento (DNIT, áreas médias)",
            "talude_infinito — FS de talude infinito (Das / NBR 11682)",
            "talude_fellenius — FS de talude por Fellenius, fatias circulares (NBR 11682)",
            "montar_orcamento — orçamento custo direto + BDI, base tipo SINAPI (amostra)",
            "consultar_preco_sinapi — preço unitário de um código na base SINAPI (amostra)",
            "combinar_acoes_elu — combinação última normal de ações (NBR 8681/6118)",
            "consultar_peso_material — peso específico de material (NBR 6120:2019 Tab.2)",
            "consultar_carga_uso — carga acidental por uso do ambiente (NBR 6120:2019)",
            "verificar_unidades — conversão/validação dimensional (pint)",
        ],
        "memoria_e_documentacao": [
            "salvar_projeto — cria/atualiza o registro de um projeto (memória persistente)",
            "carregar_projeto — carrega um projeto e seu histórico de cálculos",
            "listar_projetos — lista os projetos existentes na memória",
            "registrar_calculo_no_projeto — anexa um bundle de cálculo ao histórico",
            "gerar_relatorio_projeto — relatório técnico consolidado (Markdown) do projeto",
        ],
        "nota": (
            "Resultados numéricos só vêm destas ferramentas. Para cálculos não listados, "
            "informe que não há ferramenta disponível — não invente valores. Os preços "
            "SINAPI são de AMOSTRA e devem ser atualizados pela tabela vigente/regional."
        ),
    }


def _selftest() -> int:
    viga = solve_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )
    pilar = solve_rectangular_column(
        nk_kn=500.0, mk_topo_knm=20.0, b_cm=40.0, h_cm=30.0, le_cm=300.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    )
    sapata = solve_square_footing(
        nk_kn=500.0, sigma_adm_kpa=200.0, pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    # geotecnia: capacidade de carga de fundação rasa (Vesic)
    fundacao = solve_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0, b_m=2.0, depth_df_m=1.5,
    )
    # metálicas: barra comprimida de aço (NBR 8800 §5.3)
    aco = solve_compression(designacao="W250x22,3", kl_cm=300.0, fy_mpa=250.0)
    # hidráulica: conduto forçado por Hazen-Williams
    conduto = solve_pipe_flow(
        Q_m3s=0.05, D_m=0.30, L_m=1000.0, metodo="hazen-williams", C=130.0,
    )
    # orçamento: alguns itens da base de amostra com BDI 25%
    orcamento = solve_orcamento(
        itens=[
            {"codigo": "92873", "quantidade": 1.5},
            {"codigo": "92915", "quantidade": 180.0},
            {"codigo": "92438", "quantidade": 18.0},
        ],
        bdi_pct=25.0,
        csv_path=str(_ROOT / "data" / "sinapi_amostra.csv"),
    )
    # estabilidade de taludes: talude infinito (Das / NBR 11682)
    talude = solve_infinite_slope(
        c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0, z_m=3.0, beta_deg=20.0,
    )
    bundles = [viga, pilar, sapata, fundacao, aco, conduto, orcamento, talude]
    ok = all(b["aprovado"] and "6.496/77" in b["aviso"] for b in bundles)
    print("SELFTEST OK" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    mcp.run()
