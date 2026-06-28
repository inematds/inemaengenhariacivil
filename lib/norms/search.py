"""Busca léxica em tabelas normativas (Fase 5).

Consulta por palavra-chave/substring sobre os arquivos JSON em
``normas/<NORMA>/tables/*.json``.

Natureza da busca
-----------------
É uma busca **LÉXICA**: casamento por substring, sem acento e case-insensitive
(normalização Unicode NFKD). **Não** usa embeddings nem qualquer semântica — não
"entende" sinônimos, só encontra o que está escrito nas tabelas.

Princípio da abstenção
----------------------
Devolve somente as entradas que estão nas tabelas; nunca inventa valores de
norma. Um termo sem correspondência resulta em lista vazia (o agente deve então
abster-se em vez de chutar um valor).

Sem efeitos colaterais
----------------------
As funções apenas leem os arquivos e devolvem dados; não escrevem nada.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any


def _normalize(s: object) -> str:
    """Minúsculas + remoção de acentos (casamento robusto, sem acento)."""
    nfkd = unicodedata.normalize("NFKD", str(s))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def _is_catalog(value: Any) -> bool:
    """True se ``value`` é um dicionário-catálogo (dict não vazio cujos valores são dicts).

    Identifica os contêineres de linhas (``perfis``, ``solos``, ``estacas``…) e
    descarta metadados como ``meta``/``unidades`` (cujos valores não são todos dicts).
    """
    return (
        isinstance(value, dict)
        and len(value) > 0
        and all(isinstance(v, dict) for v in value.values())
    )


def _collect_strings(value: Any) -> list[str]:
    """Coleta recursivamente todos os valores string (e chaves) em ``value``."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            out.append(str(k))
            out.extend(_collect_strings(v))
    elif isinstance(value, (list, tuple)):
        for v in value:
            out.extend(_collect_strings(v))
    return out


def _file_text(data: dict, arquivo: str, norma: str) -> str:
    """Texto pesquisável de nível de arquivo (nome, norma e metadados — sem catálogos)."""
    partes: list[str] = [arquivo, norma]
    for chave, valor in data.items():
        partes.append(str(chave))
        if not _is_catalog(valor):
            partes.extend(_collect_strings(valor))
    return _normalize(" ".join(partes))


def _iter_table_files(base_dir: str | Path):
    """Itera ``(path, norma)`` sobre os arquivos ``<NORMA>/tables/*.json``."""
    base = Path(base_dir)
    for path in sorted(base.glob("*/tables/*.json")):
        yield path, path.parent.parent.name


def listar_tabelas(base_dir: str | Path = "normas") -> list[str]:
    """Lista os caminhos relativos das tabelas JSON disponíveis (ordenados).

    Caminhos relativos a ``base_dir`` (ex.: ``NBR8800/tables/perfis_w.json``).
    """
    base = Path(base_dir)
    return [str(path.relative_to(base)) for path, _ in _iter_table_files(base)]


def buscar_tabela(termo: str, base_dir: str | Path = "normas") -> list[dict]:
    """Busca léxica por ``termo`` nas tabelas normativas.

    Varre ``normas/<NORMA>/tables/*.json`` e devolve as entradas (linhas dos
    catálogos) cuja chave, dados, ou os metadados do arquivo (nome do arquivo,
    norma, fonte, nota…) contenham ``termo`` — substring, sem acento,
    case-insensitive.

    Args:
        termo: palavra-chave/substring a procurar (ex.: ``"W250"``, ``"aoki"``).
        base_dir: raiz das normas (``"normas"`` por padrão).

    Returns:
        Lista de hits ``{"norma": str, "arquivo": str, "chave": str, "dados": dict}``.
        Lista **vazia** quando nada casa (princípio da abstenção — não inventa valores).
    """
    alvo = _normalize(termo)
    hits: list[dict] = []
    if not alvo:
        return hits

    for path, norma in _iter_table_files(base_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue

        arquivo = path.name
        file_match = alvo in _file_text(data, arquivo, norma)

        for container, rows in data.items():
            if not _is_catalog(rows):
                continue
            for chave, dados in rows.items():
                row_text = _normalize(
                    " ".join([str(chave), str(container), *_collect_strings(dados)])
                )
                if file_match or alvo in row_text:
                    hits.append(
                        {
                            "norma": norma,
                            "arquivo": arquivo,
                            "chave": chave,
                            "dados": dados,
                        }
                    )
    return hits
