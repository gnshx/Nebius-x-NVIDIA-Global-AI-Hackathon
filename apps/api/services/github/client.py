"""
RepoMedic — GitHub API Client

Provides an async, installation-token-authenticated HTTP client for all
GitHub API operations required by the RepoMedic agent pipeline.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
import structlog

from .app import github_app

logger = structlog.get_logger(__name__)

BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns a non-2xx status."""

    def __init__(self, status_code: int, message: str, url: str = "") -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"GitHub API error {status_code} on {url!r}: {message}")


def _raise_for_github(resp: httpx.Response) -> None:
    """Raise GitHubAPIError with a descriptive message on non-2xx responses."""
    if resp.is_error:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise GitHubAPIError(resp.status_code, detail, str(resp.url))


async def _headers(installation_id: int) -> dict[str, str]:
    token = await github_app.get_installation_token(installation_id)
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


class GitHubClient:
    """Async GitHub API client authenticated via GitHub App installation tokens."""

    # ------------------------------------------------------------------ #
    #  Repository / Issue reads                                            #
    # ------------------------------------------------------------------ #

    async def get_repo(self, installation_id: int, full_name: str) -> dict[str, Any]:
        """Fetch repository metadata."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}",
                headers=await _headers(installation_id),
            )
        _raise_for_github(resp)
        return resp.json()

    async def get_issue(
        self, installation_id: int, full_name: str, number: int
    ) -> dict[str, Any]:
        """Fetch a single issue by number."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}/issues/{number}",
                headers=await _headers(installation_id),
            )
        _raise_for_github(resp)
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Tree / file operations                                              #
    # ------------------------------------------------------------------ #

    async def get_repo_tree(
        self, installation_id: int, full_name: str, sha: str
    ) -> list[dict[str, Any]]:
        """Return the recursive file tree for a given commit SHA."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}/git/trees/{sha}",
                params={"recursive": "1"},
                headers=await _headers(installation_id),
            )
        _raise_for_github(resp)
        data = resp.json()
        return data.get("tree", [])

    async def get_file_content(
        self,
        installation_id: int,
        full_name: str,
        path: str,
        ref: str,
    ) -> str:
        """Fetch and decode a file's content from the given ref."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}/contents/{path}",
                params={"ref": ref},
                headers=await _headers(installation_id),
            )
        _raise_for_github(resp)
        data = resp.json()
        encoded = data.get("content", "")
        # GitHub returns base64 with newlines
        return base64.b64decode(encoded.replace("\n", "")).decode("utf-8", errors="replace")

    async def get_default_branch_sha(
        self, installation_id: int, full_name: str
    ) -> str:
        """Return the HEAD commit SHA of the repository's default branch."""
        repo = await self.get_repo(installation_id, full_name)
        default_branch = repo["default_branch"]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}/branches/{default_branch}",
                headers=await _headers(installation_id),
            )
        _raise_for_github(resp)
        return resp.json()["commit"]["sha"]

    # ------------------------------------------------------------------ #
    #  Branch / commit operations                                          #
    # ------------------------------------------------------------------ #

    async def create_branch(
        self,
        installation_id: int,
        full_name: str,
        branch_name: str,
        sha: str,
    ) -> None:
        """Create a new branch pointing to the given SHA."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/repos/{full_name}/git/refs",
                headers=await _headers(installation_id),
                json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            )
        _raise_for_github(resp)
        logger.info("branch_created", repo=full_name, branch=branch_name, sha=sha)

    async def create_or_update_file(
        self,
        installation_id: int,
        full_name: str,
        path: str,
        message: str,
        content: str,
        branch: str,
        sha: str | None = None,
    ) -> dict[str, Any]:
        """
        Create or update a file in the repository.

        `sha` is required when updating an existing file (the blob SHA of
        the current version). Omit it for new files.
        """
        encoded = base64.b64encode(content.encode()).decode()
        body: dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if sha:
            body["sha"] = sha

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{BASE_URL}/repos/{full_name}/contents/{path}",
                headers=await _headers(installation_id),
                json=body,
            )
        _raise_for_github(resp)
        return resp.json()

    # ------------------------------------------------------------------ #
    #  Pull Request operations                                             #
    # ------------------------------------------------------------------ #

    async def create_pull_request(
        self,
        installation_id: int,
        full_name: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> dict[str, Any]:
        """Open a new pull request."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/repos/{full_name}/pulls",
                headers=await _headers(installation_id),
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                },
            )
        _raise_for_github(resp)
        pr = resp.json()
        logger.info("pull_request_created", repo=full_name, pr_number=pr.get("number"))
        return pr

    async def check_existing_pr(
        self,
        installation_id: int,
        full_name: str,
        head_branch: str,
    ) -> dict[str, Any] | None:
        """
        Return the first open PR for `head_branch`, or None if not found.

        GitHub's `head` filter format is `owner:branch`.
        """
        owner = full_name.split("/")[0]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/repos/{full_name}/pulls",
                headers=await _headers(installation_id),
                params={
                    "state": "open",
                    "head": f"{owner}:{head_branch}",
                },
            )
        _raise_for_github(resp)
        prs = resp.json()
        return prs[0] if prs else None

    # ------------------------------------------------------------------ #
    #  Comments                                                            #
    # ------------------------------------------------------------------ #

    async def post_comment(
        self,
        installation_id: int,
        full_name: str,
        issue_number: int,
        body: str,
    ) -> dict[str, Any]:
        """Post a comment on an issue or pull request."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/repos/{full_name}/issues/{issue_number}/comments",
                headers=await _headers(installation_id),
                json={"body": body},
            )
        _raise_for_github(resp)
        return resp.json()


# Singleton used across the application
github_client = GitHubClient()
