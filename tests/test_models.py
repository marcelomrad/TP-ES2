from __future__ import annotations

from datetime import datetime
from pathlib import Path

from repo_miner.models import AnalysisResult, FileHotspot, HistoryMetrics


def make_hotspot(path: str = "app.py", score: float = 50.0, risk: str = "medio") -> FileHotspot:
    return FileHotspot(
        path=path,
        commits=5,
        added_lines=100,
        deleted_lines=30,
        line_churn=130,
        authors=2,
        total_complexity=10,
        max_function_complexity=5,
        average_function_complexity=3.3,
        functions=3,
        nloc=80,
        score=score,
        risk=risk,
    )


def test_history_metrics_register_change_accumulates() -> None:
    metrics = HistoryMetrics(path="src/app.py")
    ts1 = datetime(2026, 1, 1)
    ts2 = datetime(2026, 6, 1)

    metrics.register_change(added_lines=10, deleted_lines=5, author="alice", changed_at=ts1)
    metrics.register_change(added_lines=20, deleted_lines=8, author="bob", changed_at=ts2)

    assert metrics.commits == 2
    assert metrics.added_lines == 30
    assert metrics.deleted_lines == 13
    assert metrics.authors == {"alice", "bob"}
    assert metrics.first_modified == ts1
    assert metrics.last_modified == ts2


def test_history_metrics_line_churn() -> None:
    metrics = HistoryMetrics(path="src/app.py")
    metrics.register_change(added_lines=15, deleted_lines=7, author="alice", changed_at=datetime.now())
    assert metrics.line_churn == 22


def test_history_metrics_ignores_none_author() -> None:
    metrics = HistoryMetrics(path="src/app.py")
    metrics.register_change(added_lines=5, deleted_lines=0, author=None, changed_at=datetime.now())
    assert metrics.authors == set()


def test_history_metrics_clamps_negative_lines() -> None:
    metrics = HistoryMetrics(path="src/app.py")
    metrics.register_change(added_lines=-5, deleted_lines=-3, author="dev", changed_at=datetime.now())
    assert metrics.added_lines == 0
    assert metrics.deleted_lines == 0


def test_file_hotspot_to_row_contains_all_fields() -> None:
    row = make_hotspot().to_row()
    expected_keys = {
        "path", "risk", "score", "commits", "line_churn",
        "added_lines", "deleted_lines", "authors",
        "total_complexity", "max_function_complexity",
        "average_function_complexity", "functions", "nloc",
    }
    assert set(row.keys()) == expected_keys


def test_file_hotspot_to_row_rounds_score() -> None:
    row = make_hotspot(score=75.6789).to_row()
    assert row["score"] == 75.68


def test_analysis_result_has_hotspots_false_when_empty(tmp_path: Path) -> None:
    result = AnalysisResult(
        repository=tmp_path,
        hotspots=(),
        commits_analyzed=0,
        files_seen=0,
        files_analyzed=0,
    )
    assert result.has_hotspots is False


def test_analysis_result_has_hotspots_true_when_nonempty(tmp_path: Path) -> None:
    result = AnalysisResult(
        repository=tmp_path,
        hotspots=(make_hotspot(),),
        commits_analyzed=1,
        files_seen=1,
        files_analyzed=1,
    )
    assert result.has_hotspots is True
