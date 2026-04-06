"""Heuristic gap detection on student text + optional lesson context."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GapFinding:
    summary: str
    evidence: str
    tags: list[str] = field(default_factory=list)


# regex bits for decimal / estimation / lesson cues (not an answer key)

_DECIMAL_OP_RE = re.compile(
    r"\d+\.\d+\s*[×x*]\s*\d+|\d+\s*[×x*]\s*\d+\.\d+|\d+\.\d+\s*[×x*]\s*\d+\.\d+",
    re.IGNORECASE,
)
_HAS_DECIMAL_IN_WORK = re.compile(r"\d+\.\d+")
_RAW_MULT_LINE = re.compile(
    r"\b(\d+)\s*[×x*]\s*(\d+)\s*=\s*(\d+)\b",
    re.IGNORECASE,
)
_ESTIMATE_HINTS = re.compile(
    r"\b(estimate|round|about|approximately|roughly|guess)\b",
    re.IGNORECASE,
)
_SHOW_WORK = re.compile(
    r"\b(no work|idk|don't know|just guessed|only wrote the answer)\b",
    re.IGNORECASE,
)
_FRACTION_MIXED = re.compile(r"\b\d+\s+\d+/\d+\b|\b\d+/\d+\s*[+\-×x*]\b")
_PLACE_VALUE_CONFUS = re.compile(
    r"\b(line up|lineup|decimal point.*line|move the decimal wrong)\b",
    re.IGNORECASE,
)
_MULT_VS_ADD = re.compile(
    r"line\s+up.*decimal|same\s+way\s+as.*add|like\s+adding|adding\s+decimals|before\s+multiply",
    re.IGNORECASE,
)
_LESSON_MULT_MISCONCEPTION = re.compile(
    r"bring\s+down|adding.*decimal|multiply.*decimal|confus.*standard\s+algorithm|misconception",
    re.IGNORECASE,
)
_DOT_OH_TWO_OH_OH_THREE = re.compile(
    r"0?\.2\b.*0?\.03\b|0?\.03\b.*0?\.2\b",
    re.IGNORECASE,
)


def _snippet(text: str, max_len: int = 120) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 3] + "..."


def _best_evidence_line(student_text: str) -> str:
    lines = [ln.strip() for ln in student_text.splitlines() if ln.strip()]
    if not lines:
        return _snippet(student_text)
    scored: list[tuple[int, str]] = []
    for ln in lines:
        score = 0
        if re.search(
            r"typed stand-in|^\s*Saga\s+|Page\s+\d+|Image Source|student pre-assessment\s*\(",
            ln,
            re.I,
        ):
            score -= 20
        if len(ln) > 160 and not re.search(r"=\s*\d|×|[x*]\s*\(", ln):
            score -= 5
        if re.search(r"\d", ln):
            score += 2
        if re.search(r"[×x*]|multiply|decimal|\.|=\s*\d", ln, re.I):
            score += 3
        if re.search(r"\b238\b|wrong|not sure|unsure|maybe\b", ln, re.I):
            score += 2
        scored.append((score, ln))
    scored.sort(key=lambda t: t[0], reverse=True)
    if scored[0][0] > 0:
        return _snippet(scored[0][1])
    return _snippet(lines[0])


def _student_attempted_estimate(st: str) -> bool:
    if re.search(r"didn'?t estimate|did not estimate|no estimate|forgot to estimate", st, re.I):
        return False
    return bool(_ESTIMATE_HINTS.search(st))


def identify_learning_gaps(student_text: str, lesson_text: str | None = None) -> list[GapFinding]:
    findings: list[GapFinding] = []
    st = student_text.strip()
    _bad_prefixes = (
        "[No OCR:",
        "[Could not decode",
        "[OCR unavailable:",
        "[No text extracted from PDF:",
        "[Image read/OCR failed:",
    )
    if not st or any(st.startswith(p) for p in _bad_prefixes):
        findings.append(
            GapFinding(
                summary="Insufficient readable student work for analysis",
                evidence=_snippet(st),
                tags=["representation"],
            )
        )
        return findings

    lower = st.lower()

    # Using full digit string from a reference fact but wrong decimal (M6.4.2 style tasks)
    if re.search(r"96.*437|437.*96|41952", st.replace(" ", ""), re.I):
        if re.search(r"419\.52|guess.*decimal|without\s+moving|wrong\s+place", lower):
            findings.append(
                GapFinding(
                    summary="Placing the decimal when the whole-number product is already known",
                    evidence=_best_evidence_line(st),
                    tags=["conceptual", "procedural"],
                )
            )

    # Decimal / multiplication reasoning
    if _DECIMAL_OP_RE.search(st) or (_HAS_DECIMAL_IN_WORK.search(st) and re.search(r"[×x*]", st)):
        if re.search(r"\b238\b|\bwrong place|not sure|unsure|maybe\b", lower):
            findings.append(
                GapFinding(
                    summary="Decimal placement / scaling after multiplication",
                    evidence=_best_evidence_line(st),
                    tags=["conceptual", "procedural"],
                )
            )
        elif not re.search(r"\b(tenths|hundredths|place value|decimal places?)\b", lower, re.I):
            findings.append(
                GapFinding(
                    summary="Procedure for decimal multiplication may lack place-value justification",
                    evidence=_best_evidence_line(st),
                    tags=["procedural", "conceptual"],
                )
            )

    # Estimation / reasoning
    lesson_wants_estimate = bool(lesson_text and _ESTIMATE_HINTS.search(lesson_text or ""))
    student_estimated = _student_attempted_estimate(st)
    if lesson_wants_estimate and not student_estimated:
        findings.append(
            GapFinding(
                summary="Missing estimation or reasonableness check",
                evidence=_best_evidence_line(st),
                tags=["metacognitive", "conceptual"],
            )
        )
    if ("didn't estimate" in lower or "did not estimate" in lower) and not any(
        f.summary.startswith("Missing estimation") for f in findings
    ):
        findings.append(
            GapFinding(
                summary="Acknowledged lack of estimation / reasoning step",
                evidence=_best_evidence_line(st),
                tags=["metacognitive"],
            )
        )

    # Procedural: whole-number multiplication visible but decimal problem stated
    if _HAS_DECIMAL_IN_WORK.search(st) and _RAW_MULT_LINE.search(st.replace("×", "x")):
        findings.append(
            GapFinding(
                summary="Possible gap connecting whole-number algorithm to decimal product",
                evidence=_best_evidence_line(st),
                tags=["procedural"],
            )
        )

    # Fractions
    if _FRACTION_MIXED.search(st) and re.search(r"\b(add|adding).*denominator\b", lower):
        findings.append(
            GapFinding(
                summary="Fraction operation may confuse numerator/denominator roles",
                evidence=_snippet(st),
                tags=["conceptual", "procedural"],
            )
        )

    # Metacognitive / work shown
    if _SHOW_WORK.search(st):
        findings.append(
            GapFinding(
                summary="Limited explicit reasoning or justification in work",
                evidence=_snippet(st),
                tags=["metacognitive", "representation"],
            )
        )

    if _PLACE_VALUE_CONFUS.search(st):
        findings.append(
            GapFinding(
                summary="Confusion aligning or interpreting place value / decimal notation",
                evidence=_snippet(st),
                tags=["representation", "conceptual"],
            )
        )

    # Treating decimal multiplication like addition (line up decimals first)
    if _MULT_VS_ADD.search(st):
        findings.append(
            GapFinding(
                summary="Applying decimal-addition alignment to multiplication (standard algorithm confusion)",
                evidence=_best_evidence_line(st),
                tags=["procedural", "representation", "conceptual"],
            )
        )

    # Classic magnitude error: 0.2 * 0.03 should be thousandths, not 0.6
    if _DOT_OH_TWO_OH_OH_THREE.search(st.replace(" ", "")):
        if re.search(r"=\s*0?\.6\b|=\s*6\b|=\s*0\.60\b", st) or re.search(
            r"\b2.*3.*=\s*6\b.*decimal", lower
        ):
            findings.append(
                GapFinding(
                    summary="Decimal product magnitude (tenths x hundredths -> thousandths)",
                    evidence=_best_evidence_line(st),
                    tags=["conceptual", "procedural"],
                )
            )

    lt = lesson_text or ""
    if _LESSON_MULT_MISCONCEPTION.search(lt) and re.search(r"bring\s+down|line\s+up.*decimal", lower):
        findings.append(
            GapFinding(
                summary="Work may reflect the \"bring down / line up\" multiplication misconception noted in the lesson plan",
                evidence=_best_evidence_line(st),
                tags=["procedural", "conceptual"],
            )
        )

    # Deduplicate by summary
    seen: set[str] = set()
    unique: list[GapFinding] = []
    for g in findings:
        if g.summary not in seen:
            seen.add(g.summary)
            unique.append(g)

    if not unique:
        unique.append(
            GapFinding(
                summary="No strong heuristic signals; review work manually or add richer response",
                evidence=_snippet(st),
                tags=["metacognitive"],
            )
        )

    return unique


def rank_support_areas(findings: list[GapFinding], max_n: int | None = 3) -> list[GapFinding]:
    def score(g: GapFinding) -> tuple[int, int]:
        tier = 0
        summary_l = g.summary.lower()
        for needle, wt in (
            ("decimal placement", 12),
            ("whole-number product", 12),
            ("magnitude", 11),
            ("addition alignment", 11),
            ("bring down", 10),
            ("whole-number algorithm", 9),
            ("estimation", 7),
            ("place value", 8),
            ("reasoning", 6),
        ):
            if needle in summary_l:
                tier += wt
        if "conceptual" in g.tags:
            tier += 2
        if "procedural" in g.tags:
            tier += 2
        return (tier, len(g.evidence))

    ingest_fail = [f for f in findings if "Insufficient readable" in f.summary]
    rest = [f for f in findings if "Insufficient readable" not in f.summary]
    ranked_rest = sorted(rest, key=score, reverse=True)
    merged = ingest_fail + ranked_rest
    if max_n is None:
        return merged
    return merged[: max(1, max_n)]
