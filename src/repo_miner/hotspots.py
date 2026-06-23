from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from fnmatch import fnmatch
from math import sqrt
from pathlib import Path

from repo_miner.complexity import analyze_complexity, is_source_file, normalize_languages
from repo_miner.git_mining import clone_remote, is_remote_url, mine_history
from repo_miner.models import AnalysisResult, ComplexityMetrics, FileHotspot, HistoryMetrics

DEFAULT_EXCLUDE_PATTERNS = (
    ".git/*",
    ".venv/*",
    "venv/*",
    "env/*",
    "__pycache__/*",
    "*.pyc",
    ".mypy_cache/*",
    ".pytest_cache/*",
    "*.egg-info/*",
    "node_modules/*",
    "*/node_modules/*",
    "dist/*",
    "build/*",
    "target/*",
    ".idea/*",
    ".vscode/*",
    "*.min.js",
    "*.lock",
    "htmlcov/*",
)
VALID_RISK_LEVELS = {"baixo", "medio", "alto"}
VALID_SORT_MODES = {"score", "commits", "complexity", "churn"}


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


def normalize_risk_levels(risks: Iterable[str] | None) -> set[str]:
    if not risks:
        return set()

    normalized = {risk.strip().lower() for risk in risks if risk.strip()}
    invalid = normalized - VALID_RISK_LEVELS
    if invalid:
        supported = ", ".join(sorted(VALID_RISK_LEVELS))
        received = ", ".join(sorted(invalid))
        raise ValueError(f"Invalid risk level '{received}'. Use one of: {supported}.")
    return normalized


def normalize_sort_mode(sort_by: str) -> str:
    normalized = sort_by.strip().lower()
    if normalized not in VALID_SORT_MODES:
        supported = ", ".join(sorted(VALID_SORT_MODES))
        raise ValueError(f"Invalid sort mode '{sort_by}'. Use one of: {supported}.")
    return normalized


def hotspot_sort_key(hotspot: FileHotspot, sort_by: str) -> tuple[float | int, ...]:
    if sort_by == "commits":
        return (hotspot.commits, hotspot.score, hotspot.total_complexity, hotspot.line_churn)
    if sort_by == "complexity":
        return (hotspot.total_complexity, hotspot.score, hotspot.commits, hotspot.line_churn)
    if sort_by == "churn":
        return (hotspot.line_churn, hotspot.score, hotspot.commits, hotspot.total_complexity)
    return (hotspot.score, hotspot.commits, hotspot.total_complexity, hotspot.line_churn)


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
    repository: str | Path,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    languages: Iterable[str] | None = None,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    min_commits: int = 1,
    min_score: float = 0.0,
    risks: Iterable[str] | None = None,
    sort_by: str = "score",
) -> AnalysisResult:
    if min_commits < 1:
        raise ValueError("min_commits must be greater than or equal to 1.")
    if since and until and until < since:
        raise ValueError("until must be greater than or equal to since.")

    if isinstance(repository, str) and is_remote_url(repository):
        history, commits_analyzed = mine_history(repository, since=since, until=until)
        with clone_remote(repository) as local_path:
            return _build_result(
                repository=local_path,
                display_repository=repository,
                history=history,
                commits_analyzed=commits_analyzed,
                languages=languages,
                include=include,
                exclude=exclude,
                min_commits=min_commits,
                min_score=min_score,
                risks=risks,
                sort_by=sort_by,
                since=since,
                until=until,
            )

    local_repository = Path(repository).expanduser().resolve()
    history, commits_analyzed = mine_history(local_repository, since=since, until=until)
    return _build_result(
        repository=local_repository,
        display_repository=local_repository,
        history=history,
        commits_analyzed=commits_analyzed,
        languages=languages,
        include=include,
        exclude=exclude,
        min_commits=min_commits,
        min_score=min_score,
        risks=risks,
        sort_by=sort_by,
        since=since,
        until=until,
    )


def _build_result(
    repository: Path,
    display_repository: str | Path,
    history: dict[str, HistoryMetrics],
    commits_analyzed: int,
    *,
    languages: Iterable[str] | None,
    include: Iterable[str] | None,
    exclude: Iterable[str] | None,
    min_commits: int,
    min_score: float,
    risks: Iterable[str] | None,
    sort_by: str,
    since: datetime | None,
    until: datetime | None,
) -> AnalysisResult:
    risk_levels = normalize_risk_levels(risks)
    sort_mode = normalize_sort_mode(sort_by)
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
            key=lambda hotspot: hotspot_sort_key(hotspot, sort_mode),
            reverse=True,
        )
    )

    if min_score > 0.0:
        hotspots = tuple(h for h in hotspots if h.score >= min_score)
    if risk_levels:
        hotspots = tuple(h for h in hotspots if h.risk in risk_levels)

    return AnalysisResult(
        repository=display_repository,
        hotspots=hotspots,
        commits_analyzed=commits_analyzed,
        files_seen=len(history),
        files_analyzed=len(candidate_paths),
        since=since,
        until=until,
    )
