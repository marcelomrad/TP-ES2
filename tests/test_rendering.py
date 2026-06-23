from datetime import datetime

from rich.console import Console

from repo_miner.models import AnalysisResult
from repo_miner.rendering import render_summary


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
