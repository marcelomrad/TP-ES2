from datetime import datetime

import pytest

from repo_miner.hotspots import (
    _build_result,
    analyze_repository,
    build_hotspot,
    classify_risk,
    compute_hotspot_score,
    matches_any,
    normalize_metric,
    parse_date,
)
from repo_miner.models import ComplexityMetrics, HistoryMetrics


def test_parse_date_returns_none_for_none() -> None:
    assert parse_date(None) is None


def test_parse_date_returns_none_for_empty_string() -> None:
    assert parse_date("") is None
    assert parse_date("   ") is None


def test_parse_date_raises_on_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid date"):
        parse_date("31/12/2026")


def test_hotspot_score_prioritizes_files_with_churn_and_complexity() -> None:
    score = compute_hotspot_score(
        commits=10,
        total_complexity=20,
        line_churn=200,
        max_commits=10,
        max_complexity=20,
        max_line_churn=200,
    )

    assert score == 100
    assert classify_risk(score) == "alto"


def test_hotspot_score_penalizes_complexity_without_change_frequency() -> None:
    score = compute_hotspot_score(
        commits=1,
        total_complexity=20,
        line_churn=10,
        max_commits=10,
        max_complexity=20,
        max_line_churn=200,
    )

    assert score < 40
    assert classify_risk(score) == "baixo"


def test_parse_date_accepts_iso_date() -> None:
    parsed = parse_date("2026-06-22")

    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 6
    assert parsed.day == 22


def test_analyze_repository_rejects_until_before_since() -> None:
    with pytest.raises(ValueError, match="until"):
        analyze_repository(
            ".",
            since=datetime(2026, 6, 22),
            until=datetime(2026, 1, 1),
        )


def test_build_result_filters_by_risk_level(tmp_path, monkeypatch) -> None:
    histories = {
        "high.py": _make_history(path="high.py", commits=10, churn=200),
        "low.py": _make_history(path="low.py", commits=1, churn=5),
    }
    complexities = {
        "high.py": ComplexityMetrics(
            path="high.py",
            total_complexity=20,
            max_function_complexity=10,
            functions=2,
            nloc=80,
        ),
        "low.py": ComplexityMetrics(
            path="low.py",
            total_complexity=1,
            max_function_complexity=1,
            functions=1,
            nloc=10,
        ),
    }
    for path in histories:
        (tmp_path / path).write_text("x = 1\n", encoding="utf-8")

    monkeypatch.setattr(
        "repo_miner.hotspots.analyze_complexity",
        lambda _file_path, relative_path: complexities[relative_path],
    )

    result = _build_result(
        repository=tmp_path,
        display_repository=tmp_path,
        history=histories,
        commits_analyzed=11,
        languages=["python"],
        include=None,
        exclude=None,
        min_commits=1,
        min_score=0.0,
        risks=["alto"],
        since=None,
        until=None,
    )

    assert [hotspot.path for hotspot in result.hotspots] == ["high.py"]


def test_matches_any_returns_true_on_matching_pattern() -> None:
    assert matches_any("node_modules/lodash/index.js", ["node_modules/*"]) is True


def test_matches_any_returns_false_on_no_match() -> None:
    assert matches_any("src/app.py", ["node_modules/*", "dist/*"]) is False


def test_matches_any_returns_false_for_none_patterns() -> None:
    assert matches_any("src/app.py", None) is False


def test_matches_any_returns_false_for_empty_patterns() -> None:
    assert matches_any("src/app.py", []) is False


def test_normalize_metric_returns_zero_when_max_is_zero() -> None:
    assert normalize_metric(10, 0) == 0.0


def test_normalize_metric_returns_one_at_maximum() -> None:
    assert normalize_metric(5, 5) == 1.0


def test_normalize_metric_returns_half_at_half_maximum() -> None:
    assert normalize_metric(5, 10) == 0.5


def test_classify_risk_boundary_baixo_to_medio() -> None:
    assert classify_risk(39.9) == "baixo"
    assert classify_risk(40.0) == "medio"


def test_classify_risk_boundary_medio_to_alto() -> None:
    assert classify_risk(69.9) == "medio"
    assert classify_risk(70.0) == "alto"


def test_classify_risk_extremes() -> None:
    assert classify_risk(0.0) == "baixo"
    assert classify_risk(100.0) == "alto"


def _make_history(path: str = "app.py", commits: int = 5, churn: int = 100) -> HistoryMetrics:
    metrics = HistoryMetrics(path=path)
    metrics.register_change(
        added_lines=churn,
        deleted_lines=0,
        author="dev",
        changed_at=datetime(2026, 1, 1),
    )
    for _ in range(commits - 1):
        metrics.register_change(
            added_lines=0, deleted_lines=0, author="dev", changed_at=datetime(2026, 2, 1)
        )
    return metrics


def test_build_hotspot_sets_correct_risk_alto() -> None:
    history = _make_history(commits=10, churn=200)
    complexity = ComplexityMetrics(
        path="app.py", total_complexity=20, max_function_complexity=10, functions=2, nloc=50
    )

    hotspot = build_hotspot(
        history, complexity, max_commits=10, max_complexity=20, max_line_churn=200
    )

    assert hotspot.path == "app.py"
    assert hotspot.risk == "alto"
    assert hotspot.score == 100.0


def test_build_hotspot_counts_authors() -> None:
    history = HistoryMetrics(path="app.py")
    history.register_change(
        added_lines=10, deleted_lines=0, author="alice", changed_at=datetime(2026, 1, 1)
    )
    history.register_change(
        added_lines=10, deleted_lines=0, author="bob", changed_at=datetime(2026, 2, 1)
    )
    complexity = ComplexityMetrics(path="app.py")

    hotspot = build_hotspot(history, complexity, max_commits=2, max_complexity=1, max_line_churn=20)

    assert hotspot.authors == 2
