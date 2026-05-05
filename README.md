# TP: Mineração de Repositórios de Software

## 1. Membros do Grupo

| Nome | Matrícula |
|------|-----------|
| Marcelo Augusto Mrad Marteleto | 2021031548 |
| Tomas Lacerda Muniz | 2021088116 |
| Lorenzo Carneiro Magalhães | 2021031505 |

---

## 2. Descrição do Sistema

Esta ferramenta de linha de comando (CLI) realiza a **mineração de repositórios Git** com o objetivo de identificar problemas de manutenção de software por meio da análise de *hot spots*.

Um *hot spot* é um arquivo que combina **alta frequência de modificações** (code churn) com **alta complexidade ciclomática** — ou seja, arquivos que mudam constantemente e são difíceis de entender ou manter. Esses arquivos concentram o maior risco de débito técnico em um projeto.

### Funcionamento

A ferramenta percorre o histórico de commits de um repositório Git local, coleta métricas por arquivo e cruza duas dimensões:

- **Code Churn**: número de commits que modificaram cada arquivo em um intervalo de tempo configurável.
- **Complexidade Ciclomática (CC)**: métrica estrutural que mede o número de caminhos independentes no código-fonte de cada arquivo.

O resultado é um **score de hot spot** calculado pela combinação normalizada dessas duas métricas, permitindo rankear os arquivos mais críticos do projeto. Os resultados são apresentados em tabelas formatadas no terminal e em um scatter plot (churn × complexidade), facilitando a visualização dos arquivos que mais demandam atenção de refatoração.

### Comandos disponíveis

```bash
# Analisar o repositório e coletar métricas
python -m repo_miner analyze <caminho> --since <data> --lang <linguagem>

# Listar os arquivos com maior score de hot spot
python -m repo_miner hotspots <caminho> --top 10

# Gerar relatório exportável
python -m repo_miner report <caminho> --format csv --out results.csv
```

---

## 3. Tecnologias Utilizadas

### Interface de Linha de Comando

| Ferramenta | Descrição |
|------------|-----------|
| [Typer](https://github.com/fastapi/typer) | Framework moderno para CLIs em Python, com suporte a type hints, autocompletion e help automático |
| [Click](https://github.com/pallets/click) | Alternativa consolidada para construção de CLIs, base do Typer |

### Mineração de Repositórios Git

| Ferramenta | Descrição |
|------------|-----------|
| [PyDriller](https://github.com/ishepard/pydriller) | Framework Python para análise de repositórios Git; permite iterar commits, autores, arquivos modificados e diffs |
| [GitPython](https://github.com/gitpython-developers/GitPython) | Biblioteca Python de baixo nível para interação com repositórios Git |

### Análise de Métricas de Código

| Ferramenta | Descrição |
|------------|-----------|
| [Lizard](https://github.com/terryyin/lizard) | Analisador de complexidade de código com suporte multilinguagem (Python, Java, JavaScript, C++ etc.); calcula complexidade ciclomática, LOC e número de parâmetros |
| [Radon](https://github.com/rubik/radon) | Biblioteca Python para diversas métricas de código (CC, índice de manutenibilidade, métricas de Halstead) |

### Qualidade e Segurança de Código

| Ferramenta | Descrição |
|------------|-----------|
| [Flake8](https://github.com/PyCQA/flake8) | Verificador de qualidade de código Python (PEP 8, erros lógicos) |
| [Bandit](https://github.com/PyCQA/bandit) | Ferramenta de análise estática para identificação de vulnerabilidades de segurança em código Python |

### Apresentação dos Resultados

| Ferramenta | Descrição |
|------------|-----------|
| [Rich](https://github.com/Textualize/rich) | Biblioteca para renderização de tabelas e texto formatado no terminal |
| [Plotext](https://github.com/piccolomo/plotext) | Geração de gráficos diretamente no terminal (scatter plot de churn × complexidade) |
