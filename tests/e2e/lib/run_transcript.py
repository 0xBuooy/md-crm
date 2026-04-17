#!/usr/bin/env python3
"""Drive one or many md-crm transcripts against an agent CLI.

Usage (single transcript):
    run_transcript.py \
        --transcript fixtures/01-basic-coffee-chat.yaml \
        --agent-cmd "hermes chat --skill md-crm --non-interactive" \
        --wiki-path /tmp/wiki \
        --raw-path /tmp/raw

Usage (whole fixture dir):
    run_transcript.py \
        --transcripts-dir fixtures \
        --agent-cmd "..." \
        --wiki-path /tmp/wiki \
        --raw-path /tmp/raw \
        [--filter 09-company-change]

The runner wipes `wiki_path` and `raw_path` between transcripts so each
scenario starts from a clean slate. The agent is re-spawned per step so it
has no implicit chat memory — state lives on disk.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate import validate_file  # noqa: E402


def snapshot(root: pathlib.Path) -> dict[str, float]:
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
    if "response_not_contains" in expect:
        deny = expect["response_not_contains"]
        if isinstance(deny, str):
            deny = [deny]
        for s in deny:
            if s.lower() in response.lower():
                errors.append(f"response unexpectedly contains {s!r}")
    if "response_regex" in expect:
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
    if "files_absent" in expect:
        missing = expect["files_absent"]
        if isinstance(missing, str):
            missing = [missing]
        for rel in missing:
            if (wiki / rel).exists():
                errors.append(f"{rel}: expected to be absent")


def run_step(
    step: dict,
    agent_cmd: str,
    wiki: pathlib.Path,
    before: dict,
    timeout: int,
) -> tuple[list[str], dict]:
    step_id = step.get("id", "step")
    print(f"\n  --- step: {step_id} ---")
    print(f"  > {step['input'].strip().splitlines()[0][:120]}")
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
        print(f"  [agent exited {proc.returncode}]")

    errors: list[str] = []
    expect = step.get("expect") or {}
    check_response(response, expect, errors)

    after = snapshot(wiki)
    check_filesystem(wiki, expect, before, after, errors)

    if errors:
        print(f"  FAIL ({len(errors)}):")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  OK")
    return errors, after


def wipe(path: pathlib.Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_transcript(
    transcript_path: pathlib.Path,
    agent_cmd: str,
    wiki: pathlib.Path,
    raw: pathlib.Path,
    timeout: int,
) -> tuple[int, int]:
    """Return (errors, steps_run)."""
    doc = yaml.safe_load(transcript_path.read_text())
    name = doc.get("name", transcript_path.stem)
    print(f"\n=== transcript: {name} ({transcript_path.name}) ===")
    if desc := doc.get("description"):
        print(f"    {desc}")

    wipe(wiki)
    wipe(raw)

    snap = snapshot(wiki)
    errors = 0
    steps = doc.get("steps") or []
    for step in steps:
        step_errs, snap = run_step(step, agent_cmd, wiki, snap, timeout)
        errors += len(step_errs)
    return errors, len(steps)


def iter_transcripts(
    dir_path: pathlib.Path, filter_expr: str | None
) -> list[pathlib.Path]:
    files = sorted(dir_path.glob("*.yaml"))
    if filter_expr:
        files = [f for f in files if filter_expr in f.name]
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--transcript", type=pathlib.Path)
    src.add_argument("--transcripts-dir", type=pathlib.Path)
    ap.add_argument("--filter", help="Substring filter applied in dir mode")
    ap.add_argument("--agent-cmd", required=True)
    ap.add_argument("--wiki-path", required=True, type=pathlib.Path)
    ap.add_argument("--raw-path", required=True, type=pathlib.Path)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    wiki = args.wiki_path.resolve()
    raw = args.raw_path.resolve()

    if args.transcript:
        transcripts = [args.transcript]
    else:
        transcripts = iter_transcripts(args.transcripts_dir, args.filter)
        if not transcripts:
            print(f"no transcripts matched under {args.transcripts_dir}")
            return 2

    results: list[tuple[str, int, int]] = []
    for t in transcripts:
        try:
            errs, steps = run_transcript(t, args.agent_cmd, wiki, raw, args.timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR running {t.name}: {exc}")
            errs, steps = 1, 0
        results.append((t.name, errs, steps))

    print("\n==== summary ====")
    failed = 0
    for name, errs, steps in results:
        status = "PASS" if errs == 0 else f"FAIL ({errs})"
        print(f"  {status:<10} {name}  ({steps} step{'s' if steps != 1 else ''})")
        if errs:
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} transcripts passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
