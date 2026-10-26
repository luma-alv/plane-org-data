"""Read-only, bounded audit of the public GitHub API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_REPOSITORY = "makeplane/plane"
DEFAULT_BRANCH = "preview"
API_ROOT = "https://api.github.com"
LINK_RE = re.compile(r'<([^>]+)>; rel="([^"]+)"')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_link_header(value: str | None) -> dict[str, str]:
    """Return relation names and URLs from a GitHub Link header."""
    return {relation: url for url, relation in LINK_RE.findall(value or "")}


def pagination_status(headers: Mapping[str, str], *, requested_page: int = 1) -> dict[str, Any]:
    links = parse_link_header(headers.get("Link") or headers.get("link"))
    return {
        "requested_page": requested_page,
        "has_next": "next" in links,
        "next_url": links.get("next"),
        "last_url": links.get("last"),
        "complete": "next" not in links,
    }


def rate_limit_status(headers: Mapping[str, str]) -> dict[str, Any]:
    def integer(name: str) -> int | None:
        value = headers.get(name) or headers.get(name.lower())
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "limit": integer("X-RateLimit-Limit"),
        "remaining": integer("X-RateLimit-Remaining"),
        "reset_epoch": integer("X-RateLimit-Reset"),
        "used": integer("X-RateLimit-Used"),
    }


class GitHubAPI:
    def __init__(self, token: str | None = None, timeout: int = 30) -> None:
        self.token = token
        self.timeout = timeout
        self.rate_limits: list[dict[str, Any]] = []

    def get(self, path_or_url: str) -> tuple[Any, dict[str, str]]:
        url = path_or_url if path_or_url.startswith("http") else API_ROOT + path_or_url
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "plane-org-data-audit"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                response_headers = dict(response.headers.items())
                self.rate_limits.append(rate_limit_status(response_headers))
                return json.load(response), response_headers
        except HTTPError as error:
            response_headers = dict(error.headers.items()) if error.headers else {}
            self.rate_limits.append(rate_limit_status(response_headers))
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API HTTP {error.code} for {url}: {detail[:500]}") from error
        except URLError as error:
            raise RuntimeError(f"GitHub API connection error for {url}: {error.reason}") from error


def count_search(api: GitHubAPI, query: str) -> dict[str, Any]:
    data, headers = api.get("/search/issues?q=" + query.replace(" ", "+"))
    return {
        "count": data.get("total_count"),
        "incomplete_results": data.get("incomplete_results"),
        "pagination": pagination_status(headers),
    }


def bounded_endpoint(api: GitHubAPI, path: str) -> dict[str, Any]:
    data, headers = api.get(path)
    records = data if isinstance(data, list) else data.get("items", [])
    return {"records_returned": len(records), "pagination": pagination_status(headers)}


def run_audit(repository: str = DEFAULT_REPOSITORY, branch: str = DEFAULT_BRANCH, token: str | None = None) -> dict[str, Any]:
    started = utc_now()
    api = GitHubAPI(token=token)
    result: dict[str, Any] = {
        "audit": {"started_at": started, "ended_at": None, "read_only": True, "repository": repository, "branch": branch},
        "repository": {},
        "counts": {"issues": {}, "pull_requests": {}},
        "sample": {"pull_request": 10016, "reviews": {}, "commits": {}, "comments": {}},
        "rate_limits": [],
        "errors": [],
        "limitations": [
            "This audit uses bounded metadata, search counts, and one pull-request sample.",
            "It does not download the repository history or all issues, pull requests, comments, reviews, or commits.",
            "Search counts and API state can change after this snapshot.",
        ],
    }

    def capture(key: str, operation: Any) -> None:
        try:
            result[key] = operation()
        except RuntimeError as error:
            result["errors"].append({"operation": key, "message": str(error)})

    capture("repository", lambda: api.get(f"/repos/{repository}")[0])
    capture("reference", lambda: api.get(f"/repos/{repository}/branches/{branch}")[0].get("commit", {}))
    capture("counts", lambda: {
        "issues": {"open": count_search(api, f"repo:{repository} is:issue state:open"), "closed": count_search(api, f"repo:{repository} is:issue state:closed")},
        "pull_requests": {"open": count_search(api, f"repo:{repository} is:pr state:open"), "closed": count_search(api, f"repo:{repository} is:pr state:closed"), "merged": count_search(api, f"repo:{repository} is:pr is:merged")},
    })
    capture("sample", lambda: {
        "pull_request": 10016,
        "reviews": bounded_endpoint(api, f"/repos/{repository}/pulls/10016/reviews"),
        "commits": bounded_endpoint(api, f"/repos/{repository}/pulls/10016/commits"),
        "comments": bounded_endpoint(api, f"/repos/{repository}/issues/10016/comments"),
    })
    result["rate_limits"] = api.rate_limits
    result["audit"]["ended_at"] = utc_now()
    return result


def write_manifest(result: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"github_audit_{stamp}.json"
    suffix = 1
    while path.exists():
        path = output_dir / f"github_audit_{stamp}_{suffix}.json"
        suffix += 1
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--output-dir", default="data/interim")
    args = parser.parse_args(argv)
    result = run_audit(args.repository, args.branch, os.environ.get("GITHUB_TOKEN"))
    path = write_manifest(result, Path(args.output_dir))
    print(path)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
