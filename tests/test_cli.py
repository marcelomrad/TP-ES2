from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from repo_miner.cli import app
from repo_miner.models import AnalysisResult

runner = CliRunner()

FAKE_RESULT = AnalysisResult(
    repository="https://github.com/user/repo.git",
    hotspots=(),
    commits_analyzed=10,
    files_seen=5,
    files_analyzed=0,
)


def test_analyze_rejects_nonexistent_local_path() -> None:
    result = runner.invoke(app, ["analyze", "/nonexistent/path/to/repo"])
    assert result.exit_code != 0
    assert "Erro" in result.output


def test_analyze_accepts_remote_url() -> None:
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT):
        result = runner.invoke(
            app,
            ["analyze", "https://github.com/user/repo.git", "--no-plot"],
        )
    assert result.exit_code == 0


def test_report_accepts_remote_url(tmp_path: Path) -> None:
    out_file = tmp_path / "report.csv"
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT):
        result = runner.invoke(
            app,
            [
                "report",
                "https://github.com/user/repo.git",
                "--format", "csv",
                "--out", str(out_file),
            ],
        )
    assert result.exit_code == 0


def test_hotspots_accepts_remote_url() -> None:
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT):
        result = runner.invoke(
            app,
            ["hotspots", "https://github.com/user/repo.git"],
        )
    assert result.exit_code == 0


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "hotscope" in result.output


def test_hotspots_respects_top_option() -> None:
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT):
        result = runner.invoke(
            app,
            ["hotspots", "https://github.com/user/repo.git", "--top", "5"],
        )
    assert result.exit_code == 0


def test_report_rejects_invalid_format(tmp_path: Path) -> None:
    out_file = tmp_path / "report.xml"
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT):
        result = runner.invoke(
            app,
            [
                "report", "https://github.com/user/repo.git",
                "--format", "xml", "--out", str(out_file),
            ],
        )
    assert result.exit_code != 0
    assert "Erro" in result.output


def test_analyze_accepts_min_score_option() -> None:
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT) as mock:
        result = runner.invoke(
            app,
            ["analyze", "https://github.com/user/repo.git", "--no-plot", "--min-score", "50"],
        )
    assert result.exit_code == 0
    mock.assert_called_once()
    _, kwargs = mock.call_args
    assert kwargs["min_score"] == 50.0


def test_hotspots_accepts_min_score_option() -> None:
    with patch("repo_miner.cli.analyze_repository", return_value=FAKE_RESULT) as mock:
        result = runner.invoke(
            app,
            ["hotspots", "https://github.com/user/repo.git", "--min-score", "30"],
        )
    assert result.exit_code == 0
    _, kwargs = mock.call_args
    assert kwargs["min_score"] == 30.0
