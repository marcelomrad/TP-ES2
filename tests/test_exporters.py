import json
from pathlib import Path

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
