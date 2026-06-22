from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import lizard

from repo_miner.models import ComplexityMetrics

LANGUAGE_EXTENSIONS: dict[str, set[str]] = {
    "python": {".py"},
    "java": {".java"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs"},
    "typescript": {".ts", ".tsx"},
    "c": {".c", ".h"},
    "cpp": {".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"},
    "csharp": {".cs"},
    "go": {".go"},
    "ruby": {".rb"},
    "php": {".php"},
    "swift": {".swift"},
    "kotlin": {".kt", ".kts"},
    "rust": {".rs"},
    "scala": {".scala"},
}

SUPPORTED_EXTENSIONS = frozenset(
    extension for extensions in LANGUAGE_EXTENSIONS.values() for extension in extensions
)


def normalize_languages(languages: Iterable[str] | None) -> set[str] | None:
    if not languages:
        return None

    normalized = {language.strip().lower() for language in languages if language.strip()}
    unknown = normalized - set(LANGUAGE_EXTENSIONS)
    if unknown:
        supported = ", ".join(sorted(LANGUAGE_EXTENSIONS))
        unknown_values = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown language(s): {unknown_values}. Supported: {supported}.")

    return normalized


def is_source_file(path: str | Path, languages: Iterable[str] | None = None) -> bool:
    extension = Path(path).suffix.lower()
    normalized_languages = normalize_languages(languages)

    if normalized_languages is None:
        return extension in SUPPORTED_EXTENSIONS

    allowed_extensions = set()
    for language in normalized_languages:
        allowed_extensions.update(LANGUAGE_EXTENSIONS[language])

    return extension in allowed_extensions


def analyze_complexity(file_path: Path, relative_path: str) -> ComplexityMetrics:
    try:
        file_info = lizard.analyze_file(str(file_path))
    except Exception:
        return ComplexityMetrics(path=relative_path)

    complexities = [
        int(getattr(function, "cyclomatic_complexity", 0) or 0)
        for function in getattr(file_info, "function_list", [])
    ]
    total_complexity = sum(complexities)
    function_count = len(complexities)
    average_complexity = total_complexity / function_count if function_count else 0.0

    return ComplexityMetrics(
        path=relative_path,
        total_complexity=total_complexity,
        max_function_complexity=max(complexities, default=0),
        average_function_complexity=average_complexity,
        functions=function_count,
        nloc=int(getattr(file_info, "nloc", 0) or 0),
    )
