"""
PolicyCraft Recommendation Engine - Core Analysis and Generation Components.

This module implements the recommendation engine for PolicyCraft, providing
comprehensive analysis of AI policy documents and generating evidence-based
recommendations for higher education institutions. The engine combines ethical
framework analysis with contextual recommendation generation.

Key Components:
- PolicyDimension: Enumeration of ethical AI policy dimensions
- PolicyRecommendation: Data structure for recommendation storage
- EthicalFrameworkAnalyser: Core analysis engine for policy evaluation
- RecommendationGenerator: Contextual policy recommendation generation

The engine analyses policies across multiple dimensions including transparency,
accountability, human oversight, and bias mitigation, providing structured
feedback and actionable recommendations grounded in academic literature.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import sys
import json
import os
import logging
import re
import random
from typing import Dict, List, Any, Optional, Union
from enum import Enum, auto
from dataclasses import dataclass, field

try:
    from src.literature.knowledge_manager import KnowledgeBaseManager
except ImportError:
    KnowledgeBaseManager = None
try:
    from src.analysis_engine.literature.repository import LiteratureRepository
except Exception:
    LiteratureRepository = None  # type: ignore
try:
    from src.analysis_engine.metrics import (
        compute_confidence,
        assess_stakeholders_impact,
        assess_risk_benefit,
    )
except Exception:
    compute_confidence = assess_stakeholders_impact = assess_risk_benefit = None  # type: ignore
try:
    from src.analysis_engine.engine import PolicyAnalysisEngine
except Exception:
    PolicyAnalysisEngine = None  # type: ignore

# Semantic embeddings for enhanced relevance scoring
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    np = None
    
logger = logging.getLogger(__name__)

# Reused literals/constants
IMPLEMENTATION_TIME_MEDIUM = "3-6 months"
IMPLEMENTATION_TIME_SHORT = "2-4 months"
IMPLEMENTATION_TIME_2_3 = "2-3 months"
IMPLEMENTATION_TIME_3_5 = "3-5 months"
IMPLEMENTATION_TIME_1_3 = "1-3 months"
IMPLEMENTATION_TIME_4_8 = "4-8 months"
IMPLEMENTATION_TIME_6_12 = "6-12 months"
UNIVERSITY_POLICY_LITERAL = "university policy"
YEAR_REGEX = r"(19|20)\d{2}"

class PolicyDimension(Enum):
    ACCOUNTABILITY = "Accountability and Governance"
    TRANSPARENCY = "Transparency and Explainability"
    HUMAN_AGENCY = "Human Agency and Oversight"
    INCLUSIVENESS = "Inclusiveness and Fairness"
    
DIMENSION_KEYWORDS = {
    PolicyDimension.ACCOUNTABILITY: [
        "accountable", "governance", "oversight", "responsibility", "compliance", "audit", "monitor"
    ],
    PolicyDimension.TRANSPARENCY: [
        "transparent", "explain", "disclose", "acknowledge", "acknowledgement", "document", "clear", "interpretable", "explainable"
    ],
    PolicyDimension.HUMAN_AGENCY: [
        "human", "oversight", "control", "decision", "judgment", "intervention", "review"
    ],
    PolicyDimension.INCLUSIVENESS: [
        "inclusive", "fair", "bias", "diverse", "equitable", "discrimination", "representation"
    ],
}

@dataclass
class PolicyRecommendation:
    """A single recommendation for improving a policy."""
    id: str
    title: str
    description: str
    rationale: str
    priority: str  # "high", "medium", "low"
    dimension: PolicyDimension
    implementation_guidance: str = ""
    references: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the recommendation to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority,
            "dimension": self.dimension.value,
            "implementation_guidance": self.implementation_guidance,
            "references": self.references or []
        }

class EthicalFrameworkAnalyzer:
    """
    Analyses policy text against ethical AI frameworks and provides structured feedback.
    """
    
    def __init__(self, knowledge_manager: Optional[KnowledgeBaseManager] = None):
        """Initialise with an optional knowledge manager for reference lookups."""
        self.knowledge_manager = knowledge_manager
        self.dimensions = list(PolicyDimension)
        
    def analyse_policy(self, policy_text: str, institution_type: str = "university") -> Dict[str, Any]:
        """
        Analyse a policy text and return a structured analysis.
        
        Args:
            policy_text: The text of the policy to analyse
            institution_type: Type of institution (university, college, etc.)
            
        Returns:
            Dict containing analysis results including scores and recommendations
        """
        # This is a placeholder - in a real implementation, this would use NLP
        # to analyze the policy text against each dimension
        
        analysis = {
            "institution_type": institution_type,
            "dimension_scores": {dim.value: self._score_dimension(dim, policy_text) 
                               for dim in self.dimensions},
            "overall_score": 0.0,
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": []
        }
        
        # Calculate overall score (simple average for now)
        scores = [s["score"] for s in analysis["dimension_scores"].values()]
        analysis["overall_score"] = sum(scores) / len(scores) if scores else 0
        
        # Generate recommendations
        for dim in self.dimensions:
            dim_score = analysis["dimension_scores"][dim.value]["score"]
            if dim_score < 0.5:  # Threshold for needing improvement
                analysis["areas_for_improvement"].append(dim.value)
                analysis["recommendations"].extend(
                    self._generate_dimension_recommendations(dim, policy_text)
                )
            else:
                analysis["strengths"].append(dim.value)
        
        return analysis
        
    def _score_dimension(self, dimension: PolicyDimension, text: str) -> Dict[str, Any]:
        """Score a single dimension of the policy (0-1 scale) with more sophisticated analysis."""
        # Enhanced implementation with more keywords and contextual analysis
        keywords = {
            PolicyDimension.ACCOUNTABILITY: [
                "accountable", "governance", "oversight", "responsibility", "compliance", 
                "audit", "monitor", "review", "assess", "evaluate", "report", "board", 
                "committee", "authority", "regulation", "standard", "policy", "procedure"
            ],
            PolicyDimension.TRANSPARENCY: [
                "transparent", "explain", "disclose", "acknowledge", "acknowledgement", "document", "clear", "interpretable", 
                "explainable", "communication", "inform", "publish", "report", "accessible", 
                "visibility", "clarity", "understandable", "documentation", "openness"
            ],
            PolicyDimension.HUMAN_AGENCY: [
                "human", "oversight", "control", "decision", "judgment", "intervention", 
                "review", "autonomy", "choice", "consent", "opt-out", "appeal", "override", 
                "supervise", "authority", "discretion", "input", "feedback", "participation"
            ],
            PolicyDimension.INCLUSIVENESS: [
                "inclusive", "fair", "bias", "diverse", "equitable", "discrimination", 
                "representation", "accessibility", "equality", "diversity", "inclusion", 
                "minority", "underrepresented", "vulnerable", "marginalized", "equity"
            ]
        }
        
        # Advanced phrases that indicate strong policy in each dimension
        advanced_phrases = {
            PolicyDimension.ACCOUNTABILITY: [
                "clear lines of responsibility", "governance framework", "oversight committee", 
                "regular auditing", "compliance monitoring", "reporting mechanisms", 
                "accountability structures", "responsibility matrix"
            ],
            PolicyDimension.TRANSPARENCY: [
                "transparency report", "disclosure policy", "must disclose", "explainable ai", 
                "clear documentation", "public reporting", "information access", 
                "algorithmic transparency", "open communication"
            ],
            PolicyDimension.HUMAN_AGENCY: [
                "human in the loop", "meaningful human control", "human oversight", 
                "appeal process", "human review", "manual override", "human judgment", 
                "human decision-making"
            ],
            PolicyDimension.INCLUSIVENESS: [
                "bias mitigation", "fairness assessment", "inclusive design", 
                "diversity considerations", "equitable outcomes", "accessibility requirements", 
                "non-discrimination", "representation of diverse groups"
            ]
        }
        
        text_lower = text.lower()
        
        # Count keyword matches with more weight for important terms
        keyword_matches = sum(1 for kw in keywords[dimension] if kw in text_lower)
        # High-weight transparency indicators get a small bonus
        if dimension == PolicyDimension.TRANSPARENCY:
            if "disclose" in text_lower:
                keyword_matches += 1
            if "acknowledge" in text_lower:
                keyword_matches += 1
        
        # Count advanced phrase matches with higher weight
        phrase_matches = sum(2 for phrase in advanced_phrases[dimension] if phrase in text_lower)
        
        # Calculate total possible score
        total_possible = len(keywords[dimension]) + (len(advanced_phrases[dimension]) * 2)
        
        # Calculate raw score (0-1 scale)
        raw_score = (keyword_matches + phrase_matches) / (total_possible * 0.5)  # Slightly easier to reach meaningful %
        score = min(1.0, raw_score)  # Cap at 1.0
        
        # Detailed analysis results
        return {
            "score": round(score, 2),
            "keywords_found": [kw for kw in keywords[dimension] if kw in text_lower],
            "keywords_missing": [kw for kw in keywords[dimension] if kw not in text_lower],
            "advanced_phrases_found": [phrase for phrase in advanced_phrases[dimension] if phrase in text_lower],
            "advanced_phrases_missing": [phrase for phrase in advanced_phrases[dimension] if phrase not in text_lower],
            "analysis_summary": self._generate_dimension_analysis_summary(dimension, score)
        }
        
    def _generate_dimension_analysis_summary(self, dimension: PolicyDimension, score: float) -> str:
        """Generate a human-readable summary of the dimension analysis."""
        # determine strength based on score - might want to adjust these thresholds later
        if score >= 0.8:
            strength_level = "strong"
        elif score >= 0.5: strength_level = "moderate"  # different formatting style
        else:
            strength_level = "weak"
            
        summaries = {
            PolicyDimension.ACCOUNTABILITY: {
                "strong": "The policy demonstrates strong accountability measures with clear governance structures and oversight mechanisms.",
                "moderate": "The policy includes some accountability measures but could benefit from more defined governance structures.",
                "weak": "The policy lacks sufficient accountability measures and requires clearer governance structures."
            },
            PolicyDimension.TRANSPARENCY: {
                "strong": "The policy demonstrates strong commitment to transparency with clear disclosure and explanation requirements.",
                "moderate": "The policy addresses transparency but could benefit from more specific disclosure requirements.",
                "weak": "The policy lacks sufficient transparency measures and needs clearer disclosure requirements."
            },
            PolicyDimension.HUMAN_AGENCY: {
                "strong": "The policy strongly supports human agency with clear human oversight and intervention mechanisms.",
                "moderate": "The policy acknowledges human agency but could strengthen human oversight provisions.",
                "weak": "The policy insufficiently addresses human agency and requires stronger human oversight provisions."
            },
            PolicyDimension.INCLUSIVENESS: {
                "strong": "The policy demonstrates strong commitment to inclusiveness with robust bias mitigation and fairness measures.",
                "moderate": "The policy addresses inclusiveness but could benefit from more specific bias mitigation strategies.",
                "weak": "The policy lacks sufficient inclusiveness measures and needs clearer bias mitigation strategies."
            }
        }
        
        return summaries.get(dimension, {}).get(strength_level, "No analysis available.")
    
    def _generate_dimension_recommendations(self, dimension: PolicyDimension, text: str) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific dimension based on policy text analysis."""
        text_lower = text.lower()
        recommendations = []
        
        # Local helper to reduce repeated dict construction
        def add_rec(rid: str, title: str, description: str, rationale: str, priority: str, impl_time: str, steps: List[str]) -> None:
            recommendations.append({
                "id": rid,
                "title": title,
                "description": description,
                "rationale": rationale,
                "priority": priority,
                "dimension": dimension.value,
                "implementation_time": impl_time,
                "implementation_steps": steps,
            })
        
        # Get dimension-specific keywords and their presence in the text
        found_keywords = [kw for kw in DIMENSION_KEYWORDS.get(dimension, []) if kw in text_lower]
        missing_keywords = [kw for kw in DIMENSION_KEYWORDS.get(dimension, []) if kw not in text_lower]
        
        # Generate context-aware recommendations via per-dimension helpers
        if dimension == PolicyDimension.ACCOUNTABILITY:
            self._recs_accountability(dimension, found_keywords, missing_keywords, add_rec, recommendations)
        elif dimension == PolicyDimension.TRANSPARENCY:
            self._recs_transparency(dimension, found_keywords, add_rec)
        elif dimension == PolicyDimension.HUMAN_AGENCY:
            self._recs_human_agency(dimension, found_keywords, add_rec)
        elif dimension == PolicyDimension.INCLUSIVENESS:
            self._recs_inclusiveness(dimension, found_keywords, add_rec)
        
        # If no specific recommendations were generated, provide a generic one
        if not recommendations:
            add_rec(
                f"{dimension.value.lower().split()[0][:5]}-gen",
                f"Strengthen {dimension.value} in Your AI Policy",
                f"Review and enhance your policy's approach to {dimension.value.lower()}.",
                f"A robust approach to {dimension.value.lower()} is essential for ethical AI governance.",
                "medium",
                IMPLEMENTATION_TIME_MEDIUM,
                [
                    f"Conduct a comprehensive review of your policy's {dimension.value.lower()} provisions",
                    f"Benchmark against best practices in {dimension.value.lower()} from leading institutions",
                    f"Identify specific gaps in your {dimension.value.lower()} approach",
                    "Develop targeted improvements for each identified gap",
                    "Implement changes and establish metrics to track effectiveness",
                ],
            )
            
        return recommendations

    # ---- Extracted per-dimension helpers to reduce branching ----
    def _recs_accountability(self, dimension: PolicyDimension, found_keywords: List[str], missing_keywords: List[str], add_rec, recommendations: List[Dict[str, Any]]) -> None:
        if len(missing_keywords) > len(found_keywords):
            add_rec(
                "acc-001",
                "Establish Clear Accountability Structures",
                "Define clear roles and responsibilities for AI governance within your institution.",
                "Clear accountability ensures that AI systems are used responsibly and that there is oversight at all levels.",
                "high",
                IMPLEMENTATION_TIME_MEDIUM,
                [
                    "Form an AI governance committee with representatives from key stakeholders",
                    "Define clear roles and responsibilities for AI oversight",
                    "Establish reporting lines and accountability mechanisms",
                    "Document governance structures in formal policy documents",
                    "Communicate governance framework to all relevant staff",
                ],
            )
        if "audit" not in found_keywords or "monitor" not in found_keywords:
            add_rec(
                "acc-002",
                "Implement Regular Auditing and Monitoring",
                "Establish procedures for regular auditing and monitoring of AI systems to ensure compliance with ethical standards.",
                "Regular auditing helps identify issues early and ensures continuous improvement of AI governance.",
                "medium",
                IMPLEMENTATION_TIME_SHORT,
                [
                    "Develop an AI audit framework with clear metrics and benchmarks",
                    "Establish a regular audit schedule (quarterly or bi-annually)",
                    "Create audit templates and checklists for consistency",
                    "Train staff on audit procedures and ethical standards",
                    "Implement reporting mechanisms for audit findings",
                ],
            )
        if "compliance" not in found_keywords:
            recommendations.append({
                "id": "acc-003",
                "title": "Develop Compliance Frameworks for AI Systems",
                "description": "Create comprehensive compliance frameworks that align with regulatory requirements and ethical standards.",
                "rationale": "Structured compliance frameworks reduce legal risks and ensure ethical AI deployment.",
                "priority": "high",
                "dimension": dimension.value,
                "implementation_time": IMPLEMENTATION_TIME_4_8,
                "implementation_steps": [
                    "Research relevant AI regulations and ethical standards in your jurisdiction",
                    "Develop a compliance matrix mapping requirements to institutional policies",
                    "Create compliance documentation templates and checklists",
                    "Establish compliance verification procedures for AI systems",
                    "Implement regular compliance reviews and updates as regulations evolve"
                ]
            })

    def _recs_transparency(self, dimension: PolicyDimension, found_keywords: List[str], add_rec) -> None:
        if "explain" not in found_keywords or "explainable" not in found_keywords:
            add_rec(
                "trans-001",
                "Improve Explainability of AI Systems",
                "Implement mechanisms to explain AI decisions in clear, non-technical language to affected stakeholders.",
                "Explainable AI builds trust and enables meaningful human oversight of automated decisions.",
                "high",
                IMPLEMENTATION_TIME_MEDIUM,
                [
                    "Audit current AI systems for explainability gaps",
                    "Develop explainability standards for different stakeholder groups",
                    "Implement technical solutions for generating explanations (e.g., LIME, SHAP)",
                    "Create user-friendly interfaces for displaying explanations",
                    "Train staff on communicating AI decisions to non-technical audiences",
                ],
            )
        if "document" not in found_keywords:
            add_rec(
                "trans-002",
                "Enhance Documentation of AI Systems",
                "Create comprehensive documentation for all AI systems, including their purpose, limitations, and potential risks.",
                "Thorough documentation enables better understanding and evaluation of AI systems by all stakeholders.",
                "medium",
                IMPLEMENTATION_TIME_SHORT,
                [
                    "Develop documentation templates for AI systems",
                    "Conduct inventory of all AI systems requiring documentation",
                    "Document technical specifications, data sources, and algorithms used",
                    "Include known limitations, biases, and potential risks in documentation",
                    "Establish a process for regular documentation updates as systems evolve",
                ],
            )
        if "disclose" not in found_keywords:
            add_rec(
                "trans-003",
                "Establish Disclosure Protocols",
                "Develop clear protocols for when and how to disclose AI use to affected individuals and communities.",
                "Appropriate disclosure respects autonomy and enables informed consent regarding AI-driven decisions.",
                "medium",
                IMPLEMENTATION_TIME_2_3,
                [
                    "Identify all contexts where AI is used to make or support decisions",
                    "Define clear disclosure requirements for each context",
                    "Create standardised disclosure templates",
                    "Train staff on when and how to disclose AI use",
                    "Establish processes for obtaining informed consent where appropriate",
                ],
            )

    def _recs_human_agency(self, dimension: PolicyDimension, found_keywords: List[str], add_rec) -> None:
        if "oversight" not in found_keywords or "intervention" not in found_keywords:
            add_rec(
                "human-001",
                "Strengthen Human Oversight Mechanisms",
                "Ensure that human oversight is built into all AI decision-making processes.",
                "Human oversight is essential for ensuring accountability and preventing harmful outcomes from automated systems.",
                "high",
                IMPLEMENTATION_TIME_MEDIUM,
                [
                    "Define clear criteria for when human intervention is required",
                    "Implement human-in-the-loop controls for critical decisions",
                    "Establish procedures for reviewing and overriding AI decisions",
                    "Train staff on responsible use and oversight of AI systems",
                    "Create feedback mechanisms for reporting concerns about AI decisions",
                ],
            )
        if "approval" not in found_keywords:
            add_rec(
                "human-002",
                "Implement Approval Processes for AI Use",
                "Establish approval processes for AI use in sensitive academic contexts.",
                "Approval processes ensure appropriate oversight and alignment with institutional values.",
                "medium",
                IMPLEMENTATION_TIME_SHORT,
                [
                    "Define criteria for AI use requiring prior approval",
                    "Establish an approval committee with cross-disciplinary representation",
                    "Create application and review processes for AI use proposals",
                    "Document approval decisions and conditions",
                    "Implement review procedures for ongoing AI use",
                ],
            )

    def _recs_inclusiveness(self, dimension: PolicyDimension, found_keywords: List[str], add_rec) -> None:
        if "bias" not in found_keywords or "fairness" not in found_keywords:
            add_rec(
                "incl-001",
                "Implement Bias Mitigation Strategies",
                "Develop and implement strategies to identify and mitigate bias in AI systems used in academic contexts.",
                "Bias mitigation is essential for ensuring equitable outcomes and preventing discrimination.",
                "high",
                IMPLEMENTATION_TIME_MEDIUM,
                [
                    "Conduct bias audits of AI systems",
                    "Develop fairness metrics appropriate for academic contexts",
                    "Implement debiasing techniques and fairness-aware algorithms",
                    "Train staff on recognising and addressing bias in AI systems",
                    "Establish monitoring procedures for fairness over time",
                ],
            )
        if "accessibility" not in found_keywords:
            add_rec(
                "incl-002",
                "Ensure Accessibility in AI Systems",
                "Ensure that AI systems and their interfaces are accessible to all users, including those with disabilities.",
                "Accessibility is a fundamental requirement for inclusive AI systems in higher education.",
                "medium",
                IMPLEMENTATION_TIME_SHORT,
                [
                    "Audit AI system interfaces for accessibility compliance",
                    "Implement accessibility improvements based on audit findings",
                    "Provide alternative formats and assistive technologies where needed",
                    "Train staff on accessibility best practices for AI systems",
                    "Establish ongoing accessibility monitoring and user feedback channels",
                ],
            )

    # --- Compatibility API expected by tests ---
    def analyze_coverage(self, themes: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Produce coverage per dimension with percentage score and details.

        Returns a dict with keys for each dimension name in lowercase, each value containing:
        - score (0-100)
        - item_count
        - matched_items (keywords and phrases)
        - status: weak/moderate/strong
        """
        text_lower = (text or "").lower()

        coverage: Dict[str, Any] = {}
        for dim in [PolicyDimension.ACCOUNTABILITY, PolicyDimension.TRANSPARENCY, PolicyDimension.HUMAN_AGENCY, PolicyDimension.INCLUSIVENESS]:
            # Reuse scoring config from _score_dimension
            scored = self._score_dimension(dim, text_lower)
            keywords_found = scored.get("keywords_found", [])
            phrases_found = scored.get("advanced_phrases_found", [])
            total_items = len(keywords_found) + len(phrases_found)

            pct = int(round(scored.get("score", 0.0) * 100))
            if pct >= 67:
                status = "strong"
            elif pct >= 34:
                status = "moderate"
            else:
                status = "weak"

            # tests use plain keys: 'transparency', 'human_agency', etc.
            coverage[dim.name.lower()] = {
                "score": pct,
                "item_count": total_items,
                "matched_items": keywords_found + [f"PHRASE: {p}" for p in phrases_found],
                "status": status,
            }

        return coverage

    def detect_existing_policies(self, text: str) -> Dict[str, bool]:
        """Detect existing policy elements in text.

        Returns booleans such as disclosure_requirements and approval_processes.
        """
        t = (text or "").lower()
        return {
            "disclosure_requirements": any(k in t for k in ["disclose", "acknowledge", "cite ai", "disclosure"]),
            "approval_processes": any(k in t for k in ["approval", "approved", "faculty approval", "committee approval", "authorisation", "authorization"]),
        }

    def identify_gaps(self, coverage: Dict[str, Any], classification: str) -> List[Dict[str, Any]]:
        """Create gap objects from coverage dict.

        Each gap contains: dimension, type, priority, current_score, description
        """
        gaps: List[Dict[str, Any]] = []
        for dim_key, data in (coverage or {}).items():
            score = float(data.get("score", 0))
            if score >= 67:
                continue
            # Map to friendly names
            dim_map = {
                "accountability": "accountability",
                "transparency": "transparency",
                "human_agency": "human_agency",
                "inclusiveness": "inclusiveness",
            }
            priority = "high" if score < 34 else "medium"
            gap_type = "coverage_gap" if score < 34 else "improvement_opportunity"
            gaps.append({
                "dimension": dim_map.get(dim_key, dim_key),
                "type": gap_type,
                "priority": priority,
                "current_score": score,
                "description": f"Low {dim_map.get(dim_key, dim_key).replace('_',' ')} coverage for classification '{classification}'.",
            })
        return gaps

class RecommendationGenerator:
    """
    Generates policy recommendations based on ethical frameworks and best practices.
    Integrates with knowledge base for evidence-based recommendations.
    """
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialise the recommendation generator.
        
        Args:
            knowledge_base_path: Path to the knowledge base directory (required)
        """  
        logger.info("Initialising RecommendationGenerator...")
        
        # Initialise knowledge base manager
        self.knowledge_manager = None
        self.knowledge_base_available = False
        
        if KnowledgeBaseManager is not None and knowledge_base_path:
            try:
                logger.info(f"Initialising KnowledgeBaseManager with path: {knowledge_base_path}")
                self.knowledge_manager = KnowledgeBaseManager(knowledge_base_path)
                
                # Verify if the knowledge base contains any documents
                try:
                    documents = self.knowledge_manager.get_all_documents()
                    if documents and len(documents) > 0:
                        self.knowledge_base_available = True
                        logger.info(f"Found {len(documents)} documents in knowledge base")
                    else:
                        logger.error("Knowledge base is empty - cannot generate recommendations")
                except Exception as e:
                    logger.error(f"Error while checking knowledge base contents: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Failed to initialise knowledge base: {str(e)}")
        else:
            logger.error("No knowledge base path provided or KnowledgeBaseManager not available")
        
        # Initialise analyser only if we have access to knowledge base
        if self.knowledge_base_available:
            self.analyzer = EthicalFrameworkAnalyzer(self.knowledge_manager)
            
            # Initialise literature repository if available
            self.lit_repo = None
            try:
                if LiteratureRepository is not None:
                    self.lit_repo = LiteratureRepository.get()
            except Exception as e:
                logger.error(f"Failed to initialise literature repository: {str(e)}")
                self.lit_repo = None
            
            # Initialise semantic embedder if available
            self.embedder = None
            if EMBEDDINGS_AVAILABLE:
                try:
                    self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("Semantic embedder loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load semantic embedder: {str(e)}")
                    self.embedder = None
            
            logger.info("PolicyCraft Recommendation Engine initialised with knowledge base access")
        else:
            self.analyzer = None
            self.lit_repo = None
            self.embedder = None
            logger.error("Cannot initialise analyser - no access to knowledge base")
        
    def generate_recommendations(self, policy_text: str = "", institution_type: str = "university", **kwargs) -> Dict[str, Any]:
        """
        Generate recommendations for improving a policy.
        
        Args:
            policy_text: The text of the policy to analyse
            institution_type: Type of institution (university, college, etc.)
            **kwargs: Additional parameters (e.g., analysis_id for tracking)
            
        Returns:
            Dict containing analysis and recommendations
            
        Raises:
            ValueError: If knowledge base is not available or policy text is empty
        """
        # Check if knowledge base is available
        if not self.knowledge_base_available or not self.analyzer:
            raise ValueError(
                "Cannot generate recommendations - knowledge base is unavailable. "
                "Please try again later or contact the system administrator."
            )

        # Compatibility: allow tests to pass text via 'text' kwarg
        if not policy_text and "text" in kwargs:
            policy_text = kwargs.get("text", "")

        # If the contextual API is used (gaps/classification/themes), return list of recommendations
        if "gaps" in kwargs:
            gaps: List[Dict[str, Any]] = kwargs.get("gaps", []) or []
            themes = kwargs.get("themes", []) or []
            return self._generate_from_gaps(gaps=gaps, themes=themes, policy_text=policy_text)

        if not policy_text.strip():
            raise ValueError("Policy text cannot be empty")
            
        logger.info("Generating recommendations for %s policy (%d characters)", institution_type, len(policy_text))
        
        # Analyse policy using ethical framework
        analysis = self.analyzer.analyse_policy(policy_text, institution_type)
        
        # Track the analysis ID if provided
        analysis_id = kwargs.get('analysis_id', None)
        if analysis_id:
            analysis['analysis_id'] = analysis_id
        
        # Enhance recommendations with university-specific context
        for rec in analysis["recommendations"]:
            # Ensure recommendation is tailored for university context
            self._tailor_for_university_context(rec)
            
            # Ensure timeframe is set for template display
            self._ensure_timeframe(rec)
        
        # Enhance with knowledge base - required
        if not self.knowledge_manager:
            raise ValueError(
                "Knowledge base manager is not available. "
                "Cannot generate recommendations without a valid knowledge base."
            )
        self._enhance_with_kb(analysis)
        
        return analysis
        
    def _tailor_for_university_context(self, recommendation: Dict[str, Any]) -> None:
        """
        Tailor a recommendation specifically for university context.
        
        Args:
            recommendation: The recommendation to tailor
        """
        # Get current fields
        title = recommendation.get("title", "")
        description = recommendation.get("description", "")
        
        university_terms = ["university", "universities", "higher education", "academic", "faculty", "campus"]
        if self._is_already_university_tailored(title, description, university_terms):
            return
        
        # Title adjustment
        recommendation["title"] = self._adjust_title_for_university(title)
        
        # Description augmentation
        recommendation["description"] = self._augment_description_for_university(description)
        
        # Steps tailoring
        if "implementation_steps" in recommendation:
            recommendation["implementation_steps"] = self._tailor_steps_for_university(
                recommendation.get("implementation_steps", []), university_terms
            )

    # ---- Extracted micro-helpers for tailoring ----
    def _is_already_university_tailored(self, title: str, description: str, terms: List[str]) -> bool:
        t = (title or "").lower()
        d = (description or "").lower()
        return any(term in t or term in d for term in terms)

    def _adjust_title_for_university(self, title: str) -> str:
        if not title:
            return title
        lower = title.lower()
        if "policy" in lower and UNIVERSITY_POLICY_LITERAL not in lower:
            return title.replace("Policy", "University Policy").replace("policy", UNIVERSITY_POLICY_LITERAL)
        return title

    def _augment_description_for_university(self, description: str) -> str:
        if not description:
            return description
        lower = description.lower()
        if "university" in lower or "higher education" in lower:
            return description
        # Keep original capitalisation after the prefix where possible
        return f"In the university context, {lower[0]}{description[1:]}"

    def _tailor_steps_for_university(self, steps: List[str], terms: List[str]) -> List[str]:
        tailored: List[str] = []
        for step in steps:
            s_lower = (step or "").lower()
            if any(term in s_lower for term in terms):
                tailored.append(step)
                continue
            if "stakeholders" in s_lower and "faculty" not in s_lower:
                step = step.replace("stakeholders", "faculty, staff, students and other stakeholders")
            elif "training" in s_lower and "faculty" not in s_lower:
                step = step.replace("training", "faculty and staff training")
            elif "policy" in s_lower and "university" not in s_lower:
                step = step.replace("policy", UNIVERSITY_POLICY_LITERAL)
            tailored.append(step)
        return tailored

    # ---- Helper methods to reduce cognitive complexity ----
    def _generate_from_gaps(self, gaps: List[Dict[str, Any]], themes: List[Dict[str, Any]], policy_text: str) -> List[Dict[str, Any]]:
        """Generate contextual recommendations from gaps flow and dedupe results."""
        institution_context = self._analyze_institution_context(themes, policy_text)
        recs: List[Dict[str, Any]] = []
        existing = self._detect_existing_policies(policy_text)
        impl_type = "enhancement" if existing.get("disclosure_requirements") else "new_implementation"

        for gap in gaps:
            rec = self._generate_contextual_recommendation(
                dimension=gap.get("dimension", "transparency"),
                institution_context=institution_context,
                implementation_type=impl_type,
                priority=gap.get("priority", "medium"),
                current_score=float(gap.get("current_score", 0.0)),
                gap_details=gap,
            )
            if rec:
                self._ensure_timeframe(rec)
                recs.append(rec)

            # Add additional evidence-based recommendations for the same dimension
            # to avoid under-providing suggestions (ethically safer to provide
            # a broader set for human review rather than an overly narrow set).
            try:
                from typing import cast
                # Map gap dimension string to PolicyDimension enum safely
                dim_key = (gap.get("dimension", "") or "").upper()
                # Normalise potential keys
                dim_map = {
                    "ACCOUNTABILITY": "ACCOUNTABILITY",
                    "TRANSPARENCY": "TRANSPARENCY",
                    "HUMAN_AGENCY": "HUMAN_AGENCY",
                    "HUMAN AGENCY": "HUMAN_AGENCY",
                    "INCLUSIVENESS": "INCLUSIVENESS",
                }
                enum_key = dim_map.get(dim_key, "TRANSPARENCY")
                # PolicyDimension is defined in this module; import locally to avoid cycles
                from enum import Enum
                PD = cast(Enum, PolicyDimension)
                enum_dim = getattr(PD, enum_key)

                extra = self.analyzer._generate_dimension_recommendations(enum_dim, policy_text)
                # Take top 2 complementary suggestions per dimension to keep report concise
                # Ensure each receives a distinct implementation_type so dedupe by (dimension, implementation_type)
                # will retain them alongside the primary recommendation for that dimension.
                extra_types = ["pilot_programme", "training_and_capacity", "governance_controls"]
                for idx, extra_rec in enumerate(extra[:2] if isinstance(extra, list) else []):
                    # Tag implementation type if missing or identical to primary
                    if not extra_rec.get("implementation_type") or extra_rec.get("implementation_type") == impl_type:
                        extra_rec["implementation_type"] = extra_types[idx % len(extra_types)]
                    # Ensure timeframe field for template/UI
                    self._ensure_timeframe(extra_rec)
                    recs.append(extra_rec)
            except Exception as _e:
                logger.debug("Could not enrich recommendations for dimension '%s': %s", gap.get("dimension"), str(_e))

        # Ensure a minimum number of strategic recommendations for a useful brief
        try:
            MIN_RECS = 8
            if len(recs) < MIN_RECS:
                from typing import cast
                from enum import Enum
                PD = cast(Enum, PolicyDimension)
                extra_types_fill = [
                    "pilot_programme",
                    "training_and_capacity",
                    "governance_controls",
                    "documentation_transparency",
                    "evaluation_and_monitoring",
                ]
                type_idx = 0
                # Iterate all dimensions to top-up
                for dim in PD:
                    if len(recs) >= MIN_RECS:
                        break
                    try:
                        extra = self.analyzer._generate_dimension_recommendations(dim, policy_text)
                        for x in (extra if isinstance(extra, list) else []):
                            if len(recs) >= MIN_RECS:
                                break
                            if not x.get("implementation_type"):
                                x["implementation_type"] = extra_types_fill[type_idx % len(extra_types_fill)]
                                type_idx += 1
                            self._ensure_timeframe(x)
                            recs.append(x)
                    except Exception:
                        continue
        except Exception as _e:
            logger.debug("Top-up recommendations skipped: %s", str(_e))

        # First, de-duplicate by normalised (dimension, implementation_type)
        recs = self._dedupe_by_dimension_impl(recs)
        # Then, de-duplicate by title to maintain clarity and avoid repetition
        return self._dedupe_by_title(recs)

    def _dedupe_by_title(self, recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for r in recs:
            title = r.get("title", "")
            if title not in seen:
                seen.add(title)
                deduped.append(r)
        return deduped

    def _norm_dim_name(self, n: str) -> str:
        """Normalise dimension name to a canonical lower-case form.

        Maps short/underscore variants to full names used in PolicyDimension values.
        """
        s = (n or "").strip().lower()
        s = s.replace("&", "and").replace("_", " ")
        s = " ".join(s.split())
        # Known canonical full names (lower-case)
        canonical = {
            "accountability and governance": "accountability and governance",
            "transparency and explainability": "transparency and explainability",
            "human agency and oversight": "human agency and oversight",
            "inclusiveness and fairness": "inclusiveness and fairness",
        }
        if s in canonical:
            return s
        # Map common short keys
        short_map = {
            "accountability": "accountability and governance",
            "transparency": "transparency and explainability",
            "human agency": "human agency and oversight",
            "human_agency": "human agency and oversight",
            "humanagency": "human agency and oversight",
            "inclusiveness": "inclusiveness and fairness",
            "fairness": "inclusiveness and fairness",
        }
        return short_map.get(s, s)

    def _dedupe_by_dimension_impl(self, recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates based on normalised (dimension, implementation_type).

        Preserves first occurrence ordering. Also normalises the 'dimension' field
        only for comparison; it does NOT overwrite the original display value to
        preserve expected short labels in tests and API outputs.
        """
        seen: set[tuple[str, Optional[str]]] = set()
        out: List[Dict[str, Any]] = []
        for r in recs:
            dim_raw = r.get("dimension", "") or ""
            impl = r.get("implementation_type")
            norm = self._norm_dim_name(dim_raw)
            key = (norm, impl or None)
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out

    def _ensure_timeframe(self, rec: Dict[str, Any]) -> None:
        if "implementation_time" in rec and "timeframe" not in rec:
            rec["timeframe"] = rec["implementation_time"]

    def _enhance_with_kb(self, analysis: Dict[str, Any]) -> None:
        """Attach KB-based evidence and ensure diverse sources; keep behaviour identical."""
        try:
            logger.info("Enhancing recommendations with knowledge base integration")
            analysis["knowledge_base_integration"] = True
            analysis["kb_references"] = []

            # Prefer LiteratureRepository for up-to-date, incremental view
            kb_documents: List[Dict[str, Any]] = []
            used_backend = "repository"
            try:
                if self.lit_repo is None and LiteratureRepository is not None:
                    self.lit_repo = LiteratureRepository.get()
                if self.lit_repo is not None:
                    records = self.lit_repo.find_sources()  # returns all when query empty
                    for r in records:
                        pub_date = None
                        if getattr(r, "year", None):
                            pub_date = f"{int(r.year)}-01-01"
                        kb_documents.append({
                            "id": r.document_id,
                            "document_id": r.document_id,
                            "title": r.title,
                            "author": ", ".join(r.authors or []),
                            "publication_date": pub_date,
                            "quality_score": r.quality,
                            "filename": r.filename,
                        })
                else:
                    used_backend = "knowledge_manager"
            except Exception:
                used_backend = "knowledge_manager"

            # Fallback to KnowledgeBaseManager if repository isn't available
            if not kb_documents:
                if self.knowledge_manager is None:
                    raise RuntimeError("No literature backend available")
                kb_documents = self.knowledge_manager.get_all_documents()
                used_backend = "knowledge_manager"

            logger.info("Found %d documents in knowledge base via %s", len(kb_documents), used_backend)

            for i, doc in enumerate(kb_documents):
                logger.debug(
                    "Document %d: ID=%s Title=%s Author=%s PubDate=%s QualityScore=%s",
                    i + 1,
                    doc.get('id', 'Unknown'),
                    doc.get('title', 'Unknown'),
                    doc.get('author', 'Unknown'),
                    doc.get('publication_date', 'Unknown'),
                    doc.get('quality_score', 'Unknown'),
                )

            all_used_citations: List[str] = []

            for rec in analysis["recommendations"]:
                logger.debug("Finding supporting evidence for recommendation: %s", rec.get('title', 'Unknown'))
                supporting_evidence = self._find_supporting_evidence(rec, kb_documents, all_used_citations)
                logger.debug("Found %d supporting evidence items", len(supporting_evidence))
                rec["supporting_evidence"] = supporting_evidence

                if not rec.get("references"):
                    rec["references"] = []

                for evidence in supporting_evidence:
                    citation = evidence.get("citation")
                    reference = {
                        "citation": citation,
                        "source": evidence.get("source"),
                        "year": evidence.get("year"),
                        "relevance": evidence.get("relevance", "high"),
                    }
                    if citation and not any(r.get("citation") == citation for r in rec["references"]):
                        rec["references"].append(reference)
                        if citation not in all_used_citations:
                            all_used_citations.append(citation)

                if not rec.get("sources"):
                    rec["sources"] = []
                for ref in rec.get("references", []):
                    if ref.get("citation") and ref["citation"] not in rec["sources"]:
                        rec["sources"].append(ref["citation"])

                logger.debug("Final sources for recommendation '%s': %s", rec.get('title', 'Unknown'), rec.get('sources', []))

                if not rec["sources"]:
                    self._assign_diverse_sources([rec], self.DEFAULT_SOURCES, used=all_used_citations, sample_up_to=6)

                for ref in rec.get("references", []):
                    if ref.get("citation") and not any(r.get("citation") == ref.get("citation") for r in analysis["kb_references"]):
                        analysis["kb_references"].append(ref)

            logger.info("Enhanced %d recommendations with knowledge base evidence", len(analysis['recommendations']))
            logger.info("Added %d unique references from knowledge base", len(analysis['kb_references']))
            logger.info("Total unique citations used across recommendations: %d", len(all_used_citations))

        except Exception as e:
            logger.warning("Error querying knowledge base: %s", str(e))
            analysis["knowledge_base_integration"] = False
            # Fallback to diverse sources assignment
            self._assign_diverse_sources(analysis["recommendations"], self.DEFAULT_SOURCES)

    def _assign_diverse_sources(
        self,
        recs: List[Dict[str, Any]],
        default_sources: List[str],
        *,
        used: Optional[List[str]] = None,
        sample_up_to: int = 3,
    ) -> None:
        """Assign diverse placeholder sources to recommendations that lack them.

        Arguments:
            recs: recommendations to mutate
            default_sources: pool of default citations
            used: optional list to track already used citations across recs
            sample_up_to: max number of sources to sample per recommendation (default 3, earlier path used 6)
        """
        import random

        if used is None:
            used = []

        for i, rec in enumerate(recs):
            if rec.get("sources"):
                continue
            start_idx = (i * 2) % len(default_sources)
            pool = [s for s in default_sources if s not in used] or default_sources
            # Keep behaviour similar: deterministic slice or random sample in KB path
            if sample_up_to <= 3:
                rec_sources = [pool[(start_idx + j) % len(pool)] for j in range(min(3, len(pool)))]
            else:
                rec_sources = random.sample(pool, min(sample_up_to, len(pool)))
            rec["sources"] = rec_sources
            for s in rec_sources:
                if s not in used:
                    used.append(s)
    
    def _find_supporting_evidence(self, recommendation: Dict[str, Any], kb_documents: List[Dict[str, Any]], used_citations: List[str] = None) -> List[Dict[str, Any]]:
        """
{{ ... }}
        # Try to extract year from publication date
        pub_date = doc.get("publication_date", "")
        if pub_date:
            year_match = YEAR_REGEX.search(pub_date)
            if year_match:
                doc_year = year_match.group(0)
        Find supporting evidence for a recommendation from knowledge base documents.
        Prioritizes diverse sources that haven't been used in other recommendations.
        
        Args:
            recommendation: The recommendation to find evidence for
            kb_documents: List of knowledge base documents
            used_citations: List of citations already used in other recommendations (to promote diversity)
            
        Returns:
            List of supporting evidence items with source information
        """
        supporting_evidence = []
        min_evidence_count = 4  # Ensure at least 4 citations per recommendation for better diversity
        
        # Initialise used_citations if not provided
        if used_citations is None:
            used_citations = []
        
        # Extract key terms from the recommendation
        rec_title = recommendation.get("title", "").lower()
        rec_desc = recommendation.get("description", "").lower()
        rec_rationale = recommendation.get("rationale", "").lower()
        rec_dimension = recommendation.get("dimension", "").lower()
        rec_implementation_steps = recommendation.get("implementation_steps", [])
        
        # Keywords to search for based on the recommendation dimension
        dimension_keywords = {
            "accountability and governance": ["accountability", "governance", "compliance", "oversight", "regulation", "audit", "responsibility", "framework", "policy", "standard", "guideline"],
            "transparency and explainability": ["transparency", "explainability", "explainable", "interpretable", "disclosure", "clarity", "understandable", "communication", "documentation", "explanation", "report"],
            "human agency and oversight": ["human agency", "oversight", "control", "autonomy", "intervention", "supervision", "human-in-the-loop", "decision-making", "authority", "review", "approval"],
            "inclusiveness and fairness": ["inclusiveness", "fairness", "bias", "discrimination", "equity", "accessibility", "diversity", "representation", "inclusion", "equality", "justice"]
        }
        
        # Get keywords for this recommendation's dimension
        keywords = dimension_keywords.get(rec_dimension.lower(), [])
        
        # Add keywords from the recommendation title, description, and rationale
        for text in [rec_title, rec_desc, rec_rationale]:
            # Extract significant words (3+ chars)
            words = [w for w in text.split() if len(w) >= 3 and w not in ["the", "and", "for", "with", "that"]]
            keywords.extend(words[:5])  # Add up to 5 significant words
        
        # Add keywords from implementation steps
        for step in rec_implementation_steps:
            step_lower = step.lower()
            # Extract significant words from each step
            words = [w for w in step_lower.split() if len(w) >= 3 and w not in ["the", "and", "for", "with", "that"]]
            keywords.extend(words[:2])  # Add up to 2 significant words per step
        
        # Remove duplicates and ensure all keywords are strings
        keywords = [str(k) for k in keywords]
        keywords = list(set(keywords))
        
        # Score each document based on relevance to this recommendation
        scored_documents = []
        for doc in kb_documents:
            # Skip if document has no content - but first try to load content from file
            if not doc.get("content"):
                try:
                    # Attempt to read content from the file
                    file_path = os.path.join(self.knowledge_manager.knowledge_base_path, doc.get("filename", ""))
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            doc["content"] = f.read()
                    else:
                        logger.warning("Could not find file for document %s: %s", doc.get('id', 'Unknown'), file_path)
                        continue
                except Exception as e:
                    logger.warning("Could not read content for document %s: %s", doc.get('id', 'Unknown'), str(e))
                    continue
                
            doc_id = doc.get("id", "")
            doc_title = doc.get("title", "").lower()
            doc_content = doc.get("content", "").lower()
            doc_author = doc.get("author", "Unknown")
            doc_year = "Unknown"
            
            # Try to extract year from publication date
            pub_date = doc.get("publication_date", "")
            if pub_date:
                year_match = re.search(YEAR_REGEX, pub_date)
                if year_match:
                    doc_year = year_match.group(0)
            
            # Format citation in APA style - skip documents with missing metadata
            if not doc_author or doc_author == "Unknown":
                logger.info("Skipping document with missing author: %s", doc.get('title', 'Unknown title'))
                continue
                
            if doc_year != "Unknown":
                citation = f"{doc_author} ({doc_year})"
            else:
                # Try to extract year from filename or other metadata if available
                if doc.get("filename"):
                    year_match = re.search(YEAR_REGEX, doc.get("filename", ""))
                    if year_match:
                        doc_year = year_match.group(0)
                        citation = f"{doc_author} ({doc_year})"
                    else:
                        citation = f"{doc_author} (n.d.)"
                else:
                    citation = f"{doc_author} (n.d.)"
                
            # Give strong preference to citations not already used elsewhere
            diversity_bonus = 5.0 if citation not in used_citations else 0.0
                
            # Calculate relevance score using both keyword matching and semantic similarity
            relevance_score = 0
            confidence_score = 0.0
            
            # Keyword-based scoring (traditional method)
            keyword_score = 0
            
            # Title match bonus
            for keyword in keywords:
                if keyword in doc_title:
                    keyword_score += 2  # Higher weight for title matches
            
            # Content match
            content_matches = 0
            for keyword in keywords:
                if doc_content and keyword in doc_content:
                    content_matches += 1
            
            # Add score based on content matches (with diminishing returns)
            if content_matches > 0:
                keyword_score += min(3, content_matches)
            
            relevance_score += keyword_score
            
            # Semantic similarity scoring (enhanced method)
            semantic_score = 0
            if self.embedder and doc_content:
                try:
                    # Create recommendation context for semantic comparison
                    rec_context = f"{rec_title}. {rec_desc}. {rec_rationale}"
                    
                    # Extract meaningful content from document (first 1000 chars to avoid token limits)
                    doc_excerpt = doc_content[:1000]
                    
                    # Calculate semantic similarity
                    rec_embedding = self.embedder.encode([rec_context])
                    doc_embedding = self.embedder.encode([doc_excerpt])
                    
                    # Cosine similarity
                    similarity = np.dot(rec_embedding[0], doc_embedding[0]) / (
                        np.linalg.norm(rec_embedding[0]) * np.linalg.norm(doc_embedding[0])
                    )
                    
                    # Convert similarity to relevance score (0-10 scale)
                    semantic_score = max(0, similarity * 10)
                    
                    # Confidence score based on semantic similarity
                    confidence_score = min(1.0, max(0.0, similarity))
                    
                    logger.debug(f"Semantic similarity for {doc.get('title', 'Unknown')}: {similarity:.3f}")
                    
                except Exception as e:
                    logger.debug(f"Semantic scoring failed for document {doc_id}: {e}")
                    semantic_score = 0
                    confidence_score = 0.0
            
            # Combine keyword and semantic scores (weighted average)
            if semantic_score > 0:
                relevance_score = (keyword_score * 0.4) + (semantic_score * 0.6)  # Favor semantic similarity
            else:
                relevance_score = keyword_score  # Fallback to keyword-only
                confidence_score = min(1.0, keyword_score / 10.0)  # Estimate confidence from keywords
                
            # Add diversity bonus to promote citation diversity
            relevance_score += diversity_bonus
            
            # If document seems relevant, add it to scored documents
            if relevance_score > 0:
                scored_documents.append({
                    "document_id": doc_id,
                    "title": doc.get("title", ""),
                    "citation": citation,
                    "source": doc.get("filename", ""),
                    "year": doc_year,
                    "quality_score": doc.get("quality_score", 0),
                    "match_score": relevance_score,
                    "confidence_score": confidence_score,
                    "has_semantic_score": semantic_score > 0
                })
        
        # Sort by relevance score, confidence, and diversity (prioritise high confidence, unused citations)
        scored_documents.sort(key=lambda x: (
            -x.get("match_score", 0),        # Higher relevance first
            -x.get("confidence_score", 0),   # Higher confidence first
            0 if x.get("citation") in used_citations else 1,  # Unused citations first
            -x.get("quality_score", 0)       # Higher quality first
        ))
        
        # Debug: Print scored documents with enhanced metrics
        logger.debug("Found %d potentially relevant documents for recommendation", len(scored_documents))
        for i, doc in enumerate(scored_documents[:5]):
            logger.debug("  Document %d: %s - Score: %.2f - Confidence: %.2f - Semantic: %s - Citation: %s", 
                        i+1, 
                        doc.get('title', 'Unknown')[:50] + '...' if len(doc.get('title', '')) > 50 else doc.get('title', 'Unknown'),
                        doc.get('match_score', 0), 
                        doc.get('confidence_score', 0),
                        'Yes' if doc.get('has_semantic_score', False) else 'No',
                        doc.get('citation', 'Unknown'))
        
        # Select diverse sources - prioritise different authors and unused citations
        authors_selected = set()
        for doc in scored_documents:
            citation = doc.get("citation", "")
            author = citation.split(" (")[0] if " (" in citation else citation
            
            # Track if this citation is already used in other recommendations
            citation_used_elsewhere = citation in used_citations
            
            # Apply confidence threshold - only include sources with reasonable confidence
            confidence_score = doc.get("confidence_score", 0)
            if confidence_score < 0.15:  # Minimum confidence threshold
                continue
                
            # Prioritize diverse authors (max 1 citation per author if already used elsewhere)
            max_per_author = 1 if citation_used_elsewhere else 2
            if len([e for e in supporting_evidence if e.get("citation", "").startswith(author)]) < max_per_author:
                # Determine relevance level using both match score and confidence
                relevance_score = doc.get("match_score", 0)
                confidence_score = doc.get("confidence_score", 0)
                
                # Enhanced relevance classification
                if relevance_score >= 5 and confidence_score >= 0.4:
                    relevance = "high"
                elif relevance_score >= 3 and confidence_score >= 0.25:
                    relevance = "medium"
                else:
                    relevance = "low"
                
                doc["relevance"] = relevance
                supporting_evidence.append(doc)
                authors_selected.add(author)
                
                # Add this citation to the used citations list to track across recommendations
                if citation and citation not in used_citations:
                    used_citations.append(citation)
                
                # Stop once we have enough diverse sources
                if len(supporting_evidence) >= min_evidence_count and len(authors_selected) >= 3:
                    break
        
        # If we still don't have enough evidence, add more documents regardless of author diversity
        if len(supporting_evidence) < min_evidence_count:
            # Get documents not already included
            remaining_docs = [doc for doc in scored_documents if not any(e.get("document_id") == doc.get("document_id") for e in supporting_evidence)]
            
            # Sort remaining docs to prioritize unused citations and higher quality scores
            # Give higher priority to citations not used elsewhere (reverse=True means higher values first)
            remaining_docs.sort(key=lambda x: (1 if x.get("citation") not in used_citations else 0, x.get("quality_score", 0)), reverse=True)
            
            # Debug: Print remaining docs
            logger.debug("Adding more documents to reach minimum evidence count (%d). Currently have %d", min_evidence_count, len(supporting_evidence))
            for i, doc in enumerate(remaining_docs[:3]):
                logger.debug("  Additional document %d: %s - Quality: %s - Citation: %s", i+1, doc.get('title', 'Unknown'), doc.get('quality_score', 0), doc.get('citation', 'Unknown'))
            
            # Add top documents until we reach minimum count
            for doc in remaining_docs:
                if len(supporting_evidence) >= min_evidence_count:
                    break
                
                # Determine relevance level
                relevance_score = doc.get("match_score", 0)
                relevance = "medium"
                if relevance_score >= 5:
                    relevance = "high"
                elif relevance_score <= 2:
                    relevance = "low"
                
                doc["relevance"] = relevance
                supporting_evidence.append(doc)
                
                # Track this citation as used
                citation = doc.get("citation", "")
                if citation and citation not in used_citations:
                    used_citations.append(citation)
        
        # If we still don't have enough evidence, add documents from the knowledge base
        # regardless of keyword matching
        if len(supporting_evidence) < min_evidence_count:
            # Get documents not already included
            used_ids = {e.get("document_id") for e in supporting_evidence}
            remaining_docs = [doc for doc in kb_documents if doc.get("id") and doc.get("id") not in used_ids]
            
            # Debug: Print fallback docs
            logger.debug("Using fallback method to add documents. Need %d more documents", min_evidence_count - len(supporting_evidence))
            logger.debug("Found %d unused documents in knowledge base", len(remaining_docs))
            
            # Sort by quality score if available
            remaining_docs.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        # Debug: Print final supporting evidence
        logger.debug("Final supporting evidence count: %d", len(supporting_evidence))
        for i, evidence in enumerate(supporting_evidence):
            logger.debug("  Evidence %d: %s - Relevance: %s", i+1, evidence.get('citation', 'Unknown'), evidence.get('relevance', 'Unknown'))
            
        return supporting_evidence

    def _analyze_institution_context(self, themes: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        t = (text or "").lower()
        score_research = sum(1 for k in ["research", "publication", "graduate", "phd", "faculty"] if k in t)
        score_teaching = sum(1 for k in ["teaching", "undergraduate", "classroom", "pedagogy", "student"] if k in t)
        score_technical = sum(1 for k in ["engineering", "technical", "institute", "laboratory", "computing"] if k in t)
        if score_research >= max(score_teaching, score_technical):
            itype = "research_university"
        elif score_teaching >= max(score_research, score_technical):
            itype = "teaching_focused"
        else:
            itype = "technical_institute"
        return {"type": itype}

    def _detect_existing_policies(self, text: str) -> Dict[str, bool]:
        t = (text or "").lower()
        return {
            "disclosure_requirements": any(k in t for k in ["disclose", "acknowledge", "cite ai", "disclosure"]),
            "approval_processes": any(k in t for k in ["approval", "approved", "faculty approval", "committee approval", "authorisation", "authorization"]),
        }

    def _generate_contextual_recommendation(
        self,
        dimension: str,
        institution_context: Dict[str, Any],
        implementation_type: str,
        priority: str,
        current_score: float,
        gap_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        dim_title = dimension.replace("_", " ").title()
        context_type = institution_context.get("type", "university").replace("_", " ")
        title = f"{dim_title}: {('Enhance' if implementation_type=='enhancement' else 'Implement')} Policy Measures"
        description = (
            f"Develop and {('enhance' if implementation_type=='enhancement' else 'implement')} {dim_title.lower()} measures "
            f"appropriate for a {context_type} context."
        )
        rationale = f"Address identified gap ({gap_details.get('type','gap')}) with current score {current_score}%."
        impl_time = IMPLEMENTATION_TIME_MEDIUM if priority == "high" else IMPLEMENTATION_TIME_2_3
        rec = {
            "id": f"{dimension[:4]}-{priority[:1]}-{int(max(1, 100-current_score))}",
            "title": title,
            "description": description,
            "rationale": rationale,
            "priority": priority,
            "dimension": dimension,
            "implementation_time": impl_time,
            "implementation_steps": [
                "Assess current state and gaps",
                "Define objectives and success metrics",
                "Engage stakeholders (faculty, students, staff)",
                "Roll out in phases with feedback loops",
            ],
            "sources": [],
        }
        return rec


class RecommendationEngine:
    """Integration wrapper combining analysis and recommendation generation.

    Exposes a single generate_recommendations() API used by integration tests.
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """Initialise the recommendation engine.
        
        Args:
            knowledge_base_path: Path to the knowledge base directory (required)
        """
        if not knowledge_base_path:
            logger.error("No knowledge base path provided to RecommendationEngine")
            raise ValueError("Knowledge base path is required")
            
        self.knowledge_base_path = knowledge_base_path
        self.generator = RecommendationGenerator(knowledge_base_path=knowledge_base_path)
        
        # Verify knowledge base is available
        if not hasattr(self.generator, 'knowledge_base_available') or not self.generator.knowledge_base_available:
            logger.error("Failed to initialise with knowledge base at: %s", knowledge_base_path)
            raise ValueError(
                "Cannot initialise recommendation engine - knowledge base is not available. "
                "Please check the knowledge base configuration and try again."
            )
            
        # Initialize analyzer for coverage analysis
        self.analyzer = EthicalFrameworkAnalyzer()

    def generate_recommendations(
        self,
        themes: List[Dict[str, Any]] | None,
        classification: Dict[str, Any] | str,
        text: str,
        analysis_id: str | None = None,
    ) -> Dict[str, Any]:
        """Run coverage analysis and produce contextual recommendations.

        Returns:
            Dict containing analysis results with keys: analysis_metadata, coverage_analysis, 
            recommendations, summary.
            
        Raises:
            ValueError: If knowledge base is not available or text is empty
        """
        if not text.strip():
            raise ValueError("Policy text cannot be empty")
            
        if not hasattr(self, 'generator') or not hasattr(self.generator, 'knowledge_base_available') or not self.generator.knowledge_base_available:
            raise ValueError(
                "Cannot generate recommendations - knowledge base is not available. "
                "Please try again later or contact the system administrator."
            )
        # Verify knowledge base is available before proceeding
        if not hasattr(self, 'generator') or not hasattr(self.generator, 'knowledge_base_available') or not self.generator.knowledge_base_available:
            raise ValueError(
                "Cannot generate recommendations - knowledge base is not available. "
                "Please try again later or contact the system administrator."
            )
            
        # Normalise inputs
        themes = themes or []
        classification_str = (
            classification.get("classification")
            if isinstance(classification, dict)
            else str(classification or "")
        ) or "Moderate"

        try:
            # Coverage analysis
            coverage = self.analyzer.analyze_coverage(themes, text)

            # Identify gaps based on coverage and classification
            gaps = self.analyzer.identify_gaps(coverage, classification_str)

            # Generate recommendations - this will raise ValueError if knowledge base is unavailable
            recs = self.generator.generate_recommendations(
                gaps=gaps,
                classification=classification_str,
                themes=themes,
                text=text,
            )
        except ValueError as e:
            if "knowledge base" in str(e).lower():
                raise ValueError(
                    "Cannot generate recommendations - knowledge base is not available. "
                    "Please try again later or contact the system administrator."
                ) from e
            raise

        # Ensure default tags for I-U-F matrix if absent
        for r in recs:
            try:
                if "impact" not in r:
                    r["impact"] = "high" if (r.get("priority", "").lower() == "high") else "medium"
                if "urgency" not in r:
                    r["urgency"] = (r.get("priority") or "medium").lower()
                if "feasibility" not in r:
                    # Slightly easier for documentation/transparency items
                    dim = (r.get("dimension") or "").lower()
                    r["feasibility"] = "high" if any(k in dim for k in ["transparency", "documentation"]) else "medium"
            except Exception:
                pass

        # Build metadata and summary
        from datetime import datetime, timezone

        scores = [dim.get("score", 0.0) for dim in coverage.values()] if isinstance(coverage, dict) else []
        avg_coverage = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Normalise academic sources labels like "UNESCO (2023)" -> "UNESCO 2023"
        raw_sources = list(getattr(self.generator, "DEFAULT_SOURCES", []))
        try:
            normalised_sources = [re.sub(r"\s*\((\d{4})\)", r" \1", s) for s in raw_sources]
        except Exception:
            normalised_sources = raw_sources

        # Build narrative (template-based, UK style, grounded in sources)
        narrative_html, narrative_meta = self._generate_narrative(
            recommendations=recs,
            themes=themes,
            classification=classification_str,
            coverage=coverage,
            sources=normalised_sources,
            text=text,
            analysis_id=analysis_id or "unknown",
        )

        # Compute extended metrics (confidence, stakeholders, risk-benefit)
        extended = {}
        try:
            repo = getattr(self.generator, "lit_repo", None)
            if compute_confidence is not None:
                extended["confidence"] = compute_confidence(
                    themes=themes,
                    classification=classification if isinstance(classification, dict) else {"confidence": 0},
                    text_length=len(text or ""),
                    repo=repo,
                )
            if assess_stakeholders_impact is not None:
                extended["stakeholders"] = assess_stakeholders_impact(themes=themes)
            if assess_risk_benefit is not None:
                extended["risk_benefit"] = assess_risk_benefit(themes=themes)

            # Optional: augment via advanced analysis engine (feature-flagged)
            use_advanced = os.environ.get("FEATURE_ADVANCED_ENGINE", "0").lower() in {"1", "true", "yes", "on"}
            if use_advanced and PolicyAnalysisEngine is not None:
                try:
                    engine = PolicyAnalysisEngine()
                    context_params = {
                        "themes": themes,
                        "classification": classification if isinstance(classification, dict) else {"classification": str(classification or "")},
                        "organization_profile": {},
                        "analysis_mode": os.environ.get("ANALYSIS_MODE", "default"),
                    }
                    adv = engine.analyze_policy(policy_text=text or "", context_params=context_params)
                    # Merge where applicable without overwriting existing keys unless present
                    if isinstance(adv, dict):
                        # Confidence
                        adv_conf = adv.get("confidence")
                        if adv_conf and isinstance(adv_conf, dict):
                            extended["confidence"] = adv_conf
                        # Dimensions
                        dims = adv.get("dimensions") or {}
                        if isinstance(dims, dict):
                            if dims.get("stakeholder_impact"):
                                extended["stakeholders"] = dims.get("stakeholder_impact")
                            if dims.get("risk_benefit"):
                                extended["risk_benefit"] = dims.get("risk_benefit")
                        # Context (surfaced for templates if needed)
                        if adv.get("context"):
                            extended["context"] = adv.get("context")
                except Exception:
                    # Do not fail the flow if advanced engine errors
                    pass
        except Exception:
            pass

        result = {
            "analysis_metadata": {
                "analysis_id": analysis_id or "unknown",
                # Use timezone-aware UTC timestamp and keep 'Z' suffix for compatibility
                "generated_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "framework_version": "1.0",
                "methodology": "EthicalFrameworkAnalyzer + Contextual RecommendationGenerator + LiteratureRepository-backed metrics",
                "academic_sources": normalised_sources,
            },
            "coverage_analysis": coverage,
            "recommendations": recs,
            "summary": {
                "total_recommendations": len(recs) if isinstance(recs, list) else 0,
                "overall_coverage": avg_coverage,
            },
            "narrative": {
                "html": narrative_html,
                "style": narrative_meta.get("style"),
                "seed": narrative_meta.get("seed"),
                "sources_used": narrative_meta.get("sources_used", []),
            },
            # Extended metrics surfaced for templates
            "analysis": {
                "analysis_id": analysis_id or "unknown",
                "classification": classification_str,
                "confidence_pct": extended.get("confidence", {}).get("overall_pct") if extended else None,
                "confidence_factors": extended.get("confidence", {}).get("factors") if extended else None,
                "stakeholders": extended.get("stakeholders") if extended else None,
                "risk_benefit": extended.get("risk_benefit") if extended else None,
            },
        }

        return result

    def _generate_narrative(
        self,
        recommendations: List[Dict[str, Any]] | None,
        themes: List[Dict[str, Any]] | None,
        classification: str,
        coverage: Dict[str, Any] | None,
        sources: List[str] | None,
        text: str,
        analysis_id: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Generate a UK-style narrative explaining the recommendations.

        Template-based (no LLM). Ensures variability using a deterministic seed from analysis_id.
        Uses British English spelling and cites knowledge base sources inline.
        Returns HTML and metadata.
        """
        recommendations = recommendations or []
        themes = themes or []
        sources = sources or []

        # Derive seed for variability (stable per analysis, varied across analyses)
        seed = sum(ord(c) for c in (analysis_id or "")) % 10_000
        rng = random.Random(seed)

        # Pick style variant
        tones = [
            ("Formal", "measured", "considered"),
            ("Warm", "supportive", "collaborative"),
            ("Pragmatic", "practical", "implementable"),
        ]
        tone = rng.choice(tones)
        tone_name, tone_adj1, tone_adj2 = tone

        # Headline and openers
        openings = [
            "This analysis suggests a coherent programme of work, balancing ambition with due diligence.",
            "The findings point towards a thoughtfully sequenced programme that is both credible and proportionate.",
            "Our review indicates a balanced programme of improvement, attentive to institutional realities.",
        ]
        opening = rng.choice(openings)

        # Executive overview (2–3 sentences)
        class_map = {
            "Restrictive": "a cautious baseline that would benefit from carefully broadened provisions",
            "Moderate": "a well-balanced baseline that invites clearer operational guidance",
            "Permissive": "an enabling baseline that warrants stronger safeguards and documentation",
        }
        class_phrase = class_map.get(classification, "a balanced baseline that warrants clearer articulation")

        # Extract top themes
        top_themes = [t.get("name", "") for t in themes[:3] if isinstance(t, dict)]
        theme_str = ", ".join([t for t in top_themes if t]) or "governance, transparency and inclusion"

        # Select 3–5 sources to cite inline (more variety), keep deterministic order (British English throughout)
        rng.shuffle(sources)
        cite_used = sources[:5]
        cite_inline = "; ".join(cite_used)

        # Build key actions prioritising lowest coverage dimensions (British spelling)
        key_actions: list[str] = []
        # Normalise dimension names and provide polished labels + tailored actions
        def _norm_dim_name(n: str) -> str:
            n = (n or "").strip()
            low = n.lower().replace(" ", "_")
            mapping = {
                "accountability": "Accountability",
                "transparency": "Transparency",
                "inclusiveness": "Inclusiveness",
                "inclusion": "Inclusiveness",
                "human_agency": "Human Agency",
                "agency": "Human Agency",
                "data_governance": "Data Governance",
                "governance": "Data Governance",
                "assessment": "Assessment",
            }
            return mapping.get(low, n.title())

        dim_actions = {
            "Accountability": "Define clear ownership and decision rights; publish a RACI and escalation routes.",
            "Transparency": "Publish a concise disclosure template and exemplar for staff/students; record disclosures centrally.",
            "Inclusiveness": "Co‑design guidance with student reps and accessibility leads; include reasonable adjustments.",
            "Human Agency": "Require meaningful human oversight sign‑off for high‑impact uses; document interventions.",
            "Data Governance": "Introduce a register of datasets, provenance and retention schedules; assign data stewards.",
            "Assessment": "Document permitted/forbidden AI uses per assessment; align with briefs and integrity policy.",
        }

        # KPIs per dimension (micro-metrics)
        dim_kpis = {
            "Accountability": [
                "RACI published and owned (Yes/No)",
                "% decisions with documented owner",
                "# escalations resolved within 10 working days",
            ],
            "Transparency": [
                "% modules/assessments with disclosure requirements",
                "% staff/student disclosures submitted",
                "Median time to update public-facing guidance (days)",
            ],
            "Inclusiveness": [
                "% guidance with accessibility check passed",
                "# consultations with SU/EDI completed",
                "% reasonable adjustments incorporated",
            ],
            "Human Agency": [
                "% high‑impact uses with sign‑off recorded",
                "# interventions documented per term",
                "% exceptions reviewed at governance group",
            ],
            "Data Governance": [
                "% active datasets registered",
                "% datasets with retention schedule",
                "# data stewards assigned",
            ],
            "Assessment": [
                "% briefs linked to AI use matrix",
                "% suspected cases handled under integrity policy",
                "Median appeal turnaround (days)",
            ],
        }

        def _target_for(score: float) -> tuple[int, str]:
            # Return (target percentage, timeframe)
            if score < 20:
                return 60, "90 days"
            if score < 40:
                return 70, "120 days"
            if score < 60:
                return 80, "180 days"
            return 85, "180 days"

        # Deliverables library per dimension (artefacts, owners, acceptance)
        dim_deliverables = {
            "Accountability": {
                "deliverable": "RACI for AI uses and exception path",
                "owner": "PVC Education / Registry",
                "artefact": "1‑page RACI + escalation workflow",
                "acceptance": "Published on policy site; owners acknowledged",
            },
            "Transparency": {
                "deliverable": "AI use disclosure template + exemplars",
                "owner": "Quality Office / Programme Leads",
                "artefact": "Template (docx) + 2 exemplars",
                "acceptance": ">=70% assessments include disclosure requirements",
            },
            "Inclusiveness": {
                "deliverable": "Inclusive guidance with reasonable adjustments",
                "owner": "EDI / Students’ Union",
                "artefact": "Accessible PDF guidance (WCAG 2.1 AA)",
                "acceptance": "Consulted with SU; accessibility check passed",
            },
            "Human Agency": {
                "deliverable": "Oversight sign‑off form for high‑impact uses",
                "owner": "Module Leaders / Ethics Committee",
                "artefact": "1‑page sign‑off form + register",
                "acceptance": ">=90% of high‑impact uses recorded with sign‑off",
            },
            "Data Governance": {
                "deliverable": "Register of datasets and retention schedules",
                "owner": "Information Governance / Library",
                "artefact": "Dataset register (sheet) + retention table",
                "acceptance": ">=80% active datasets registered",
            },
            "Assessment": {
                "deliverable": "Matrix of permitted/forbidden AI uses per assessment",
                "owner": "Programme Leads / Quality",
                "artefact": "1‑page matrix linked to briefs",
                "acceptance": ">=80% briefs linked to matrix",
            },
        }

        # Derive gaps from coverage (if available)
        gap_items: list[tuple[str, float]] = []
        if isinstance(coverage, dict):
            for dim, info in coverage.items():
                try:
                    score = float(info.get("score", 0))
                except Exception:
                    score = 0.0
                gap_items.append((str(dim), score))
            gap_items.sort(key=lambda x: x[1])

        # Use either gaps from coverage or fall back to existing recs
        if gap_items:
            # Show up to 8 weakest dimensions in key actions to avoid artificial limit of 4
            for dim_raw, score in gap_items[:8]:
                dim = _norm_dim_name(dim_raw)
                action_text = dim_actions.get(dim, "Establish lightweight controls and documentation appropriate to risk.")
                target, timeframe = _target_for(score)
                key_actions.append(
                    f"<li><strong>{dim}.</strong> Raise coverage from {score:.0f}% to {target}% in {timeframe}: {action_text}</li>"
                )
        else:
            rng.shuffle(recommendations)
            # Show up to 8 recommendations when coverage gaps are not available
            for rec in recommendations[:8]:
                title = rec.get("title") or rec.get("dimension") or "Recommendation"
                rationale = rec.get("rationale") or ""
                impl = rec.get("implementation_steps", [])
                first_step = impl[0] if impl else "Define scope and success measures"
                key_actions.append(f"<li><strong>{title}.</strong> {first_step}. <em>{rationale}</em></li>")
            if not key_actions:
                key_actions.append("<li><strong>Establish an AI governance committee.</strong> Define remit, membership and reporting lines.</li>")

        # Build deliverables list for top 2 weakest dimensions
        deliverables_html = ""
        top2 = gap_items[:2] if gap_items else []
        if top2:
            items = []
            for dim_raw, score in top2:
                dim = _norm_dim_name(dim_raw)
                d = dim_deliverables.get(dim, {
                    "deliverable": "Lightweight controls and guidance",
                    "owner": "Policy Owner",
                    "artefact": "1‑page guidance",
                    "acceptance": "Published and communicated",
                })
                # Example filenames to make it actionable
                example_file = {
                    "Accountability": "AI_Governance_RACI_v1.pdf",
                    "Transparency": "Disclosure_Template_v1.docx",
                    "Inclusiveness": "Inclusive_Guidance_v1.pdf",
                    "Human Agency": "Human_Oversight_Signoff_v1.docx",
                    "Data Governance": "Dataset_Register_v1.xlsx",
                    "Assessment": "Assessment_AI_Use_Matrix_v1.xlsx",
                }.get(dim, "Policy_Artefact_v1.docx")
                items.append(
                    f"<li><strong>{dim}.</strong> <em>{d['deliverable']}</em> — Owner: {d['owner']}; Artefact: {d['artefact']} (<code>{example_file}</code>); Acceptance: {d['acceptance']}.</li>"
                )
            deliverables_html = "<ul>" + "".join(items) + "</ul>"

        # KPI list for top three weakest dimensions
        kpis_html = ""
        top3 = gap_items[:3] if gap_items else []
        if top3:
            kpi_items = []
            for dim_raw, _ in top3:
                dim = _norm_dim_name(dim_raw)
                kpis = dim_kpis.get(dim, ["% policy tasks completed", "# issues resolved", "SLA adherence (%)"])
                bullets = "".join([f"<li>{k}</li>" for k in kpis])
                kpi_items.append(f"<li><strong>{dim}.</strong><ul>{bullets}</ul></li>")
            kpis_html = "<ul>" + "".join(kpi_items) + "</ul>"

        # Quick wins (30 days)
        quick_wins = [
            "Publish disclosure template and 2 exemplars; add link to all new briefs.",
            "Stand‑up dataset register skeleton; capture at least the top 10 active datasets.",
            "Introduce human oversight sign‑off for one high‑impact pilot and review outcomes.",
        ]
        quick_wins_html = "<ul>" + "".join([f"<li>{q}</li>" for q in quick_wins]) + "</ul>"

        # Risks and mitigations (templated)
        risks = [
            ("Scope creep", "Use phased milestones with entry/exit criteria to maintain discipline."),
            ("Stakeholder fatigue", "Adopt lightweight consultations and clear communication points."),
            ("Documentation burden", "Provide concise templates and exemplars to cut overheads."),
        ]
        rng.shuffle(risks)
        risks_html = "".join([f"<li><strong>{r}.</strong> {m}</li>" for r, m in risks[:2]])

        # Implementation framing
        impl_phrases = [
            "pilot in one faculty before institution-wide scaling",
            "sequence work over two terms with a formal mid-point review",
            "adopt a light-touch governance cadence (monthly) with quarterly deep-dives",
        ]
        impl_choice = rng.choice(impl_phrases)

        # Compose HTML (British spelling: organisation, programme)
        html = f"""
        <div class=\"narrative-card\">
          <h2>📝 Policy Implementation Brief</h2>
          <p><strong>Executive overview.</strong> The policy reflects {class_phrase}. {opening} The brief below sets out a {tone_adj1}, {tone_adj2} path grounded in current evidence ({cite_inline}).</p>
          <hr class=\"narrative-sep\" />

          <h3>What we recommend</h3>
          <ul>
            {''.join(key_actions)}
          </ul>
          <hr class=\"narrative-sep\" />

          <h3>Why it matters</h3>
          <p>Across the themes of {theme_str}, international guidance emphasises clear accountability, transparent documentation and meaningful human oversight. Addressing the lowest‑scoring areas first delivers the greatest risk reduction and improves staff and student confidence. The approach aligns with sector guidance cited above and the institution’s overall classification.</p>
          <hr class=\"narrative-sep\" />

          <h3>How to implement</h3>
          <p>Start small and build confidence: {impl_choice}. Assign ownership within the organisation, publish concise documentation, and track measurable outcomes. Suggested metrics: policy disclosure coverage (%), audit completion rate (%), training completion rate (%), number of appeals resolved within target. Report progress monthly and conduct a formal mid‑point review.</p>

          <h3>Key metrics</h3>
          {kpis_html if kpis_html else '<p>Key metrics will be confirmed during the baseline audit.</p>'}

          <h3>Phased plan</h3>
          <ul>
            <li><strong>Phase 0 (2 weeks).</strong> Appoint owners; publish disclosure template and RACI; agree metrics and targets.</li>
            <li><strong>Phase 1 (0–3 months).</strong> Baseline audit; fix critical gaps in {', '.join([_norm_dim_name(d) for d, _ in gap_items[:2]]) if gap_items else 'priority areas'}; launch training pilots.</li>
            <li><strong>Phase 2 (3–6 months).</strong> Scale disclosures and oversight; embed data register; integrate with assessment briefs.</li>
            <li><strong>Phase 3 (6–9 months).</strong> Evaluate outcomes; refine guidance; publish transparency report.</li>
          </ul>

          <h3>Quick wins (30 days)</h3>
          {quick_wins_html}

          <h3>Deliverables and owners</h3>
          {deliverables_html if deliverables_html else '<p>Deliverables will be confirmed following the baseline audit in Phase 1.</p>'}

          <h3>Ownership and governance</h3>
          <p>Establish an AI governance group (Chair: PVC Education; Members: Registry, Quality, Library, IT, Students’ Union). Use a monthly light‑touch cadence with quarterly deep‑dives. Document decisions and exceptions.</p>

          <h3>Risks and mitigations</h3>
          <ul>
            {risks_html}
          </ul>
          <p><em>Notes on evidence and compliance mapping.</em> Human oversight aligns with EU AI Act Art. 14; transparency obligations align with Art. 52. UNESCO (2021/2023) emphasises governance and inclusion; BERA (2018) frames ethical practice in assessment. Citations: {cite_inline}.</p>

          <div class=\"narrative-footnote\">
            <strong>Notes on evidence.</strong> The pathway above is informed by sector guidance and recent reviews ({cite_inline}). Where appropriate, adapt language to local practice and ensure staff development is resourced.
          </div>
        </div>
        """

        meta = {
            "style": f"UK/{tone_name}",
            "seed": seed,
            "sources_used": cite_used,
        }
        return html, meta
