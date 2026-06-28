"""Domínio de ORÇAMENTO — base de preços (tipo SINAPI) e montagem de orçamento.

Camada determinística: o LLM nunca soma/multiplica preços; chama estas funções via MCP
e apenas explica o resultado. Os preços do CSV de amostra são ILUSTRATIVOS e devem ser
substituídos pela SINAPI vigente/regional.
"""
