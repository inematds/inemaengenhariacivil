# NBR 7190:1997 — Projeto de Estruturas de Madeira

## Metadados

- **Código:** ABNT NBR 7190
- **Edição:** 1997 (1ª edição)
- **Título:** Projeto de estruturas de madeira
- **Status:** Em revisão (nova edição prevista)

## Tabelas Disponíveis

| Arquivo | Conteúdo |
|---------|---------|
| `tabela_C1.json` | Propriedades das classes de madeira (C20, C25, C30, C40, D20...) |
| `tabela_coeficientes_modificacao.json` | Coeficientes kmod1, kmod2, kmod3 |

## Classes de Madeira

| Classe | fck,0 (MPa) | E0,m (MPa) |
|--------|------------|-----------|
| C20 | 20 | 9500 |
| C25 | 25 | 11000 |
| C30 | 30 | 12500 |
| C40 | 40 | 14500 |
| D20 | 20 | 9500 |
| D30 | 30 | 13000 |
| D40 | 40 | 16000 |
| D50 | 50 | 18000 |

## Coeficientes de Modificação

- **kmod1:** classe de carregamento (0.6 a 1.1)
- **kmod2:** classe de umidade (0.8 a 1.0)
- **kmod3:** tratamento preservativo (0.9 a 1.0)
- **kmod = kmod1 × kmod2 × kmod3**

## Coeficientes de Segurança

| Situação | γf | γm |
|----------|----|----|
| ELU normal | 1.4 | 1.4 |
| ELU excepcional | 1.0 | 1.4 |
