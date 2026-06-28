"""Dimensionamento de pavimento flexível — método empírico DNER/DNIT (CBR / N).

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado. O aviso de
responsabilidade técnica NÃO é inserido aqui (entra na camada de integração).

Fonte do método
---------------
DNER (1981), "Método de Projeto de Pavimentos Flexíveis" (Eng. Murillo Lopes de
Souza), reproduzido no DNIT (2006) "Manual de Pavimentação". O dimensionamento é
empírico, baseado no CBR do subleito e no número N de solicitações do eixo padrão
de 8,2 tf.

Hipóteses adotadas
------------------
1. Espessura total de material granular equivalente sobre uma camada de CBR dado,
   por ajuste analítico do ábaco de dimensionamento do DNER:

       H = 77,67 · N^0,0482 · CBR^-0,598   [cm]

   (curva de ajuste largamente citada na literatura de pavimentação brasileira —
   aproximação do nomograma; documentada explicitamente como hipótese).
2. Coeficientes de equivalência estrutural K (DNER): revestimento em concreto
   asfáltico K_R = 2,0; base granular K_B = 1,0; sub-base granular K_S = 1,0;
   reforço do subleito K_ref = 1,0. São parametrizáveis na função.
3. Verificação por inequações de equivalência estrutural (DNER):
       R·K_R + B·K_B                         >= H20   (espessura sobre a sub-base)
       R·K_R + B·K_B + S·K_S                 >= Hn    (sobre o reforço, se houver)
       R·K_R + B·K_B + S·K_S + Ref·K_ref     >= Hm    (sobre o subleito)
   onde H20 usa CBR = 20 (mínimo exigido para a sub-base), Hn usa o CBR do reforço
   e Hm usa o CBR do subleito.
4. Espessura mínima do revestimento betuminoso pela tabela do DNER em função de N.
5. Espessuras das camadas granulares adotadas em cm inteiros (arredondamento para
   cima) e respeitando mínimos construtivos/de compactação.

O método é válido para subleito com 2% <= CBR <= 20% (acima disso a espessura é
governada por mínimos construtivos) e expansão <= 2% (não verificada aqui).
"""

from __future__ import annotations

import math

from pydantic import BaseModel

# --- faixas de validade (abstenção fora delas) ------------------------------
CBR_MIN = 2.0          # % — abaixo, subleito impróprio para o método empírico
CBR_MAX = 20.0         # % — acima, espessura governada por mínimos construtivos
N_MIN = 1.0e4          # número N — limite inferior razoável do método
N_MAX = 1.0e8          # número N — limite superior razoável do método
CBR_SUBBASE = 20.0     # CBR de referência da sub-base (DNER)

# --- coeficientes de equivalência estrutural K (DNER) -----------------------
K_REV_PADRAO = 2.0     # revestimento de concreto asfáltico (CBUQ)
K_BASE_PADRAO = 1.0    # base granular (brita graduada / estabilizada)
K_SUBBASE_PADRAO = 1.0  # sub-base granular
K_REFORCO_PADRAO = 1.0  # reforço do subleito

# --- coeficiente da equação de ajuste do ábaco DNER -------------------------
_A_COEF = 77.67
_N_EXP = 0.0482
_CBR_EXP = -0.598

# --- mínimos construtivos das camadas (cm) ----------------------------------
MIN_BASE_CM = 15.0
MIN_SUBBASE_CM = 15.0
MIN_REFORCO_CM = 15.0

TOL = 1e-6


class PavementInequality(BaseModel):
    """Inequação de equivalência estrutural verificada (DNER)."""
    nome: str
    esquerda_cm: float   # Σ espessura·K acumulada (material granular equivalente)
    direita_cm: float    # espessura H exigida sobre a camada (CBR de referência)
    atende: bool


class PavementResult(BaseModel):
    """Resultado completo do dimensionamento de pavimento flexível (DNER/DNIT)."""
    # entrada (eco)
    cbr_subleito: float
    cbr_reforco: float | None
    n_trafego: float
    k_rev: float
    k_base: float
    k_subbase: float
    k_reforco: float
    # espessuras de material granular equivalente exigidas (cm)
    hm_cm: float                 # sobre o subleito (CBR do subleito)
    h20_cm: float                # sobre a sub-base (CBR = 20)
    hn_cm: float | None          # sobre o reforço (CBR do reforço), se houver
    # espessuras adotadas por camada (cm)
    r_cm: float                  # revestimento
    b_cm: float                  # base
    s_cm: float                  # sub-base
    reforco_cm: float | None     # reforço do subleito (se houver)
    r_min_cm: float              # revestimento mínimo (tabela DNER)
    espessura_total_cm: float
    # verificação
    inequacoes: list[PavementInequality]
    # metadados
    metodo: str = "DNER/DNIT empírico (CBR / número N)"
    warnings: list[str] = []


