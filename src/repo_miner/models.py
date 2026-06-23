from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class HistoryMetrics:
    path: str
    commits: int = 0
    added_lines: int = 0
    deleted_lines: int = 0
    authors: set[str] = field(default_factory=set)
    first_modified: datetime | None = None
    last_modified: datetime | None = None

    @property
    def line_churn(self) -> int:
        return self.added_lines + self.deleted_lines

    def register_change(
        self,
        *,
        added_lines: int,
        deleted_lines: int,
        author: str | None,
        changed_at: datetime,
    ) -> None:
        self.commits += 1
        self.added_lines += max(added_lines, 0)
        self.deleted_lines += max(deleted_lines, 0)

        if author:
            self.authors.add(author)

        if self.first_modified is None or changed_at < self.first_modified:
            self.first_modified = changed_at
        if self.last_modified is None or changed_at > self.last_modified:
            self.last_modified = changed_at


@dataclass(frozen=True)
class ComplexityMetrics:
    path: str
    total_complexity: int = 0
    max_function_complexity: int = 0
    average_function_complexity: float = 0.0
    functions: int = 0
    nloc: int = 0


@dataclass(frozen=True)
class FileHotspot:
    path: str
    commits: int
    added_lines: int
    deleted_lines: int
    line_churn: int
    authors: int
    total_complexity: int
    max_function_complexity: int
    average_function_complexity: float
    functions: int
    nloc: int
    score: float
    risk: str

    def to_row(self) -> dict[str, str | int | float]:
        return {
            "path": self.path,
            "risk": self.risk,
            "score": round(self.score, 2),
            "commits": self.commits,
            "line_churn": self.line_churn,
            "added_lines": self.added_lines,
            "deleted_lines": self.deleted_lines,
            "authors": self.authors,
            "total_complexity": self.total_complexity,
            "max_function_complexity": self.max_function_complexity,
            "average_function_complexity": round(self.average_function_complexity, 2),
            "functions": self.functions,
            "nloc": self.nloc,
        }


@dataclass(frozen=True)
class AnalysisResult:
    repository: str | Path
    hotspots: tuple[FileHotspot, ...]
    commits_analyzed: int
    files_seen: int
    files_analyzed: int
    since: datetime | None = None
    until: datetime | None = None
    languages: tuple[str, ...] = ()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    min_commits: int = 1
    min_score: float = 0.0
    risks: tuple[str, ...] = ()
    sort_by: str = "score"

    @property
    def has_hotspots(self) -> bool:
        return bool(self.hotspots)
