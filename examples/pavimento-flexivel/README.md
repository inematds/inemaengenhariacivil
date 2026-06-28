# Exemplo: Pavimento Flexível — Método Empírico DNER/DNIT

## Problema

Dimensionar as camadas de um pavimento flexível pelo método empírico do DNER/DNIT
(CBR do subleito × número N de tráfego):

- **CBR do subleito:** 10%
- **Número N de tráfego:** 1×10⁶ (eixo padrão de 8,2 tf)
- **Coeficientes de equivalência estrutural (DNER):** K_R = 2,0; K_B = 1,0; K_S = 1,0

## O que a engine calcula

1. Espessuras de material granular equivalente exigidas pela equação de ajuste do ábaco
   do DNER: H = 77,67·N^0,0482·CBR^−0,598 (cm) — sobre o subleito (Hm) e sobre a sub-base
   (H20, com CBR = 20%).
2. Espessura mínima do revestimento betuminoso pela tabela do DNER em função de N.
3. Espessuras adotadas por camada (revestimento R, base B, sub-base S), em cm inteiros e
   respeitando mínimos construtivos.
4. Verificação das inequações de equivalência estrutural.

## Fora do escopo (abstenção)

Pavimento rígido, método mecanístico-empírico (MeDiNa, fadiga e deformação permanente),
drenagem, expansão do subleito e pavimentos intertravados/semirrígidos não são tratados
— princípio da abstenção.

## Geração

`solution.md` é gerado pela engine `lib.service.solve_flexible_pavement`.

## Referência

DNER (1981), Método de Projeto de Pavimentos Flexíveis; DNIT (2006), Manual de
Pavimentação. Para CBR = 10% e N = 1×10⁶: espessura total = 39 cm (R = 2 + B = 22 + S = 15).
