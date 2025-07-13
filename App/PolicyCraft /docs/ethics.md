# PolicyCraft Ethics Considerations

PolicyCraft analyses university policies on generative AI. Below is a summary of the project’s key ethical considerations.

## 1. Avoiding Bias
* The hybrid model uses simple keywords alongside a trained LR classifier on a small corpus.
* Risk: over-representation of terminology from English-speaking institutions.
* Mitigation: tests across diverse institution types (USA, UK, PL, JP) and a **fairness** metric in `evaluate_models.py`.

## 2. Privacy and Data Protection
* The system does not collect personal data of students or staff.
* Analysed policy documents are publicly available.
* User credentials are stored locally in SQLite; passwords are hashed with Bcrypt.

## 3. Model Security
* No external APIs – all inference runs locally.
* Models and rules are transparent (interpretability via the `/api/explain/<id>` endpoint).

## 4. Transparency
* Open-source code (MIT).  
* Architecture diagram in `docs/architecture.md`.

## 5. Responsible Use
The system does not replace expert judgement; results should be interpreted within the institution’s policy and cultural context.

---
_Date: 2025-07-11, Author: Jacek Robert Kszczot_
