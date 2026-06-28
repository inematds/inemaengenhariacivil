# Como Adicionar uma Nova Norma

## Estrutura de uma Norma

```
normas/
└── NBR6118/
    ├── README.md           # Metadados e índice das tabelas
    └── tables/
        ├── tabela_17_3.json    # Armadura mínima de vigas
        ├── tabela_6_1.json     # Classes de agressividade
        └── tabela_7_2.json     # Combinações de ações
```

## Formato das Tabelas JSON

```json
{
  "meta": {
    "norma": "NBR 6118",
    "edicao": "2014",
    "tabela": "17.3",
    "titulo": "Taxas de armadura mínima de vigas",
    "pagina": 105,
    "data_vigencia": "2014-03-31"
  },
  "columns": ["Seção", "ρ_min (%)"],
  "rows": [
    ["Retangular", "0.150"],
    ["T (alma)", "0.150"],
    ["T (mesa)", "0.040"]
  ],
  "notes": [
    "ρ_min = As_min / (b × d)",
    "Para aço CA-50, fyk = 500 MPa"
  ]
}
```

## Passo a Passo

### 1. Criar pasta da norma

```bash
mkdir -p normas/NBRxxxx/tables
```

### 2. Criar README.md da norma

```markdown
# NBR xxxx:AAAA — Título da Norma

## Metadados

- **Código:** NBR xxxx
- **Edição:** AAAA
- **Título completo:** [título oficial ABNT]
- **Status:** Em vigor / Em revisão
- **Substitui:** NBR xxxx:BBBB (se aplicável)

## Tabelas Disponíveis

| Arquivo | Tabela | Conteúdo |
|---------|--------|---------|
| `tabela_X_Y.json` | Tab. X.Y | Descrição |

## Uso no Código

from lib.validators.normative_check import get_norm_table
tabela = get_norm_table("NBR6118", "17.3")
```

### 3. Extrair tabelas para JSON

Extrair manualmente (ou com assistência de LLM) as tabelas relevantes para o formato JSON descrito acima.

### 4. Atualizar normative_check.py

```python
# lib/validators/normative_check.py
NORM_REGISTRY = {
    "NBR6118": {
        "path": "normas/NBR6118/tables/",
        "edicao": "2014",
    },
    "NBRxxxx": {               # adicionar aqui
        "path": "normas/NBRxxxx/tables/",
        "edicao": "AAAA",
    },
}
```

## Checklist de Nova Norma

- [ ] Pasta criada em `normas/`
- [ ] README.md com metadados completos
- [ ] Tabelas extraídas em JSON com metadados
- [ ] `normative_check.py` atualizado
- [ ] Testes de interpolação para as tabelas críticas
- [ ] Agentes relevantes atualizados com referência à norma
