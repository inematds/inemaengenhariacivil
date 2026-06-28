# Exemplo: Estaca por SPT — Aoki-Velloso × Décourt-Quaresma

## Problema

Estimar a capacidade de carga de uma estaca pré-moldada Ø 30 cm a partir de um perfil de
sondagem SPT simples, comparando os dois métodos semiempíricos correntes no Brasil.

- **Tipo de estaca:** pré-moldada
- **Diâmetro:** D = 0,30 m
- **Fator de segurança global:** FS = 2,0 (NBR 6122)
- **Perfil SPT** (topo → ponta):

| Camada | N (SPT) | Solo | Espessura |
|--------|---------|------|-----------|
| 1 | 8 | argila siltosa | 4,0 m |
| 2 | 20 | areia siltosa | 6,0 m |

A ponta fica na base da 2ª camada; o comprimento é L = 10,0 m.

## O que a engine calcula

1. **Aoki-Velloso (1975):** Rp = (K·Np/F1)·Ap ; Rl = Σ (α·K·Nl/F2)·U·ΔL.
2. **Décourt-Quaresma (1978):** Rp = C·Np·Ap ; Rl = 10·(Ns/3 + 1)·U·L.
3. **Comparação:** divergência relativa de Rult; convergem se ≤ 20%.

Os coeficientes vêm de `normas/NBR6122/tables/` (espelham `lib/geotechnical/piles.py`).

## Fora do escopo (abstenção)

Número de estacas, bloco de coroamento, recalque do grupo, atrito negativo e prova de
carga não são tratados — são de responsabilidade do engenheiro.

## Geração

`solution.md` é gerado pela engine `lib.service.solve_pile_comparison`.

## Referência

NBR 6122:2010; Cintra, J.C.A.; Aoki, N. (2010). *Fundações por Estacas*. EESC-USP.
