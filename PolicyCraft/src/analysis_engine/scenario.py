from __future__ import annotations

from typing import Any, Dict


class ScenarioPlanner:
    def generate_scenarios(self, base_recommendation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal scenarios with adjusted labels only; deterministic
        return {
            "scenarios": {
                "optimistic": {"label": "optimistic", "success_probability": 0.7},
                "realistic": {"label": "realistic", "success_probability": 0.55},
                "pessimistic": {"label": "pessimistic", "success_probability": 0.4},
            },
            "recommended_scenario": "realistic",
        }
