"""Pick scaffold/extension lines from gap types + a few phrase triggers."""

from __future__ import annotations

import re

VALID_ORDER = ["conceptual", "procedural", "representation", "metacognitive"]

_SCAFFOLD_BANK: dict[str, list[str]] = {
    "conceptual": [
        "Use a concrete or visual model (e.g. base-ten blocks, area model) before the symbolic step.",
        "Have the student restate the problem in their own words and identify what each number represents.",
        "Connect the operation to a simpler known case, then build back up.",
    ],
    "procedural": [
        "Co-construct a short checklist of steps and have the student narrate each step aloud.",
        "Work one fully worked example side-by-side, then a parallel problem with prompts only.",
        'Use an error-analysis prompt: "Where might the steps differ for decimals versus whole numbers?"',
    ],
    "representation": [
        "Offer a template (table, place-value chart, or annotated vertical form) and fill the first row together.",
        "Ask the student to label units (tenths, ones, etc.) next to digits before operating.",
        "Use color or brackets to separate partial products or remainder parts.",
    ],
    "metacognitive": [
        "Before calculating, ask for a rough estimate and a sentence on why it is reasonable.",
        'After solving, prompt: "How would you spot a mistake without re-doing everything?"',
        "Have the student rate confidence and cite one specific step they would double-check.",
    ],
}

_EXTENSION_BANK: dict[str, list[str]] = {
    "conceptual": [
        "Pose a compare problem: same structure but different magnitude; ask what changes conceptually.",
        "Introduce a mild counterexample and ask the student to explain why a naive rule would fail.",
    ],
    "procedural": [
        "Increase digits or steps (e.g. two decimal factors) while keeping the same strategy.",
        'Mix in one "missing information" item so they must choose an operation.',
    ],
    "representation": [
        "Ask for two different representations of the same solution and to explain the link.",
        "Translate a word problem into a diagram and back into symbols.",
    ],
    "metacognitive": [
        "Use a three-column reflection: plan -> execute -> verify with estimation bounds.",
        'Challenge with a "which answer is impossible?" multiple-reasoning item.',
    ],
}


def _pick_strategies(text: str, bank: dict[str, list[str]], types: list[str], count: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    if re.search(r"decimal|tenth|hundredth", text, re.I):
        hint = (
            "Use a place-value chart: multiply as whole numbers, then justify decimal position from total decimal places."
        )
        if hint not in seen:
            seen.add(hint)
            out.append(hint)
    if re.search(r"fraction|denominator|numerator", text, re.I):
        hint = "Use fraction strips or a double number line to compare sizes before operating."
        if hint not in seen:
            seen.add(hint)
            out.append(hint)
    if re.search(r"estimate|reasonableness", text, re.I):
        hint = (
            "Round to nearby whole numbers or simple benchmarks first; "
            "state upper and lower bounds for the answer."
        )
        if hint not in seen:
            seen.add(hint)
            out.append(hint)

    for t in types:
        for item in bank.get(t, []):
            if item not in seen and len(out) < count:
                seen.add(item)
                out.append(item)
    for t in VALID_ORDER:
        for item in bank.get(t, []):
            if item not in seen and len(out) < count:
                seen.add(item)
                out.append(item)
    return out[:count]


def generate_scaffolds(gap_summary: str, types: list[str]) -> list[str]:
    return _pick_strategies(gap_summary, _SCAFFOLD_BANK, types, count=4)


def generate_extensions(gap_summary: str, types: list[str]) -> list[str]:
    return _pick_strategies(gap_summary, _EXTENSION_BANK, types, count=3)
