from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.analysis_engine.metrics import assess_stakeholders_impact


class StakeholderImpactAnalyzer:
    def analyze(self, *, themes: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        return assess_stakeholders_impact(themes=themes)
