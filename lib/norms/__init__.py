"""Consulta às tabelas normativas (Fase 5).

Camada de leitura sobre os arquivos ``normas/<NORMA>/tables/*.json``. A busca é
LÉXICA (substring, sem acento, case-insensitive) — não usa embeddings. Princípio
da abstenção: devolve apenas o que está tabelado, nunca inventa valores de norma.
"""

from lib.norms.search import buscar_tabela, listar_tabelas

__all__ = ["buscar_tabela", "listar_tabelas"]
