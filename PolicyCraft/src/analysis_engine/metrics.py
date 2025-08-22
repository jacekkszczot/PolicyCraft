"""
PolicyCraft Analysis Metrics

British English. Lightweight, deterministic analytics that derive:
- Confidence metrics (0–100%) from internal signals and LiteratureRepository
- Stakeholder perspective highlights (students, faculty, administration/IT)
- Risk–Benefit balance snapshot

These utilities avoid external calls and work with partial data; they
should never raise on missing fields. They are designed to be wired
into the RecommendationEngine or routes without changing persistence.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from src.analysis_engine.literature.repository import LiteratureRepository
except Exception:
    LiteratureRepository = None  # type: ignore


def _safe_len(x) -> int:
    try:
        return len(x) if x is not None else 0
    except Exception:
        return 0


def compute_confidence(
    *,
    themes: Optional[List[Dict[str, Any]]],
    classification: Optional[Dict[str, Any]] | str,
    text_length: int | None,
    repo: Any | None,
) -> Dict[str, Any]:
    """Compute an overall confidence in [0,100] using simple interpretable signals.

    Signals (weights sum ~1.0):
    - Theme support (count and average theme confidence) …… 0.45
    - Classification confidence (if available) …………………… 0.25
    - Text quality proxy: cleaned text length ……………………… 0.15
    - Literature evidence diversity (unique sources) ………… 0.15
    """
    themes = themes or []
    # Average theme confidence (already in 0–100)
    if themes:
        avg_theme_conf = sum(t.get("confidence", 0) for t in themes) / max(1, len(themes))
        theme_support = min(100.0, avg_theme_conf + 2.0 * min(6, _safe_len(themes)))  # small bonus for multiple themes
    else:
        theme_support = 0.0

    # Classification confidence normalised
    if isinstance(classification, dict):
        cls_conf = classification.get("confidence") or 0
        cls_conf = cls_conf * 100 if 0 <= cls_conf <= 1 else cls_conf
    else:
        cls_conf = 0
    cls_conf = max(0.0, min(100.0, float(cls_conf)))

    # Text length proxy: normalise vs a modest target (3k chars)
    tl = float(text_length or 0)
    text_quality = max(0.0, min(100.0, (tl / 3000.0) * 100.0))

    # Evidence diversity from repo
    diversity = 0.0
    unique_titles = 0
    try:
        if repo is not None:
            records = repo.find_sources()
            unique_titles = len({getattr(r, "title", None) for r in records if getattr(r, "title", None)})
            # Cap at 12 for diminishing returns
            diversity = max(0.0, min(100.0, (unique_titles / 12.0) * 100.0))
    except Exception:
        diversity = 0.0

    overall = (
        0.45 * theme_support
        + 0.25 * cls_conf
        + 0.15 * text_quality
        + 0.15 * diversity
    )

    return {
        "overall_pct": round(overall, 1),
        "factors": {
            "avg_theme_support": round(theme_support, 1),
            "classification_conf": round(cls_conf, 1),
            "text_quality": round(text_quality, 1),
            "evidence_diversity": round(diversity, 1),
            "unique_sources": unique_titles,
        },
    }


def assess_stakeholders_impact(
    *,
    themes: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Very light heuristic mapping themes → stakeholder concerns.
    Returns per‑stakeholder bullet points.
    """
    themes = themes or []
    theme_names = {str(t.get("name", "")).lower() for t in themes}

    def has_any(keys: List[str]) -> bool:
        low = {k.lower() for k in keys}
        return any(k in theme_names for k in low)

    students = [
        "Transparency of AI usage and appeal processes",
        "Accessible guidance on permitted vs non‑permitted use",
    ]
    faculty = [
        "Workload reduction through checklists and rubrics",
        "Training on interpretability and good practice",
    ]
    admin = [
        "Compliance monitoring and policy maintenance",
        "Data security and event logging",
    ]

    if has_any(["bias", "fairness", "inclusion", "inclusiveness"]):
        students.append("Bias mitigation and equitable outcomes")
    if has_any(["transparency", "explainability", "documentation"]):
        faculty.append("Clear documentation and disclosure standards")
    if has_any(["governance", "accountability", "audit", "monitoring"]):
        admin.append("Regular audit cycle and governance oversight")

    return {
        "students": students,
        "faculty": faculty,
        "administration_it": admin,
    }


def assess_risk_benefit(
    *,
    themes: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Simple risk/benefit snapshot based on theme mix.
    Outputs discrete levels: low/medium/high.
    """
    themes = themes or []
    names = {str(t.get("name", "")).lower() for t in themes}

    risk_score = 0
    benefit_score = 0

    # Risk signals
    for key in ["privacy", "security", "misuse", "bias"]:
        if any(key in n for n in names):
            risk_score += 1

    # Benefit signals
    for key in ["efficiency", "innovation", "support", "learning", "accessibility"]:
        if any(key in n for n in names):
            benefit_score += 1

    def level(v: int) -> str:
        return "high" if v >= 3 else ("medium" if v == 2 else "low")

    return {
        "risk_level": level(risk_score),
        "benefit_level": level(benefit_score),
    }
