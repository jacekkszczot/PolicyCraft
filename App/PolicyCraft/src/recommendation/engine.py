import sys
import json
import os
import logging
import re
from typing import Dict, List, Any, Optional, Union
from enum import Enum, auto
from dataclasses import dataclass, field

try:
    from src.literature.knowledge_manager import KnowledgeBaseManager
except ImportError:
    KnowledgeBaseManager = None
    
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
    Analyzes policy text against ethical AI frameworks and provides structured feedback.
    """
    
    def __init__(self, knowledge_manager: Optional[KnowledgeBaseManager] = None):
        """Initialize with an optional knowledge manager for reference lookups."""
        self.knowledge_manager = knowledge_manager
        self.dimensions = list(PolicyDimension)
        
    def analyze_policy(self, policy_text: str, institution_type: str = "university") -> Dict[str, Any]:
        """
        Analyze a policy text and return a structured analysis.
        
        Args:
            policy_text: The text of the policy to analyze
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
        if score >= 0.8:
            strength_level = "strong"
        elif score >= 0.5:
            strength_level = "moderate"
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
    
    # Default sources when knowledge base is not available or fails
    DEFAULT_SOURCES = [
        "BERA (2018)",
        "UNESCO (2021)",
        "JISC (2023)",
        "Selwyn et al. (2020)",
        "Chan & Hu (2023)",
        "Li et al. (2024)",
        "EU AI Act (2024)",
        "UNESCO (2023)"
    ]
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize the recommendation generator.
        
        Args:
            knowledge_base_path: Optional path to the knowledge base directory
        """  
        logger.info("Initializing RecommendationGenerator...")
        
        # Initialize knowledge manager if available
        self.knowledge_manager = None
        if KnowledgeBaseManager is not None and knowledge_base_path:
            try:
                logger.info("Initializing KnowledgeBaseManager with path: %s", knowledge_base_path)
                self.knowledge_manager = KnowledgeBaseManager(knowledge_base_path)
                logger.info("KnowledgeBaseManager initialized successfully")
                
                # Test knowledge base access
                try:
                    doc_count = len(self.knowledge_manager.get_all_documents())
                    logger.info("Knowledge base contains %d documents", doc_count)
                except Exception as e:
                    logger.warning("Could not access knowledge base documents: %s", str(e))
                    
            except Exception as e:
                logger.warning("Could not initialize KnowledgeBaseManager: %s", str(e))
                logger.warning("Knowledge base integration will be disabled")
        else:
            logger.info("Knowledge base integration disabled: No path provided or KnowledgeBaseManager not available")
        
        # Initialize the ethical framework analyzer
        self.analyzer = EthicalFrameworkAnalyzer(self.knowledge_manager)
        
        logger.info("PolicyCraft Recommendation Engine loaded with the following capabilities:")
        logger.info("   • Ethical framework analysis with multi-dimensional scoring")
        logger.info("   • Evidence-based policy recommendations")
        logger.info("   • Knowledge base integration for academic references")
        logger.info("   • Context-aware prioritization of recommendations")
        
    def generate_recommendations(self, policy_text: str = "", institution_type: str = "university", **kwargs) -> Dict[str, Any]:
        """
        Generate recommendations for improving a policy.
        
        Args:
            policy_text: The text of the policy to analyze
            institution_type: Type of institution (university, college, etc.)
            **kwargs: Additional parameters (e.g., analysis_id for tracking)
            
        Returns:
            Dict containing analysis and recommendations
        """
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
        
        # Analyze the policy using the ethical framework
        analysis = self.analyzer.analyze_policy(policy_text, institution_type)
        
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
        
        # Enhance with knowledge base if available
        if self.knowledge_manager:
            self._enhance_with_kb(analysis)
        else:
            analysis["knowledge_base_integration"] = False
            self._assign_diverse_sources(analysis["recommendations"], self.DEFAULT_SOURCES)
        
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

    def _ensure_timeframe(self, rec: Dict[str, Any]) -> None:
        if "implementation_time" in rec and "timeframe" not in rec:
            rec["timeframe"] = rec["implementation_time"]

    def _enhance_with_kb(self, analysis: Dict[str, Any]) -> None:
        """Attach KB-based evidence and ensure diverse sources; keep behaviour identical."""
        try:
            logger.info("Enhancing recommendations with knowledge base integration")
            analysis["knowledge_base_integration"] = True
            analysis["kb_references"] = []

            kb_documents = self.knowledge_manager.get_all_documents()
            logger.info("Found %d documents in knowledge base", len(kb_documents))

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
        
        # Initialize used_citations if not provided
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
                
            # Calculate relevance score
            relevance_score = 0
            
            # Title match bonus
            for keyword in keywords:
                if keyword in doc_title:
                    relevance_score += 2  # Higher weight for title matches
            
            # Content match
            content_matches = 0
            for keyword in keywords:
                if doc_content and keyword in doc_content:
                    content_matches += 1
            
            # Add score based on content matches (with diminishing returns)
            if content_matches > 0:
                relevance_score += min(3, content_matches)
                
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
                    "match_score": relevance_score
                })
        
        # Sort by relevance score (high to low) and then by diversity (unused citations first)
        scored_documents.sort(key=lambda x: (-x.get("match_score", 0), 0 if x.get("citation") in used_citations else 1))
        
        # Debug: Print scored documents
        logger.debug("Found %d potentially relevant documents for recommendation", len(scored_documents))
        for i, doc in enumerate(scored_documents[:5]):
            logger.debug("  Document %d: %s - Score: %s - Citation: %s", i+1, doc.get('title', 'Unknown'), doc.get('match_score', 0), doc.get('citation', 'Unknown'))
        
        # Select diverse sources - prioritize different authors and unused citations
        authors_selected = set()
        for doc in scored_documents:
            citation = doc.get("citation", "")
            author = citation.split(" (")[0] if " (" in citation else citation
            
            # Track if this citation is already used in other recommendations
            citation_used_elsewhere = citation in used_citations
            
            # Prioritize diverse authors (max 1 citation per author if already used elsewhere)
            max_per_author = 1 if citation_used_elsewhere else 2
            if len([e for e in supporting_evidence if e.get("citation", "").startswith(author)]) < max_per_author:
                # Determine relevance level
                relevance_score = doc.get("match_score", 0)
                relevance = "medium"
                if relevance_score >= 5:
                    relevance = "high"
                elif relevance_score <= 2:
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
        self.analyzer = EthicalFrameworkAnalyzer()
        self.generator = RecommendationGenerator(knowledge_base_path=knowledge_base_path)

    def generate_recommendations(
        self,
        themes: List[Dict[str, Any]] | None,
        classification: Dict[str, Any] | str,
        text: str,
        analysis_id: str | None = None,
    ) -> Dict[str, Any]:
        """Run coverage analysis and produce contextual recommendations.

        Returns a dict with keys: analysis_metadata, coverage_analysis, recommendations, summary.
        """
        # Normalise inputs
        themes = themes or []
        classification_str = (
            classification.get("classification")
            if isinstance(classification, dict)
            else str(classification or "")
        ) or "Moderate"

        # Coverage analysis
        coverage = self.analyzer.analyze_coverage(themes, text)

        # Identify gaps based on coverage and classification
        gaps = self.analyzer.identify_gaps(coverage, classification_str)

        # Generate recommendations
        recs = self.generator.generate_recommendations(
            gaps=gaps,
            classification=classification_str,
            themes=themes,
            text=text,
        )

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

        result = {
            "analysis_metadata": {
                "analysis_id": analysis_id or "unknown",
                # Use timezone-aware UTC timestamp and keep 'Z' suffix for compatibility
                "generated_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "framework_version": "1.0",
                "methodology": "EthicalFrameworkAnalyzer + Contextual RecommendationGenerator",
                "academic_sources": normalised_sources,
            },
            "coverage_analysis": coverage,
            "recommendations": recs,
            "summary": {
                "total_recommendations": len(recs) if isinstance(recs, list) else 0,
                "overall_coverage": avg_coverage,
            },
        }

        return result
