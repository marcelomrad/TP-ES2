from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repo_miner.git_mining import RepositoryMiningError, clone_remote, is_remote_url


@pytest.mark.parametrize(
    "source,expected",
    [
        ("https://github.com/user/repo.git", True),
        ("http://github.com/user/repo.git", True),
        ("git@github.com:user/repo.git", True),
        ("git://github.com/user/repo.git", True),
        ("ssh://git@github.com/user/repo.git", True),
        ("/home/user/myrepo", False),
        ("./relative/path", False),
        ("C:\\Users\\user\\repo", False),
        (".", False),
    ],
)
def test_is_remote_url(source: str, expected: bool) -> None:
    assert is_remote_url(source) == expected


def test_clone_remote_raises_on_invalid_url() -> None:
    with pytest.raises(RepositoryMiningError, match="Could not clone repository"):
        with clone_remote("https://github.com/invalid-user-xyz/nonexistent-repo-xyz.git"):
            pass


def test_clone_remote_yields_path(tmp_path: Path) -> None:
    fake_clone_path = tmp_path / "repo"
    fake_clone_path.mkdir()

    with patch("repo_miner.git_mining.subprocess.run") as mock_run, \
         patch("repo_miner.git_mining.tempfile.TemporaryDirectory") as mock_tmp:
        mock_tmp.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        mock_run.return_value = MagicMock(returncode=0)

        with clone_remote("https://github.com/user/repo.git") as path:
            assert isinstance(path, Path)
            assert path == tmp_path / "repo"
