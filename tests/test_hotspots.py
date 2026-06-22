from repo_miner.hotspots import classify_risk, compute_hotspot_score, parse_date


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
