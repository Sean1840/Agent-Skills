#!/usr/bin/env python3
"""Install Agent-Skills into local coding agents (Grok, Codex/GPT, Kimi, Qwen, …)."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()

# Primary user-level skill dirs. Aliases share a target.
# Grok is special: it can scan this repo recursively via config.toml paths.
AGENTS = {
    "grok": {
        "user": HOME / ".grok" / "skills",
        "project": Path(".grok") / "skills",
        "detect": [HOME / ".grok", "grok"],
        "via": "paths",
    },
    "gpt": {
        "user": HOME / ".codex" / "skills",
        "project": Path(".agents") / "skills",
        "detect": [HOME / ".codex", "codex"],
        "via": "link",
    },
    "codex": {
        "user": HOME / ".codex" / "skills",
        "project": Path(".agents") / "skills",
        "detect": [HOME / ".codex", "codex"],
        "via": "link",
    },
    "kimi": {
        "user": HOME / ".kimi-code" / "skills",
        "project": Path(".agents") / "skills",
        "detect": [HOME / ".kimi-code", HOME / ".kimi", "kimi"],
        "via": "link",
        "user_fallback": [
            HOME / ".config" / "agents" / "skills",
            HOME / ".agents" / "skills",
        ],
    },
    "qwen": {
        "user": HOME / ".qwen" / "skills",
        "project": Path(".qwen") / "skills",
        "detect": [HOME / ".qwen", "qwen"],
        "via": "link",
    },
    "deepseek": {
        "user": HOME / ".agents" / "skills",
        "project": Path(".agents") / "skills",
        "detect": [HOME / ".deepseek", HOME / ".dsh", "dsh", "deepseek"],
        "via": "link",
    },
    "claude": {
        "user": HOME / ".claude" / "skills",
        "project": Path(".claude") / "skills",
        "detect": [HOME / ".claude", "claude"],
        "via": "link",
    },
    "cursor": {
        "user": HOME / ".cursor" / "skills",
        "project": Path(".cursor") / "skills",
        "detect": [HOME / ".cursor", "cursor"],
        "via": "link",
    },
}

SHARED_USER = HOME / ".agents" / "skills"
GROK_CONFIG = HOME / ".grok" / "config.toml"


def discover_skills() -> list[Path]:
    wip = (REPO / "wip").resolve()
    found: list[Path] = []
    for skill_md in REPO.rglob("SKILL.md"):
        d = skill_md.parent.resolve()
        if d == wip or wip in d.parents:
            continue
        if d == REPO:
            continue
        found.append(d)
    found.sort(key=lambda p: p.name)
    return found


def on_path(name: str) -> bool:
    return shutil.which(name) is not None


def detected(agent: str) -> bool:
    for item in AGENTS[agent]["detect"]:
        if isinstance(item, Path):
            if item.exists():
                return True
        elif on_path(item):
            return True
    return False


def user_dir(agent: str) -> Path:
    meta = AGENTS[agent]
    primary = meta["user"]
    if primary.exists() or agent not in ("kimi",):
        return primary
    for fb in meta.get("user_fallback", []):
        if fb.exists():
            return fb
    return primary


def same_target(dst: Path, src: Path) -> bool:
    try:
        if dst.is_symlink() and dst.resolve() == src.resolve():
            return True
    except OSError:
        pass
    if os.name == "nt" and dst.exists() and src.exists():
        try:
            if dst.resolve() == src.resolve():
                return True
        except OSError:
            pass
    return False


def link_or_copy(src: Path, dst: Path) -> str:
    if same_target(dst, src):
        return "exists"
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src, dst, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    if os.name == "nt":
        r = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dst), str(src)],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return "junction"
    shutil.copytree(src, dst)
    return "copy"


def remove_install(dst: Path) -> bool:
    if not (dst.exists() or dst.is_symlink()):
        return False
    if dst.is_symlink() or (os.name == "nt" and dst.is_dir()):
        try:
            dst.unlink()
            return True
        except OSError:
            pass
    if dst.is_dir():
        shutil.rmtree(dst)
        return True
    dst.unlink()
    return True


def ensure_grok_paths() -> str:
    GROK_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    repo = str(REPO).replace("\\", "/")
    wip = f"{repo}/wip"
    block = f'[skills]\npaths = ["{repo}"]\nignore = ["{wip}"]\n'
    if GROK_CONFIG.exists():
        text = GROK_CONFIG.read_text(encoding="utf-8")
        if repo in text and "[skills]" in text:
            return "exists"
        if re.search(r"^\[skills\]", text, re.M):
            text = re.sub(
                r"^\[skills\][^\[]*",
                block + "\n",
                text,
                count=1,
                flags=re.M,
            )
        else:
            text = text.rstrip() + "\n\n" + block
        GROK_CONFIG.write_text(text, encoding="utf-8")
        return "updated"
    GROK_CONFIG.write_text(block, encoding="utf-8")
    return "created"


def parse_agents(raw: str | None, detect_default: bool) -> list[str]:
    if raw:
        names = [a.strip().lower() for a in raw.split(",") if a.strip()]
        if names == ["all"]:
            return list(dict.fromkeys(AGENTS))
        unknown = [a for a in names if a not in AGENTS]
        if unknown:
            sys.exit(f"unknown agent: {', '.join(unknown)}. choose from: {', '.join(AGENTS)}")
        return list(dict.fromkeys(names))
    if not detect_default:
        return []
    found = [a for a in AGENTS if detected(a)]
    return found or ["grok"]


def install(skills: list[Path], agents: list[str], scope: str, project: Path, shared: bool) -> None:
    for skill in skills:
        print(f"skill {skill.name}  ({skill.relative_to(REPO)})")
        for agent in agents:
            meta = AGENTS[agent]
            if scope == "user" and meta["via"] == "paths":
                how = ensure_grok_paths()
                print(f"  {agent:8}  config paths  {how}")
                continue
            dest_root = user_dir(agent) if scope == "user" else (project / meta["project"])
            dest = dest_root / skill.name
            how = link_or_copy(skill, dest)
            print(f"  {agent:8}  {how:8}  {dest}")
        if shared and scope == "user":
            dest = SHARED_USER / skill.name
            how = link_or_copy(skill, dest)
            print(f"  {'shared':8}  {how:8}  {dest}")


def uninstall(skills: list[Path], agents: list[str], scope: str, project: Path, shared: bool) -> None:
    for skill in skills:
        for agent in agents:
            if scope == "user" and AGENTS[agent]["via"] == "paths":
                print(f"  {agent:8}  skip (grok uses config paths; edit ~/.grok/config.toml)")
                continue
            dest_root = user_dir(agent) if scope == "user" else (project / AGENTS[agent]["project"])
            dest = dest_root / skill.name
            print(f"  {skill.name:24} {agent:8}  {'removed' if remove_install(dest) else 'absent'}")
        if shared and scope == "user":
            dest = SHARED_USER / skill.name
            print(f"  {skill.name:24} {'shared':8}  {'removed' if remove_install(dest) else 'absent'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install SKILL.md packs into Grok / Codex(GPT) / Kimi / Qwen / DeepSeek / Claude / Cursor.",
    )
    parser.add_argument("skills", nargs="*", help="skill folder names (default: all)")
    parser.add_argument(
        "--agent",
        help="comma list: grok,gpt,codex,kimi,qwen,deepseek,claude,cursor,all (default: detected)",
    )
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project root when --scope project")
    parser.add_argument("--no-shared", action="store_true", help="do not also install to ~/.agents/skills")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()

    all_skills = discover_skills()
    if args.list:
        print("skills in this repo:")
        for s in all_skills:
            print(f"  {s.name:24} {s.relative_to(REPO)}")
        print("\nagents:")
        for name in AGENTS:
            mark = "yes" if detected(name) else "no"
            print(f"  {name:8} detected={mark:3}  user={user_dir(name)}")
        return 0

    if args.skills:
        wanted = set(args.skills)
        skills = [s for s in all_skills if s.name in wanted]
        missing = wanted - {s.name for s in skills}
        if missing:
            sys.exit(f"skill not found: {', '.join(sorted(missing))}")
    else:
        skills = all_skills
    if not skills:
        sys.exit("no skills found (need <name>/SKILL.md)")

    agents = parse_agents(args.agent, detect_default=not args.uninstall)
    if args.uninstall and not agents:
        agents = parse_agents("all", detect_default=False)
    if not agents:
        sys.exit("no agent selected")

    shared = not args.no_shared
    if args.uninstall:
        uninstall(skills, agents, args.scope, args.project.resolve(), shared)
    else:
        install(skills, agents, args.scope, args.project.resolve(), shared)
        print("\nreload the agent (new session, or /skills) to pick them up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
