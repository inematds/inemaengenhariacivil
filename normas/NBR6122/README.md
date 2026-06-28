# NBR 6122:2010 — Projeto e Execução de Fundações

## Metadados

- **Código:** ABNT NBR 6122
- **Edição:** 2010 (3ª edição)
- **Título:** Projeto e execução de fundações
- **Status:** Em vigor

## Tabelas Disponíveis

| Arquivo | Conteúdo |
|---------|---------|
| `tables/aoki_velloso_k_alpha.json` | Coeficientes K (kPa) e α por tipo de solo (Aoki-Velloso) |
| `tables/aoki_velloso_f1_f2.json` | Fatores F1 e F2 por tipo de estaca (Aoki-Velloso) |
| `tables/decourt_c.json` | Coeficiente C (kPa) por tipo de solo (Décourt-Quaresma) |

> As três tabelas espelham os valores hardcoded em `lib/geotechnical/piles.py`
> (`AOKI_SOLO`, `AOKI_F1F2`, `DECOURT_C`) — servem como fonte de consulta e são
> verificadas em `tests/unit/test_service_phase3.py`.

## Métodos de Capacidade de Carga

### Estacas
- **Aoki-Velloso (1975):** baseado em SPT, amplamente usado no Brasil
- **Décourt-Quaresma (1978):** baseado em SPT, especialmente para estacas escavadas

### Fundações Diretas
- **Terzaghi:** clássico, para solos homogêneos
- **Meyerhof:** incorpora profundidade e inclinação de carga

## Fatores de Segurança (NBR 6122)

| Tipo | FS mínimo |
|------|-----------|
| Fundação direta (tensão admissível) | 3,0 |
| Estaca (capacidade de carga) | 2,0 |
| Estabilidade global de taludes | 1,5 |
