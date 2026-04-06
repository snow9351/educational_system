"""CLI + shared `run_pipeline*` entrypoints. JSON out is built here."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as `python src/main.py` from project root (or any cwd)
_SRC_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SRC_DIR.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from analyze import identify_learning_gaps, rank_support_areas  # noqa: E402
from classify import classify_gap  # noqa: E402
from ingest import load_input  # noqa: E402
from scaffold import generate_extensions, generate_scaffolds  # noqa: E402
from standards import extract_standards  # noqa: E402
from student_language import curriculum_friend_to_student  # noqa: E402


def run_pipeline_from_extracted(
    *,
    context_teacher_text: str,
    context_materials_text: str,
    context_assessment_text: str,
    student_work_text: str,
    meta_inputs: dict[str, Any] | None = None,
    max_support_areas: int | None = None,
    wrap_meta: bool = True,
) -> dict[str, Any] | list[dict[str, Any]]:
    merged_context = "\n\n--- context segment ---\n\n".join(
        t for t in (context_teacher_text, context_materials_text, context_assessment_text) if t
    ).strip()
    context_for_standards = "\n".join(
        x for x in (context_teacher_text, context_materials_text, merged_context) if x
    )

    findings = identify_learning_gaps(student_work_text, lesson_text=merged_context)
    findings = rank_support_areas(findings, max_n=max_support_areas)

    rows: list[dict[str, Any]] = []
    for finding in findings:
        types = classify_gap(finding.summary, finding.tags)
        scaff = generate_scaffolds(finding.summary, types)
        exts = generate_extensions(finding.summary, types)
        rows.append(
            {
                "gap": curriculum_friend_to_student(finding.summary),
                "type": types,
                "evidence": curriculum_friend_to_student(finding.evidence),
                "scaffold": [curriculum_friend_to_student(x) for x in scaff],
                "extension": [curriculum_friend_to_student(x) for x in exts],
            }
        )

    if not wrap_meta:
        return rows

    standards = extract_standards(context_for_standards)
    meta: dict[str, Any] = {
        "standards_detected": standards,
        "max_support_areas": max_support_areas,
        "support_areas_count": len(rows),
        "context_char_count": len(merged_context),
        "student_work_char_count": len(student_work_text),
    }
    if meta_inputs is not None:
        meta["inputs"] = meta_inputs

    return {"meta": meta, "support_areas": rows}


def run_pipeline(
    lesson_path: str | Path,
    student_path: str | Path,
    *,
    student_materials_path: str | Path | None = None,
    assessment_blank_path: str | Path | None = None,
    max_support_areas: int = 3,
    wrap_meta: bool = True,
) -> dict[str, Any] | list[dict[str, Any]]:
    teacher_p = Path(lesson_path)
    work_p = Path(student_path)
    materials_p = Path(student_materials_path) if student_materials_path else None
    blank_p = Path(assessment_blank_path) if assessment_blank_path else None

    ct = load_input(teacher_p) if teacher_p.is_file() else ""
    mt = load_input(materials_p) if materials_p and materials_p.is_file() else ""
    bt = load_input(blank_p) if blank_p and blank_p.is_file() else ""
    stu = load_input(work_p)

    meta_inputs = {
        "teacher_or_context": str(teacher_p.resolve()) if teacher_p.is_file() else str(teacher_p),
        "student_materials": str(materials_p.resolve()) if materials_p and materials_p.is_file() else None,
        "assessment_blank": str(blank_p.resolve()) if blank_p and blank_p.is_file() else None,
        "student_work": str(work_p.resolve()) if work_p.is_file() else str(work_p),
    }
    return run_pipeline_from_extracted(
        context_teacher_text=ct,
        context_materials_text=mt,
        context_assessment_text=bt,
        student_work_text=stu,
        meta_inputs=meta_inputs,
        max_support_areas=max_support_areas,
        wrap_meta=wrap_meta,
    )


def default_paths_genius_blend() -> tuple[Path, Path, Path]:
    root = _PROJECT_ROOT
    return (
        root / "data" / "lesson_context_genius_blend.txt",
        root / "data" / "student_materials_genius_blend.txt",
        root / "data" / "saga_student_work_sample.txt",
    )


def default_paths_legacy() -> tuple[Path, Path]:
    root = _PROJECT_ROOT
    return root / "data" / "lesson.txt", root / "data" / "student.txt"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lesson + student files → JSON. 0 args = bundled demo; 3 = teacher, materials, work; 2 = context, work."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="0 args demo; 2 args: context work; 3 args: teacher materials work",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output JSON path (default: project/output/sample_output.json)",
    )
    parser.add_argument(
        "-n",
        "--max-support-areas",
        type=int,
        default=3,
        metavar="N",
        help="Limit how many support rows after ranking (default 3)",
    )
    parser.add_argument(
        "--assessment-blank",
        type=str,
        default=None,
        help="Optional blank assessment PDF for additional context (standards bank, item stems).",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Emit a bare JSON array (legacy) instead of {meta, support_areas}.",
    )
    args = parser.parse_args()

    n = max(1, min(10, args.max_support_areas))
    blank = Path(args.assessment_blank) if args.assessment_blank else None

    pos = args.paths
    if len(pos) == 0:
        t, m, w = default_paths_genius_blend()
        payload = run_pipeline(
            t,
            w,
            student_materials_path=m,
            assessment_blank_path=blank,
            max_support_areas=n,
            wrap_meta=not args.flat,
        )
    elif len(pos) == 2:
        payload = run_pipeline(
            pos[0],
            pos[1],
            assessment_blank_path=blank,
            max_support_areas=n,
            wrap_meta=not args.flat,
        )
    elif len(pos) == 3:
        payload = run_pipeline(
            pos[0],
            pos[2],
            student_materials_path=pos[1],
            assessment_blank_path=blank,
            max_support_areas=n,
            wrap_meta=not args.flat,
        )
    else:
        parser.error("Provide 0, 2, or 3 file paths (see --help).")

    out_path = Path(args.output) if args.output else _PROJECT_ROOT / "output" / "sample_output.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    out_path.write_text(text, encoding="utf-8")

    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
