# TP: Mineração de Repositórios de Software

![CI](https://github.com/marcelomrad/TP-ES2/actions/workflows/ci.yml/badge.svg)

Ferramenta de linha de comando para minerar repositórios Git locais e identificar
arquivos com maior risco de manutenção por meio de análise de **hot spots**.

## 1. Membros do Grupo

| Nome | Matrícula |
|------|-----------|
| Marcelo Augusto Mrad Marteleto | 2021031548 |
| Tomas Lacerda Muniz | 2021088116 |
| Lorenzo Carneiro Magalhães | 2021031505 |

## 2. Problema Analisado

O trabalho identifica arquivos que combinam:

- **alta frequência de mudanças no histórico Git**;
- **alto churn de linhas**, isto é, muitas linhas adicionadas/removidas;
- **alta complexidade ciclomática atual**.

Essa combinação indica arquivos que mudam muito e são estruturalmente difíceis de
entender, testar e refatorar. No contexto de manutenção de software, esses arquivos
são candidatos naturais a revisão, decomposição, melhoria de testes ou refatoração.

## 3. Decisões do Projeto

| Decisão | Escolha |
|---|---|
| Origem dos dados | Repositório **Git local** |
| Artefatos analisados | Commits, arquivos modificados e código-fonte atual |
| Problema de manutenção | Hot spots de manutenção |
| CLI | Typer |
| Mineração Git | PyDriller |
| Métricas de código | Lizard |
| Apresentação | Rich, Plotext, CSV, JSON e Markdown |

O projeto usa Git local em vez da API do GitHub porque o objetivo principal é
minerar histórico de código. Isso evita depender de token, rate limit ou rede no
momento da análise.

## 4. Instalação

Com `uv`:

```bash
uv sync --extra dev
```

Alternativa com `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 5. Como Usar

| Comando | O que faz |
|---------|-----------|
| `analyze` | Analisa o repositório e exibe resumo, ranking e gráfico no terminal |
| `hotspots` | Lista apenas o ranking de hot spots no terminal |
| `report` | Gera relatório exportável em CSV, JSON ou Markdown |

O argumento `REPOSITORY` aceita tanto um **caminho local** quanto uma **URL remota** (`https://`, `git@`, etc.).

Analisar um repositório local:

```bash
uv run repo-miner analyze /caminho/para/repositorio --lang python --top 10
```

Analisar um repositório remoto pelo URL:

```bash
uv run repo-miner analyze https://github.com/usuario/repositorio --lang python
uv run repo-miner analyze git@github.com:usuario/repositorio.git --top 5
```

Listar apenas o ranking de hot spots:

```bash
uv run repo-miner hotspots /caminho/para/repositorio --top 5
```

Gerar relatório CSV:

```bash
uv run repo-miner report /caminho/para/repositorio --format csv --out reports/hotspots.csv
```

Gerar relatório a partir de repositório remoto:

```bash
uv run repo-miner report https://github.com/usuario/repositorio --format md --out reports/hotspots.md
```

Gerar relatório JSON:

```bash
uv run repo-miner report /caminho/para/repositorio --format json --out reports/hotspots.json
```

Gerar relatório Markdown:

```bash
uv run repo-miner report /caminho/para/repositorio --format md --out reports/hotspots.md
```

Filtrar por período:

```bash
uv run repo-miner analyze /caminho/para/repositorio --since 2026-01-01 --until 2026-06-22
```

Filtrar caminhos:

```bash
uv run repo-miner analyze /caminho/para/repositorio --include "src/*" --exclude "tests/*"
```

Exibir apenas arquivos com score acima de um limite:

```bash
uv run repo-miner analyze /caminho/para/repositorio --min-score 50
uv run repo-miner hotspots /caminho/para/repositorio --min-score 70
uv run repo-miner report /caminho/para/repositorio --min-score 40 --format csv --out reports/hotspots.csv
```

## 6. Métricas Coletadas

| Métrica | Fonte | Interpretação |
|---|---|---|
| `commits` | PyDriller | Quantidade de commits que alteraram o arquivo |
| `line_churn` | PyDriller | Linhas adicionadas + removidas |
| `authors` | PyDriller | Número de autores que alteraram o arquivo |
| `total_complexity` | Lizard | Soma da complexidade ciclomática das funções |
| `max_function_complexity` | Lizard | Maior complexidade de uma função do arquivo |
| `nloc` | Lizard | Linhas de código não vazias/não comentário |
| `score` | repo-miner | Score normalizado de risco |
| `risk` | repo-miner | Classificação: `baixo`, `medio`, `alto` |

## 7. Cálculo do Score

Cada arquivo recebe um score de 0 a 100. As métricas são normalizadas em relação
ao maior valor encontrado na análise e combinadas assim:

```text
combined_pressure = sqrt(commit_pressure * complexity_pressure)

score = 100 * (
  0.75 * combined_pressure
  + 0.15 * commit_pressure
  + 0.10 * churn_pressure
)
```

O termo principal usa a raiz do produto entre frequência de commits e complexidade.
Isso privilegia arquivos que são simultaneamente muito alterados e complexos, que é
a definição operacional de hot spot adotada pelo trabalho.

## 8. Linguagens Suportadas

A análise usa o Lizard e suporta, entre outras:

- Python
- Java
- JavaScript
- TypeScript
- C/C++
- C#
- Go
- Ruby
- PHP
- Swift
- Kotlin
- Rust
- Scala

Use `--lang` para restringir:

```bash
uv run repo-miner analyze . --lang python --lang javascript
```

## 9. Testes e Qualidade

Rodar testes:

```bash
uv run --extra dev pytest
```

Rodar lint:

```bash
uv run --extra dev ruff check .
```

Validação manual no próprio projeto:

```bash
uv run repo-miner analyze . --lang python --no-plot --top 8
uv run repo-miner report . --lang python --format json --out reports/sample-hotspots.json
```

## 10. Estrutura

```text
src/repo_miner/
  cli.py          # comandos Typer
  git_mining.py   # coleta do histórico Git com PyDriller
  complexity.py   # métricas de código com Lizard
  hotspots.py     # seleção de arquivos e cálculo do score
  exporters.py    # CSV, JSON e Markdown
  rendering.py    # tabela Rich e gráfico Plotext
  models.py       # dataclasses do domínio
tests/
  test_*.py       # testes unitários e integração com repo Git temporário
docs/
  RELATORIO.md    # relatório técnico do trabalho
```

## 11. Limitações

- A ferramenta analisa o estado atual dos arquivos para complexidade, não a
  complexidade histórica de cada versão.
- Arquivos removidos no histórico não entram no ranking final, pois não existem no
  estado atual do repositório.
- O score é heurístico, mas explícito e reproduzível.
- Issues, pull requests e CI/CD não são analisados nesta versão.

## 12. Próximos Passos Possíveis

- Coletar issues e pull requests via API do GitHub.
- Comparar evolução da complexidade ao longo do tempo.
- Gerar gráficos em PNG/HTML além do terminal.
- Adicionar sugestões automáticas de refatoração por tipo de arquivo.
