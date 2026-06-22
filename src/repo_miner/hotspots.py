from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from fnmatch import fnmatch
from math import sqrt
from pathlib import Path

from repo_miner.complexity import analyze_complexity, is_source_file, normalize_languages
from repo_miner.git_mining import mine_history
from repo_miner.models import AnalysisResult, ComplexityMetrics, FileHotspot, HistoryMetrics

DEFAULT_EXCLUDE_PATTERNS = (
    ".git/*",
    ".venv/*",
    "venv/*",
    "__pycache__/*",
    "node_modules/*",
    "*/node_modules/*",
    "dist/*",
    "build/*",
    "target/*",
    "*.min.js",
    "*.lock",
)


def parse_date(value: str | None) -> datetime | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD or ISO datetime.") from exc


def matches_any(path: str, patterns: Iterable[str] | None) -> bool:
    if not patterns:
        return False
    return any(fnmatch(path, pattern) for pattern in patterns if pattern)


def select_candidate_paths(
    repository: Path,
    history: dict[str, HistoryMetrics],
    *,
    languages: Iterable[str] | None = None,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    min_commits: int = 1,
) -> list[str]:
    normalized_languages = normalize_languages(languages)
    exclude_patterns = tuple(exclude or DEFAULT_EXCLUDE_PATTERNS)

    candidates: list[str] = []
    for relative_path, metrics in history.items():
        if metrics.commits < min_commits:
            continue
        if include and not matches_any(relative_path, include):
            continue
        if matches_any(relative_path, exclude_patterns):
            continue
        if not is_source_file(relative_path, normalized_languages):
            continue
        if not (repository / relative_path).is_file():
            continue
        candidates.append(relative_path)

    return sorted(candidates)


def normalize_metric(value: int | float, max_value: int | float) -> float:
    if max_value <= 0:
        return 0.0
    return max(value / max_value, 0.0)


def compute_hotspot_score(
    *,
    commits: int,
    total_complexity: int,
    line_churn: int,
    max_commits: int,
    max_complexity: int,
    max_line_churn: int,
) -> float:
    commit_pressure = normalize_metric(commits, max_commits)
    complexity_pressure = normalize_metric(total_complexity, max_complexity)
    churn_pressure = normalize_metric(line_churn, max_line_churn)

    combined_pressure = sqrt(commit_pressure * complexity_pressure)
    score = 100 * (
        0.75 * combined_pressure
        + 0.15 * commit_pressure
        + 0.10 * churn_pressure
    )
    return round(score, 4)


def classify_risk(score: float) -> str:
    if score >= 70:
        return "alto"
    if score >= 40:
        return "medio"
    return "baixo"


def build_hotspot(
    history: HistoryMetrics,
    complexity: ComplexityMetrics,
    *,
    max_commits: int,
    max_complexity: int,
    max_line_churn: int,
) -> FileHotspot:
    score = compute_hotspot_score(
        commits=history.commits,
        total_complexity=complexity.total_complexity,
        line_churn=history.line_churn,
        max_commits=max_commits,
        max_complexity=max_complexity,
        max_line_churn=max_line_churn,
    )

    return FileHotspot(
        path=history.path,
        commits=history.commits,
        added_lines=history.added_lines,
        deleted_lines=history.deleted_lines,
        line_churn=history.line_churn,
        authors=len(history.authors),
        total_complexity=complexity.total_complexity,
        max_function_complexity=complexity.max_function_complexity,
        average_function_complexity=complexity.average_function_complexity,
        functions=complexity.functions,
        nloc=complexity.nloc,
        score=score,
        risk=classify_risk(score),
    )


def analyze_repository(
    repository: Path,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    languages: Iterable[str] | None = None,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    min_commits: int = 1,
) -> AnalysisResult:
    if min_commits < 1:
        raise ValueError("min_commits must be greater than or equal to 1.")

    repository = repository.expanduser().resolve()
    history, commits_analyzed = mine_history(repository, since=since, until=until)
    candidate_paths = select_candidate_paths(
        repository,
        history,
        languages=languages,
        include=include,
        exclude=exclude,
        min_commits=min_commits,
    )

    complexities = {
        path: analyze_complexity(repository / path, path)
        for path in candidate_paths
    }

    max_commits = max((history[path].commits for path in candidate_paths), default=0)
    max_complexity = max(
        (complexities[path].total_complexity for path in candidate_paths),
        default=0,
    )
    max_line_churn = max((history[path].line_churn for path in candidate_paths), default=0)

    hotspots = tuple(
        sorted(
            (
                build_hotspot(
                    history[path],
                    complexities[path],
                    max_commits=max_commits,
                    max_complexity=max_complexity,
                    max_line_churn=max_line_churn,
                )
                for path in candidate_paths
            ),
            key=lambda hotspot: (
                hotspot.score,
                hotspot.commits,
                hotspot.total_complexity,
                hotspot.line_churn,
            ),
            reverse=True,
        )
    )

    return AnalysisResult(
        repository=repository,
        hotspots=hotspots,
        commits_analyzed=commits_analyzed,
        files_seen=len(history),
        files_analyzed=len(candidate_paths),
        since=since,
        until=until,
    )
