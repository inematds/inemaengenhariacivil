# Estratégia de Evolução Futura

## Princípio de Extensibilidade

O sistema foi projetado para crescer sem reescrita. Cada ponto de extensão é isolado e não afeta os componentes existentes.

## Como Adicionar Novos Componentes

### Adicionar um Novo Agente

1. Criar pasta em `agents/<domínio>/<nome>/`
2. Criar `SKILL.md` seguindo o template em `docs/10-como-adicionar-agente.md`
3. Registrar no `agents/orchestrator/SKILL.md` (tabela de roteamento)
4. Nenhum outro arquivo precisa ser tocado

### Adicionar um Novo Cálculo

1. Adicionar função em `lib/<domínio>/arquivo.py`
2. Tipar input/output com Pydantic
3. Adicionar testes em `tests/unit/`
4. Registrar ferramenta no MCP server
5. O agente existente pode usá-la imediatamente

### Adicionar uma Nova Norma

1. Extrair tabelas para JSON em `normas/NBRxxxx/tables/`
2. Atualizar `lib/validators/normative_check.py`
3. Nenhum agente precisa ser reescrito

---

## Agnóstico ao Modelo

O MCP server é independente do modelo de IA:

| Componente | Dependência |
|------------|------------|
| `lib/` (Python) | Zero — puro Python |
| `mcp/calc-server` | MCP Protocol apenas |
| `agents/` (SKILL.md) | Claude Code |
| Ferramentas de cálculo | Qualquer LLM com MCP |

Para usar com outro LLM (GPT-4, modelos OpenRouter):
- O `calc-server` e `report-server` continuam iguais
- Apenas os SKILL.md precisam ser adaptados para o formato do outro assistente

---

## Versionamento de Normas

Cada tabela normativa tem metadados:

```json
{
  "norma": "NBR 6118",
  "edicao": "2014",
  "data_vigencia": "2014-03-31",
  "proxima_revisao_prevista": "2025",
  "tabela": "17.3",
  "descricao": "Taxas de armadura mínima de vigas"
}
```

Quando uma norma for atualizada:
1. Criar nova pasta `normas/NBR6118-2025/tables/`
2. O sistema verifica `data_vigencia` e avisa se o cálculo usou versão anterior

---

## Roadmap de Longo Prazo

| Etapa | Capacidade |
|-------|-----------|
| v1.0 | Plataforma completa (todas as 6 fases) |
| v1.5 | Integração BIM (IFC, Revit API) |
| v2.0 | MEF completo (OpenSees, CalculiX via MCP) |
| v2.5 | Integração AutoCAD/Revit para exportar detalhamento |
| v3.0 | Multi-projeto com base de dados central (PostgreSQL) |

---

## Padrões de Qualidade Permanentes

- **Clean Code:** funções com responsabilidade única
- **SOLID:** especialmente SRP e OCP (aberto/fechado)
- **DRY:** sem duplicação de lógica de cálculo
- **Tipos:** 100% tipado com mypy
- **Testes:** toda função nova tem teste unitário
- **Cobertura:** mínimo 90% nos módulos de cálculo
