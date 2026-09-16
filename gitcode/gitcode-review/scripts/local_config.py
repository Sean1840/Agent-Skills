#!/usr/bin/env python3
"""User-local Agent-Skills config. Do not invent paths or tokens.

File: ~/.agent-skills/config.json (override with AGENT_SKILLS_CONFIG).
Missing keys mean: stop and ask the user, then set().
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCHEMA = "agent-skills.config.v1"


def config_path() -> Path:
    env = os.environ.get("AGENT_SKILLS_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".agent-skills" / "config.json"


def suggested_review_root() -> Path:
    """Display-only default. Never create or clone here until the user confirms."""
    return Path.home() / "review"


def load() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {"schema": SCHEMA}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema": SCHEMA}
    if not isinstance(data, dict):
        return {"schema": SCHEMA}
    data.setdefault("schema", SCHEMA)
    return data


def save(data: dict[str, Any]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["schema"] = SCHEMA
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _gitcode(data: dict[str, Any] | None = None) -> dict[str, Any]:
    blob = data if data is not None else load()
    return blob.setdefault("gitcode", {})


def get_token() -> str | None:
    env = os.environ.get("GITCODE_API_TOKEN", "").strip()
    if env:
        return env
    token = str(_gitcode().get("api_token") or "").strip()
    return token or None


def set_token(token: str) -> None:
    token = token.strip()
    if not token:
        raise ValueError("empty token")
    os.environ["GITCODE_API_TOKEN"] = token
    data = load()
    _gitcode(data)["api_token"] = token
    save(data)
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "GITCODE_API_TOKEN", 0, winreg.REG_SZ, token)
            winreg.CloseKey(key)
        except OSError:
            pass


def get_review_root() -> Path | None:
    raw = str(_gitcode().get("review_root") or "").strip()
    return Path(raw).expanduser() if raw else None


def set_review_root(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    data = load()
    _gitcode(data)["review_root"] = str(resolved)
    save(data)
    return resolved


def get_clone_path(owner: str, repo: str) -> Path | None:
    key = f"{owner}/{repo}"
    clones = _gitcode().get("clones") or {}
    raw = str(clones.get(key) or "").strip()
    if raw:
        return Path(raw).expanduser()
    root = get_review_root()
    if root:
        return root / repo
    return None


def set_clone_path(owner: str, repo: str, path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    data = load()
    gc = _gitcode(data)
    clones = dict(gc.get("clones") or {})
    clones[f"{owner}/{repo}"] = str(resolved)
    gc["clones"] = clones
    if not gc.get("review_root"):
        gc["review_root"] = str(resolved.parent)
    save(data)
    return resolved


def get_summary_output_dir() -> Path | None:
    raw = str(_gitcode().get("summary_output_dir") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return get_review_root()


def set_summary_output_dir(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    data = load()
    _gitcode(data)["summary_output_dir"] = str(resolved)
    save(data)
    return resolved


def set_cann_repo_path(repo_id: str, path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    data = load()
    cann = data.setdefault("cann", {})
    mapping = dict(cann.get("repo_paths") or {})
    mapping[repo_id] = str(resolved)
    cann["repo_paths"] = mapping
    save(data)
    return resolved


def missing_for_review(owner: str, repo: str) -> list[str]:
    missing = []
    if get_clone_path(owner, repo) is None:
        missing.append("clone_path")
    return missing


def missing_for_summary() -> list[str]:
    missing = []
    if get_review_root() is None and get_summary_output_dir() is None:
        missing.append("summary_output_dir")
    return missing


def _cmd_show(_: argparse.Namespace) -> int:
    data = load()
    public = json.loads(json.dumps(data))
    token = ((public.get("gitcode") or {}).get("api_token") or "")
    if token:
        public["gitcode"]["api_token"] = "<set>"
    public["_path"] = str(config_path())
    public["_env_token"] = bool(os.environ.get("GITCODE_API_TOKEN"))
    print(json.dumps(public, ensure_ascii=False, indent=2))
    return 0


def _cmd_set(args: argparse.Namespace) -> int:
    if args.key == "gitcode.review_root":
        set_review_root(args.value)
    elif args.key == "gitcode.summary_output_dir":
        set_summary_output_dir(args.value)
    elif args.key == "gitcode.api_token":
        set_token(args.value)
    else:
        print(f"unknown key: {args.key}", file=sys.stderr)
        return 1
    print(str(config_path()))
    return 0


def _cmd_set_cann_repo(args: argparse.Namespace) -> int:
    set_cann_repo_path(args.repo_id, args.path)
    print(str(config_path()))
    return 0


def _cmd_set_clone(args: argparse.Namespace) -> int:
    if "/" not in args.repo:
        print("repo must be owner/name", file=sys.stderr)
        return 1
    owner, repo = args.repo.split("/", 1)
    set_clone_path(owner, repo, args.path)
    print(str(config_path()))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent-Skills local config")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show").set_defaults(func=_cmd_show)
    p_set = sub.add_parser("set")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=_cmd_set)
    p_clone = sub.add_parser("set-clone")
    p_clone.add_argument("repo", help="owner/name")
    p_clone.add_argument("path")
    p_clone.set_defaults(func=_cmd_set_clone)
    p_cann = sub.add_parser("set-cann-repo")
    p_cann.add_argument("repo_id", help="catalog id, e.g. ascend/msprof")
    p_cann.add_argument("path")
    p_cann.set_defaults(func=_cmd_set_cann_repo)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
