from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class OrganizationProfile:
    institution_type: str = "teaching_focused"
    size: str = "medium"
    budget_category: str = "medium"
    risk_tolerance: str = "moderate"
    existing_ai_maturity: str = "developing"
    regulatory_environment: str = "standard"
    stakeholder_priorities: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class EnhancedRecommendation:
    original_recommendation: Dict[str, Any]
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    stakeholder_impacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    risk_benefit_profile: Dict[str, Any] = field(default_factory=dict)
    confidence_metrics: Dict[str, Any] = field(default_factory=dict)
    implementation_scenarios: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    change_management_notes: str = ""
