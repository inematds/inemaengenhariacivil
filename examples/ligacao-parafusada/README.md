# Exemplo: Ligação Parafusada (cortante)

## Problema

Dimensionar o número de parafusos de uma ligação solicitada ao cortante:

- **Força solicitante de cálculo:** 200 kN
- **Parafuso:** M20 (db = 20 mm), fub = 800 MPa (ASTM A325 / classe 8.8)
- **Chapa:** espessura t = 9,5 mm, fu = 400 MPa (aço MR250)
- **Planos de corte:** 1 (corte simples)
- **Plano de corte:** na parte rosqueada (coeficiente 0,4)

## Verificações Necessárias

1. Resistência ao cortante por parafuso Fv,Rd (§6.3.3.2)
2. Resistência à pressão de contato / esmagamento Fc,Rd (§6.3.3.3)
3. Resistência governante = mínimo(Fv,Rd, Fc,Rd)
4. Número de parafusos n = ⌈força/Rd⌉ e capacidade total da ligação

## Fora do escopo (abstenção)

Espaçamentos e distâncias às bordas, ruptura por rasgamento / colapso de bloco,
ligações por atrito (protensão), tração nos parafusos — de responsabilidade do
engenheiro no detalhamento. Assume-se que os espaçamentos/bordas mínimos da
NBR 8800 são atendidos (parcela 1,2·lf não governa o esmagamento).

## Referência

NBR 8800:2008, §6.3 (ligações com parafusos).

> Gerado pela engine `lib.service.solve_bolted_connection`. Resultado: **APROVADO**
> (n = 3 parafusos M20; capacidade total = 223,40 kN ≥ 200 kN). Veja `solution.md`.
