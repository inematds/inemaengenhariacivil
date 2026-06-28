"""Terraplenagem — volumes de corte/aterro, empolamento e balanço.

Toda a aritmética vive aqui (camada Python determinística). O LLM apenas interpreta
o problema, chama estas funções via MCP e explica o resultado. O aviso de
responsabilidade técnica NÃO é inserido aqui (entra na camada de integração).

Fonte do método
---------------
Método das áreas médias (average end area), padrão em topografia e terraplenagem
rodoviária (DNIT, Manual de Implantação Básica de Rodovia):

    V = (A1 + A2) / 2 · L

Estados de volume de solo (terraplenagem):
    1. Corte / banco (in situ): volume geométrico natural.
    2. Solto (transporte): V_solto = V_corte · Fe, Fe = fator de empolamento >= 1
       (swell — o material expande ao ser escavado/desagregado).
    3. Compactado (aterro): V_comp = V_solto · Fc, Fc = fator de compactação < 1
       (o material solto é adensado no aterro).
    Logo V_comp = V_corte · Fe · Fc.

Valores típicos documentados (referência; o usuário deve aferir em laboratório):
    - Fe (empolamento): solo comum ~1,25; argila ~1,30; rocha sã ~1,50.
    - Fc (solto -> compactado): ~0,72, de modo que V_comp ≈ 0,90·V_corte.
"""

from __future__ import annotations

from pydantic import BaseModel

# --- faixas de validade (abstenção fora delas) ------------------------------
FE_MIN = 1.0   # fator de empolamento — material no mínimo conserva o volume
FE_MAX = 1.5   # fator de empolamento — acima disso, fora da faixa usual de solos

# --- valores padrão documentados --------------------------------------------
FE_PADRAO = 1.25   # empolamento típico de solo comum
FC_PADRAO = 0.72   # fator solto -> compactado (resulta em ~0,90·V_corte)


class EarthworkResult(BaseModel):
    """Balanço de terraplenagem corte × aterro."""
    # entrada (eco)
    volume_corte_m3: float
    volume_aterro_m3: float
    fator_empolamento: float
    # derivados
    volume_corte_solto_m3: float       # volume solto a transportar (corte·Fe)
    balanco_m3: float                  # corte − aterro (+ excesso / − déficit)
    situacao: str                      # "excesso" | "deficit" | "equilibrio"
    volume_emprestimo_m3: float        # material a importar (déficit), em banco
    volume_bota_fora_m3: float         # material a descartar (excesso), em banco
    volume_bota_fora_solto_m3: float   # bota-fora em volume solto (·Fe)
    # metadados
    metodo: str = "Balanço corte/aterro (áreas médias + empolamento)"
    warnings: list[str] = []


def volume_entre_secoes(area1_m2: float, area2_m2: float, distancia_m: float) -> float:
    """Volume entre duas seções pelo método das áreas médias: V = (A1+A2)/2·L."""
    if area1_m2 < 0 or area2_m2 < 0:
        raise ValueError("Áreas das seções devem ser >= 0.")
    if distancia_m <= 0:
        raise ValueError("Distância entre seções deve ser > 0.")
    return (area1_m2 + area2_m2) / 2.0 * distancia_m


def volume_total(areas: list[float], distancias: list[float]) -> float:
    """Volume total por somatório de trechos (áreas médias).

    ``areas`` tem n seções; ``distancias`` tem n-1 distâncias entre seções
    consecutivas. V = Σ (A_i + A_{i+1})/2 · d_i.
    """
    if len(areas) < 2:
        raise ValueError("São necessárias ao menos 2 seções.")
    if len(distancias) != len(areas) - 1:
        raise ValueError(
            f"São necessárias {len(areas) - 1} distâncias para {len(areas)} seções; "
            f"recebidas {len(distancias)}."
        )
    total = 0.0
    for i, d in enumerate(distancias):
        total += volume_entre_secoes(areas[i], areas[i + 1], d)
    return total


def ajustar_empolamento(volume_corte_m3: float, fator_empolamento: float) -> float:
    """Converte volume de corte (banco) em volume solto: V_solto = V_corte · Fe."""
    if volume_corte_m3 < 0:
        raise ValueError("Volume de corte deve ser >= 0.")
    if fator_empolamento < FE_MIN:
        raise ValueError(
            f"Fator de empolamento {fator_empolamento} < {FE_MIN} (o solo não "
            "contrai ao ser escavado)."
        )
    return volume_corte_m3 * fator_empolamento


def volume_compactado(
    volume_corte_m3: float,
    fator_empolamento: float = FE_PADRAO,
    fator_compactacao: float = FC_PADRAO,
) -> float:
    """Volume compactado (aterro) a partir do corte: corte → solto → compactado.

    V_solto = V_corte · Fe ; V_comp = V_solto · Fc = V_corte · Fe · Fc.
    """
    if volume_corte_m3 < 0:
        raise ValueError("Volume de corte deve ser >= 0.")
    if fator_empolamento < FE_MIN:
        raise ValueError(f"Fator de empolamento {fator_empolamento} < {FE_MIN}.")
    if not (0.0 < fator_compactacao <= 1.0):
        raise ValueError(
            f"Fator de compactação {fator_compactacao} deve estar em (0, 1]."
        )
    return volume_corte_m3 * fator_empolamento * fator_compactacao


def balanco_corte_aterro(
    volume_corte_m3: float,
    volume_aterro_m3: float,
    fator_empolamento: float = 1.0,
) -> EarthworkResult:
    """Balanço de terraplenagem: compara corte e aterro (volumes geométricos).

    ``balanco = corte − aterro``: positivo indica excesso (bota-fora) e negativo
    indica déficit (empréstimo). ``fator_empolamento`` (em [1,0; 1,5]) é usado
    para reportar o volume solto a transportar. Abstém-se (``ValueError``) para
    volumes negativos ou Fe fora da faixa.
    """
    if volume_corte_m3 < 0 or volume_aterro_m3 < 0:
        raise ValueError("Volumes de corte e aterro devem ser >= 0.")
    if not (FE_MIN <= fator_empolamento <= FE_MAX):
        raise ValueError(
            f"Fator de empolamento {fator_empolamento} fora da faixa "
            f"[{FE_MIN}, {FE_MAX}]."
        )

    balanco = volume_corte_m3 - volume_aterro_m3
    if abs(balanco) <= 1e-9:
        situacao = "equilibrio"
    elif balanco > 0:
        situacao = "excesso"
    else:
        situacao = "deficit"

    bota_fora = max(balanco, 0.0)
    emprestimo = max(-balanco, 0.0)

    warnings: list[str] = []
    if situacao == "deficit":
        warnings.append(
            f"Déficit de {emprestimo:.1f} m³: prever empréstimo (importação de solo)."
        )
    elif situacao == "excesso":
        warnings.append(
            f"Excesso de {bota_fora:.1f} m³: prever bota-fora (descarte de solo)."
        )

    return EarthworkResult(
        volume_corte_m3=volume_corte_m3,
        volume_aterro_m3=volume_aterro_m3,
        fator_empolamento=fator_empolamento,
        volume_corte_solto_m3=volume_corte_m3 * fator_empolamento,
        balanco_m3=balanco,
        situacao=situacao,
        volume_emprestimo_m3=emprestimo,
        volume_bota_fora_m3=bota_fora,
        volume_bota_fora_solto_m3=bota_fora * fator_empolamento,
        warnings=warnings,
    )
