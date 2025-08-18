"""
PolicyCraft Advanced Analysis Engine.

This module implements the advanced multi-dimensional analysis engine for PolicyCraft,
providing sophisticated policy evaluation capabilities with integrated literature
repository support and confidence calculation. The engine serves as the core
analytical component for processing policy documents with enhanced accuracy.

Key Features:
- Multi-dimensional policy analysis framework
- Literature repository integration for evidence-based insights
- Advanced confidence calculation algorithms
- Contextual analysis with stakeholder considerations

The engine processes policy texts through multiple analytical layers, incorporating
academic literature insights and generating comprehensive analysis results with
confidence metrics and contextual recommendations.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from src.analysis_engine.literature.repository import LiteratureRepository
except Exception:
    LiteratureRepository = None  # type: ignore

from src.analysis_engine.confidence import AdvancedConfidenceCalculator
from src.analysis_engine.stakeholder import StakeholderImpactAnalyzer
from src.analysis_engine.risk_benefit import RiskBenefitAnalyzer
from src.analysis_engine.readiness import ImplementationReadinessAnalyzer
from src.analysis_engine.context import ContextSensitivityEngine, AlternativeAnalysisModes


class PolicyAnalysisEngine:
    def __init__(self) -> None:
        self.analysis_dimensions = {
            "stakeholder_impact": StakeholderImpactAnalyzer(),
            "risk_benefit": RiskBenefitAnalyzer(),
        }
        self.confidence_calc = AdvancedConfidenceCalculator()
        self.readiness = ImplementationReadinessAnalyzer()
        self.context_engine = ContextSensitivityEngine()

    def analyze_policy(self, policy_text: str, context_params: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[Dict[str, Any]] = context_params.get("themes") or []
        classification = context_params.get("classification")
        repo = LiteratureRepository.get() if LiteratureRepository else None

        confidence = self.confidence_calc.calculate_confidence(
            themes=themes,
            classification=classification,
            text_length=len(policy_text or ""),
            repo=repo,
        )
        analyses: Dict[str, Any] = {}
        for dim, analyzer in self.analysis_dimensions.items():
            analyses[dim] = analyzer.analyze(themes=themes)

        result = {
            "confidence": confidence,
            "dimensions": analyses,
            "context": {
                "profile": context_params.get("organization_profile", {}),
                "mode": context_params.get("analysis_mode", "default"),
            },
        }
        return result
