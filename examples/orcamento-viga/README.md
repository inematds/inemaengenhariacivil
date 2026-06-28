# Exemplo: Orçamento dos Insumos de uma Viga

## Problema

Orçar os insumos principais de execução de uma viga de concreto armado, com BDI de 25%.

Quantitativos (códigos da base de amostra `data/sinapi_amostra.csv`):

| Código | Serviço/insumo | Unid. | Quantidade |
|--------|----------------|-------|------------|
| 92873  | Concreto usinado C25 lançado e adensado | m³ | 1,50 |
| 92915  | Armadura aço CA-50 (corte, dobra, montagem) | kg | 180,00 |
| 92438  | Forma de madeira compensada resinada | m² | 18,00 |

- **BDI:** 25%
- **Base de preços:** `data/sinapi_amostra.csv` (amostra ILUSTRATIVA)

> ⚠️ Os preços são de **amostra**. Em uso real, substitua pela tabela **SINAPI vigente
> e regional** (desonerada/não desonerada, mês de referência e UF do projeto).

## Solução

Ver `solution.md` — gerado pela engine via `solve_orcamento` (custo direto + BDI),
com a tabela de itens, subtotal (R$ 4.560,00), BDI (R$ 1.140,00), total (R$ 5.700,00),
validação aritmética automática e o aviso de responsabilidade técnica.

## Como Reproduzir

```bash
uv run python -c "
from lib.service import solve_orcamento
b = solve_orcamento(
    itens=[
        {'codigo':'92873','quantidade':1.5},
        {'codigo':'92915','quantidade':180.0},
        {'codigo':'92438','quantidade':18.0},
    ],
    bdi_pct=25.0,
)
print(b['memorial_markdown'])
"
```

Ou, no Claude Code:

```
# "Monte o orçamento do exemplo examples/orcamento-viga com BDI 25%"
```

## Referência

Acórdão TCU 2622/2013 (faixas de BDI); tabela SINAPI (Caixa/IBGE) para preços reais.
