# Exemplo: Terraplenagem — Balanço Corte/Aterro

## Problema

Fazer o balanço de terraplenagem de um trecho, comparando os volumes de corte e de
aterro e avaliando o material excedente a transportar:

- **Volume de corte (banco/in situ):** 5000 m³
- **Volume de aterro (compactado):** 3000 m³
- **Fator de empolamento Fe:** 1,25 (solo comum)

## O que a engine calcula

1. Volume de corte solto (transporte): V_solto = corte·Fe.
2. Balanço = corte − aterro (positivo = excesso/bota-fora; negativo = déficit/empréstimo).
3. Situação (excesso, déficit ou equilíbrio) e os volumes de empréstimo e bota-fora
   (este também em volume solto).

## Fora do escopo (abstenção)

Diagrama de massas (Brückner), distância média de transporte (DMT), seleção de
equipamentos, custo de movimentação e compactação no campo (Proctor/GC) não são tratados
— princípio da abstenção. Fe deve ser aferido em laboratório.

## Geração

`solution.md` é gerado pela engine `lib.service.solve_earthwork`.

## Referência

DNIT, Manual de Implantação Básica de Rodovia (método das áreas médias). Para corte =
5000 m³, aterro = 3000 m³ e Fe = 1,25: balanço = +2000 m³ (excesso/bota-fora); volume
solto a transportar = 6250 m³.
