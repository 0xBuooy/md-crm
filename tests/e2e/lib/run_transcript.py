#!/usr/bin/env python3
"""Drive a transcript of prompts against an agent CLI and assert invariants.

Usage:
    run_transcript.py \
        --transcript fixtures/transcript.yaml \
        --agent-cmd "hermes chat --skill md-crm --non-interactive" \
        --wiki-path /tmp/wiki \
        --raw-path /tmp/raw

The `agent-cmd` is a shell command that reads ONE prompt from stdin per
invocation and prints the agent's final response to stdout. Each transcript
step spawns a fresh process so the agent has no implicit memory between
steps (it must read/write files through the skill).
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate import validate_file  # noqa: E402


def snapshot(root: pathlib.Path) -> dict[str, float]:
    """Return {relative_path: mtime} for every regular file under `root`."""
    out: dict[str, float] = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root))] = p.stat().st_mtime
    return out


def diff_snapshots(before: dict, after: dict) -> tuple[list[str], list[str]]:
    new = sorted(set(after) - set(before))
    modified = sorted(p for p in set(before) & set(after) if after[p] != before[p])
    return new, modified


def check_response(response: str, expect: dict, errors: list[str]) -> None:
    if "response_contains" in expect:
        need = expect["response_contains"]
        if isinstance(need, str):
            need = [need]
        for s in need:
            if s.lower() not in response.lower():
                errors.append(f"response missing substring {s!r}")
    if "response_any_of" in expect:
        if not any(s.lower() in response.lower() for s in expect["response_any_of"]):
            errors.append(f"response missing any of {expect['response_any_of']!r}")
    if "response_regex" in expect:
        import re
        if not re.search(expect["response_regex"], response):
            errors.append(f"response does not match regex {expect['response_regex']!r}")


def check_filesystem(
    wiki: pathlib.Path,
    expect: dict,
    before: dict,
    after: dict,
    errors: list[str],
) -> None:
    for fs in expect.get("files") or []:
        validate_file(wiki, fs, errors)

    new, modified = diff_snapshots(before, after)

    if expect.get("no_new_files") and new:
        errors.append(f"expected no new files, got {new}")
    if expect.get("no_modified_files") and modified:
        errors.append(f"expected no modified files, got {modified}")
    if expect.get("no_new_people"):
        offenders = [p for p in new if p.startswith("people/")]
        if offenders:
            errors.append(f"expected no new people pages, got {offenders}")
    if expect.get("no_new_companies"):
        offenders = [p for p in new if p.startswith("companies/")]
        if offenders:
            errors.append(f"expected no new company pages, got {offenders}")


def run_step(
    step: dict,
    agent_cmd: str,
    wiki: pathlib.Path,
    before: dict,
    timeout: int,
) -> tuple[list[str], dict]:
    print(f"\n=== step: {step['id']} ===")
    print(f"> {step['input'].strip()}")
    proc = subprocess.run(
        agent_cmd,
        shell=True,
        input=step["input"],
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    response = proc.stdout + proc.stderr
    if proc.returncode != 0:
        print(f"[agent exited {proc.returncode}]")
    print(response)

    errors: list[str] = []
    expect = step.get("expect") or {}
    check_response(response, expect, errors)

    after = snapshot(wiki)
    check_filesystem(wiki, expect, before, after, errors)

    if errors:
        print(f"FAIL ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("OK")
    return errors, after


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True, type=pathlib.Path)
    ap.add_argument("--agent-cmd", required=True)
    ap.add_argument("--wiki-path", required=True, type=pathlib.Path)
    ap.add_argument("--raw-path", required=True, type=pathlib.Path)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    transcript = yaml.safe_load(args.transcript.read_text())
    wiki = args.wiki_path.resolve()
    wiki.mkdir(parents=True, exist_ok=True)
    args.raw_path.mkdir(parents=True, exist_ok=True)

    snap = snapshot(wiki)
    total_errors: list[str] = []

    for step in transcript["steps"]:
        step_errors, snap = run_step(step, args.agent_cmd, wiki, snap, args.timeout)
        total_errors.extend(step_errors)

    print()
    if total_errors:
        print(f"FAILED: {len(total_errors)} assertion(s)")
        return 1
    print(f"PASSED: {len(transcript['steps'])} step(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
