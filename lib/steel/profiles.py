"""Perfis laminados W — leitura da tabela de catálogo (NBR 8800:2008).

Camada de dados determinística: carrega as propriedades geométricas dos perfis
laminados W (catálogo Gerdau Açominas) e expõe busca com abstenção (perfil
inexistente -> ``KeyError`` listando as designações válidas).

A tabela vive em ``normas/NBR8800/tables/perfis_w.json``. A consistência interna
(rx ≈ √(Ix/A), ry ≈ √(Iy/A)) é verificada em
``tests/unit/test_steel_profiles.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

# caminho padrão da tabela (repo_root/normas/NBR8800/tables/perfis_w.json)
DEFAULT_TABLE = (
    Path(__file__).resolve().parents[2] / "normas" / "NBR8800" / "tables" / "perfis_w.json"
)


class ProfileProperties(BaseModel):
    """Propriedades geométricas de um perfil laminado W.

    Unidades: dimensões da seção em mm; áreas em cm²; inércias em cm⁴; módulos
    (elástico W e plástico Z) em cm³; raios de giração em cm; massa em kg/m.
    """

    designacao: str
    d_mm: float       # altura total da seção
    bf_mm: float      # largura da mesa
    tw_mm: float      # espessura da alma
    tf_mm: float      # espessura da mesa
    area_cm2: float   # área da seção transversal
    ix_cm4: float     # momento de inércia, eixo forte (x)
    iy_cm4: float     # momento de inércia, eixo fraco (y)
    wx_cm3: float     # módulo elástico, eixo x
    wy_cm3: float     # módulo elástico, eixo y
    zx_cm3: float     # módulo plástico, eixo x
    rx_cm: float      # raio de giração, eixo x
    ry_cm: float      # raio de giração, eixo y
    massa_kg_m: float  # massa linear nominal


def load_profiles(json_path: str | Path = DEFAULT_TABLE) -> dict[str, ProfileProperties]:
    """Carrega a tabela de perfis W em ``{designacao: ProfileProperties}``.

    Levanta ``FileNotFoundError`` se o arquivo não existir e ``KeyError`` se a
    estrutura JSON não tiver a chave ``perfis``.
    """
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    perfis = data["perfis"]
    return {
        desig: ProfileProperties(designacao=desig, **props)
        for desig, props in perfis.items()
    }


def get_profile(
    designacao: str, base: dict[str, ProfileProperties]
) -> ProfileProperties:
    """Devolve o perfil ``designacao`` da tabela ``base``.

    Abstenção: se a designação não existir, levanta ``KeyError`` com a lista das
    designações disponíveis (o cálculo não deve prosseguir com um perfil inventado).
    """
    try:
        return base[designacao]
    except KeyError:
        disponiveis = ", ".join(sorted(base))
        raise KeyError(
            f"Perfil '{designacao}' não consta na tabela NBR 8800. "
            f"Perfis disponíveis: {disponiveis}."
        ) from None
