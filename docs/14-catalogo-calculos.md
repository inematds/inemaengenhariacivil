# Catálogo de Cálculos (v1.0.0)

Lista operacional de tudo que a plataforma calcula, por domínio. Cada cálculo expõe um
orquestrador `solve_*` em `lib/service.py` (a fronteira testável) e uma ferramenta MCP
correspondente em `mcp/calc-server/server.py` (transporte fino). Todo `solve_*` devolve o
**bundle padrão** — `resultado`, `validacao`, `memorial_markdown`, `aviso`, `aprovado` —
e todo memorial termina com o aviso de responsabilidade técnica (Lei 6.496/77).

> Esta é a fonte de verdade legível por humanos. A fonte de verdade que o agente consulta
> em tempo de execução é a ferramenta `listar_capacidades`. Cálculo que não está aqui
> (nem lá) deve levar o agente a **abster-se** — nunca inventar valores.

## Estrutural — Concreto armado

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Viga retangular à flexão (ELU) | `solve_rectangular_beam` | `dimensionar_viga_retangular` | NBR 6118:2014 — flexão simples |
| Pilar retangular (2ª ordem) | `solve_rectangular_column` | `dimensionar_pilar` | NBR 6118:2014 — flexão composta normal, λ≤90 |
| Sapata isolada quadrada rígida | `solve_square_footing` | `dimensionar_sapata` | NBR 6122 / 6118 — método das bielas |
| Laje maciça armada em 1 direção | `solve_one_way_slab` | `dimensionar_laje_uma_direcao` | NBR 6118:2014 — flexão (ELU) |
| Laje maciça armada em 2 direções | `solve_two_way_slab` | `dimensionar_laje_duas_direcoes` | NBR 6118:2014 — apoiada nos 4 lados |

## Geotecnia e fundações

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Capacidade de carga de fundação rasa | `solve_bearing_capacity` | `capacidade_carga_fundacao` | NBR 6122 — Vesic |
| Recalque elástico imediato | `solve_elastic_settlement` | `recalque_elastico` | NBR 6122 (ELS) — s = q·B·(1−ν²)·Iw/Es |
| Recalque por adensamento primário | `solve_consolidation_settlement` | `recalque_adensamento` | NBR 6122 (ELS) — Terzaghi |
| Empuxo de terra — Rankine | `solve_earth_pressure_rankine` | `empuxo_rankine` | Rankine (ativo/passivo) |
| Empuxo de terra — Coulomb | `solve_earth_pressure_coulomb` | `empuxo_coulomb` | Coulomb (δ, β, α) |
| Capacidade de estaca por SPT (comparação) | `solve_pile_comparison` | `capacidade_estaca` | NBR 6122 — Aoki-Velloso × Décourt-Quaresma |

## Hidráulica e saneamento

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Escoamento em conduto forçado | `solve_pipe_flow` | `escoamento_conduto` | Hazen-Williams ou Darcy-Weisbach |
| Escoamento uniforme em canal aberto | `solve_open_channel` | `canal_aberto_manning` | Manning (retangular / trapezoidal / circular) |
| Perda de carga total | `solve_head_loss` | `perda_de_carga` | Distribuída + localizadas (coeficientes K) |

## Estruturas metálicas

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Barra comprimida (flambagem por flexão) | `solve_compression` | `dimensionar_compressao_aco` | NBR 8800:2008 §5.3 |
| Ligação parafusada à cortante | `solve_bolted_connection` | `ligacao_parafusada` | NBR 8800:2008 §6.3 |
| Solda de filete (comprimento) | `solve_weld` | `solda_filete` | NBR 8800:2008 §6.2.6 |

