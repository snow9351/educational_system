"""Regex grab CCSS-looking codes + M6.4.2 style unit tags from blob text."""

from __future__ import annotations

import re

_CCSS_DOT = re.compile(r"\b\d\.[A-Z]{2,4}\.[A-Z]\.\d\b")
_CCSS_SHORT = re.compile(r"\b[1-8]\.NS\.B\.\d\b|\b[1-8]\.RP\.A\.\d\b")
_M_UNIT = re.compile(r"\bM\d+\.\d+\.\d+\b")


def extract_standards(text: str | None) -> list[str]:
    if not text:
        return []
    found: set[str] = set()
    for rx in (_CCSS_DOT, _CCSS_SHORT, _M_UNIT):
        for m in rx.finditer(text):
            found.add(m.group(0))
    return sorted(found)
