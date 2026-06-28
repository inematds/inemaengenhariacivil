# Exemplo: Pilar Metálico (barra comprimida)

## Problema

Verificar a força axial resistente de cálculo de um pilar metálico comprimido,
sem flambagem local (Q = 1):

- **Perfil:** W250x22,3 (catálogo NBR 8800, abas paralelas)
- **Comprimento de flambagem:** KL = 300 cm
- **Aço:** MR250 (fy = 250 MPa)
- **Módulo de elasticidade:** E = 200000 MPa
- **Coeficiente de flambagem local:** Q = 1,0 (seção compacta)

## Verificações Necessárias

1. Carga de flambagem elástica de Euler (Ne) no eixo de menor inércia (Iy)
2. Esbeltez reduzida λ0 = √(Q·A·fy/Ne)
3. Fator de redução por flambagem χ
4. Força axial resistente de cálculo Nc,Rd = χ·Q·A·fy/γa1

## Fora do escopo (abstenção)

Flambagem local com Q ≠ 1, flambagem por torção/flexo-torção, flambagem lateral
com torção (FLT), flexão e cisalhamento — não tratados por este núcleo.

## Referência

NBR 8800:2008, §5.3 (barras comprimidas).
Catálogo Gerdau Açominas — Perfis Estruturais (bitolas W).

> Gerado pela engine `lib.service.solve_compression`. Resultado: **APROVADO** pela
> validação automática (Nc,Rd = 213,33 kN). Veja `solution.md`.
