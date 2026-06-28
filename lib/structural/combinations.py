"""Combinações de ações — valores característicos -> valores de cálculo.

NBR 8681:2003 (ações e segurança) + NBR 6118:2014 (tabela 11.x dos coeficientes
de ponderação γ e dos fatores de combinação ψ). Camada Python determinística: o
LLM nunca soma cargas de cabeça; chama estas funções puras via MCP.

Tipos cobertos:
- ELU normal (combinação última normal, NBR 8681 4.3 / NBR 6118 11.8.2):
      Fd = γg·Gk + γq·(Qk_princ + Σ ψ0·Qk_sec)
  A ação variável principal entra com valor pleno; as secundárias entram
  reduzidas pelo fator de combinação ψ0.
- ELS quase-permanente (NBR 8681 4.4 / NBR 6118 11.8.3.2):
      Fd,serv = Gk + Σ ψ2·Qk
  Usada em verificações de deformação (flecha) de longa duração.

Coeficientes típicos (NBR 6118:2014 Tab.11.1 e 11.2; valores usuais de edifícios):
- γg = 1.4 (permanente desfavorável), γq = 1.4 (variável desfavorável);
- ψ0 = 0.5 (cargas acidentais de edifícios residenciais/comerciais usuais);
       ψ0 = 0.6 a 0.8 para outros usos (depósitos, vento) — consultar a tabela;
- ψ2 = 0.3 (acidental de edifícios residenciais), 0.4 (comerciais),
       0.6 (bibliotecas/depósitos). O valor é responsabilidade do projetista.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

# --- coeficientes default (NBR 6118:2014) ------------------------------------
GAMMA_G = 1.4   # ponderação de ações permanentes (desfavorável)
GAMMA_Q = 1.4   # ponderação de ações variáveis (desfavorável)
PSI0 = 0.5      # fator de combinação (ELU) — acidental usual de edifícios
PSI2 = 0.3      # fator quase-permanente (ELS) — acidental residencial usual

NORMA = "NBR 8681:2003 / NBR 6118:2014"


class CombinationResult(BaseModel):
    """Resultado de uma combinação de ações.

    ``fd`` é o valor de cálculo (ELU) ou de serviço (ELS) da ação combinada, na
    mesma unidade das entradas (kN, kN/m, kN/m²…). ``parcela_permanente`` e
    ``parcela_variavel`` decompõem a soma para rastreabilidade do memorial.
    """

    fd: float
    parcela_permanente: float
    parcela_variavel: float
    tipo: str
    coeficientes: dict[str, float] = {}
    norma: str = NORMA


def _exigir_nao_negativo(nome: str, valor: float) -> None:
    if valor < 0:
        raise ValueError(
            f"{nome} = {valor} é negativo. Combinações deste módulo assumem ações "
            "de mesmo sentido (desfavoráveis, valores característicos ≥ 0). Para "
            "ações favoráveis use γg = 1.0 e trate o sinal no nível do esforço."
        )


def combinar_elu_normal(
    gk: float,
    qk_principal: float,
    qk_secundarias: Sequence[float] | None = None,
    gamma_g: float = GAMMA_G,
    gamma_q: float = GAMMA_Q,
    psi0: float = PSI0,
) -> CombinationResult:
    """Combinação última normal (ELU): Fd = γg·Gk + γq·(Qk_princ + Σ ψ0·Qk_sec).

    - ``gk``: ação permanente característica (Gk).
    - ``qk_principal``: ação variável principal característica (valor pleno).
    - ``qk_secundarias``: demais ações variáveis (reduzidas por ψ0). Default: nenhuma.
    - ``psi0``: fator de combinação das secundárias (NBR 6118 Tab.11.2; ~0.5 usual).

    Entradas negativas levantam ``ValueError`` (princípio da abstenção: não se
    presume ação favorável sem o engenheiro declarar). NBR 8681 4.3 / NBR 6118 11.8.2.
    """
    secundarias = list(qk_secundarias or [])
    _exigir_nao_negativo("Gk", gk)
    _exigir_nao_negativo("Qk_principal", qk_principal)
    for i, q in enumerate(secundarias):
        _exigir_nao_negativo(f"Qk_secundaria[{i}]", q)
    if gamma_g < 0 or gamma_q < 0 or psi0 < 0:
        raise ValueError("Coeficientes de ponderação/combinação devem ser ≥ 0.")

    parcela_permanente = gamma_g * gk
    soma_variaveis = qk_principal + psi0 * sum(secundarias)
    parcela_variavel = gamma_q * soma_variaveis
    fd = parcela_permanente + parcela_variavel

    return CombinationResult(
        fd=fd,
        parcela_permanente=parcela_permanente,
        parcela_variavel=parcela_variavel,
        tipo="ELU-normal",
        coeficientes={"gamma_g": gamma_g, "gamma_q": gamma_q, "psi0": psi0},
    )


def combinar_els_quase_permanente(
    gk: float,
    qks: Sequence[float],
    psi2: float = PSI2,
) -> CombinationResult:
    """Combinação quase-permanente de serviço (ELS): Fd,serv = Gk + Σ ψ2·Qk.

    - ``gk``: ação permanente característica (Gk), valor pleno.
    - ``qks``: ações variáveis características (todas reduzidas por ψ2).
    - ``psi2``: fator quase-permanente (NBR 6118 Tab.11.2; ~0.3 residencial usual).

    Usada na verificação de flechas de longa duração. Entradas negativas levantam
    ``ValueError``. NBR 8681 4.4 / NBR 6118 11.8.3.2.
    """
    variaveis = list(qks or [])
    _exigir_nao_negativo("Gk", gk)
    for i, q in enumerate(variaveis):
        _exigir_nao_negativo(f"Qk[{i}]", q)
    if psi2 < 0:
        raise ValueError("Fator ψ2 deve ser ≥ 0.")

    parcela_permanente = gk
    parcela_variavel = psi2 * sum(variaveis)
    fd = parcela_permanente + parcela_variavel

    return CombinationResult(
        fd=fd,
        parcela_permanente=parcela_permanente,
        parcela_variavel=parcela_variavel,
        tipo="ELS-quase-permanente",
        coeficientes={"psi2": psi2},
    )
