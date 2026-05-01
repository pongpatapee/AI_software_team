"""MCP-like GitHub adapter for issue creation.

V1 wraps the `gh` CLI. Tests use ``RecordingGitHubAdapter`` to keep the default
suite deterministic and offline.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class CreatedIssue:
    number: int
    url: str
    title: str


class GitHubAdapter(Protocol):
    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> CreatedIssue:
        ...


class GitHubAdapterError(RuntimeError):
    """Raised when the GitHub adapter cannot create an issue."""


class GhCliGitHubAdapter:
    """GitHub adapter backed by the local ``gh`` CLI.

    Requires ``gh`` to be authenticated and the working directory to point at
    the Target Project repo.
    """

    def __init__(self, target_project: str | None = None) -> None:
        self._cwd = target_project

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> CreatedIssue:
        if shutil.which("gh") is None:
            raise GitHubAdapterError("`gh` CLI not found on PATH.")

        cmd = ["gh", "issue", "create", "--title", title, "--body", body]
        for label in labels or []:
            cmd.extend(["--label", label])

        result = subprocess.run(
            cmd, cwd=self._cwd, text=True, capture_output=True, check=False
        )
        if result.returncode != 0:
            raise GitHubAdapterError(
                f"`gh issue create` failed: {result.stderr.strip() or result.stdout.strip()}"
            )

        url = result.stdout.strip().splitlines()[-1]
        number = _parse_issue_number(url)
        return CreatedIssue(number=number, url=url, title=title)


@dataclass
class RecordingGitHubAdapter:
    """Deterministic adapter for tests. Records calls and returns synthetic URLs."""

    repo: str = "owner/repo"
    calls: list[dict[str, object]] = field(default_factory=list)
    _next_number: int = 1000

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> CreatedIssue:
        number = self._next_number
        self._next_number += 1
        self.calls.append({"title": title, "body": body, "labels": list(labels or [])})
        return CreatedIssue(
            number=number,
            url=f"https://github.com/{self.repo}/issues/{number}",
            title=title,
        )


def _parse_issue_number(url: str) -> int:
    tail = url.rsplit("/", 1)[-1]
    return int(tail)


def adapter_from_env(env: dict[str, str], target_project: str | None = None) -> GitHubAdapter:
    """Resolve a GitHub adapter from environment configuration.

    ``AI_TEAM_GITHUB_ADAPTER=fake`` returns a deterministic recording adapter
    used by the default test suite. Anything else returns the ``gh`` CLI
    adapter.
    """
    selector = env.get("AI_TEAM_GITHUB_ADAPTER", "").lower()
    if selector == "fake":
        repo = env.get("AI_TEAM_GITHUB_FAKE_REPO", "owner/repo")
        return RecordingGitHubAdapter(repo=repo)
    return GhCliGitHubAdapter(target_project=target_project)


__all__ = [
    "CreatedIssue",
    "GhCliGitHubAdapter",
    "GitHubAdapter",
    "GitHubAdapterError",
    "RecordingGitHubAdapter",
    "adapter_from_env",
]
