from __future__ import annotations

from pathlib import Path

import pytest

from repo_miner.complexity import analyze_complexity, is_source_file, normalize_languages


def test_normalize_languages_returns_none_for_none() -> None:
    assert normalize_languages(None) is None


def test_normalize_languages_returns_none_for_empty_list() -> None:
    assert normalize_languages([]) is None


def test_normalize_languages_normalizes_case() -> None:
    result = normalize_languages(["Python", "JAVA"])
    assert result == {"python", "java"}


def test_normalize_languages_raises_on_unknown_language() -> None:
    with pytest.raises(ValueError, match="Unknown language"):
        normalize_languages(["cobol"])


def test_is_source_file_detects_python() -> None:
    assert is_source_file("src/main.py") is True


def test_is_source_file_detects_java() -> None:
    assert is_source_file("src/Main.java") is True


def test_is_source_file_rejects_text_file() -> None:
    assert is_source_file("README.txt") is False


def test_is_source_file_with_language_filter_matches() -> None:
    assert is_source_file("app.py", languages=["python"]) is True


def test_is_source_file_with_language_filter_excludes() -> None:
    assert is_source_file("Main.java", languages=["python"]) is False


def test_analyze_complexity_nonexistent_file_returns_zero_metrics() -> None:
    metrics = analyze_complexity(Path("/nonexistent/path/file.py"), "file.py")
    assert metrics.path == "file.py"
    assert metrics.total_complexity == 0
    assert metrics.functions == 0
    assert metrics.nloc == 0


def test_analyze_complexity_on_real_python_file(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "def foo(x):\n"
        "    if x > 0:\n"
        "        return x\n"
        "    return -x\n",
        encoding="utf-8",
    )
    metrics = analyze_complexity(source, "sample.py")
    assert metrics.functions == 1
    assert metrics.total_complexity >= 1
    assert metrics.nloc > 0
