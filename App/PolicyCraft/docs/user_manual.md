# PolicyCraft – User Manual

## Table of Contents
1. Setup
2. Typical Workflow
3. Screen Elements Explained
4. Example Validation Report
5. Database & Algorithm Overview
6. Supported File Types
7. Interpretation Examples
8. FAQ

---

### 1. Setup
1. Clone repository, create virtual env.
2. `pip install -r requirements.txt`.
3. Start MongoDB (`brew services start mongodb-community`).
4. `python app.py` → visit `http://127.0.0.1:5000/`.

Demo baseline data (user_id = -1) already present.

---

### 2. Typical Workflow
| Step | Action | Result |
|------|--------|--------|
|1|Log in / register|Dashboard list|
|2|Upload Policy PDF/DOCX|Row appears, status → Ready|
|3|Open analysis|Radar, themes, classification|
|4|Generate Recommendations|Cards with priority/timeframe/sources|
|5|Validate Citations|Modal with pass/⚠️|
|6|Export CSV|File download|

---

### 3. Screen Elements Explained
* **Classification** pill: Restrictive (red), Moderate (amber), Permissive (green). Derived by Hybrid classifier (rule + LLM). Confidence bar shows probability.
* **Priority badge**: High (red ≥0.75), Medium (amber 0.4–0.74), Low (green).
* **Timeframe**: Immediate / Short / Long term.
* **Sources list**: academic references.
* **Validate Citations**: checks whitelist + publication age ≤7 yrs.

---

### 4. Example Validation Report
```
Citation Validation Report
✅ Establish Multi-Stakeholder… – pass
⚠️ Implement Graduated Oversight – UNLISTED: BERA (2018)
```
Interpretation: first rec OK; second rec cites reference missing from whitelist.

---

### 5. Database & Algorithm Overview
* **Recommendation retrieval order**: current user → baseline → any user → generate ad-hoc.
* **Classifier**: BERT probs adjusted by rule layer → label + confidence.
* **Theme extractor**: spaCy NER + TF-IDF weighting.
* **Validator**: normalises strings, checks whitelist & year.

---

### 6. Supported File Types
PDF, DOCX, TXT (English, ≤10 MB).

---

### 7. Interpretation Examples
* Dashboard Moderate @ 55 % → ambiguous wording, manual review advised.
* Avg themes per policy 9.5 → broad coverage.
* Validation ⚠️ UNLISTED → add reference to `docs/academic_references.md`.

---

### 8. FAQ
Q: Adjust 7-year threshold?  
A: Call `validate_recommendation_sources(recs, max_age=<yrs>)`.

Q: Where are files stored?  
A: Temporarily under `uploads/`, deleted after parse; text lives in Mongo.

Q: Add logo or colours?  
A: Edit `static/css/theme.css`, place SVGs in `static/img/brands/`.

Q: “No themes extracted”?  
A: Document too short; tweak `MIN_TOKEN_COUNT`.

Q: Undo delete?  
A: Use Mongo shell to restore or re-upload.

Q: External APIs?  
A: None at runtime; future semantic check may call Crossref.

Q: Multi-user?  
A: Yes; baseline user -1 is shared.

Q: Run tests?  
A: `pytest -q tests/`.

Q: Export validation?  
A: CLI `validate_sources.py --csv out.csv`.

Q: Change priority thresholds?  
A: Edit `PRIORITY_RULES` in `recommendation/engine.py`.

---

_Last updated_: 2025-07-16
