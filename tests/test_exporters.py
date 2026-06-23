import json
from pathlib import Path

import pytest

from repo_miner.exporters import write_report
from repo_miner.models import AnalysisResult, FileHotspot


def make_result(tmp_path: Path) -> AnalysisResult:
    hotspot = FileHotspot(
        path="src/app.py",
        commits=3,
        added_lines=40,
        deleted_lines=12,
        line_churn=52,
        authors=2,
        total_complexity=9,
        max_function_complexity=5,
        average_function_complexity=3.0,
        functions=3,
        nloc=45,
        score=82.5,
        risk="alto",
    )
    return AnalysisResult(
        repository=tmp_path,
        hotspots=(hotspot,),
        commits_analyzed=4,
        files_seen=2,
        files_analyzed=1,
        languages=("python",),
        include=("src/*",),
        exclude=("tests/*",),
        min_commits=2,
        min_score=40.0,
        risks=("alto",),
        sort_by="churn",
    )


def test_write_json_report(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    write_report(make_result(tmp_path), output, "json")

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["commits_analyzed"] == 4
    assert payload["hotspots"][0]["path"] == "src/app.py"


def test_write_csv_report(tmp_path: Path) -> None:
    output = tmp_path / "report.csv"
    write_report(make_result(tmp_path), output, "csv")

    content = output.read_text(encoding="utf-8")

    assert "path,risk,score" in content
    assert "src/app.py,alto,82.5" in content


def test_write_report_raises_on_unsupported_format(tmp_path: Path) -> None:
    output = tmp_path / "report.xml"
    with pytest.raises(ValueError, match="Unsupported report format"):
        write_report(make_result(tmp_path), output, "xml")


def test_result_summary_returns_expected_fields(tmp_path: Path) -> None:
    from repo_miner.exporters import result_summary

    result = make_result(tmp_path)
    summary = result_summary(result)

    assert summary["commits_analyzed"] == 4
    assert summary["files_seen"] == 2
    assert summary["files_analyzed"] == 1
    assert summary["since"] is None
    assert summary["until"] is None
    assert summary["filters"] == {
        "languages": ["python"],
        "include": ["src/*"],
        "exclude": ["tests/*"],
        "min_commits": 2,
        "min_score": 40.0,
        "risks": ["alto"],
        "sort_by": "churn",
    }


def test_write_markdown_report(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    write_report(make_result(tmp_path), output, "md")

    content = output.read_text(encoding="utf-8")

    assert "# Relatorio de hot spots" in content
    assert "## Filtros aplicados" in content
    assert "Linguagens: python" in content
    assert "Ordenacao: churn" in content
    assert "src/app.py" in content
    assert "alto" in content
