# Workflow: Estimativa de Orçamento (custo direto + BDI)

## Gatilho

Usuário solicita orçamento de obra civil a partir de quantitativos e preços tipo SINAPI.

## Princípio

Nenhum custo é inventado: preços vêm de `consultar_preco_sinapi` e a montagem de
`montar_orcamento` (calc-server). Código fora da base => o agente se abstém. Toda saída
termina com o aviso de responsabilidade técnica.

> ⚠️ **Preços de amostra.** A base `data/sinapi_amostra.csv` é ILUSTRATIVA, só para
> demonstração. Em uso real, substitua pela **SINAPI vigente e regional**
> (desonerada/não desonerada, mês de referência e UF). Alerte sempre o usuário.

## Fluxo

### Passo 1 — Levantar quantitativos

Extraia do projeto/pedido a lista de serviços e insumos com, para cada um:

- `codigo` (código SINAPI do serviço/insumo);
- `quantidade` (na unidade do código — confira a unidade antes).

Confirme com o usuário quando faltar quantidade ou houver dúvida de unidade. Não chute.

### Passo 2 — Conferir preços (opcional, item a item)

Para validar um item isolado antes de montar a planilha:

```
consultar_preco_sinapi(codigo="92873")
→ {codigo, descricao, unidade, preco_unitario}
```

Código inexistente => erro: abstenha-se e peça o código correto da SINAPI vigente.

### Passo 3 — Definir o BDI

BDI (Benefícios e Despesas Indiretas) entra como **percentual único** sobre o custo
direto, faixa aceita **[0, 40] %** (referência Acórdão TCU 2622/2013). A composição
detalhada (administração central, risco, despesas financeiras, tributos, lucro) é
responsabilidade do orçamentista — registre as premissas adotadas.

### Passo 4 — Montar o orçamento

```
montar_orcamento(
    itens=[{"codigo": "92873", "quantidade": 1.5},
           {"codigo": "92915", "quantidade": 180.0}, ...],
    bdi_pct=25.0,
)
```

Retorna o pacote padrão: `resultado` (itens detalhados, subtotal, valor do BDI, total),
`validacao`, `memorial_markdown`, `aviso` e `aprovado`.

### Passo 5 — Validação automática

A camada `lib/validators/budget_check.py` reverifica de forma determinística: preços > 0,
quantidades ≥ 0, BDI na faixa, custo de cada item = quantidade × preço, subtotal = Σ
custos e total = subtotal·(1 + BDI). Se `aprovado` for falso, **não apresente como final**
— aponte o que reprovou e corrija.

### Passo 6 — Memorial e documentação

Apresente o `memorial_markdown` (tabela de itens com qtd/preço/custo, subtotal, BDI,
total + validação + aviso). Para consolidar com outros cálculos do projeto, registre o
bundle (`registrar_calculo_no_projeto`) e gere o relatório (`gerar_relatorio_projeto`)
pelo agente `report`.

## Saída esperada

1. Tabela orçamentária (código, descrição, unidade, quantidade, preço unit., custo).
2. Subtotal (custo direto), BDI aplicado e total geral.
3. Relatório de validação aritmética (aprovado/reprovado).
4. Alerta de que os preços são de amostra e devem ser atualizados.
5. Aviso de responsabilidade técnica (obrigatório).
