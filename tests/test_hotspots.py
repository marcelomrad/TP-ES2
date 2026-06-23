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
