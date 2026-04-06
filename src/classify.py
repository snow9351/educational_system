"""Keyword rules → conceptual | procedural | representation | metacognitive."""

from __future__ import annotations

import re

VALID_TYPES = frozenset({"conceptual", "procedural", "representation", "metacognitive"})

_KEYWORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"place value|decimal|fraction|understand|meaning|scaling|magnitude", re.I), "conceptual"),
    (re.compile(r"algorithm|procedure|step|computation|multiply|divide|carry|line up", re.I), "procedural"),
    (re.compile(r"diagram|chart|notation|represent|record|show work|number line|model", re.I), "representation"),
    (re.compile(r"estimate|reason|check|reflect|justify|metacogn|strategy|monitor", re.I), "metacognitive"),
]


def classify_gap(gap_summary: str, suggested_tags: list[str] | None = None) -> list[str]:
    types: list[str] = []
    text = (gap_summary or "").strip()

    if suggested_tags:
        for t in suggested_tags:
            if t in VALID_TYPES and t not in types:
                types.append(t)

    for pattern, label in _KEYWORD_RULES:
        if pattern.search(text) and label not in types:
            types.append(label)

    if not types:
        types.append("conceptual")

    return types
