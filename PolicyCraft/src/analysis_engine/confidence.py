from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.analysis_engine.metrics import compute_confidence


class AdvancedConfidenceCalculator:
    """Thin wrapper over compute_confidence with future-ready weights.

    Keeps compatibility with current metrics while exposing a class interface.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Placeholder for future tuning
        self.weights = weights or {
            "theme_support": 0.45,
            "classification_conf": 0.25,
            "text_quality": 0.15,
            "evidence_diversity": 0.15,
        }

    def calculate_confidence(
        self,
        *,
        themes: Optional[List[Dict[str, Any]]],
        classification: Optional[Dict[str, Any]] | str,
        text_length: int | None,
        repo: Any | None,
    ) -> Dict[str, Any]:
        return compute_confidence(
            themes=themes,
            classification=classification,
            text_length=text_length,
            repo=repo,
        )
