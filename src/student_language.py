"""Sagas and PARCC-style items say 'your friend' a lot; swap to 'the student' in exports only."""

from __future__ import annotations

import re
import unicodedata


def curriculum_friend_to_student(text: str | None) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(
        r"\byour\s+friend['\u2019]s\b",
        "the student's",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\byour\s+friends['\u2019]\b",
        "the students'",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\byour\s+friend\b", "the student", t, flags=re.IGNORECASE)
    return t
