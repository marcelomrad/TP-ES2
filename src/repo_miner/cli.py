from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from repo_miner import __version__
from repo_miner.exporters import SUPPORTED_FORMATS, write_report
from repo_miner.git_mining import RepositoryMiningError, is_remote_url
from repo_miner.hotspots import analyze_repository, parse_date
from repo_miner.rendering import render_hotspot_table, render_plot, render_summary

app = typer.Typer(
    add_completion=False,
    help="Ferramenta de mineracao de repositorios Git para identificar hot spots.",
)
console = Console()

RepositoryArgument = Annotated[
    str,
    typer.Argument(
        help="Caminho para um repositorio Git local ou URL remota (https://, git@...).",
    ),
]


def version_callback(value: bool) -> None:
    if value:
        console.print(f"hotscope {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, help="Mostra a versao da CLI."),
    ] = False,
) -> None:
    pass


@app.command()
def analyze(
    repository: RepositoryArgument,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Data inicial no formato YYYY-MM-DD ou ISO datetime."),
    ] = None,
    until: Annotated[
        str | None,
        typer.Option("--until", help="Data final no formato YYYY-MM-DD ou ISO datetime."),
    ] = None,
    lang: Annotated[
        list[str] | None,
        typer.Option("--lang", "-l", help="Filtra linguagens: python, java, javascript etc."),
    ] = None,
    include: Annotated[
        list[str] | None,
        typer.Option("--include", help="Inclui apenas caminhos que batem com este glob."),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", help="Exclui caminhos que batem com este glob."),
    ] = None,
    min_commits: Annotated[
        int,
        typer.Option("--min-commits", min=1, help="Numero minimo de commits por arquivo."),
    ] = 1,
    min_score: Annotated[
        float,
        typer.Option("--min-score", min=0.0, max=100.0, help="Score minimo para exibir (0-100)."),
    ] = 0.0,
    top: Annotated[int, typer.Option("--top", min=1, help="Quantidade de arquivos exibidos.")] = 10,
    plot: Annotated[
        bool,
        typer.Option("--plot/--no-plot", help="Mostra o scatter plot no terminal."),
    ] = True,
) -> None:
    """Executa a analise completa e mostra resumo, ranking e grafico."""
    result = run_analysis(
        repository,
        since=since,
        until=until,
        lang=lang,
        include=include,
        exclude=exclude,
        min_commits=min_commits,
        min_score=min_score,
    )
    render_summary(console, result)
    render_hotspot_table(console, result.hotspots, limit=top)
    if plot:
        render_plot(console, result.hotspots, limit=top)


@app.command()
def hotspots(
    repository: RepositoryArgument,
    since: Annotated[str | None, typer.Option("--since")] = None,
    until: Annotated[str | None, typer.Option("--until")] = None,
    lang: Annotated[list[str] | None, typer.Option("--lang", "-l")] = None,
    include: Annotated[list[str] | None, typer.Option("--include")] = None,
    exclude: Annotated[list[str] | None, typer.Option("--exclude")] = None,
    min_commits: Annotated[int, typer.Option("--min-commits", min=1)] = 1,
    min_score: Annotated[float, typer.Option("--min-score", min=0.0, max=100.0)] = 0.0,
    top: Annotated[int, typer.Option("--top", min=1)] = 10,
) -> None:
    """Lista os arquivos mais criticos pelo score de hot spot."""
    result = run_analysis(
        repository,
        since=since,
        until=until,
        lang=lang,
        include=include,
        exclude=exclude,
        min_commits=min_commits,
        min_score=min_score,
    )
    render_hotspot_table(console, result.hotspots, limit=top)


@app.command()
def report(
    repository: RepositoryArgument,
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Arquivo de saida do relatorio."),
    ],
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help=f"Formato de saida: {', '.join(sorted(SUPPORTED_FORMATS))}.",
        ),
    ] = "csv",
    since: Annotated[str | None, typer.Option("--since")] = None,
    until: Annotated[str | None, typer.Option("--until")] = None,
    lang: Annotated[list[str] | None, typer.Option("--lang", "-l")] = None,
    include: Annotated[list[str] | None, typer.Option("--include")] = None,
    exclude: Annotated[list[str] | None, typer.Option("--exclude")] = None,
    min_commits: Annotated[int, typer.Option("--min-commits", min=1)] = 1,
    min_score: Annotated[float, typer.Option("--min-score", min=0.0, max=100.0)] = 0.0,
) -> None:
    """Gera um relatorio exportavel em CSV, JSON ou Markdown."""
    result = run_analysis(
        repository,
        since=since,
        until=until,
        lang=lang,
        include=include,
        exclude=exclude,
        min_commits=min_commits,
        min_score=min_score,
    )
    try:
        report_path = write_report(result, out, output_format)
    except ValueError as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Relatorio gerado:[/green] {report_path}")


def run_analysis(
    repository: str,
    *,
    since: str | None,
    until: str | None,
    lang: list[str] | None,
    include: list[str] | None,
    exclude: list[str] | None,
    min_commits: int,
    min_score: float = 0.0,
):
    source = repository if is_remote_url(repository) else Path(repository)
    try:
        return analyze_repository(
            source,
            since=parse_date(since),
            until=parse_date(until),
            languages=lang,
            include=include,
            exclude=exclude,
            min_commits=min_commits,
            min_score=min_score,
        )
    except (RepositoryMiningError, ValueError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise typer.Exit(1) from exc
