# INEMA Engenharia Civil — Plataforma de Agentes de IA

Plataforma profissional de agentes inteligentes para cálculos de engenharia civil, construída sobre Claude Code.

## Princípio Central

**LLMs não fazem contas. Python faz contas. LLMs orquestram, interpretam e documentam.**

## Escopo e Limites

Esta plataforma é um **copiloto de apoio à engenharia, voltado a educação, pesquisa e
verificação cruzada** — não um substituto do software de cálculo consagrado (TQS,
Eberick/AltoQi, SAP2000, Robot) nem da responsabilidade técnica do engenheiro (ART).
Todo resultado numérico vem de Python determinístico, é validado (unidades, física,
norma) e acompanha aviso de responsabilidade técnica. Ver `docs/13-avaliacao-viabilidade.md`.

## Início Rápido

```bash
# Instalar dependências Python
uv sync

# Iniciar MCP server de cálculos
python mcp/calc-server/server.py

# Abrir Claude Code neste diretório
claude
```

## Documentação

Ver pasta `docs/` para arquitetura completa, guias e plano de implementação.
Destaques:

- [`docs/14-catalogo-calculos.md`](docs/14-catalogo-calculos.md) — catálogo de **todos**
  os cálculos disponíveis (por domínio, com `solve_*`, ferramenta MCP e norma/método).
- [`docs/06-fases-implementacao.md`](docs/06-fases-implementacao.md) — plano e estado das fases.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — como adicionar um cálculo (TDD, validação, disclaimer).

## Estado: v1.0.0 — Fases 1 a 6 implementadas

As seis fases do plano de implementação estão **concluídas**, com suíte de testes
(unitária + E2E) verde, `ruff` limpo e `--selftest` do MCP server OK. Domínios cobertos
nesta versão (lista completa no [catálogo](docs/14-catalogo-calculos.md)):

- **Estrutural — concreto armado:** viga, pilar (2ª ordem), sapata isolada, lajes (1 e 2 direções).
- **Geotecnia e fundações:** capacidade de carga (Vesic), recalques (elástico e adensamento),
  empuxos (Rankine e Coulomb), estacas por SPT (Aoki-Velloso × Décourt-Quaresma).
- **Hidráulica e saneamento:** conduto forçado (Hazen-Williams / Darcy-Weisbach), canal
  aberto (Manning), perda de carga.
- **Estruturas metálicas:** barra comprimida, ligação parafusada, solda de filete (NBR 8800).
- **Pavimentação, terraplenagem e taludes:** pavimento flexível (DNER/DNIT), balanço
  corte/aterro, estabilidade de taludes (infinito e Fellenius).
- **Orçamento:** custo direto + BDI (base tipo SINAPI, amostra ilustrativa).
- **Memória de projeto e documentação:** persistência por projeto e relatório consolidado.

Domínios ainda **não** cobertos (o agente deve abster-se): concreto protendido, madeira,
alvenaria estrutural, dinâmica/sísmica, entre outros.

## Licença

Uso interno INEMA Engenharia Civil.
