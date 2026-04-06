# Lesson + student work → gap suggestions (prototype)

Small Python app: feed lesson context + student responses, get a JSON list of possible learning gaps with scaffold/extension bullets. Rules only—no model API.

See **MAINTAINERS.md** for where the logic lives if you're editing it.

## Setup

```bash
cd project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Tesseract: needed for image-like PDFs / scans. [Windows builds](https://github.com/UB-Mannheim/tesseract/wiki). Optionally set `TESSERACT_CMD` to the `.exe` path if it's not on PATH.

## Run (CLI)

From `project/`:

```bash
# Bundled text demo → output/sample_output.json
python src/main.py

# Three paths: teacher PDF, student materials PDF, student work PDF
python src/main.py teacher.pdf materials.pdf work.pdf -n 5 -o out.json

# Legacy: one context file + student file
python src/main.py data/lesson.txt data/student.txt
```

Flags: `-n` max rows (default 3), `-o` output path, `--assessment-blank` extra context PDF, `--flat` raw array only.

## Streamlit

```bash
streamlit run src/ui.py
```

Upload lesson files, student work, optional extras. UI asks the pipeline for **all** ranked gaps (no `-n`). CLI keeps `-n` for shorter files.

## Output

Default JSON:

```json
{
  "meta": {
    "standards_detected": ["6.NS.B.3", "M6.4.2"],
    "max_support_areas": 3,
    "support_areas_count": 3,
    "context_char_count": 0,
    "student_work_char_count": 0,
    "inputs": { }
  },
  "support_areas": [
    { "gap": "...", "type": ["conceptual"], "evidence": "...", "scaffold": [], "extension": [] }
  ]
}
```

Lesson PDFs often say "your friend"; output strings are normalized to **the student** in JSON (see `student_language.py`).

## Data in this repo

`data/*.txt` includes a paraphrased M6.4.2-style bundle for demos—not full partner PDFs. Use your own files for real runs.

## Caveats

Heuristics miss a lot; OCR is brittle; standards are regex-pulled from text. Fine for a prototype, not for high-stakes scoring.
# educational_system
