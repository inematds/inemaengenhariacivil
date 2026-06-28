"""Sapata isolada quadrada rígida — dimensionamento (NBR 6122 + NBR 6118:2014).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Método e hipóteses:
- Área da base pela tensão admissível do solo (NBR 6122): Nk majorado por ~5% para
  estimar o peso próprio da sapata -> A_nec = 1.05·Nk / σ_adm; lado L = √A_nec
  arredondado para cima a múltiplo de 5 cm e nunca menor que o pilar.
- Verificação da tensão no solo com o peso próprio real adotado:
  σ_solo = (Nk + pp_sapata) / A_efetiva ≤ σ_adm, pp = γ_conc · A_ef · h, γ_conc=25 kN/m³.
- Sapata RÍGIDA (NBR 6118:2014 22.6.1): h ≥ (L − a_pilar)/3 em cada direção.
- Armadura de flexão pelo MÉTODO DAS BIELAS (NBR 6118:2014 22.6.4.1):
  As,dir = Nd·(L − a_pilar,dir) / (8·d·fyd), com Nd = γf·Nk (γf = 1.4).
  O detalhamento (espaçamento, ancoragem, As,mín da NBR 6118 19.3.3) deve ser
  verificado pelo engenheiro — fora do escopo deste núcleo (princípio da abstenção).
- d ≈ h − cobrimento − φ (aproximação para as duas camadas ortogonais de barras).
"""

from __future__ import annotations

import math

from pydantic import BaseModel

from lib.concrete.beams import BarChoice, select_bars

# --- constantes normativas ---------------------------------------------------
GAMMA_F = 1.4         # ponderação da carga do pilar (Nd = γf·Nk) — NBR 6118 11.7
GAMMA_S = 1.15        # ponderação do aço — NBR 6118
PESO_CONCRETO = 25.0  # kN/m³ (NBR 6120:2019) — peso próprio da sapata
FATOR_PESO_PROPRIO = 1.05   # majoração de Nk p/ pré-dimensionar a área (~5%)
MODULO_CM = 5.0       # múltiplo de arredondamento do lado/altura (cm)
SIGMA_ADM_MIN = 50.0    # kPa — faixa física aceita pelo método simplificado
SIGMA_ADM_MAX = 1000.0  # kPa


class FootingResult(BaseModel):
    """Resultado completo do dimensionamento de uma sapata isolada quadrada rígida."""

    # entrada (eco)
    nk_kn: float
    sigma_adm_kpa: float
    pilar_a_cm: float
    pilar_b_cm: float
    fck_mpa: float
    fyk_mpa: float
    # geometria
    area_nec_m2: float
    lado_cm: float
    area_efetiva_m2: float
    altura_h_cm: float
    d_cm: float
    # solo
    pp_sapata_kn: float
    sigma_solo_kpa: float
    rigida: bool
    # armadura (método das bielas)
    nd_kn: float
    fyd_mpa: float
    as_x_cm2: float
    as_y_cm2: float
    bars_x: BarChoice
    bars_y: BarChoice
    # metadados
    norma: str = "NBR 6122 / NBR 6118:2014"
    warnings: list[str] = []


def _check_inputs(nk_kn: float, sigma_adm_kpa: float, pilar_a_cm: float,
                  pilar_b_cm: float, fck_mpa: float, fyk_mpa: float) -> None:
    if nk_kn <= 0:
        raise ValueError(f"Nk={nk_kn} kN deve ser positivo (carga de compressão do pilar).")
    if sigma_adm_kpa <= 0:
        raise ValueError(f"σ_adm={sigma_adm_kpa} kPa deve ser positivo.")
    if pilar_a_cm <= 0 or pilar_b_cm <= 0:
        raise ValueError(f"Dimensões do pilar devem ser positivas (a={pilar_a_cm}, b={pilar_b_cm}).")
    if not (10.0 <= fck_mpa <= 100.0):
        raise ValueError(f"fck={fck_mpa} MPa fora da faixa física [10, 100].")
    if fck_mpa > 50.0:
        raise ValueError("fck > 50 MPa (Grupo II) ainda não implementado para sapatas.")
    if not (250.0 <= fyk_mpa <= 600.0):
        raise ValueError(f"fyk={fyk_mpa} MPa fora da faixa de aços comerciais [250, 600].")


def _arredonda_para_cima(valor_cm: float, modulo_cm: float) -> float:
    """Arredonda ``valor_cm`` para cima ao próximo múltiplo de ``modulo_cm``."""
    return math.ceil(valor_cm / modulo_cm - 1e-9) * modulo_cm


def _as_biela(nd_kn: float, balanco_cm: float, d_cm: float, fyd_k: float) -> float:
    """As pela biela: Nd·(L − a)/(8·d·fyd). Unidades em kN, cm, kN/cm² -> cm²."""
    return nd_kn * balanco_cm / (8.0 * d_cm * fyd_k)


