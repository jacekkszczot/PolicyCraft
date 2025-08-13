# PolicyCraft Model Card

## Model Details
- **Version**: 1.0.0 (24 July 2025)
- **Architecture**: Hybrid BERT + TF-IDF ensemble
- **License**: MIT
- **Maintainer**: Jacek Robert Kszczot, Leeds Trinity University

## Training Data
- **Size**: 1,250 policy excerpts
- **Categories**: Restrictive, Moderate, Permissive
- **Coverage**: 14+ countries, 50+ institutions
- **Languages**: Primarily English (UK/US variants)

## Performance (v1.0.0)
| Metric | Score |
|--------|-------|
| Accuracy | 0.87 |
| Macro-F1 | 0.86 |
| Brier Score | 0.07 |
| Calibration Error | 0.05 |

## Intended Use
- Policy analysis and categorisation
- Benchmarking AI policies
- Generating recommendations
- Research purposes

## Limitations
- Best for formal, academic English
- May misinterpret nuanced language
- Trained on data up to July 2025

## Ethical Considerations
- Regular fairness audits
- No PII processing
- Local analysis only
- Transparent reporting

## Maintenance
- Quarterly updates
- Continuous monitoring
- User feedback encouraged

_Last updated: 24 July 2025_