## Pavimentação, terraplenagem e taludes

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Pavimento flexível (CBR / número N) | `solve_flexible_pavement` | `dimensionar_pavimento_flexivel` | Método empírico DNER/DNIT |
| Balanço de terraplenagem corte × aterro | `solve_earthwork` | `terraplenagem_balanco` | DNIT — áreas médias + empolamento |
| Estabilidade de talude infinito | `solve_infinite_slope` | `talude_infinito` | Das / NBR 11682 — ruptura plana |
| Estabilidade de talude por fatias | `solve_fellenius` | `talude_fellenius` | NBR 11682 — Fellenius (fatias circulares) |

## Orçamento

| Cálculo | `solve_*` (service) | Ferramenta MCP | Norma / método |
|---|---|---|---|
| Orçamento (custo direto + BDI) | `solve_orcamento` | `montar_orcamento` | Base tipo SINAPI (amostra) + BDI |

> Os preços da base SINAPI são de **amostra ilustrativa** (`data/sinapi_amostra.csv`) e
> devem ser substituídos pela tabela vigente/regional antes de qualquer uso real.

## Consultas e utilidades (sem `solve_*`)

Ferramentas MCP de apoio (cargas, normas, conversões). Não produzem bundle de
dimensionamento; alimentam os cálculos acima ou devolvem apenas o tabelado.

| Função | Ferramenta MCP | Fonte / método |
|---|---|---|
| Combinação última de ações (ELU) | `combinar_acoes_elu` | NBR 8681 / 6118 — Fd = γg·Gk + γq·(Qk + Σψ0·Qk) |
| Peso específico de material | `consultar_peso_material` | NBR 6120:2019, Tab. 2 |
| Carga acidental por uso do ambiente | `consultar_carga_uso` | NBR 6120:2019 |
| Conversão/validação dimensional | `verificar_unidades` | `pint` (registry compartilhado) |
| Propriedades de perfil laminado W | `consultar_perfil_w` | Catálogo NBR 8800 (`perfis_w.json`) |
| Preço unitário SINAPI | `consultar_preco_sinapi` | Base tipo SINAPI (amostra) |
| Busca léxica em tabelas de norma | `consultar_tabela_norma` | `normas/<NORMA>/tables/*.json` (só o tabelado) |
| Interpolação linear de coeficientes | `interpolar_tabela` | Tabela 1D (sem extrapolar) |

## Memória de projeto e documentação

Persistência de projetos (`lib/projects/store.py`) e relatório consolidado
(`lib/reporting/report.py`).

| Função | Ferramenta MCP | Papel |
|---|---|---|
| Criar/atualizar projeto | `salvar_projeto` | grava o registro JSON do projeto |
| Carregar projeto | `carregar_projeto` | lê o registro e o histórico de cálculos |
| Listar projetos | `listar_projetos` | enumera os projetos na memória |
| Registrar cálculo no projeto | `registrar_calculo_no_projeto` | anexa um bundle ao histórico (idempotente) |
| Relatório consolidado do projeto | `gerar_relatorio_projeto` | costura os memoriais sob um cabeçalho + índice |
| Listar capacidades | `listar_capacidades` | enumera os cálculos disponíveis (fonte de verdade do agente) |

---

## Contrato comum (todo `solve_*`)

```python
{
  "resultado":        { ... },   # model_dump() do Result do núcleo (Pydantic)
  "validacao":        { "passed": bool, "checks": [...], "warnings": [...] },
  "memorial_markdown": "# Memorial — ... (termina com o aviso de responsabilidade)",
  "aviso":            "⚠️ RESPONSABILIDADE TÉCNICA ... Lei 6.496/77 ...",
  "aprovado":          bool      # == validacao.passed
}
```

Quando `aprovado` é falso, o resultado **não** deve ser apresentado como solução final:
o agente aponta o que reprovou (ver `validacao.checks`/`warnings`) e orienta o ajuste.

Para adicionar um cálculo novo a este catálogo, siga
[`11-como-adicionar-skill.md`](11-como-adicionar-skill.md) e
[`../CONTRIBUTING.md`](../CONTRIBUTING.md).