def _check_cbr(cbr: float, rotulo: str) -> None:
    if not (CBR_MIN <= cbr <= CBR_MAX):
        raise ValueError(
            f"CBR {rotulo}={cbr}% fora da faixa razoável do método "
            f"[{CBR_MIN:.0f}, {CBR_MAX:.0f}]%."
        )


def _check_n(n: float) -> None:
    if not (N_MIN <= n <= N_MAX):
        raise ValueError(
            f"Número N={n:.3g} fora da faixa de validade do método "
            f"[{N_MIN:.0g}, {N_MAX:.0g}]."
        )


def numero_n(
    volume_medio_diario: float,
    periodo_anos: float,
    fator_veiculo: float,
    fator_regional: float = 1.0,
    taxa_crescimento: float = 0.0,
) -> float:
    """Número N de solicitações do eixo padrão (8,2 tf) no período de projeto.

    Fórmula adotada (DNER): ``N = 365 · Vt · FV · FR``, onde ``Vt`` é o volume
    total de veículos comerciais no sentido de projeto ao longo do período.

    Parâmetros
    ----------
    volume_medio_diario : veículos comerciais por dia no 1º ano (Vm).
    periodo_anos        : período de projeto P (anos).
    fator_veiculo       : FV = fator de carga × fator de eixos (DNER).
    fator_regional      : FR — fator climático regional (DNER, ~0,7 a 1,4).
    taxa_crescimento    : taxa geométrica anual de crescimento do tráfego t
                          (0,05 = 5%/ano). Para t=0, tráfego constante.

    Volume acumulado:
      - t = 0:  Vt = 365 · Vm · P
      - t > 0:  Vt = 365 · Vm · ((1+t)^P − 1) / t   (progressão geométrica)
    """
    if volume_medio_diario < 0 or periodo_anos <= 0:
        raise ValueError("Vm deve ser >= 0 e o período de projeto > 0.")
    if fator_veiculo <= 0 or fator_regional <= 0:
        raise ValueError("Fatores FV e FR devem ser positivos.")
    if taxa_crescimento < 0:
        raise ValueError("Taxa de crescimento não pode ser negativa.")

    if taxa_crescimento == 0.0:
        vt = 365.0 * volume_medio_diario * periodo_anos
    else:
        t = taxa_crescimento
        vt = 365.0 * volume_medio_diario * ((1.0 + t) ** periodo_anos - 1.0) / t
    return vt * fator_veiculo * fator_regional


def espessura_total(cbr: float, n: float) -> float:
    """Espessura de material granular equivalente sobre uma camada de CBR dado.

    Ajuste analítico do ábaco do DNER (hipótese documentada):

        H = 77,67 · N^0,0482 · CBR^-0,598   [cm]
    """
    if cbr <= 0:
        raise ValueError("CBR deve ser positivo.")
    if n <= 0:
        raise ValueError("Número N deve ser positivo.")
    return _A_COEF * (n ** _N_EXP) * (cbr ** _CBR_EXP)


def revestimento_minimo_cm(n: float) -> float:
    """Espessura mínima do revestimento betuminoso pela tabela do DNER (cm).

    - N <= 1e6                : 2,0 cm  (tratamentos superficiais betuminosos)
    - 1e6 < N <= 5e6          : 5,0 cm  (revestimentos betuminosos)
    - 5e6 < N <= 1e7          : 7,5 cm  (concreto betuminoso)
    - 1e7 < N <= 5e7          : 10,0 cm (concreto betuminoso)
    - N > 5e7                 : 12,5 cm (concreto betuminoso)
    """
    if n <= 1.0e6:
        return 2.0
    if n <= 5.0e6:
        return 5.0
    if n <= 1.0e7:
        return 7.5
    if n <= 5.0e7:
        return 10.0
    return 12.5


def _adota(req_cm: float, minimo_cm: float) -> float:
    """Arredonda a espessura requerida para cima (cm inteiro), com piso mínimo."""
    return max(math.ceil(max(req_cm, 0.0) - TOL), minimo_cm)


