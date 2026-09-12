#!/usr/bin/env python3
"""List GitCode PRs merged into a base branch within a time window."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API_ROOT = "https://api.gitcode.com/api/v5"


def request(url: str, token: str):
    headers = {
        "Accept": "application/json",
        "User-Agent": "gitcode-pr-summary",
        "Authorization": f"Bearer {token}",
        "PRIVATE-TOKEN": token,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(err)
        except json.JSONDecodeError:
            body = {"raw": err}
        return exc.code, body


def parse_time(value: str | None):
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="Ascend")
    parser.add_argument("--repo", default="msprof")
    parser.add_argument("--base", default="master")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--state", default="merged", help="merged or closed")
    args = parser.parse_args()

    token = os.environ.get("GITCODE_API_TOKEN")
    if not token:
        print("GITCODE_API_TOKEN is required", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)
    collected = []
    page = 1
    while page <= 20:
        qs = urllib.parse.urlencode(
            {
                "state": args.state,
                "base": args.base,
                "sort": "updated",
                "direction": "desc",
                "per_page": 50,
                "page": page,
            }
        )
        url = f"{API_ROOT}/repos/{args.owner}/{args.repo}/pulls?{qs}"
        status, data = request(url, token)
        if status != 200 or not isinstance(data, list):
            print(json.dumps({"error": status, "body": data}, ensure_ascii=False), file=sys.stderr)
            return 1
        if not data:
            break
        stop = False
        for pr in data:
            if (pr.get("base") or {}).get("ref") not in (None, args.base) and (pr.get("base") or {}).get(
                "ref"
            ) != args.base:
                continue
            merged_at = parse_time(pr.get("merged_at") or pr.get("closed_at"))
            if pr.get("merged_at") is None and args.state == "merged":
                continue
            if merged_at and merged_at < since:
                stop = True
                continue
            if merged_at and merged_at > now:
                continue
            collected.append(
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "html_url": pr.get("html_url"),
                    "merged_at": pr.get("merged_at"),
                    "user": (pr.get("user") or {}).get("login"),
                    "base": (pr.get("base") or {}).get("ref"),
                    "merge_commit_sha": pr.get("merge_commit_sha") or pr.get("merge_commit"),
                    "head_sha": (pr.get("head") or {}).get("sha"),
                }
            )
        if stop or len(data) < 50:
            break
        page += 1

    collected.sort(key=lambda x: x.get("merged_at") or "", reverse=True)
    print(json.dumps({"since": since.isoformat(), "count": len(collected), "prs": collected}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