def design_square_footing(
    nk_kn: float,
    sigma_adm_kpa: float,
    pilar_a_cm: float,
    pilar_b_cm: float,
    fck_mpa: float,
    fyk_mpa: float,
    cobrimento_cm: float = 5.0,
    phi_long_mm: float = 12.5,
    fator_peso_proprio: float = FATOR_PESO_PROPRIO,
    peso_concreto: float = PESO_CONCRETO,
    modulo_cm: float = MODULO_CM,
) -> FootingResult:
    """Dimensiona uma sapata isolada quadrada rígida sob carga centrada ``nk_kn``.

    Sequência: área pela tensão admissível -> lado L (múltiplo de 5 cm, ≥ pilar) ->
    altura rígida h ≥ (L−a)/3 -> verificação de σ_solo com peso próprio real ->
    armadura por direção pelo método das bielas (NBR 6118 22.6.4.1).

    Entradas inválidas (Nk≤0, σ_adm≤0, pilar≤0, fck>50, fyk fora de faixa) levantam
    ``ValueError`` (abstenção). Se σ_solo exceder σ_adm, devolve o resultado com
    aviso — cabe ao engenheiro ampliar a sapata.
    """
    _check_inputs(nk_kn, sigma_adm_kpa, pilar_a_cm, pilar_b_cm, fck_mpa, fyk_mpa)

    # 1) área e lado --------------------------------------------------------
    area_nec_m2 = fator_peso_proprio * nk_kn / sigma_adm_kpa     # kN / kPa = m²
    lado_min_cm = math.sqrt(area_nec_m2) * 100.0                 # m -> cm
    lado_min_cm = max(lado_min_cm, pilar_a_cm, pilar_b_cm)
    lado_cm = _arredonda_para_cima(lado_min_cm, modulo_cm)
    area_efetiva_m2 = (lado_cm / 100.0) ** 2

    # 2) altura rígida ------------------------------------------------------
    balanco_max_cm = max(lado_cm - pilar_a_cm, lado_cm - pilar_b_cm)
    h_min_rigida_cm = balanco_max_cm / 3.0
    altura_h_cm = _arredonda_para_cima(h_min_rigida_cm, modulo_cm)
    rigida = altura_h_cm >= h_min_rigida_cm - 1e-9
    d_cm = altura_h_cm - cobrimento_cm - (phi_long_mm / 10.0)

    # 3) tensão no solo com peso próprio real -------------------------------
    pp_sapata_kn = peso_concreto * area_efetiva_m2 * (altura_h_cm / 100.0)
    sigma_solo_kpa = (nk_kn + pp_sapata_kn) / area_efetiva_m2

    # 4) armadura pelo método das bielas ------------------------------------
    nd_kn = GAMMA_F * nk_kn
    fyd_mpa = fyk_mpa / GAMMA_S
    fyd_k = fyd_mpa * 0.1                                        # MPa -> kN/cm²
    as_x_cm2 = _as_biela(nd_kn, lado_cm - pilar_a_cm, d_cm, fyd_k)
    as_y_cm2 = _as_biela(nd_kn, lado_cm - pilar_b_cm, d_cm, fyd_k)
    bars_x = select_bars(as_x_cm2, n_min=5, n_max=40)
    bars_y = select_bars(as_y_cm2, n_min=5, n_max=40)

    # 5) avisos -------------------------------------------------------------
    warnings: list[str] = []
    if sigma_solo_kpa > sigma_adm_kpa + 1e-9:
        warnings.append(
            f"Tensão no solo σ={sigma_solo_kpa:.1f} kPa > σ_adm={sigma_adm_kpa:.1f} kPa "
            "(peso próprio real superou a estimativa de 5%): ampliar o lado da sapata."
        )
    if not rigida:
        warnings.append(
            f"Sapata não rígida: h={altura_h_cm:.0f} < (L−a)/3={h_min_rigida_cm:.1f} cm "
            "(NBR 6118 22.6.1) — o método das bielas não se aplica."
        )

    return FootingResult(
        nk_kn=nk_kn, sigma_adm_kpa=sigma_adm_kpa,
        pilar_a_cm=pilar_a_cm, pilar_b_cm=pilar_b_cm,
        fck_mpa=fck_mpa, fyk_mpa=fyk_mpa,
        area_nec_m2=area_nec_m2, lado_cm=lado_cm, area_efetiva_m2=area_efetiva_m2,
        altura_h_cm=altura_h_cm, d_cm=d_cm,
        pp_sapata_kn=pp_sapata_kn, sigma_solo_kpa=sigma_solo_kpa, rigida=rigida,
        nd_kn=nd_kn, fyd_mpa=fyd_mpa,
        as_x_cm2=as_x_cm2, as_y_cm2=as_y_cm2, bars_x=bars_x, bars_y=bars_y,
        warnings=warnings,
    )
