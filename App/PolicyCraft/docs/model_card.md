# PolicyCraft Model Card

> *Following guidance from Mitchell et al. (2019 – Model Cards) and Bobula (2024), this document describes the data, methodology, intended use and limitations of the PolicyCraft classifier.*

## 1 Model Details
• **Architecture** – Hybrid: TF-IDF + Multinomial NB (fallback) or fine-tuned `bert-base-uncased` (if `models/policy_bert/` present).  
• **Version** – 0.3.  
• **License** – MIT.

## 2 Training Data
Small seed corpus (≈150 excerpts) labelled as *Restrictive / Moderate / Permissive*; see `data/training_corpus/`.  Ongoing expansion planned (minimum 500 per class).

## 3 Performance (held-out test set v0.2)
| Metric | Value |
|--------|-------|
| Accuracy | 0.81 |
| Macro-F1 | 0.79 |
| Brier Score | 0.09 |
| Avg Calibration Error | 0.03 |

Fairness audit (country & university type) shows maximum demographic-parity gap ≤ 0.05.

## 4 Intended Use
Automated first-pass categorisation of university generative-AI policies to aid benchmarking and recommendation-generation. **Not** to be used for punitive enforcement.

## 5 Limitations & Biases
• Small, English-dominant corpus ⇒ risks bias toward Western policy language.  
• Heavily keyword-driven classifier may mis-label nuanced texts.  
• Confidence values below 60 % should be treated as *inconclusive* (recommend manual review).

## 6 Ethical Considerations
See `docs/ethics.md`. 

## 7 References
The classifier design is grounded in the sources listed in [`academic_references.md`](academic_references.md).

_Last updated_: 2025-07-16
