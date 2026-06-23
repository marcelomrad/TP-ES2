# Relatório Técnico - Mineração de Repositórios de Software

## Objetivo

Desenvolver uma CLI capaz de minerar repositórios Git e apontar arquivos com
maior risco de manutenção. O problema escolhido foi a identificação de **hot
spots**, isto é, arquivos que mudam com frequência e possuem alta complexidade
ciclomática.

## Pergunta de Pesquisa

Quais arquivos de um repositório devem receber prioridade em ações de manutenção
por combinarem alta frequência de mudança com alta complexidade estrutural?

## Fonte dos Dados

A ferramenta usa repositórios Git locais. A mineração percorre o histórico de
commits com PyDriller e coleta, por arquivo:

- quantidade de commits que alteraram o arquivo;
- linhas adicionadas;
- linhas removidas;
- autores distintos;
- primeira e última modificação no intervalo analisado.

Essa escolha torna a execução reprodutível e independente de autenticação na API
do GitHub.

## Artefatos Analisados

Foram analisados dois tipos de artefato:

1. **Histórico de commits**: usado para medir frequência de mudança e churn.
2. **Código-fonte atual**: usado para medir complexidade ciclomática com Lizard.

Issues, pull requests, branches e CI/CD ficaram fora do escopo para manter a
ferramenta focada em um problema de manutenção bem definido.

## Métricas

| Métrica | Objetivo |
|---|---|
| Commits por arquivo | Estimar frequência de mudança |
| Churn de linhas | Estimar volume de alteração |
| Autores distintos | Indicar dispersão de conhecimento |
| Complexidade ciclomática total | Medir dificuldade estrutural do arquivo |
| Complexidade máxima por função | Identificar funções especialmente críticas |
| NLOC | Contextualizar tamanho do arquivo |

## Score de Hot Spot

As métricas são normalizadas pelo maior valor observado na análise. O score final
é calculado por:

```text
combined_pressure = sqrt(commit_pressure * complexity_pressure)

score = 100 * (
  0.75 * combined_pressure
  + 0.15 * commit_pressure
  + 0.10 * churn_pressure
)
```

A maior parte do peso fica no produto entre frequência de mudança e complexidade.
Assim, um arquivo só tende a chegar ao topo se for alterado com frequência **e**
for complexo. O churn de linhas funciona como fator complementar.

## Classificação de Risco

| Score | Risco |
|---:|---|
| 0 a 39.99 | baixo |
| 40 a 69.99 | medio |
| 70 a 100 | alto |

## Arquitetura

```text
CLI Typer
  -> análise de histórico com PyDriller
  -> filtro de arquivos de código
  -> análise de complexidade com Lizard
  -> cálculo de score
  -> saída no terminal ou relatório exportável
```

Módulos principais:

- `git_mining.py`: valida e percorre repositórios Git.
- `complexity.py`: detecta linguagens e calcula métricas com Lizard.
- `hotspots.py`: cruza histórico e complexidade.
- `rendering.py`: apresenta ranking e scatter plot no terminal.
- `exporters.py`: gera CSV, JSON e Markdown.

## Apresentação dos Resultados

A CLI apresenta:

- tabela ordenada por score, commits, complexidade ou churn;
- classificação de risco;
- gráfico de dispersão commits x complexidade no terminal;
- filtros por linguagem, caminho, período, score mínimo e nível de risco;
- relatórios exportáveis em CSV, JSON ou Markdown, com resumo dos filtros aplicados.

Exemplo:

```bash
uv run hotscope analyze . --lang python --top 8
```

Exemplo com filtro de risco e ordenação por churn:

```bash
uv run hotscope hotspots . --risk alto --sort-by churn --top 8
```

## Verificação

Foram criados testes automatizados para:

- cálculo do score;
- parsing de datas;
- exportação JSON e CSV;
- filtros por score, commits, linguagem e risco;
- ordenação alternativa do ranking;
- integração com um repositório Git temporário.

Comandos de validação:

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv run hotscope analyze . --lang python --no-plot --top 8
```

## Versionamento

As mudanças seguem versionamento semântico `MAJOR.MINOR.PATCH`.
Correções de documentação, validação e testes são `PATCH`. As novas opções
compatíveis da CLI, como `--risk` e `--sort-by`, justificam evolução `MINOR`.

## Limitações

- A complexidade é medida apenas no estado atual do código.
- Arquivos deletados não aparecem no ranking final.
- A classificação de risco é heurística, embora transparente e reproduzível.
- Dados sociais do GitHub, como issues e pull requests, não são considerados.

## Conclusão

A ferramenta atende ao objetivo do trabalho ao minerar dados reais do histórico
Git e combiná-los com métricas estruturais do código. O resultado ajuda a
priorizar arquivos que concentram risco de manutenção e fornece saídas adequadas
para inspeção rápida no terminal ou análise posterior em relatórios.
