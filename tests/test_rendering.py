from datetime import datetime

from rich.console import Console

from repo_miner.models import AnalysisResult, FileHotspot
from repo_miner.rendering import render_hotspot_table, render_plot, render_summary, risk_style


def make_hotspot(path: str, score: float) -> FileHotspot:
    return FileHotspot(
        path=path,
        commits=3,
        added_lines=30,
        deleted_lines=10,
        line_churn=40,
        authors=2,
        total_complexity=12,
        max_function_complexity=6,
        average_function_complexity=4.0,
        functions=3,
        nloc=80,
        score=score,
        risk="alto",
    )


def test_render_summary_includes_repository_counts_and_period() -> None:
    console = Console(record=True, width=100)
    result = AnalysisResult(
        repository="/tmp/project",
        hotspots=(),
        commits_analyzed=8,
        files_seen=5,
        files_analyzed=3,
        since=datetime(2026, 1, 1),
        until=datetime(2026, 6, 22),
    )

    render_summary(console, result)

    output = console.export_text()
    assert "Repositorio: /tmp/project" in output
    assert "8 commits, 5 arquivos vistos, 3 arquivos de codigo analisados." in output
    assert "Periodo: 2026-01-01 -> 2026-06-22" in output


def test_risk_style_maps_known_risk_levels() -> None:
    assert risk_style("alto") == "bold red"
    assert risk_style("medio") == "yellow"
    assert risk_style("baixo") == "green"


def test_render_hotspot_table_respects_limit() -> None:
    console = Console(record=True, width=120)
    hotspots = (
        make_hotspot("src/high.py", 90),
        make_hotspot("src/lower.py", 70),
    )

    render_hotspot_table(console, hotspots, limit=1)

    output = console.export_text()
    assert "src/high.py" in output
    assert "src/lower.py" not in output


def test_render_plot_noops_when_there_are_no_hotspots(capsys) -> None:
    console = Console(record=True)

    render_plot(console, (), limit=10)

    captured = capsys.readouterr()
    assert captured.out == ""
