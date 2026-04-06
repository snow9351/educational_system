# Maintainer notes

For whoever picks this up—it's a straight script pipeline, no framework beyond Streamlit for the UI.

## Flow

1. `ingest.load_input` / `load_input_bytes` — text from disk or uploads (PDF via PyMuPDF; low-text pages go through Tesseract if installed).
2. `main.run_pipeline_from_extracted` merges teacher + materials + optional assessment text, then calls `analyze.identify_learning_gaps(student, lesson_text=merged)`.
3. `analyze.rank_support_areas` sorts and optionally slices (CLI passes `-n`, the UI passes no cap so everything shows).
4. `classify.classify_gap` and `scaffold.generate_*` fill the JSON rows.
5. `student_language.curriculum_friend_to_student` does a find/replace so copy-pasted PDF lines like "your friend" read as "the student" in output only.

## Files to touch for behavior changes

| Goal | File |
|------|------|
| New gap rules / patterns | `src/analyze.py` |
| Type buckets | `src/classify.py` |
| Scaffold / extension strings | `src/scaffold.py` |
| Standards regex | `src/standards.py` |
| PDF/OCR / uploads | `src/ingest.py` |
| JSON shape / CLI | `src/main.py` |
| Browser UI only | `src/ui.py` |

## Checks

No automated tests. From repo root:

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

You should get `output/sample_output.json`. Scanned PDFs without Tesseract will show `[OCR unavailable: ...]` in text and a thin ingest result.
