from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.analysis_engine.metrics import assess_risk_benefit


class RiskBenefitAnalyzer:
    RISK_CATEGORIES = [
        "implementation_risk",
        "compliance_risk",
        "operational_risk",
        "financial_risk",
        "reputational_risk",
        "academic_freedom_risk",
    ]

    BENEFIT_CATEGORIES = [
        "compliance_improvement",
        "efficiency_gains",
        "risk_reduction",
        "stakeholder_satisfaction",
        "competitive_advantage",
        "innovation_enablement",
    ]

    def analyze(self, *, themes: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        return assess_risk_benefit(themes=themes)