def design_flexible_pavement(
    cbr_subleito: float,
    n_trafego: float,
    cbr_reforco: float | None = None,
    k_rev: float = K_REV_PADRAO,
    k_base: float = K_BASE_PADRAO,
    k_subbase: float = K_SUBBASE_PADRAO,
    k_reforco: float = K_REFORCO_PADRAO,
    r_cm: float | None = None,
) -> PavementResult:
    """Dimensiona um pavimento flexível pelo método empírico do DNER/DNIT.

    ``n_trafego`` é o número N (use :func:`numero_n` para obtê-lo a partir do
    tráfego). ``cbr_reforco`` ativa a camada de reforço do subleito (opcional).
    ``r_cm`` permite fixar a espessura do revestimento; se omitido, usa-se o
    mínimo da tabela do DNER.

    Devolve as espessuras adotadas por camada e a verificação das inequações de
    equivalência estrutural. Abstém-se (``ValueError``) para CBR fora de
    ``[2, 20]%`` ou N fora de ``[1e4, 1e8]``.
    """
    _check_cbr(cbr_subleito, "subleito")
    _check_n(n_trafego)
    if cbr_reforco is not None:
        _check_cbr(cbr_reforco, "reforço")

    warnings: list[str] = []
    if cbr_reforco is not None and cbr_reforco <= cbr_subleito:
        warnings.append(
            f"CBR do reforço ({cbr_reforco}%) não supera o do subleito "
            f"({cbr_subleito}%): camada de reforço pouco eficaz."
        )

    hm = espessura_total(cbr_subleito, n_trafego)
    h20 = espessura_total(CBR_SUBBASE, n_trafego)
    hn = espessura_total(cbr_reforco, n_trafego) if cbr_reforco is not None else None

    r_min = revestimento_minimo_cm(n_trafego)
    if r_cm is None:
        r = r_min
    else:
        r = r_cm
        if r < r_min - TOL:
            warnings.append(
                f"Revestimento R={r:.1f} cm abaixo do mínimo da tabela DNER "
                f"({r_min:.1f} cm para N={n_trafego:.2g})."
            )

    # base: fecha a espessura sobre a sub-base (H20)
    b = _adota((h20 - r * k_rev) / k_base, MIN_BASE_CM)

    if cbr_reforco is None:
        # sub-base fecha a espessura sobre o subleito (Hm)
        s = _adota((hm - r * k_rev - b * k_base) / k_subbase, MIN_SUBBASE_CM)
        reforco = None
    else:
        # sub-base fecha a espessura sobre o reforço (Hn)
        s = _adota((hn - r * k_rev - b * k_base) / k_subbase, MIN_SUBBASE_CM)
        # reforço fecha a espessura sobre o subleito (Hm)
        reforco = _adota(
            (hm - r * k_rev - b * k_base - s * k_subbase) / k_reforco,
            MIN_REFORCO_CM,
        )

    inequacoes: list[PavementInequality] = []
    lhs1 = r * k_rev + b * k_base
    inequacoes.append(PavementInequality(
        nome="sobre_subbase", esquerda_cm=lhs1, direita_cm=h20,
        atende=lhs1 + TOL >= h20))
    lhs2 = lhs1 + s * k_subbase
    alvo2 = hn if cbr_reforco is not None else hm
    inequacoes.append(PavementInequality(
        nome="sobre_reforco" if cbr_reforco is not None else "sobre_subleito",
        esquerda_cm=lhs2, direita_cm=alvo2, atende=lhs2 + TOL >= alvo2))
    if cbr_reforco is not None:
        lhs3 = lhs2 + reforco * k_reforco
        inequacoes.append(PavementInequality(
            nome="sobre_subleito", esquerda_cm=lhs3, direita_cm=hm,
            atende=lhs3 + TOL >= hm))

    total = r + b + s + (reforco or 0.0)

    return PavementResult(
        cbr_subleito=cbr_subleito, cbr_reforco=cbr_reforco, n_trafego=n_trafego,
        k_rev=k_rev, k_base=k_base, k_subbase=k_subbase, k_reforco=k_reforco,
        hm_cm=hm, h20_cm=h20, hn_cm=hn,
        r_cm=r, b_cm=b, s_cm=s, reforco_cm=reforco, r_min_cm=r_min,
        espessura_total_cm=total, inequacoes=inequacoes, warnings=warnings,
    )
