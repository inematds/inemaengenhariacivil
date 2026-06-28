# Como Adicionar um Novo Agente

## Passo a Passo

### 1. Criar a pasta do agente

```bash
mkdir -p agents/<domínio>/<nome-do-agente>
```

Exemplos:
- `agents/structural/prestressed/` — concreto protendido
- `agents/hydraulic/irrigation/` — irrigação agrícola

### 2. Criar o SKILL.md

```bash
touch agents/<domínio>/<nome-do-agente>/SKILL.md
```

### 3. Estrutura do SKILL.md

```markdown
# Agente: <Nome do Agente>

## Responsabilidade

Uma frase descrevendo exatamente o que este agente faz.
Uma frase descrevendo exatamente o que este agente NÃO faz.

## Ativação

Quando o usuário pedir: [lista de intenções que ativam este agente]

## Ferramentas MCP Disponíveis

- `ferramenta_um` — descrição
- `ferramenta_dois` — descrição

## Normas de Referência

- NBR XXXX:AAAA — título
- NBR YYYY:BBBB — título

## Fluxo de Trabalho

1. Interpretar o problema
2. Identificar parâmetros necessários
3. Chamar ferramenta MCP adequada
4. Validar resultado
5. Gerar memorial
6. Emitir aviso de responsabilidade

## Aviso Obrigatório

[Incluir sempre o aviso padrão de responsabilidade técnica]

## Limitações

- [O que este agente não cobre]
- [Quando escalar para o engenheiro]
```

### 4. Registrar no Orchestrator

Abrir `agents/orchestrator/SKILL.md` e adicionar na tabela de roteamento:

```markdown
| <domínio>/<nome> | [palavras-chave de ativação] |
```

### 5. Criar testes E2E (se necessário)

```bash
touch tests/integration/test_<nome>_agent.py
```

---

## Checklist de Novo Agente

- [ ] Pasta criada em `agents/`
- [ ] SKILL.md com responsabilidade claramente definida
- [ ] Ferramentas MCP listadas
- [ ] Normas de referência citadas
- [ ] Aviso de responsabilidade incluído
- [ ] Limitações documentadas
- [ ] Registrado no orchestrator
- [ ] Exemplo de uso documentado
