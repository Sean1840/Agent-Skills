#!/usr/bin/env python3
"""Post a GitCode PR comment on a specific new-file line.

GitCode maps `position` to the new-file line number. Using `line` creates a
timeline pr_comment instead of a Files-tab diff_comment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_ROOT = "https://api.gitcode.com/api/v5"


def request(method: str, url: str, token: str, payload: dict | None = None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "gitcode-review",
        "Authorization": f"Bearer {token}",
        "PRIVATE-TOKEN": token,
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err)
        except json.JSONDecodeError:
            parsed = {"raw": err}
        return exc.code, parsed


def post_inline(owner: str, repo: str, pr: int, path: str, position: int, commit_id: str, body: str, token: str):
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr}/comments"
    payload = {
        "body": body,
        "path": path,
        "position": position,
        "commit_id": commit_id,
    }
    return request("POST", url, token, payload)


def find_posted(owner: str, repo: str, pr: int, token: str, path: str, position: int, body_prefix: str):
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr}/comments?per_page=100"
    status, comments = request("GET", url, token)
    if status != 200 or not isinstance(comments, list):
        return status, None
    for comment in comments:
        if (comment.get("body") or "").startswith(body_prefix[:40]):
            return status, comment
        pos = comment.get("diff_position") or {}
        if comment.get("comment_type") == "diff_comment" and pos.get("start_new_line") == position:
            if path.replace("\\", "/") in (comment.get("body") or "") or True:
                # prefer body match; fall through
                pass
    # last matching diff_comment on that line from current user is enough
    for comment in reversed(comments):
        pos = comment.get("diff_position") or {}
        if comment.get("comment_type") == "diff_comment" and pos.get("start_new_line") == position:
            if body_prefix[:24] in (comment.get("body") or ""):
                return status, comment
    return status, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Post GitCode inline (diff) PR comment")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--path", required=True)
    parser.add_argument("--position", required=True, type=int, help="New-file line number (1-based)")
    parser.add_argument("--commit-id", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("GITCODE_API_TOKEN")
    if not token:
        print("GITCODE_API_TOKEN is required", file=sys.stderr)
        return 1

    body = args.body
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()
    body = body.strip()
    if not body:
        print("empty body", file=sys.stderr)
        return 1

    status, created = post_inline(
        args.owner, args.repo, args.pr, args.path, args.position, args.commit_id, body, token
    )
    print(json.dumps({"post_status": status, "created": created}, ensure_ascii=False))
    if status not in (200, 201):
        return 1

    if args.verify:
        st, comment = find_posted(
            args.owner, args.repo, args.pr, token, args.path, args.position, body
        )
        if not comment:
            print("verify failed: comment not found in GET list", file=sys.stderr)
            return 1
        pos = comment.get("diff_position") or {}
        ok = comment.get("comment_type") == "diff_comment" and pos.get("start_new_line") == args.position
        print(
            json.dumps(
                {
                    "verify_status": st,
                    "comment_id": comment.get("id"),
                    "comment_type": comment.get("comment_type"),
                    "diff_position": pos,
                    "ok": ok,
                },
                ensure_ascii=False,
            )
        )
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
