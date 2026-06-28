# Exemplo: Muro de Arrimo — Empuxo de Terra (Rankine)

## Problema

Calcular o empuxo de terra ativo e passivo sobre um muro de arrimo, pela teoria de
Rankine (tardoz vertical liso, terrapleno horizontal, solo não coesivo):

- **Peso específico do solo:** γ = 18 kN/m³
- **Altura do muro:** H = 4,0 m
- **Ângulo de atrito interno:** φ = 30°

## O que a engine calcula

1. Coeficientes Ka = tan²(45 − φ/2) e Kp = tan²(45 + φ/2).
2. Empuxo ativo Ea = 0,5·γ·H²·Ka e passivo Ep = 0,5·γ·H²·Kp (por metro de muro).
3. Ponto de aplicação a H/3 da base (distribuição triangular).

## Fora do escopo (abstenção)

Empuxo de água, sobrecargas, coesão e a estabilidade do muro (deslizamento, tombamento,
capacidade da base) não são tratados — são de responsabilidade do engenheiro.

## Geração

`solution.md` é gerado pela engine `lib.service.solve_earth_pressure_rankine`.

## Referência

Teoria de Rankine (1857); NBR 11682. Para φ = 30°: Ka = 1/3, Kp = 3.
