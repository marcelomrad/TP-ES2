# hotscope

![CI](https://github.com/marcelomrad/hotscope/actions/workflows/ci.yml/badge.svg)

Ferramenta de linha de comando para minerar repositórios Git e identificar arquivos com maior
risco de manutenção por meio de análise de **hot spots** — arquivos que combinam alta frequência
de mudanças com alta complexidade ciclomática.

## Membros do Grupo

| Nome | Matrícula |
|------|-----------|
| Marcelo Augusto Mrad Marteleto | 2021031548 |
| Tomas Lacerda Muniz | 2021088116 |
| Lorenzo Carneiro Magalhães | 2021031505 |

## Objetivo

`hotscope` identifica arquivos que simultaneamente:

- mudam com **alta frequência** no histórico Git;
- acumulam **alto churn de linhas** (linhas adicionadas + removidas);
- possuem **alta complexidade ciclomática** no estado atual.

Essa combinação aponta candidatos naturais a revisão, decomposição e refatoração — os pontos
mais críticos de manutenção de um projeto.

## Tecnologias

| Tecnologia | Papel |
|---|---|
| [PyDriller](https://github.com/ishepard/pydriller) | Mineração do histórico Git (commits, autores, churn) |
| [Lizard](https://github.com/terryyin/lizard) | Métricas de complexidade ciclomática do código-fonte |
| [Typer](https://typer.tiangolo.com/) | Interface de linha de comando |
| [Rich](https://github.com/Textualize/rich) | Tabelas e formatação no terminal |
| [Plotext](https://github.com/piccolomo/plotext) | Scatter plot no terminal |
| [pytest](https://pytest.org/) | Testes automatizados |
| [GitHub Actions](https://github.com/features/actions) | CI/CD com execução automática dos testes |

## Instalação

Com `uv` (recomendado):

```bash
uv sync --extra dev
```

Com `pip`:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Como Usar

A ferramenta oferece três comandos:

| Comando | O que faz |
|---------|-----------|
| `analyze` | Exibe resumo, ranking e gráfico no terminal |
| `hotspots` | Lista apenas o ranking de hot spots |
| `report` | Gera relatório em CSV, JSON ou Markdown |

O argumento `REPOSITORY` aceita **caminho local** ou **URL remota** (`https://`, `git@`, etc.).

### Exemplos

Analisar um repositório local:

```bash
uv run hotscope analyze /caminho/para/repositorio --lang python --top 10
```

Analisar um repositório remoto:

```bash
uv run hotscope analyze https://github.com/usuario/repositorio --lang python
```

Listar apenas o ranking de hot spots:

```bash
uv run hotscope hotspots /caminho/para/repositorio --top 5
```

Gerar relatório CSV:

```bash
uv run hotscope report /caminho/para/repositorio --format csv --out relatorio.csv
```

Gerar relatório JSON:

```bash
uv run hotscope report /caminho/para/repositorio --format json --out relatorio.json
```

Gerar relatório Markdown:

```bash
uv run hotscope report /caminho/para/repositorio --format md --out relatorio.md
```

Filtrar por período e score mínimo:

```bash
uv run hotscope analyze . --since 2026-01-01 --until 2026-06-22 --min-score 40
```

Filtrar por caminhos:

```bash
uv run hotscope analyze . --include "src/*" --exclude "tests/*"
```

Filtrar por nível de risco e mudar a ordenação:

```bash
uv run hotscope hotspots . --risk alto --sort-by churn --top 10
```

Opções de ordenação disponíveis:

| Valor | Critério principal |
|-------|--------------------|
| `score` | Score normalizado de risco |
| `commits` | Quantidade de commits por arquivo |
| `complexity` | Complexidade ciclomática total |
| `churn` | Linhas adicionadas + removidas |

Os relatórios JSON e Markdown incluem um resumo com filtros aplicados,
período, score mínimo, riscos selecionados e critério de ordenação.

## Testes

Rodar os testes localmente:

```bash
uv run pytest
```

Rodar com cobertura:

```bash
uv run pytest --cov=src/repo_miner
```

Rodar o linter:

```bash
uv run ruff check .
```

Os testes também são executados automaticamente via **GitHub Actions** a cada push.

## Versionamento

O projeto segue versionamento semântico `MAJOR.MINOR.PATCH`:

- `PATCH`: correções compatíveis, documentação e testes.
- `MINOR`: novas opções compatíveis na CLI, como filtros e ordenação.
- `MAJOR`: mudanças incompatíveis em comandos, nomes de campos ou formatos.

## Métricas Coletadas

| Métrica | Fonte | Interpretação |
|---|---|---|
| `commits` | PyDriller | Quantidade de commits que alteraram o arquivo |
| `line_churn` | PyDriller | Linhas adicionadas + removidas |
| `authors` | PyDriller | Número de autores distintos |
| `total_complexity` | Lizard | Soma da complexidade ciclomática das funções |
| `max_function_complexity` | Lizard | Maior complexidade entre as funções do arquivo |
| `nloc` | Lizard | Linhas de código (sem vazias/comentários) |
| `score` | hotscope | Score normalizado de risco (0–100) |
| `risk` | hotscope | Classificação: `baixo`, `medio`, `alto` |

## Cálculo do Score

```text
combined_pressure = sqrt(commit_pressure × complexity_pressure)

score = 100 × (0.75 × combined_pressure + 0.15 × commit_pressure + 0.10 × churn_pressure)
```

O termo principal usa a média geométrica entre frequência e complexidade, privilegiando
arquivos que são simultaneamente muito alterados e estruturalmente difíceis.

## Linguagens Suportadas

Python, Java, JavaScript, TypeScript, C, C++, C#, Go, Ruby, PHP, Swift, Kotlin, Rust, Scala.

Use `--lang` para restringir a análise:

```bash
uv run hotscope analyze . --lang python --lang javascript
```

## Estrutura do Projeto

```text
src/repo_miner/
  cli.py          # comandos Typer
  git_mining.py   # coleta do histórico Git com PyDriller
  complexity.py   # métricas de código com Lizard
  hotspots.py     # seleção de arquivos e cálculo do score
  exporters.py    # saída em CSV, JSON e Markdown
  rendering.py    # tabela Rich e gráfico Plotext
  models.py       # dataclasses do domínio
tests/
  test_models.py
  test_complexity.py
  test_hotspots.py
  test_exporters.py
  test_cli.py
  test_git_mining.py
  test_mining_integration.py
```
