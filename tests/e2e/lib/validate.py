"""Markdown / frontmatter assertions for md-crm e2e tests.

The validator reads a file produced by the skill, parses YAML frontmatter,
and checks it against a declarative spec from the transcript fixture.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

import yaml


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, m.group(2)


def match_value(actual: Any, spec: Any) -> bool:
    """Check whether `actual` satisfies the matcher `spec`.

    Matchers: bare string (case-insensitive substring), or dict with one of
    `equals`, `contains`, `regex`, `any_of`.
    """
    if spec is None:
        return actual is not None
    if isinstance(spec, str):
        return spec.lower() in str(actual).lower()
    if isinstance(spec, list):
        return any(match_value(actual, s) for s in spec)
    if isinstance(spec, dict):
        if "equals" in spec:
            return str(actual) == spec["equals"]
        if "contains" in spec:
            return spec["contains"].lower() in str(actual).lower()
        if "regex" in spec:
            return re.search(spec["regex"], str(actual)) is not None
        if "any_of" in spec:
            return any(match_value(actual, s) for s in spec["any_of"])
    return False


def _body_has(body: str, needle: str) -> bool:
    return needle.lower() in body.lower()


def validate_file(wiki_path: pathlib.Path, spec: dict, errors: list[str]) -> None:
    path = wiki_path / spec["path"]
    must_exist = spec.get("must_exist", True)
    if not path.exists():
        if must_exist:
            errors.append(f"{spec['path']}: expected to exist")
        return
    text = path.read_text()
    fm, body = parse_frontmatter(text)

    for key, matcher in (spec.get("frontmatter") or {}).items():
        if key not in fm:
            errors.append(f"{spec['path']}: frontmatter missing key {key!r}")
            continue
        if not match_value(fm[key], matcher):
            errors.append(
                f"{spec['path']}: frontmatter.{key}={fm[key]!r} "
                f"does not match {matcher!r}"
            )

    if "body_contains" in spec:
        needles = spec["body_contains"]
        if isinstance(needles, str):
            needles = [needles]
        for n in needles:
            if not _body_has(body, n):
                errors.append(f"{spec['path']}: body missing substring {n!r}")

    if "body_any_of" in spec:
        if not any(_body_has(body, n) for n in spec["body_any_of"]):
            errors.append(
                f"{spec['path']}: body missing any of {spec['body_any_of']!r}"
            )
