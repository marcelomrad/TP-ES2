import subprocess
from pathlib import Path

from repo_miner.hotspots import analyze_repository


def run_git(repository: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True, text=True)


def commit_all(repository: Path, message: str) -> None:
    run_git(repository, "add", ".")
    run_git(
        repository,
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        message,
    )


def test_min_commits_filter_excludes_files_below_threshold(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    run_git(repository, "init")

    frequent = repository / "frequent.py"
    frequent.write_text("x = 1\n", encoding="utf-8")
    commit_all(repository, "add frequent")
    frequent.write_text("x = 2\n", encoding="utf-8")
    commit_all(repository, "update frequent")

    rare = repository / "rare.py"
    rare.write_text("y = 1\n", encoding="utf-8")
    commit_all(repository, "add rare")

    result = analyze_repository(repository, languages=["python"], min_commits=2)

    paths = [h.path for h in result.hotspots]
    assert "frequent.py" in paths
    assert "rare.py" not in paths


def test_language_filter_excludes_non_python_files(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    run_git(repository, "init")

    py_file = repository / "app.py"
    py_file.write_text("def foo(): pass\n", encoding="utf-8")
    commit_all(repository, "add python file")

    js_file = repository / "main.js"
    js_file.write_text("function foo() {}\n", encoding="utf-8")
    commit_all(repository, "add javascript file")

    result = analyze_repository(repository, languages=["python"])

    paths = [h.path for h in result.hotspots]
    assert "app.py" in paths
    assert "main.js" not in paths


def test_analyze_repository_finds_python_hotspot(tmp_path: Path) -> None:
    repository = tmp_path / "sample"
    repository.mkdir()
    run_git(repository, "init")

    source = repository / "calculator.py"
    source.write_text(
        """
def add(a, b):
    return a + b
""".strip()
        + "\n",
        encoding="utf-8",
    )
    commit_all(repository, "add calculator")

    source.write_text(
        """
def add(a, b):
    if a is None:
        return b
    return a + b


def classify(value):
    if value > 10:
        return "high"
    if value > 5:
        return "medium"
    return "low"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    commit_all(repository, "increase complexity")

    result = analyze_repository(repository, languages=["python"])

    assert result.commits_analyzed == 2
    assert result.files_analyzed == 1
    assert result.hotspots[0].path == "calculator.py"
    assert result.hotspots[0].commits == 2
    assert result.hotspots[0].total_complexity > 0
