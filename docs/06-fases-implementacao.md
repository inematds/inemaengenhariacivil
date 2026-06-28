# Plano de Implementação em Fases

## Fase 1 — Fundação (Semanas 1-2)

**Objetivo:** Sistema funcionando ponta a ponta para um caso simples.

### Entregas

- [ ] Estrutura de diretórios criada
- [ ] `lib/units/converter.py` com `pint` (verificação dimensional)
- [ ] `lib/concrete/beams.py` — flexão simples (seção retangular)
- [ ] `lib/validators/units_check.py`
- [ ] `lib/validators/physical_check.py`
- [ ] MCP server `calc-server` com 3 ferramentas básicas
- [ ] Agente `concrete` com SKILL.md básico
- [ ] Template de memorial de cálculo (`templates/memorial-calculo.md`)
- [ ] Checklist de viga (`checklists/viga-concreto.json`)
- [ ] Testes unitários: `tests/unit/test_concrete_beams.py`
- [ ] Exemplo completo: `examples/viga-simples/`

### Critério de Conclusão

Usuário digita: *"Dimensione uma viga 25x50cm de concreto C30, vão 5m, carga 20kN/m"*

Sistema entrega:
1. Cálculo completo com todas as etapas explicadas
2. Memorial de cálculo em Markdown
3. Checklist de revisão preenchido
4. Aviso de responsabilidade técnica

---

## Fase 2 — Estrutural Core (Semanas 3-5)

**Objetivo:** Cobertura completa de concreto armado e fundações.

### Entregas

- [ ] `lib/concrete/columns.py` — pilares com flambagem
- [ ] `lib/concrete/slabs.py` — lajes (maciça, nervurada)
- [ ] `lib/concrete/footings.py` — sapatas isoladas
- [ ] `lib/structural/loads.py` — cargas NBR 6120
- [ ] `lib/structural/combinations.py` — combinações NBR 6118 6.3
- [ ] `lib/reporting/excel_export.py`
- [ ] `lib/reporting/pdf_export.py`
- [ ] Agentes: `foundations`, `loads`
- [ ] Agente `review` para revisão cruzada
- [ ] Testes de integração com fixtures de referência
- [ ] Exemplos: `examples/pilar-esbelto/`, `examples/sapata-isolada/`

---

## Fase 3 — Geotecnia + Hidráulica (Semanas 6-8)

**Objetivo:** Fundações e redes prediais e urbanas.

### Entregas

- [ ] `lib/geotechnical/bearing_capacity.py`
- [ ] `lib/geotechnical/settlement.py`
- [ ] `lib/geotechnical/earth_pressure.py` (Rankine, Coulomb)
- [ ] `lib/geotechnical/piles.py` (Aoki-Velloso, Décourt-Quaresma)
- [ ] `lib/hydraulic/pipe_flow.py` (Hazen-Williams, Darcy-Weisbach)
- [ ] `lib/hydraulic/open_channel.py` (Manning)
- [ ] `lib/hydraulic/head_loss.py`
- [ ] Agentes: `retaining-walls`, `water-supply`, `sewage`
- [ ] Normas JSON: `normas/NBR6122/tables/`
- [ ] Workflow completo: `workflows/pile-foundation.md`

---

## Fase 4 — Orçamento + Documentação (Semanas 9-10)

**Objetivo:** Orçamentação e geração profissional de documentos.

### Entregas

- [ ] Agente `budget` com integração SINAPI (CSV local)
- [ ] `lib/reporting/memorial.py` — geração automática de memorial
- [ ] Agente `report` com templates profissionais
- [ ] Sistema de memória por projeto (`memory/projects/`)
- [ ] Agente `orchestrator` completo
- [ ] Workflow: `workflows/budget-estimate.md`
- [ ] Templates: laudo pericial, relatório técnico

---

## Fase 5 — Normas + Metálicas (Semanas 11-12)

**Objetivo:** Estruturas metálicas e base de consulta normativa.

### Entregas

- [ ] `lib/steel/profiles.py`, `connections.py`, `stability.py`
- [ ] Base de tabelas NBR 8800 em JSON
- [ ] Agentes: `steel`, `norms`
- [ ] `lib/math/interpolation.py` para tabelas de norma
- [ ] Agente `norms` com busca semântica em tabelas

---

## Fase 6 — Polimento e Estradas (Semanas 13-14)

**Objetivo:** Completude, qualidade e documentação final.

### Entregas

- [ ] Agentes: `pavement`, `earthwork`, `slope-stability`
- [ ] Suite completa de testes E2E
- [ ] Documentação `docs/` completa
- [ ] Guia de contribuição
- [ ] Exemplos completos por domínio (um por agente)
- [ ] `pytest` passando 100%

---

## Marcos de Versão

| Versão | Fase | Capacidade Principal |
|--------|------|---------------------|
| v0.1.0 | Fase 1 | Viga de concreto simples |
| v0.2.0 | Fase 2 | Concreto armado completo |
| v0.3.0 | Fase 3 | Geotecnia + Hidráulica |
| v0.4.0 | Fase 4 | Orçamento + Documentos |
| v0.5.0 | Fase 5 | Estruturas metálicas |
| v1.0.0 | Fase 6 | Plataforma completa |
