# INEMA Engenharia Civil — Configuração Claude Code

## Projeto

Plataforma de agentes de IA para cálculos de engenharia civil.

## Comandos

```bash
uv sync                    # instalar dependências Python
python -m pytest tests/    # rodar testes unitários
python mcp/calc-server/server.py  # iniciar MCP server de cálculos
```

## Regras Críticas

1. **LLMs nunca fazem aritmética diretamente.** Todo cálculo numérico vai para Python via MCP.
2. **Todo resultado inclui aviso de responsabilidade técnica** do engenheiro.
3. **Todo cálculo passa pela camada de validação** em `lib/validators/` antes de ser apresentado.
4. **Unidades são sempre verificadas** com `pint` antes de qualquer operação.

## Estrutura de Agentes

- `agents/orchestrator/` — roteamento central
- `agents/structural/` — concreto, aço, madeira
- `agents/geotechnical/` — fundações, muros, taludes
- `agents/hydraulic/` — água, esgoto, drenagem
- `agents/budget/` — orçamento
- `agents/review/` — revisão técnica
- `agents/report/` — geração de documentos

## Aviso Obrigatório em Todo Cálculo

> Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, conforme a Lei 5.194/66 e Resolução CONFEA/CREA vigente.

## Referências

- `docs/` — arquitetura completa e guias
- `normas/` — tabelas e referências normativas
- `lib/` — engine de cálculo Python
