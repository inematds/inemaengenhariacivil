"""Ligações metálicas — parafusos e solda de filete (NBR 8800:2008 §6).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado.

Unidades internas: cm, kN e kN/cm² (1 MPa = 0,1 kN/cm²); os diâmetros, espessuras e
pernas de solda entram em **mm** (uso de projeto). As funções devolvem resistências
em kN (parafusos) ou kN/cm (solda, por unidade de comprimento).

Métodos e hipóteses normativas:

- Parafusos — cortante (NBR 8800:2008 §6.3.3.2):
  Fv,Rd = c · Ab · fub / γa2, por plano de corte, com c = 0,4 quando o plano de
  corte passa pela parte **rosqueada** do parafuso e c = 0,5 quando passa pela parte
  **não rosqueada** (fuste). Ab = π·db²/4 (área bruta da seção do parafuso). Para
  corte duplo (n planos) multiplica-se por ``planos``. γa2 = 1,35.

- Parafusos — pressão de contato / esmagamento da chapa (NBR 8800:2008 §6.3.3.3):
  a expressão completa é Fc,Rd = 1,2·lf·t·fu/γa2 ≤ 2,4·db·t·fu/γa2, sendo lf a
  distância livre, na direção da força, entre a borda do furo e a borda do furo
  adjacente ou da peça. Aqui adota-se o **limite superior** usual
  Fc,Rd = 2,4·db·t·fu/γa2, ou seja, assume-se que os espaçamentos e distâncias às
  bordas atendem aos mínimos da NBR 8800 (a parcela 1,2·lf não governa). Essa
  hipótese deve ser confirmada no detalhamento pelo engenheiro responsável
  (princípio da abstenção). γa2 = 1,35.

- Solda de filete (NBR 8800:2008 §6.2.6):
  resistência por unidade de comprimento Rd = 0,6·fw·aw/γa2, com garganta efetiva
  aw = 0,7·perna (filete de pernas iguais) e 0,6·fw como resistência ao cisalhamento
  do metal da solda. fw é a resistência à ruptura do metal da solda (eletrodo E70 →
  fw = 485 MPa). Considera-se o metal da solda governante (não o metal-base) e
  esforço paralelo ao eixo do filete (sem o fator 1 + 0,5·sen^1,5θ). γa2 = 1,35.

O detalhamento completo (espaçamentos, distâncias às bordas, ruptura por
rasgamento/colapso de bloco, soldas mínimas por espessura) é de responsabilidade do
engenheiro — fora do escopo deste núcleo.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- constantes normativas (NBR 8800:2008) -----------------------------------
GAMMA_A2 = 1.35           # ponderação da resistência (ruptura) — NBR 8800 Tabela 3
COEF_ROSCA = 0.4          # plano de corte na parte rosqueada — §6.3.3.2
COEF_FUSTE = 0.5          # plano de corte fora da rosca (fuste) — §6.3.3.2
COEF_CISALH_SOLDA = 0.6   # 0,6·fw = cisalhamento do metal da solda — §6.2.6
COEF_GARGANTA = 0.7       # garganta efetiva aw = 0,7·perna (filete) — §6.2.6.1
COEF_ESMAG = 2.4          # limite superior do esmagamento (2,4·db·t·fu) — §6.3.3.3
FW_E70_MPA = 485.0        # resistência do metal da solda, eletrodo E70 (MPa)

# Bitolas comerciais usuais de parafusos estruturais (mm) e faixa aceita
BITOLAS_USUAIS_MM = (12.5, 16.0, 20.0, 22.0, 25.0)
DB_MIN_MM = 12.5
DB_MAX_MM = 25.0
PERNA_MIN_MM = 3.0        # perna mínima prática de filete (mm)

_MPA_TO_KNCM2 = 0.1       # 1 MPa = 0,1 kN/cm²


class BoltedConnectionResult(BaseModel):
    """Resultado do dimensionamento de uma ligação parafusada à cortante."""
    # entrada (eco)
    forca_kn: float
    db_mm: float
    fub_mpa: float
    t_mm: float
    fu_mpa: float
    planos: int
    rosca_no_plano: bool
    gamma_a2: float
    # geometria
    ab_cm2: float
    # resistências por parafuso
    fv_rd_kn: float          # cortante
    fc_rd_kn: float          # pressão de contato (esmagamento)
    rd_bolt_kn: float        # governante (mínimo)
    governante: str          # "cortante" | "pressão de contato"
    # dimensionamento
    n_parafusos: int
    capacidade_total_kn: float
    # metadados
    norma: str = "NBR 8800:2008"
    warnings: list[str] = []


class WeldResult(BaseModel):
    """Resultado do dimensionamento de uma solda de filete."""
    # entrada (eco)
    forca_kn: float
    perna_mm: float
    fw_mpa: float
    gamma_a2: float
    # geometria e resistência
    aw_cm: float             # garganta efetiva
    rd_kn_cm: float          # resistência por unidade de comprimento
    comprimento_nec_cm: float
    # metadados
    norma: str = "NBR 8800:2008"
    warnings: list[str] = []


def _require_positive(**valores: float) -> None:
    """Abstenção: rejeita entradas não positivas com mensagem clara."""
    for nome, v in valores.items():
        if v <= 0:
            raise ValueError(f"{nome}={v} inválido: deve ser > 0.")


def _bitola_warnings(db_mm: float) -> list[str]:
    if not (DB_MIN_MM <= db_mm <= DB_MAX_MM):
        return [
            f"bitola db={db_mm:g} mm fora da faixa usual "
            f"[{DB_MIN_MM:g}, {DB_MAX_MM:g}] mm de parafusos estruturais."
        ]
    return []


def bolt_shear_resistance(
    db_mm: float,
    fub_mpa: float,
    planos: int = 1,
    rosca_no_plano: bool = True,
    gamma_a2: float = GAMMA_A2,
) -> float:
    """Resistência de cálculo ao cortante de um parafuso, em kN (NBR 8800 §6.3.3.2).

    ``rosca_no_plano=True`` usa o coeficiente 0,4 (plano de corte na rosca);
    ``False`` usa 0,5 (plano no fuste). ``planos`` é o número de planos de corte.
    """
    _require_positive(db_mm=db_mm, fub_mpa=fub_mpa, gamma_a2=gamma_a2)
    if planos < 1:
        raise ValueError(f"planos={planos} inválido: deve ser >= 1.")

    db_cm = db_mm / 10.0
    ab_cm2 = math.pi * db_cm**2 / 4.0
    fub_kncm2 = fub_mpa * _MPA_TO_KNCM2
    coef = COEF_ROSCA if rosca_no_plano else COEF_FUSTE
    return coef * ab_cm2 * fub_kncm2 / gamma_a2 * planos


def bolt_bearing_resistance(
    db_mm: float,
    t_mm: float,
    fu_mpa: float,
    gamma_a2: float = GAMMA_A2,
) -> float:
    """Resistência ao esmagamento (pressão de contato), em kN (NBR 8800 §6.3.3.3).

    Adota o limite superior Fc,Rd = 2,4·db·t·fu/γa2 (espaçamentos/bordas mínimos
    atendidos — ver hipóteses no docstring do módulo).
    """
    _require_positive(db_mm=db_mm, t_mm=t_mm, fu_mpa=fu_mpa, gamma_a2=gamma_a2)

    db_cm = db_mm / 10.0
    t_cm = t_mm / 10.0
    fu_kncm2 = fu_mpa * _MPA_TO_KNCM2
    return COEF_ESMAG * db_cm * t_cm * fu_kncm2 / gamma_a2


def design_bolted_connection(
    forca_kn: float,
    db_mm: float,
    fub_mpa: float,
    t_mm: float,
    fu_mpa: float,
    planos: int = 1,
    rosca_no_plano: bool = True,
    gamma_a2: float = GAMMA_A2,
) -> BoltedConnectionResult:
    """Dimensiona o número de parafusos de uma ligação solicitada à cortante.

    Calcula a resistência por parafuso como o mínimo entre cortante e pressão de
    contato e adota ``n = ceil(forca / Rd_parafuso)``. Reporta a resistência de cada
    modo, o modo governante e a capacidade total da ligação.
    """
    _require_positive(forca_kn=forca_kn, db_mm=db_mm, fub_mpa=fub_mpa,
                      t_mm=t_mm, fu_mpa=fu_mpa, gamma_a2=gamma_a2)
    if planos < 1:
        raise ValueError(f"planos={planos} inválido: deve ser >= 1.")

    fv_rd = bolt_shear_resistance(db_mm, fub_mpa, planos, rosca_no_plano, gamma_a2)
    fc_rd = bolt_bearing_resistance(db_mm, t_mm, fu_mpa, gamma_a2)

    if fc_rd < fv_rd:
        rd_bolt = fc_rd
        governante = "pressão de contato"
    else:
        rd_bolt = fv_rd
        governante = "cortante"

    n = math.ceil(forca_kn / rd_bolt - 1e-9)
    n = max(n, 1)

    db_cm = db_mm / 10.0
    ab_cm2 = math.pi * db_cm**2 / 4.0

    return BoltedConnectionResult(
        forca_kn=forca_kn, db_mm=db_mm, fub_mpa=fub_mpa, t_mm=t_mm, fu_mpa=fu_mpa,
        planos=planos, rosca_no_plano=rosca_no_plano, gamma_a2=gamma_a2,
        ab_cm2=ab_cm2,
        fv_rd_kn=fv_rd, fc_rd_kn=fc_rd, rd_bolt_kn=rd_bolt, governante=governante,
        n_parafusos=n, capacidade_total_kn=n * rd_bolt,
        warnings=_bitola_warnings(db_mm),
    )


def fillet_weld_resistance(
    perna_mm: float,
    fw_mpa: float = FW_E70_MPA,
    gamma_a2: float = GAMMA_A2,
) -> float:
    """Resistência da solda de filete por unidade de comprimento, em kN/cm.

    Rd = 0,6·fw·aw/γa2, com aw = 0,7·perna (NBR 8800 §6.2.6).
    """
    _require_positive(perna_mm=perna_mm, fw_mpa=fw_mpa, gamma_a2=gamma_a2)

    perna_cm = perna_mm / 10.0
    aw_cm = COEF_GARGANTA * perna_cm
    fw_kncm2 = fw_mpa * _MPA_TO_KNCM2
    return COEF_CISALH_SOLDA * fw_kncm2 * aw_cm / gamma_a2


def design_fillet_weld(
    forca_kn: float,
    perna_mm: float,
    fw_mpa: float = FW_E70_MPA,
    gamma_a2: float = GAMMA_A2,
) -> WeldResult:
    """Dimensiona o comprimento necessário de solda de filete para ``forca_kn``.

    ``comprimento_nec = forca / Rd`` (Rd por unidade de comprimento, NBR 8800 §6.2.6).
    """
    _require_positive(forca_kn=forca_kn, perna_mm=perna_mm, fw_mpa=fw_mpa,
                      gamma_a2=gamma_a2)

    rd = fillet_weld_resistance(perna_mm, fw_mpa, gamma_a2)
    perna_cm = perna_mm / 10.0
    aw_cm = COEF_GARGANTA * perna_cm

    warnings: list[str] = []
    if perna_mm < PERNA_MIN_MM:
        warnings.append(
            f"perna={perna_mm:g} mm abaixo do mínimo prático de {PERNA_MIN_MM:g} mm."
        )

    return WeldResult(
        forca_kn=forca_kn, perna_mm=perna_mm, fw_mpa=fw_mpa, gamma_a2=gamma_a2,
        aw_cm=aw_cm, rd_kn_cm=rd, comprimento_nec_cm=forca_kn / rd,
        warnings=warnings,
    )
