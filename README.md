# Lesson + Student Work → Learning Gap Analysis (Prototype)

This project is a **small working prototype** of an AI-assisted instructional support system.

It demonstrates how lesson materials and student work can be processed to:

* Identify **learning gaps**
* Classify gap types (conceptual, procedural, etc.)
* Generate **instructional scaffolds and extensions**

The goal is to simulate a **core “data-to-instruction” pipeline** for an edtech platform.

---

## 🧠 What this prototype shows

This prototype focuses on the **core intelligence layer**:

INPUT (lesson + student work)
→ ANALYSIS (learning gap detection)
→ CLASSIFICATION (gap types)
→ OUTPUT (scaffolds + extensions)

It is intentionally lightweight and uses **rule-based heuristics** instead of LLM APIs.

---

## 📁 Project Structure

```
project/
│
├── README.md
├── requirements.txt
│
├── data/                # Sample inputs
├── src/
│   ├── ingest.py        # Input loading (text + basic PDF)
│   ├── analyze.py       # Learning gap detection
│   ├── classify.py      # Gap classification
│   ├── scaffold.py      # Instructional suggestions
│   ├── main.py          # Pipeline runner
│   ├── ui.py            # Optional Streamlit UI
│
├── output/
│   └── sample_output.json
```

---

## ⚙️ Setup

```bash
cd project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Optional: OCR support

This prototype includes optional OCR support for scanned PDFs using Tesseract.

Install from:
https://github.com/UB-Mannheim/tesseract/wiki

If needed, set:

```
TESSERACT_CMD=<path-to-tesseract.exe>
```

---

## ▶️ Run (CLI)

```bash
# Default demo
python src/main.py

# With PDF inputs
python src/main.py teacher.pdf materials.pdf work.pdf -n 5 -o out.json

# With text inputs
python src/main.py data/lesson.txt data/student.txt
```

Flags:

* `-n`: max number of support areas (default: 3)
* `-o`: output file path
* `--assessment-blank`: optional additional context
* `--flat`: return raw array only

---

## 🖥️ Run (UI)

```bash
streamlit run src/ui.py
```

Upload lesson materials and student work to see generated support areas.

---

## 📤 Output Format

```json
{
  "support_areas": [
    {
      "gap": "Decimal placement misunderstanding",
      "type": ["conceptual", "procedural"],
      "evidence": "Incorrect decimal placement in multiplication",
      "scaffold": [
        "Use place value chart",
        "Multiply as whole numbers, then adjust decimal"
      ],
      "extension": [
        "Provide multi-step decimal challenges"
      ]
    }
  ]
}
```

---

## 🧩 Assumptions

* Inputs are primarily **clean text or machine-readable PDFs**
* Student work is available as typed responses (not handwritten)
* Heuristic rules approximate instructional reasoning

---

## ⚠️ Limitations

* PDF parsing is basic (PyPDF2 + optional OCR)
* No reliable handling of complex layouts (tables, diagrams)
* OCR is brittle and may introduce noise
* Gap detection is rule-based (not model-driven)
* Standards detection uses simple regex extraction

---

## 🚀 Future Improvements

This prototype is designed to evolve toward a production system:

* Robust document ingestion (PDF, images, OCR, layout parsing)
* LLM-based reasoning and scaffold generation
* Privacy-first data handling (anonymization, secure processing)
* Standards-aligned strategy library
* Feedback loops and continuous improvement

---

## 🎯 Why this matters

This project demonstrates how raw instructional materials can be transformed into **actionable teaching strategies**.

It reflects a core idea:

> Translating student performance + context → meaningful instructional support

---

## 🧪 Notes

* Sample data in `/data` is simplified and paraphrased
* Designed for demonstration purposes only
* Not suitable for high-stakes assessment

---

## 📌 Maintainers

See `MAINTAINERS.md` for details on where logic is implemented.
