# React Review Screen (Unissant UC3)

**Author:** Huy Ngoc Minh Truong (@SuperHuyGaming)  
**Role:** Frontend, Data & Search (TNUX)  
**Task:** Evidence-First Legal Narrative Review Screen

---

## Overview

This screen renders the output of the GenAI Gap Analysis engine (`pipeline/report.py` / `backend/sample_report.json`). It enables an officer or reviewing supervisor to audit an investigative narrative in seconds.

### Key Capabilities & Guardrails
1. **Per-Charge Status Cards:** Color-coded status badges for each cited charge:
   - `complete` (green): All statutory elements documented.
   - `gaps` (amber): Missing statutory elements clearly flagged.
   - `human_review` (purple): Triggers human review with specific statutory reason.
2. **Missing Facts List:** Explicitly lists every missing fact required by USCIS Policy Manual / INA statute.
3. **Evidence-First Grounded Quotes:** Shows the exact quoted phrase extracted from the narrative alongside its model confidence badge.
4. **Interactive Sentence Highlighting:**
   - Hovering or clicking on any found fact highlights the corresponding sentence(s) in the narrative pane and marks the grounded quote text.
   - Clicking on a sentence in the narrative reveals all statutory claims grounded in that sentence.
5. **Mandatory Disclaimer:** Displays the required disclaimer on every result:
   > *"Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result."*
6. **Strict Prohibition on Suggested Charges:** In compliance with Unissant project constraints and legal safety guardrails, this screen **never suggests or recommends alternative charges**.
7. **Preset Demos & Live API Support:**
   - Includes preset test cases: Unissant Sample Case, Fully Complete Case, Contradiction Case (Routes to Human Review), and Uncovered Statute Case.
   - Supports live testing against Ethan's `POST /review` FastAPI endpoint (`http://localhost:8000/review`).

---

## How to Run

### Method 1: Standard Vite Development Server
```bash
cd ui
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Method 2: Instant Standalone Preview (Zero-Install)
You can directly open `ui/standalone.html` in any web browser without needing `npm install`.

---

## Data Contract
Follows the contract defined in `pipeline/schemas.py`:
- `disclaimer` (string)
- `sentences` (map of sentence ID -> sentence text)
- `charges` (array of charge evaluation objects with `citation`, `name`, `source`, `status`, `reason`, `facts`, `missing`, `conflicts`, `disagreed`)
