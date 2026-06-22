from __future__ import annotations

from itertools import islice

import plotext as plt
from rich.console import Console
from rich.table import Table

from repo_miner.models import AnalysisResult, FileHotspot


def render_summary(console: Console, result: AnalysisResult) -> None:
    console.print(f"[bold]Repositorio:[/bold] {result.repository}")
    console.print(
        "[bold]Resumo:[/bold] "
        f"{result.commits_analyzed} commits, "
        f"{result.files_seen} arquivos vistos, "
        f"{result.files_analyzed} arquivos de codigo analisados."
    )

    if result.since or result.until:
        since = result.since.date().isoformat() if result.since else "inicio"
        until = result.until.date().isoformat() if result.until else "HEAD"
        console.print(f"[bold]Periodo:[/bold] {since} -> {until}")


def render_hotspot_table(
    console: Console,
    hotspots: tuple[FileHotspot, ...],
    *,
    limit: int,
) -> None:
    table = Table(title=f"Top {min(limit, len(hotspots))} hot spots")
    table.add_column("#", justify="right")
    table.add_column("Risco")
    table.add_column("Score", justify="right")
    table.add_column("Arquivo", overflow="fold")
    table.add_column("Commits", justify="right")
    table.add_column("Churn", justify="right")
    table.add_column("CC total", justify="right")
    table.add_column("CC max", justify="right")
    table.add_column("NLOC", justify="right")

    for index, hotspot in enumerate(islice(hotspots, limit), start=1):
        style = risk_style(hotspot.risk)
        table.add_row(
            str(index),
            hotspot.risk,
            f"{hotspot.score:.2f}",
            hotspot.path,
            str(hotspot.commits),
            str(hotspot.line_churn),
            str(hotspot.total_complexity),
            str(hotspot.max_function_complexity),
            str(hotspot.nloc),
            style=style,
        )

    console.print(table)


def render_plot(console: Console, hotspots: tuple[FileHotspot, ...], *, limit: int) -> None:
    selected = list(islice(hotspots, limit))
    if not selected:
        return

    plt.clf()
    plt.cld()
    plt.theme("clear")
    plt.title("Hot spots: commits x complexidade")
    plt.xlabel("commits que alteraram o arquivo")
    plt.ylabel("complexidade ciclomatica total")
    plt.scatter(
        [hotspot.commits for hotspot in selected],
        [hotspot.total_complexity for hotspot in selected],
    )
    print(plt.build())


def risk_style(risk: str) -> str:
    if risk == "alto":
        return "bold red"
    if risk == "medio":
        return "yellow"
    return "green"
