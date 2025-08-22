from __future__ import annotations

from typing import Dict, Any, List


class ContextSensitivityEngine:
    def __init__(self) -> None:
        self.organizational_contexts: Dict[str, Dict[str, Any]] = {
            "research_intensive": {
                "priorities": ["academic_freedom", "innovation", "collaboration"],
                "risk_tolerance": "high",
                "change_speed": "deliberate",
            },
            "teaching_focused": {
                "priorities": ["student_experience", "accessibility", "consistency"],
                "risk_tolerance": "medium",
                "change_speed": "moderate",
            },
            "community_college": {
                "priorities": ["cost_effectiveness", "simplicity", "support"],
                "risk_tolerance": "low",
                "change_speed": "gradual",
            },
        }

    def contextualize_analysis(self, base_analysis: Dict[str, Any], org_context: str, user_priorities: List[str]) -> Dict[str, Any]:
        return {
            "original_analysis": base_analysis,
            "contextual_adjustments": [],
            "context_rationale": {
                "context": org_context,
                "priorities": user_priorities,
            },
        }


class AlternativeAnalysisModes:
    ANALYSIS_LENSES: Dict[str, Dict[str, Any]] = {
        "legal_compliance": {
            "weight_adjustments": {"compliance": 1.5, "risk_mitigation": 1.3},
            "focus_areas": ["regulatory_alignment", "audit_readiness", "documentation"],
        },
        "student_centric": {
            "weight_adjustments": {"inclusiveness": 1.4, "transparency": 1.2},
            "focus_areas": ["user_experience", "accessibility", "support_systems"],
        },
        "efficiency_focused": {
            "weight_adjustments": {"cost_efficiency": 1.5, "implementation_speed": 1.3},
            "focus_areas": ["automation", "resource_optimisation", "streamlined_processes"],
        },
        "innovation_enabler": {
            "weight_adjustments": {"flexibility": 1.4, "academic_freedom": 1.3},
            "focus_areas": ["experimentation", "emerging_technologies", "pilot_programs"],
        },
    }
