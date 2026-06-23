import pytest

from repo_miner.hotspots import classify_risk, compute_hotspot_score, matches_any, normalize_metric, parse_date


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
