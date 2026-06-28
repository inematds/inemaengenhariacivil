# Exemplo: Rede de Água — Conduto Forçado (Hazen-Williams)

## Problema

Calcular a perda de carga distribuída e a velocidade num trecho de adutora de água
(conduto forçado, seção plena), pela fórmula de Hazen-Williams:

- **Vazão:** Q = 0,05 m³/s
- **Diâmetro:** D = 0,30 m
- **Comprimento:** L = 1000 m
- **Coeficiente de Hazen-Williams:** C = 130 (tubo usual)

## O que a engine calcula

1. Velocidade média V = Q/A, com A = π·D²/4.
2. Perda de carga distribuída hf = 10,67·Q^1,852·L / (C^1,852·D^4,87) (forma SI).
3. Validação da faixa de velocidade razoável (0,5–3,0 m/s).

## Fora do escopo (abstenção)

Bombeamento, linha piezométrica completa, golpe de aríete, redes malhadas e demanda
populacional não são tratados — são de responsabilidade do engenheiro. Perdas localizadas
podem ser somadas à parte com a ferramenta `perda_de_carga`.

## Geração

`solution.md` é gerado pela engine `lib.service.solve_pipe_flow` (método Hazen-Williams).

## Referência

Azevedo Netto, *Manual de Hidráulica*, 8ª ed. (forma SI de Hazen-Williams).
