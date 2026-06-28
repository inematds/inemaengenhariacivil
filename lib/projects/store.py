"""Memória por projeto — persistência em JSON (Fase 4).

Um arquivo por projeto: ``<base_dir>/<project_id>.json``. A pasta-raiz padrão é
``memory/projects/`` (relativa ao diretório de trabalho). Nada de relógio interno:
quando um carimbo de tempo for necessário, o chamador o fornece (``timestamp``).

Princípios (CLAUDE.md): nada de aritmética/efeitos colaterais escondidos. A camada
de cima é responsável pelo disclaimer; aqui só guardamos os bundles produzidos pelo
service. ``project_id`` é validado para ser um nome de arquivo seguro — em caso de
nome inseguro, abstém-se (levanta ``ValueError``).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_BASE_DIR = "memory/projects"

# project_id seguro: letras, dígitos, '_', '-', '.', sem separadores de caminho.
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
# nomes reservados que escapam do diretório-alvo
_RESERVED_IDS = {".", ".."}


class ProjectRecord(BaseModel):
    """Registro persistível de um projeto e seu histórico de cálculos."""

    project_id: str
    nome: str
    responsavel: str | None = None
    criado_em: str | None = None
    calculos: list[dict] = Field(default_factory=list)
    metadados: dict = Field(default_factory=dict)


def _validate_id(project_id: str) -> str:
    """Garante que ``project_id`` vira um nome de arquivo seguro; senão, abstém-se."""
    if not isinstance(project_id, str):
        raise ValueError("project_id deve ser uma string.")
    pid = project_id.strip()
    if not pid:
        raise ValueError("project_id vazio não é permitido.")
    if pid in _RESERVED_IDS or not _SAFE_ID.fullmatch(pid):
        raise ValueError(
            f"project_id inseguro: {project_id!r}. Use apenas letras, dígitos, "
            "'_', '-' ou '.' (sem '/', '\\' ou '..')."
        )
    return pid


def _path_for(project_id: str, base_dir: str) -> Path:
    return Path(base_dir) / f"{_validate_id(project_id)}.json"


def save_project(record: ProjectRecord, base_dir: str = DEFAULT_BASE_DIR) -> str:
    """Grava ``record`` em ``<base_dir>/<project_id>.json`` e devolve o caminho.

    Cria ``base_dir`` se não existir. Levanta ``ValueError`` se ``project_id`` for
    inseguro (abstenção — não grava nada).
    """
    path = _path_for(record.project_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def load_project(project_id: str, base_dir: str = DEFAULT_BASE_DIR) -> ProjectRecord:
    """Carrega o registro de ``project_id``.

    Levanta ``ValueError`` se o id for inseguro e ``FileNotFoundError`` (mensagem
    clara) se o projeto não existir — em ambos os casos a camada de cima deve abster-se.
    """
    path = _path_for(project_id, base_dir)
    if not path.is_file():
        raise FileNotFoundError(
            f"Projeto {project_id!r} não encontrado em {base_dir!r}."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return ProjectRecord(**data)


def list_projects(base_dir: str = DEFAULT_BASE_DIR) -> list[str]:
    """Lista os ``project_id`` existentes em ``base_dir`` (ordenados). Vazio se não houver pasta."""
    root = Path(base_dir)
    if not root.is_dir():
        return []
    return sorted(p.stem for p in root.glob("*.json") if p.is_file())


def add_calculo(
    project_id: str,
    bundle: dict,
    base_dir: str = DEFAULT_BASE_DIR,
    timestamp: str | None = None,
) -> ProjectRecord:
    """Anexa um cálculo ao histórico do projeto e regrava o arquivo.

    ``bundle`` é um cálculo do service (bundle completo ou resumo). Se ``timestamp``
    for informado, registra-o em ``registrado_em`` numa cópia do bundle (sem mutar o
    original). Idempotência razoável: se o cálculo idêntico já estiver no histórico,
    não duplica.
    """
    record = load_project(project_id, base_dir=base_dir)

    entry = dict(bundle)
    if timestamp is not None:
        entry.setdefault("registrado_em", timestamp)

    if entry not in record.calculos:
        record.calculos.append(entry)
        save_project(record, base_dir=base_dir)

    return record
