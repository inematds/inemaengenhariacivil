# Dependências

## Python (pyproject.toml)

### Core

| Pacote | Versão | Uso |
|--------|--------|-----|
| `numpy` | >=1.26 | Arrays, álgebra linear, operações numéricas |
| `scipy` | >=1.12 | Otimização, integração, equações diferenciais |
| `sympy` | >=1.12 | Álgebra simbólica, verificação analítica |
| `pint` | >=0.23 | Verificação dimensional de unidades |
| `pydantic` | >=2.5 | Validação de schemas de entrada/saída |
| `mcp` | >=1.0 | SDK do Model Context Protocol |

### Relatórios

| Pacote | Versão | Uso |
|--------|--------|-----|
| `openpyxl` | >=3.1 | Geração e leitura de planilhas Excel |
| `reportlab` | >=4.0 | Geração de PDF programático |
| `matplotlib` | >=3.8 | Gráficos de esforços, diagramas |
| `pandas` | >=2.1 | Manipulação de tabelas, importação CSV |

### Desenvolvimento

| Pacote | Versão | Uso |
|--------|--------|-----|
| `pytest` | >=8.0 | Framework de testes |
| `pytest-cov` | >=4.0 | Cobertura de código |
| `ruff` | >=0.3 | Linter e formatador |

## MCP Servers

### Internos (este projeto)

| Server | Porta | Responsabilidade |
|--------|-------|-----------------|
| `calc-server` | 8001 | Ferramentas de cálculo Python |
| `report-server` | 8002 | Geração de documentos |

### Externos (opcionais)

| Server | Uso |
|--------|-----|
| `@modelcontextprotocol/server-filesystem` | Leitura/escrita de arquivos |
| `mcp-server-git` | Versionamento de projetos |
| `mcp-server-sqlite` | Banco de dados de projetos |

## Runtime

| Ferramenta | Versão | Uso |
|------------|--------|-----|
| Python | >=3.11 | Engine de cálculo |
| `uv` | latest | Gerenciamento de dependências Python |
| Claude Code | latest | Interface de agentes |

## Instalação

```bash
# Instalar uv (gerenciador Python moderno)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências do projeto
cd inemaengenhariacivil
uv sync

# Instalar dependências de desenvolvimento
uv sync --extra dev

# Verificar instalação
python -c "import numpy, scipy, pint, pydantic; print('OK')"
```

## Versões de Normas Utilizadas

| Norma | Ano | Status |
|-------|-----|--------|
| NBR 6118 | 2014 | Em vigor (revisar 2025) |
| NBR 6120 | 2019 | Em vigor |
| NBR 6122 | 2010 | Em vigor |
| NBR 6123 | 1988 | Em vigor |
| NBR 7190 | 1997 | Em revisão |
| NBR 8800 | 2008 | Em vigor |
| NBR 9649 | 1986 | Em vigor |
| NBR 12218 | 2017 | Em vigor |
| NBR 15812 | 2010 | Em vigor |
