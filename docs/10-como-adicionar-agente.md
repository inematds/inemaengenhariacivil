# Como Adicionar um Novo Agente

Um **agente** é a camada de *persona* da plataforma: um `SKILL.md` que lê o pedido em
linguagem natural, escolhe a(s) ferramenta(s) MCP de cálculo, apresenta o memorial e
reforça a abstenção e o disclaimer. **O agente não faz contas** — todo número vem das
ferramentas MCP do `calc-server` (que por sua vez chamam a engine Python determinística).

> **Pré-requisito.** Um agente só pode acionar uma ferramenta que já exista. Se o cálculo
> ainda não tem núcleo/validador/memorial/`solve_*`/ferramenta MCP, crie-o **primeiro**
> seguindo [`11-como-adicionar-skill.md`](11-como-adicionar-skill.md). Adicionar um agente
> não adiciona capacidade de cálculo — só dá uma porta de entrada e roteamento a ela.

## Onde o agente vive

Cada agente é uma pasta sob `agents/` com um único arquivo `SKILL.md`. A organização é
plana, uma pasta por agente (não aninhada por domínio):

```
agents/
├── concrete/SKILL.md
├── foundations/SKILL.md
├── earthwork/SKILL.md
├── orchestrator/SKILL.md     # roteador central
└── <novo-agente>/SKILL.md    # o seu
```

## Passo a Passo

### 1. Decidir: novo agente ou expandir um existente?

- **Novo agente:** um domínio/persona novo, com intenções de ativação próprias e um
  conjunto coeso de ferramentas (ex.: `pavement`, `slope-stability`).
- **Expandir existente:** o cálculo é vizinho de um agente que já existe (mesma persona,
  mesmas intenções). Nesse caso só adicione a nova ferramenta ao `Fluxo`/`Escopo` do
  `SKILL.md` existente — não crie pasta nova.

### 2. Criar a pasta e o `SKILL.md`

```bash
mkdir -p agents/<novo-agente>
$EDITOR agents/<novo-agente>/SKILL.md
```

### 3. Escrever o `SKILL.md` (frontmatter + seções)

Siga o padrão dos agentes atuais (ex.: `agents/earthwork/SKILL.md`). O arquivo tem um
**frontmatter YAML** (`name` + `description` orientada a ativação) e seções fixas:

```markdown
---
name: <novo-agente>
description: >-
  Use quando o usuário pedir <intenções de ativação em linguagem natural>. Interpreta
  o problema, chama a ferramenta MCP de cálculo e apresenta o memorial. NÃO faz contas.
---

# Agente — <Título legível>

## Princípio inegociável

**Você não faz aritmética.** Todo número vem da ferramenta MCP `<nome_da_ferramenta>`
do `calc-server`. Se a ferramenta não existir, ou o pedido fugir do que ela calcula,
**diga que não há ferramenta para isso e abstenha-se** — nunca invente valores
(ver `listar_capacidades`).

## Fluxo

1. **Interprete** o enunciado e extraia os parâmetros de entrada (com unidades).
2. **Confirme hipóteses** faltantes com o usuário em texto livre (nunca chute carga,
   geometria, σ_adm, etc.).
3. **Chame** `<nome_da_ferramenta>(...)` com os dados extraídos.
4. **Apresente** o `memorial_markdown` retornado e explique o resultado.
5. **Verifique a validação**: se `aprovado` for falso, NÃO apresente como solução final —
   aponte o que reprovou e oriente.
6. **Sempre** termine com o aviso de responsabilidade técnica retornado (`aviso`).

## Escopo

- ✅ [o que a ferramenta cobre]
- ❌ [o que fica de fora — avise que não há ferramenta e abstenha-se]

## Limites legais

O cálculo é suporte à decisão. A responsabilidade técnica é do engenheiro responsável,
formalizada via ART (Lei 6.496/77, Lei 5.194/66, Resolução CONFEA/CREA).
```

Pontos não negociáveis (são o que diferencia esta plataforma):

- **Abstenção explícita.** O agente deve recusar o que não está em `listar_capacidades`
  em vez de inventar números.
- **Validação antes de apresentar.** Sempre olhar `aprovado`/`validacao` do bundle.
- **Disclaimer obrigatório.** A resposta termina com o `aviso` retornado pela ferramenta
  (que cita a Lei 6.496/77) — ele nunca é redigido pelo agente.

### 4. Registrar no Orchestrator

Abra `agents/orchestrator/SKILL.md` e acrescente uma linha na tabela **Roteamento por
domínio**, ligando os sinais do pedido ao novo agente:

```markdown
| <palavras-chave que ativam> | <Domínio> | `<novo-agente>` |
```

Se o agente trouxer um domínio inédito, atualize também a seção **Escopo atual da
plataforma** do orquestrador.

### 5. Garantir a cobertura E2E

A capacidade que o agente expõe já deve estar coberta pela suíte E2E
(`tests/integration/test_e2e_dominios.py`), que exercita cada `solve_*` de ponta a ponta.
Se o agente expõe uma ferramenta nova, acrescente o caso aprovado correspondente ao
dicionário `_CASOS_APROVADOS` daquela suíte (ver
[`11-como-adicionar-skill.md`](11-como-adicionar-skill.md), passo de testes).

### 6. (Opcional) Exemplo de uso

Adicione um caso real em `examples/<nome>/` (`README.md` com o enunciado +
`solution.md` com a saída esperada), no padrão dos exemplos existentes.

---

## Checklist de Novo Agente

- [ ] A ferramenta MCP que o agente usa já existe (senão, ver `11-como-adicionar-skill.md`)
- [ ] Pasta `agents/<nome>/` criada com `SKILL.md`
- [ ] Frontmatter YAML (`name`, `description` de ativação) preenchido
- [ ] Princípio inegociável de abstenção presente ("não faço contas")
- [ ] Fluxo lista a(s) ferramenta(s) MCP reais por nome
- [ ] Escopo ✅/❌ explícito (o que NÃO cobre é abstenção, não chute)
- [ ] Verificação de `aprovado`/`validacao` antes de apresentar
- [ ] Aviso de responsabilidade técnica (`aviso`) ao final
- [ ] Registrado na tabela de roteamento do `orchestrator`
- [ ] Caso aprovado coberto na suíte E2E
- [ ] (Opcional) Exemplo em `examples/<nome>/`
