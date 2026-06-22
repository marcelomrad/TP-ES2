from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydriller import Repository

from repo_miner.models import HistoryMetrics


class RepositoryMiningError(RuntimeError):
    """Raised when a path cannot be mined as a Git repository."""


def is_remote_url(source: str) -> bool:
    return source.startswith(("https://", "http://", "git@", "git://", "ssh://"))


def ensure_git_repository(repository: Path) -> Path:
    repository = repository.expanduser().resolve()
    if not repository.exists():
        raise RepositoryMiningError(f"Repository path does not exist: {repository}")
    if not (repository / ".git").exists():
        raise RepositoryMiningError(f"Path is not a Git repository: {repository}")
    return repository


def normalize_repo_path(path: str | None) -> str | None:
    if path is None:
        return None
    return path.replace("\\", "/")


def mine_history(
    repository: Path,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[dict[str, HistoryMetrics], int]:
    repository = ensure_git_repository(repository)
    repository_args: dict[str, datetime] = {}

    if since is not None:
        repository_args["since"] = since
    if until is not None:
        repository_args["to"] = until

    history: dict[str, HistoryMetrics] = {}
    commits_analyzed = 0

    try:
        commits = Repository(str(repository), **repository_args).traverse_commits()
        for commit in commits:
            commits_analyzed += 1
            author = getattr(commit.author, "name", None) or getattr(commit.author, "email", None)
            changed_at = commit.author_date

            for modified_file in commit.modified_files:
                relative_path = normalize_repo_path(
                    modified_file.new_path or modified_file.old_path
                )
                if relative_path is None:
                    continue

                file_history = history.setdefault(relative_path, HistoryMetrics(path=relative_path))
                file_history.register_change(
                    added_lines=int(modified_file.added_lines or 0),
                    deleted_lines=int(modified_file.deleted_lines or 0),
                    author=author,
                    changed_at=changed_at,
                )
    except Exception as exc:
        raise RepositoryMiningError(f"Could not mine repository history: {exc}") from exc

    return history, commits_analyzed
