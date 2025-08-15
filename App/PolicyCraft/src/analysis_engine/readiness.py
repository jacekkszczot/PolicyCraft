from __future__ import annotations

from typing import Dict, Any


class ImplementationReadinessAnalyzer:
    READINESS_FACTORS = {
        "technical_capability": {
            "weight": 0.25,
            "indicators": ["existing_systems", "it_expertise", "infrastructure"],
        },
        "organizational_culture": {
            "weight": 0.20,
            "indicators": ["change_appetite", "innovation_history", "leadership_support"],
        },
        "resource_availability": {
            "weight": 0.25,
            "indicators": ["budget_allocation", "staff_capacity", "time_availability"],
        },
        "stakeholder_alignment": {
            "weight": 0.20,
            "indicators": ["faculty_buy_in", "student_support", "admin_commitment"],
        },
        "external_pressures": {
            "weight": 0.10,
            "indicators": ["regulatory_timeline", "competitive_pressure", "funding_requirements"],
        },
    }

    def assess_readiness(self, organization_profile: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal, deterministic placeholder based on presence of indicators
        scores: Dict[str, float] = {}
        overall = 0.0
        for factor, cfg in self.READINESS_FACTORS.items():
            present = 0
            for ind in cfg["indicators"]:
                if organization_profile.get(ind):
                    present += 1
            # normalise to 0..100 per factor
            factor_score = (present / max(1, len(cfg["indicators"]))) * 100.0
            scores[factor] = round(factor_score, 1)
            overall += factor_score * cfg["weight"]

        return {
            "readiness_score": round(overall, 1),
            "factor_breakdown": scores,
            "improvement_recommendations": [],
            "implementation_timeline": "phased",
        }
