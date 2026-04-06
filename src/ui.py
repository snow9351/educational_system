"""Streamlit: uploads left, analysis right. From project/: streamlit run src/ui.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
_ROOT = _SRC.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402
from ingest import load_input_bytes, merge_loaded_segments  # noqa: E402
from main import run_pipeline_from_extracted  # noqa: E402

_UPLOADER_TYPES = ["pdf", "png", "jpg", "jpeg", "txt"]
# None = return every detected problem point (ranked). CLI still defaults to -n 3.
_ALL_DETECTED_SUPPORT_AREAS: int | None = None


def _text_from_uploads(uploads: list | None) -> tuple[str, list[str]]:
    if not uploads:
        return "", []
    labeled = [(f.name, load_input_bytes(f.name, f.getvalue())) for f in uploads]
    names = [f.name for f in uploads]
    return merge_loaded_segments(labeled), names


def _plain_language_types(s: str) -> str:
    mapping = {
        "conceptual": "big idea",
        "procedural": "steps / procedure",
        "representation": "how work is shown",
        "metacognitive": "thinking about thinking",
    }
    parts = [x.strip() for x in s.replace("[", "").replace("]", "").split(",") if x.strip()]
    return ", ".join(mapping.get(p.lower(), p) for p in parts) if parts else s


def _render_results(payload: object, *, embedded: bool) -> None:
    if not embedded:
        st.divider()
        st.header("Review summary")
    else:
        st.markdown("##### Review summary")

    if not isinstance(payload, dict) or "support_areas" not in payload:
        st.json(payload)
        return

    areas = payload["support_areas"]

    if not areas:
        st.warning(
            "We could not read enough from the student's file. "
            "Try a PDF with selectable text, or install Tesseract for scanned pages."
        )
        return

    st.subheader("1. Problem points")
    for i, row in enumerate(areas, start=1):
        st.markdown(f"{i}. **{row.get('gap', '')}**")

    st.divider()
    st.subheader("2. Educational ways and extensions")
    for i, row in enumerate(areas, start=1):
        gap = row.get("gap", "")
        st.markdown(f"#### Problem point {i}: {gap}")
        types_raw = row.get("type", [])
        if types_raw:
            st.caption("Type of need: " + _plain_language_types(", ".join(str(t) for t in types_raw)))
        ev = row.get("evidence") or ""
        if ev:
            st.markdown("**Evidence from the student's work**")
            snippet = ev[:1500] + ("..." if len(ev) > 1500 else "")
            st.text(snippet)
        sc = row.get("scaffold") or []
        if sc:
            st.markdown("**Educational ways** (teaching moves and supports)")
            for item in sc[:4]:
                st.markdown(f"- {item}")
        ex = row.get("extension") or []
        if ex:
            st.markdown("**Extension** (for students who are ready to go deeper)")
            for item in ex[:3]:
                st.markdown(f"- {item}")
        st.markdown("")

    raw = json.dumps(payload, indent=2, ensure_ascii=False)
    st.download_button(
        label="Download report (for sharing or your records)",
        data=raw.encode("utf-8"),
        file_name="student_support_suggestions.json",
        mime="application/json",
        use_container_width=True,
    )
    if st.button("Start over with new files", use_container_width=True, key="btn_start_over"):
        st.session_state.last_payload = None
        st.session_state.last_error = None
        st.rerun()
    with st.expander("Technical details (JSON)"):
        st.code(raw, language="json")


st.set_page_config(page_title="Student support suggestions", layout="wide", initial_sidebar_state="collapsed")

if "last_payload" not in st.session_state:
    st.session_state.last_payload = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

st.title("Student support suggestions")
st.markdown(
    "Use the **Upload** panel to add files, then **Run analysis** on the right to see "
    "**problem points**, **educational ways**, and **extensions**."
)

col_upload, col_analyze = st.columns([1, 1.15], gap="large")
error_msg: str | None = None

with col_upload:
    with st.container(border=True):
        st.subheader("Upload panel")
        st.caption("Add your lesson packet and the student's work here.")
        st.markdown("**1. Lesson materials**")
        st.caption("Teacher guide, handouts, slide exports. Several files allowed.")
        up_lesson = st.file_uploader(
            "Lesson files",
            type=_UPLOADER_TYPES,
            accept_multiple_files=True,
            key="up_lesson",
            label_visibility="collapsed",
        )
        st.caption("Selected: " + ("nothing yet" if not up_lesson else f"{len(up_lesson)} file(s)"))
        st.markdown("**2. Student's work**")
        st.caption("Quiz, homework, or photos of written work. At least one file.")
        up_student = st.file_uploader(
            "Student work files",
            type=_UPLOADER_TYPES,
            accept_multiple_files=True,
            key="up_student",
            label_visibility="collapsed",
        )
        st.caption("Selected: " + ("nothing yet" if not up_student else f"{len(up_student)} file(s)"))
        st.markdown("**3. Optional extras**")
        st.caption("Tests or rubrics. Skip if you do not need them.")
        up_extra = st.file_uploader(
            "Optional PDFs",
            type=_UPLOADER_TYPES,
            accept_multiple_files=True,
            key="up_extra",
            label_visibility="collapsed",
        )
        go = st.button("Run analysis", type="primary", use_container_width=True, key="btn_run")

if go:
    lesson_text, lesson_names = _text_from_uploads(up_lesson)
    extra_text, extra_names = _text_from_uploads(up_extra)
    stu, stu_names = _text_from_uploads(up_student)
    if not lesson_text.strip():
        error_msg = "Please upload at least one lesson file (step 1)."
    elif not stu.strip():
        error_msg = "Please upload at least one student work file (step 2)."
    else:
        with st.spinner("Reading files and preparing suggestions..."):
            try:
                st.session_state.last_payload = run_pipeline_from_extracted(
                    context_teacher_text=lesson_text,
                    context_materials_text="",
                    context_assessment_text=extra_text,
                    student_work_text=stu,
                    meta_inputs={
                        "lesson_sources": lesson_names or None,
                        "optional_extra_sources": extra_names or None,
                        "student_work_sources": stu_names or None,
                    },
                    max_support_areas=_ALL_DETECTED_SUPPORT_AREAS,
                    wrap_meta=True,
                )
                st.session_state.last_error = None
            except Exception as e:
                st.session_state.last_error = str(e)
                st.session_state.last_payload = None
        out = _ROOT / "output" / "sample_output.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if st.session_state.last_payload is not None:
            out.write_text(
                json.dumps(st.session_state.last_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

with col_analyze:
    with st.container(border=True):
        if error_msg:
            st.error(error_msg)
        if st.session_state.last_error:
            st.error("Something went wrong: " + st.session_state.last_error)
        if st.session_state.last_payload is not None:
            _render_results(st.session_state.last_payload, embedded=True)
        elif not error_msg and not st.session_state.last_error:
            st.info("Upload files on the left, then click **Run analysis**.")

st.divider()
st.caption(
    "Scanned PDFs may need **Tesseract** for OCR. "
    "For file paths without upload, use: python src/main.py (see README)."
)
