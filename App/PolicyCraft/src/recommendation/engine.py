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
        "transparent", "explain", "disclose", "document", "clear", "interpretable", "explainable"
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
                "transparent", "explain", "disclose", "document", "clear", "interpretable", 
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
                "transparency report", "disclosure policy", "explainable ai", 
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
        
        # Count advanced phrase matches with higher weight
        phrase_matches = sum(2 for phrase in advanced_phrases[dimension] if phrase in text_lower)
        
        # Calculate total possible score
        total_possible = len(keywords[dimension]) + (len(advanced_phrases[dimension]) * 2)
        
        # Calculate raw score (0-1 scale)
        raw_score = (keyword_matches + phrase_matches) / (total_possible * 0.6)  # Only need 60% for full score
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
        
        # Get dimension-specific keywords and their presence in the text
        found_keywords = [kw for kw in DIMENSION_KEYWORDS.get(dimension, []) if kw in text_lower]
        missing_keywords = [kw for kw in DIMENSION_KEYWORDS.get(dimension, []) if kw not in text_lower]
        
        # Generate context-aware recommendations based on missing keywords and dimension
        if dimension == PolicyDimension.ACCOUNTABILITY:
            if len(missing_keywords) > len(found_keywords):
                recommendations.append({
                    "id": "acc-001",
                    "title": "Establish Clear Accountability Structures",
                    "description": "Define clear roles and responsibilities for AI governance within your institution.",
                    "rationale": "Clear accountability ensures that AI systems are used responsibly and that there is oversight at all levels.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": IMPLEMENTATION_TIME_MEDIUM,
                    "implementation_steps": [
                        "Form an AI governance committee with representatives from key stakeholders",
                        "Define clear roles and responsibilities for AI oversight",
                        "Establish reporting lines and accountability mechanisms",
                        "Document governance structures in formal policy documents",
                        "Communicate governance framework to all relevant staff"
                    ]
                })
                
            if "audit" not in found_keywords or "monitor" not in found_keywords:
                recommendations.append({
                    "id": "acc-002",
                    "title": "Implement Regular Auditing and Monitoring",
                    "description": "Establish procedures for regular auditing and monitoring of AI systems to ensure compliance with ethical standards.",
                    "rationale": "Regular auditing helps identify issues early and ensures continuous improvement of AI governance.",
                    "priority": "medium",
                    "dimension": dimension.value,
                    "implementation_time": IMPLEMENTATION_TIME_SHORT,
                    "implementation_steps": [
                        "Develop an AI audit framework with clear metrics and benchmarks",
                        "Establish a regular audit schedule (quarterly or bi-annually)",
                        "Create audit templates and checklists for consistency",
                        "Train staff on audit procedures and ethical standards",
                        "Implement reporting mechanisms for audit findings"
                    ]
                })
                
            if "compliance" not in found_keywords:
                recommendations.append({
                    "id": "acc-003",
                    "title": "Develop Compliance Frameworks for AI Systems",
                    "description": "Create comprehensive compliance frameworks that align with regulatory requirements and ethical standards.",
                    "rationale": "Structured compliance frameworks reduce legal risks and ensure ethical AI deployment.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": "4-8 months",
                    "implementation_steps": [
                        "Research relevant AI regulations and ethical standards in your jurisdiction",
                        "Develop a compliance matrix mapping requirements to institutional policies",
                        "Create compliance documentation templates and checklists",
                        "Establish compliance verification procedures for AI systems",
                        "Implement regular compliance reviews and updates as regulations evolve"
                    ]
                })
                
        elif dimension == PolicyDimension.TRANSPARENCY:
            if "explain" not in found_keywords or "explainable" not in found_keywords:
                recommendations.append({
                    "id": "trans-001",
                    "title": "Improve Explainability of AI Systems",
                    "description": "Implement mechanisms to explain AI decisions in clear, non-technical language to affected stakeholders.",
                    "rationale": "Explainable AI builds trust and enables meaningful human oversight of automated decisions.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": IMPLEMENTATION_TIME_MEDIUM,
                    "implementation_steps": [
                        "Audit current AI systems for explainability gaps",
                        "Develop explainability standards for different stakeholder groups",
                        "Implement technical solutions for generating explanations (e.g., LIME, SHAP)",
                        "Create user-friendly interfaces for displaying explanations",
                        "Train staff on communicating AI decisions to non-technical audiences"
                    ]
                })
                
            if "document" not in found_keywords:
                recommendations.append({
                    "id": "trans-002",
                    "title": "Enhance Documentation of AI Systems",
                    "description": "Create comprehensive documentation for all AI systems, including their purpose, limitations, and potential risks.",
                    "rationale": "Thorough documentation enables better understanding and evaluation of AI systems by all stakeholders.",
                    "priority": "medium",
                    "dimension": dimension.value,
                    "implementation_time": IMPLEMENTATION_TIME_SHORT,
                    "implementation_steps": [
                        "Develop documentation templates for AI systems",
                        "Conduct inventory of all AI systems requiring documentation",
                        "Document technical specifications, data sources, and algorithms used",
                        "Include known limitations, biases, and potential risks in documentation",
                        "Establish a process for regular documentation updates as systems evolve"
                    ]
                })
                
            if "disclose" not in found_keywords:
                recommendations.append({
                    "id": "trans-003",
                    "title": "Establish Disclosure Protocols",
                    "description": "Develop clear protocols for when and how to disclose AI use to affected individuals and communities.",
                    "rationale": "Appropriate disclosure respects autonomy and enables informed consent regarding AI-driven decisions.",
                    "priority": "medium",
                    "dimension": dimension.value,
                    "implementation_time": "2-3 months",
                    "implementation_steps": [
                        "Identify all contexts where AI is used to make or support decisions",
                        "Develop disclosure templates for different stakeholder groups and contexts",
                        "Create guidelines for timing and method of AI use disclosure",
                        "Train staff on disclosure protocols and addressing stakeholder concerns",
                        "Implement feedback mechanisms to improve disclosure effectiveness"
                    ]
                })
                
        elif dimension == PolicyDimension.HUMAN_AGENCY:
            if "oversight" not in found_keywords or "control" not in found_keywords:
                recommendations.append({
                    "id": "human-001",
                    "title": "Strengthen Human Oversight Mechanisms",
                    "description": "Implement robust human oversight processes for all high-impact AI decision systems.",
                    "rationale": "Human oversight ensures that AI systems remain aligned with human values and institutional goals.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": "3-5 months",
                    "implementation_steps": [
                        "Identify all high-impact AI decision systems requiring human oversight",
                        "Design oversight protocols with clear escalation paths",
                        "Establish oversight committees with diverse expertise",
                        "Implement technical solutions for human review of AI decisions",
                        "Create regular reporting mechanisms on oversight activities"
                    ]
                })
                
            if "intervention" not in found_keywords:
                recommendations.append({
                    "id": "human-002",
                    "title": "Enable Meaningful Human Intervention",
                    "description": "Design AI systems with clear mechanisms for human intervention when necessary.",
                    "rationale": "The ability to intervene in automated processes is essential for maintaining human agency and addressing edge cases.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": "2-4 months",
                    "implementation_steps": [
                        "Assess current AI systems for intervention capabilities",
                        "Design intervention interfaces for different user roles",
                        "Implement technical safeguards and override mechanisms",
                        "Create decision logs for all human interventions",
                        "Train staff on intervention protocols and decision criteria"
                    ]
                })
                
            if "review" not in found_keywords:
                recommendations.append({
                    "id": "human-003",
                    "title": "Establish Regular Review Processes",
                    "description": "Implement scheduled reviews of AI systems to assess their impact on human agency and decision-making.",
                    "rationale": "Regular reviews help identify mission creep and ensure AI systems continue to support rather than undermine human agency.",
                    "priority": "medium",
                    "dimension": dimension.value,
                    "implementation_time": "1-3 months",
                    "implementation_steps": [
                        "Develop review criteria focused on human agency impacts",
                        "Establish a review schedule for all AI systems",
                        "Create review templates and documentation processes",
                        "Form review committees with diverse stakeholder representation",
                        "Implement feedback loops to incorporate review findings into system improvements"
                    ]
                })
                
        elif dimension == PolicyDimension.INCLUSIVENESS:
            if "bias" not in found_keywords:
                recommendations.append({
                    "id": "incl-001",
                    "title": "Implement Bias Detection and Mitigation",
                    "description": "Develop processes to systematically identify and address biases in AI systems throughout their lifecycle.",
                    "rationale": "Proactive bias mitigation is essential for ensuring AI systems serve all users fairly and equitably.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": "3-6 months",
                    "implementation_steps": [
                        "Develop bias assessment frameworks for different types of AI systems",
                        "Implement regular bias audits throughout the AI lifecycle",
                        "Create diverse test datasets that represent varied demographics",
                        "Establish bias mitigation protocols for identified issues",
                        "Train development teams on bias detection and mitigation techniques"
                    ]
                })
                
            if "diverse" not in found_keywords or "representation" not in found_keywords:
                recommendations.append({
                    "id": "incl-002",
                    "title": "Enhance Diversity in AI Development",
                    "description": "Ensure diverse perspectives are included in the design, development, and testing of AI systems.",
                    "rationale": "Diverse teams and inclusive design processes lead to AI systems that work better for all users.",
                    "priority": "medium",
                    "dimension": dimension.value,
                    "implementation_time": "6-12 months",
                    "implementation_steps": [
                        "Assess current diversity in AI development teams and processes",
                        "Develop recruitment and retention strategies for diverse talent",
                        "Implement inclusive design methodologies for AI systems",
                        "Create diverse stakeholder panels for testing and feedback",
                        "Establish metrics to track progress on diversity and inclusion goals"
                    ]
                })
                
            if "discrimination" not in found_keywords:
                recommendations.append({
                    "id": "incl-003",
                    "title": "Prevent Algorithmic Discrimination",
                    "description": "Establish safeguards to prevent AI systems from creating or reinforcing discriminatory practices.",
                    "rationale": "Preventing discrimination is both an ethical imperative and often a legal requirement for AI systems.",
                    "priority": "high",
                    "dimension": dimension.value,
                    "implementation_time": "4-8 months",
                    "implementation_steps": [
                        "Develop anti-discrimination guidelines for AI development",
                        "Implement pre-deployment testing for discriminatory outcomes",
                        "Create monitoring systems to detect discrimination in deployed AI",
                        "Establish remediation protocols for addressing identified discrimination",
                        "Provide training on legal and ethical aspects of algorithmic discrimination"
                    ]
                })
        
        # If no specific recommendations were generated, provide a generic one
        if not recommendations:
            recommendations.append({
                "id": f"{dimension.value.lower().split()[0][:5]}-gen",
                "title": f"Strengthen {dimension.value} in Your AI Policy",
                "description": f"Review and enhance your policy's approach to {dimension.value.lower()}.",
                "rationale": f"A robust approach to {dimension.value.lower()} is essential for ethical AI governance.",
                "priority": "medium",
                "dimension": dimension.value,
                "implementation_time": "3-6 months",
                "implementation_steps": [
                    f"Conduct a comprehensive review of your policy's {dimension.value.lower()} provisions",
                    f"Benchmark against best practices in {dimension.value.lower()} from leading institutions",
                    f"Identify specific gaps in your {dimension.value.lower()} approach",
                    "Develop targeted improvements for each identified gap",
                    "Implement changes and establish metrics to track effectiveness"
                ]
            })
            
        return recommendations

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
        
    def generate_recommendations(self, policy_text: str, institution_type: str = "university", **kwargs) -> Dict[str, Any]:
        """
        Generate recommendations for improving a policy.
        
        Args:
            policy_text: The text of the policy to analyze
            institution_type: Type of institution (university, college, etc.)
            **kwargs: Additional parameters (e.g., analysis_id for tracking)
            
        Returns:
            Dict containing analysis and recommendations
        """
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
            if "implementation_time" in rec and not "timeframe" in rec:
                rec["timeframe"] = rec["implementation_time"]
        
        # Enhance with knowledge base if available
        if self.knowledge_manager:
            try:
                logger.info("Enhancing recommendations with knowledge base integration")
                analysis["knowledge_base_integration"] = True
                analysis["kb_references"] = []
                
                # Get all documents from the knowledge base
                kb_documents = self.knowledge_manager.get_all_documents()
                logger.info("Found %d documents in knowledge base", len(kb_documents))
                
                # Debug: Print details of each document
                for i, doc in enumerate(kb_documents):
                    logger.debug("Document %d: ID=%s Title=%s Author=%s PubDate=%s QualityScore=%s",
                                 i+1,
                                 doc.get('id', 'Unknown'),
                                 doc.get('title', 'Unknown'),
                                 doc.get('author', 'Unknown'),
                                 doc.get('publication_date', 'Unknown'),
                                 doc.get('quality_score', 'Unknown'))
                
                # Track used citations across all recommendations to promote diversity
                all_used_citations = []
                
                # Process each recommendation to add supporting evidence
                for rec in analysis["recommendations"]:
                    # Find relevant documents for this recommendation, considering already used citations
                    logger.debug("Finding supporting evidence for recommendation: %s", rec.get('title', 'Unknown'))
                    supporting_evidence = self._find_supporting_evidence(rec, kb_documents, all_used_citations)
                    logger.debug("Found %d supporting evidence items", len(supporting_evidence))
                    rec["supporting_evidence"] = supporting_evidence
                    
                    # Add references to the recommendation
                    if not rec.get("references"):
                        rec["references"] = []
                    
                    # Add unique references from supporting evidence
                    for evidence in supporting_evidence:
                        citation = evidence.get("citation")
                        reference = {
                            "citation": citation,
                            "source": evidence.get("source"),
                            "year": evidence.get("year"),
                            "relevance": evidence.get("relevance", "high")
                        }
                        
                        # Only add if not already present
                        if citation and not any(r.get("citation") == citation for r in rec["references"]):
                            rec["references"].append(reference)
                            
                            # Track this citation for diversity across recommendations
                            if citation not in all_used_citations:
                                all_used_citations.append(citation)
                    
                    # Set sources field for template display
                    if not rec.get("sources"):
                        rec["sources"] = []
                    
                    # Add citations to sources for template display
                    for ref in rec.get("references", []):
                        if ref.get("citation") and ref["citation"] not in rec["sources"]:
                            rec["sources"].append(ref["citation"])
                    
                    # Debug: Print sources for this recommendation
                    logger.debug("Final sources for recommendation '%s': %s", rec.get('title', 'Unknown'), rec.get('sources', []))
                    
                    # If no sources were found, add diverse placeholder sources
                    if not rec["sources"]:
                        # Use different default sources for each recommendation to ensure diversity
                        default_sources = self.DEFAULT_SOURCES
                        
                        # Select sources not already used in other recommendations
                        available_sources = [s for s in default_sources if s not in all_used_citations]
                        
                        # If all sources are used, reuse some but ensure each recommendation has different ones
                        if not available_sources:
                            available_sources = default_sources
                            
                        # Select 4-6 sources for this recommendation to ensure more diversity
                        import random
                        selected_sources = random.sample(available_sources, min(6, len(available_sources)))
                        rec["sources"] = selected_sources
                        
                        # Track these sources as used
                        for source in selected_sources:
                            if source not in all_used_citations:
                                all_used_citations.append(source)
                    
                    # Track all unique references for the entire analysis
                    for ref in rec.get("references", []):
                        if ref.get("citation") and not any(r.get("citation") == ref.get("citation") for r in analysis["kb_references"]):
                            analysis["kb_references"].append(ref)
                    
                logger.info("Enhanced %d recommendations with knowledge base evidence", len(analysis['recommendations']))
                logger.info("Added %d unique references from knowledge base", len(analysis['kb_references']))
                logger.info("Total unique citations used across recommendations: %d", len(all_used_citations))
                    
            except Exception as e:
                logger.warning("Error querying knowledge base: %s", str(e))
                analysis["knowledge_base_integration"] = False
                
                # Even if knowledge base integration fails, ensure recommendations have diverse sources
                default_sources = self.DEFAULT_SOURCES
                
                used_sources = []
                for i, rec in enumerate(analysis["recommendations"]):
                    if not rec.get("sources"):
                        # Select different sources for each recommendation
                        import random
                        start_idx = (i * 2) % len(default_sources)
                        rec_sources = [default_sources[(start_idx + j) % len(default_sources)] for j in range(3)]
                        rec["sources"] = rec_sources
                        used_sources.extend(rec_sources)
        else:
            analysis["knowledge_base_integration"] = False
            
            # Even without knowledge base, ensure recommendations have diverse sources
            default_sources = self.DEFAULT_SOURCES
            
            used_sources = []
            for i, rec in enumerate(analysis["recommendations"]):
                if not rec.get("sources"):
                    # Select different sources for each recommendation
                    import random
                    start_idx = (i * 2) % len(default_sources)
                    rec_sources = [default_sources[(start_idx + j) % len(default_sources)] for j in range(3)]
                    rec["sources"] = rec_sources
                    used_sources.extend(rec_sources)
        
        return analysis
        
    def _tailor_for_university_context(self, recommendation: Dict[str, Any]) -> None:
        """
        Tailor a recommendation specifically for university context.
        
        Args:
            recommendation: The recommendation to tailor
        """
        # Get the current title and description
        title = recommendation.get("title", "")
        description = recommendation.get("description", "")
        
        # Only modify if not already tailored for universities
        university_terms = ["university", "universities", "higher education", "academic", "faculty", "campus"]
        
        # Check if already tailored
        already_tailored = any(term in title.lower() or term in description.lower() for term in university_terms)
        
        if not already_tailored:
            # Adjust title for university context if needed
            if "policy" in title.lower() and UNIVERSITY_POLICY_LITERAL not in title.lower():
                recommendation["title"] = title.replace("Policy", "University Policy").replace("policy", UNIVERSITY_POLICY_LITERAL)
            
            # Enhance description with university context
            if "university" not in description.lower() and "higher education" not in description.lower():
                recommendation["description"] = f"In the university context, {description.lower()[0]}{description[1:]}"
            
            # Ensure implementation steps are university-specific
            if "implementation_steps" in recommendation:
                steps = recommendation["implementation_steps"]
                university_specific_steps = []
                
                for step in steps:
                    # Only modify if not already tailored
                    if not any(term in step.lower() for term in university_terms):
                        if "stakeholders" in step.lower() and "faculty" not in step.lower():
                            step = step.replace("stakeholders", "faculty, staff, students and other stakeholders")
                        elif "training" in step.lower() and "faculty" not in step.lower():
                            step = step.replace("training", "faculty and staff training")
                        elif "policy" in step.lower() and "university" not in step.lower():
                            step = step.replace("policy", UNIVERSITY_POLICY_LITERAL)
                    
                    university_specific_steps.append(step)
                
                recommendation["implementation_steps"] = university_specific_steps
    
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
            
            # Add top documents until we reach minimum count
            for doc in remaining_docs:
                if len(supporting_evidence) >= min_evidence_count:
                    break
                    
                doc_id = doc.get("id", "")
                doc_author = doc.get("author", "Unknown")
                doc_year = "Unknown"
                
                # Try to extract year from publication date
                pub_date = doc.get("publication_date", "")
                if pub_date:
                    year_match = re.search(YEAR_REGEX, pub_date)
                    if year_match:
                        doc_year = year_match.group(0)
                
                # Format citation in APA style
                if doc_author and doc_year != "Unknown":
                    citation = f"{doc_author} ({doc_year})"
                elif doc_author:
                    citation = f"{doc_author} (n.d.)"
                else:
                    citation = f"Unknown ({doc_year if doc_year != 'Unknown' else 'n.d.'})"
                
                # Prioritize citations not already used elsewhere
                if citation not in used_citations:
                    # Add as supporting evidence with low relevance
                    supporting_evidence.append({
                        "document_id": doc_id,
                        "title": doc.get("title", ""),
                        "citation": citation,
                        "source": doc.get("filename", ""),
                        "year": doc_year,
                        "quality_score": doc.get("quality_score", 0),
                        "relevance": "low"
                    })
                    
                    # Track this citation as used
                    if citation not in used_citations:
                        used_citations.append(citation)
                    
                    # Stop once we have enough evidence
                    if len(supporting_evidence) >= min_evidence_count:
                        break
        
        # Debug: Print final supporting evidence
        logger.debug("Final supporting evidence count: %d", len(supporting_evidence))
        for i, evidence in enumerate(supporting_evidence):
            logger.debug("  Evidence %d: %s - Relevance: %s", i+1, evidence.get('citation', 'Unknown'), evidence.get('relevance', 'Unknown'))
            
        return supporting_evidence
