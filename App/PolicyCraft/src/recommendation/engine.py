"""
Advanced Recommendation Engine for PolicyCraft - FIXED VERSION
Based on academic framework from Bond et al. (2024) and Dabis & Csáki (2024).

🔧 FIXES IMPLEMENTED:
- Less restrictive coverage scoring (15-35% realistic range instead of 0%)
- Enhanced keyword matching with weights and phrase detection
- Better recognition of existing disclosure requirements and governance structures
- Context-aware recommendations tailored to institution type
- Proper deduplication and gap_type error fixes

Implements ethical AI framework with 4 key dimensions:
- Accountability and Responsibility
- Transparency and Explainability  
- Human Agency and Oversight
- Inclusiveness and Diversity

Author: Jacek Robert Kszczot
Research: MSc Data Science & AI - COM7016
"""

import logging
from typing import Dict, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class EthicalFrameworkAnalyzer:
    """
    Analyses policy themes against established ethical AI framework.
    Based on Dabis & Csáki (2024) analysis of 30 leading universities.
    
    🔧 FIXED: Enhanced with weighted keywords and phrase detection to properly
    recognise existing provisions like Columbia's disclosure requirements.
    """
    
    def __init__(self):
        """
        Initialise with enhanced ethical framework mapping.
        
        🔧 IMPROVEMENT: Added weighted keywords and contextual phrases to better
        detect existing policies. Columbia's "must disclose" should now score ~25-35%
        instead of 0% in transparency dimension.
        """
        
        # Enhanced ethical dimensions with weights and phrases
        self.ethical_dimensions = {
            'accountability': {
                'keywords': [
                    'responsibility', 'accountable', 'oversight', 'governance', 
                    'liable', 'responsible party', 'institutional responsibility',
                    'academic responsibility', 'student responsibility', 'faculty oversight',
                    'working group', 'committee', 'ai team', 'policy team'
                ],
                'keyword_weights': {
                    # High importance indicators (3.0 weight)
                    'governance': 3.0, 'oversight': 3.0, 'working group': 3.0,
                    'committee': 3.0, 'accountable': 3.0,
                    # Medium importance (2.0 weight)
                    'responsibility': 2.0, 'responsible party': 2.0,
                    'institutional responsibility': 2.0,
                    # Standard indicators (1.0 weight)
                    'liable': 1.0, 'academic responsibility': 1.0
                },
                'phrases': [
                    'working group', 'governance structure', 'oversight committee',
                    'responsible for', 'accountability framework', 'policy oversight'
                ],
                'weight': 1.0,
                'description': 'Clear assignment of responsibility and governance structures'
            },
            'transparency': {
                'keywords': [
                    'transparent', 'explainable', 'clear guidelines', 'disclosure',
                    'open', 'communicate', 'inform', 'clarity', 'explicit',
                    'declare', 'state clearly', 'make known', 'transparency',
                    'disclose', 'acknowledge', 'report', 'must disclose'
                ],
                'keyword_weights': {
                    # High importance - direct disclosure language (3.0 weight)
                    'disclose': 3.0, 'disclosure': 3.0, 'declare': 3.0,
                    'acknowledge': 3.0, 'must disclose': 3.0,
                    # Medium importance - transparency concepts (2.0 weight)
                    'transparent': 2.0, 'communicate': 2.0, 'inform': 2.0,
                    'report': 2.0, 'transparency': 2.0,
                    # Lower importance - general clarity (1.0 weight)
                    'clear guidelines': 1.0, 'open': 1.0, 'clarity': 1.0
                },
                'phrases': [
                    'must disclose', 'required to disclose', 'shall declare',
                    'transparency requirement', 'disclosure requirement',
                    'must acknowledge', 'required to acknowledge'
                ],
                'weight': 1.0,
                'description': 'Clear communication and explainable AI usage'
            },
            'human_agency': {
                'keywords': [
                    'human oversight', 'human control', 'human decision', 'final decision',
                    'human judgment', 'human review', 'instructor approval',
                    'faculty decision', 'human intervention', 'manual review',
                    'approval', 'permission', 'instructor permission'
                ],
                'keyword_weights': {
                    # High importance - direct human control (3.0 weight)
                    'human oversight': 3.0, 'human control': 3.0, 'final decision': 3.0,
                    'instructor approval': 3.0, 'human decision': 3.0,
                    # Medium importance - review processes (2.0 weight)
                    'human review': 2.0, 'approval': 2.0, 'permission': 2.0,
                    'faculty decision': 2.0,
                    # Standard importance (1.0 weight)
                    'human judgment': 1.0, 'manual review': 1.0
                },
                'phrases': [
                    'human oversight required', 'instructor approval needed',
                    'faculty permission', 'human final decision', 'manual verification'
                ],
                'weight': 1.0,
                'description': 'Maintaining human control and decision-making authority'
            },
            'inclusiveness': {
                'keywords': [
                    'inclusive', 'accessible', 'equity', 'diversity', 'fair',
                    'equal opportunity', 'barrier-free', 'inclusive design',
                    'equitable access', 'diverse needs', 'accessibility',
                    'accommodation', 'disability', 'support'
                ],
                'keyword_weights': {
                    # High importance - direct inclusion language (3.0 weight)
                    'accessible': 3.0, 'accessibility': 3.0, 'inclusive': 3.0,
                    'accommodation': 3.0, 'equitable access': 3.0,
                    # Medium importance - equity concepts (2.0 weight)
                    'equity': 2.0, 'diversity': 2.0, 'fair': 2.0,
                    'equal opportunity': 2.0,
                    # Standard importance (1.0 weight)
                    'barrier-free': 1.0, 'diverse needs': 1.0, 'support': 1.0
                },
                'phrases': [
                    'accessible to all', 'equitable access', 'inclusive design',
                    'disability accommodation', 'barrier-free access'
                ],
                'weight': 1.0,
                'description': 'Ensuring equitable access and diverse perspectives'
            }
        }
        
        # Policy classification patterns (from your classifier)
        self.classification_patterns = {
            'restrictive': {
                'characteristics': ['prohibit', 'ban', 'forbid', 'not allowed', 'restriction'],
                'risk_areas': ['accountability', 'transparency'],
                'strength_areas': ['human_agency']
            },
            'moderate': {
                'characteristics': ['guidelines', 'with permission', 'under supervision', 'limited use'],
                'risk_areas': ['inclusiveness'],
                'strength_areas': ['accountability', 'transparency']
            },
            'permissive': {
                'characteristics': ['encouraged', 'freely', 'flexible', 'student choice'],
                'risk_areas': ['accountability', 'human_agency'],
                'strength_areas': ['inclusiveness']
            }
        }

    def analyze_coverage(self, themes: List[Dict], text: str) -> Dict:
        """
        🔧 COMPLETELY REWRITTEN: More realistic coverage analysis with enhanced scoring.
        
        Columbia should now get ~25-35% for transparency instead of 0% because
        it has "must disclose" language which gets high weight (3.0) scoring.
        
        Args:
            themes: Extracted themes from NLP pipeline
            text: Original policy text
            
        Returns:
            Dict with coverage analysis and realistic scores (15-35% range expected)
        """
        coverage = {}
        text_lower = text.lower()
        
        for dimension, config in self.ethical_dimensions.items():
            dimension_score = 0
            matched_items = []
            
            # 🔧 ENHANCED: Weighted keyword matching instead of binary counting
            for keyword in config['keywords']:
                if keyword.lower() in text_lower:
                    weight = config.get('keyword_weights', {}).get(keyword, 1.0)
                    dimension_score += weight
                    matched_items.append(f"{keyword} (weight: {weight})")
            
            # 🔧 NEW: Phrase matching for contextual understanding
            # This catches "must disclose" as stronger indicator than just "disclose"
            for phrase in config.get('phrases', []):
                if phrase.lower() in text_lower:
                    dimension_score += 2.0  # Phrases get bonus points
                    matched_items.append(f"PHRASE: {phrase}")
            
            # 🔧 ENHANCED: Theme boost (more generous than before)
            theme_boost = 0
            for theme in themes:
                theme_name = theme.get('name', '').lower()
                if any(kw.lower() in theme_name for kw in config['keywords'][:3]):
                    theme_boost += theme.get('score', 0) * 0.3  # Increased from 0.1
            
            # 🔧 COMPLETELY NEW SCORING ALGORITHM
            # Problem: Old system used len(keywords) as denominator, making scores too low
            # Solution: Use weighted maximum possible score
            max_keyword_weight = 3.0  # Highest possible weight
            max_phrase_bonus = len(config.get('phrases', [])) * 2.0
            max_possible_base = len(config['keywords']) * max_keyword_weight + max_phrase_bonus
            
            # Calculate realistic percentage
            if max_possible_base > 0:
                raw_score = (dimension_score / max_possible_base) * 100
            else:
                raw_score = 0
            
            # Add theme boost and cap at 100%
            final_score = min(100, raw_score + theme_boost)
            
            # 🔧 ADJUSTED THRESHOLDS: Much less restrictive than original 70%
            # Columbia's disclosure should now get 'moderate' status instead of 'weak'
            if final_score >= 40:
                status = 'strong'
            elif final_score >= 15:  # Was 70% before - way too high!
                status = 'moderate'
            else:
                status = 'weak'
            
            coverage[dimension] = {
                'score': round(final_score, 1),
                'matched_items': matched_items,
                'item_count': len(matched_items),
                'description': config['description'],
                'status': status,
                'raw_score': round(raw_score, 1),
                'theme_boost': round(theme_boost, 1),
                'debug_info': {
                    'dimension_score': dimension_score,
                    'max_possible': max_possible_base,
                    'keyword_matches': len([i for i in matched_items if 'PHRASE:' not in i]),
                    'phrase_matches': len([i for i in matched_items if 'PHRASE:' in i])
                }
            }
        
        return coverage

    def detect_existing_policies(self, text: str) -> Dict:
        """
        🔧 NEW METHOD: Detect existing policy elements to avoid redundant recommendations.
        
        This addresses the issue where system recommended things that already existed
        in Columbia's policy (like disclosure requirements).
        
        Args:
            text: Original policy text
            
        Returns:
            Dict mapping policy types to boolean existence flags
        """
        text_lower = text.lower() if text else ""
        existing_policies = {
            'disclosure_requirements': False,
            'approval_processes': False,
            'governance_structure': False,
            'training_programs': False,
            'accessibility_measures': False,
            'bias_checking': False,
            'accuracy_verification': False,
            'ip_protection': False
        }
        
        # Enhanced pattern matching for existing policies
        policy_patterns = {
            'disclosure_requirements': [
                'must disclose', 'require disclosure', 'acknowledge', 'cite.*use',
                'transparent.*use', 'declare.*use', 'must be transparent',
                'required to disclose', 'shall declare', 'must acknowledge'
            ],
            'approval_processes': [
                'permission.*instructor', 'approval', 'prior.*permission', 
                'contact.*before', 'prohibited.*without', 'granting permission',
                'instructor.*approval', 'faculty.*permission'
            ],
            'governance_structure': [
                'working group', 'committee', 'ai team', 'governance', 
                'oversight.*group', 'policy.*team', 'advisory.*group',
                'governance.*structure', 'oversight.*committee'
            ],
            'training_programs': [
                'training', 'education', 'workshop', 'consultation', 
                'learning.*community', 'faculty.*development', 'literacy.*program'
            ],
            'accessibility_measures': [
                'accessibility', 'disability', 'accommodation', 'barrier.*free',
                'inclusive.*design', 'equitable.*access', 'diverse.*needs'
            ],
            'bias_checking': [
                'check.*bias', 'bias.*output', 'discriminatory', 'disparate.*impact',
                'protected.*classification', 'consider.*bias', 'bias.*aware'
            ],
            'accuracy_verification': [
                'check.*accuracy', 'verify.*accuracy', 'confirm.*accuracy',
                'additional.*sources', 'fact.*check', 'review.*output',
                'verify.*information', 'cross.*check'
            ],
            'ip_protection': [
                'intellectual.*property', 'copyright', 'plagiarism', 'ip.*rights',
                'third.*party.*rights', 'respect.*ip', 'citation.*required'
            ]
        }
        
        # Check for existing policies using regex patterns
        for policy_type, patterns in policy_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    existing_policies[policy_type] = True
                    break
        
        return existing_policies

    def identify_gaps(self, coverage: Dict, classification: str) -> List[Dict]:
        """
        🔧 FIXED: Added missing 'type' field that was causing errors.
        
        Identify gaps in policy coverage based on ethical framework.
        
        Args:
            coverage: Coverage analysis from analyze_coverage()
            classification: Policy classification (restrictive/moderate/permissive)
            
        Returns:
            List of identified gaps with all required fields
        """
        gaps = []
        
        # Check for weak coverage areas
        for dimension, analysis in coverage.items():
            if analysis['status'] == 'weak':
                gaps.append({
                    'dimension': dimension,
                    'type': 'coverage_gap',  # 🔧 FIX: Added missing field
                    'priority': 'high',
                    'current_score': analysis['score'],
                    'description': f"Low coverage of {analysis['description'].lower()}",
                    'matched_items': analysis.get('matched_items', [])
                })
            elif analysis['status'] == 'moderate':
                gaps.append({
                    'dimension': dimension,
                    'type': 'improvement_opportunity',  # 🔧 FIX: Added missing field
                    'priority': 'medium',
                    'current_score': analysis['score'],
                    'description': f"Moderate coverage of {analysis['description'].lower()}",
                    'matched_items': analysis.get('matched_items', [])
                })
        
        # Add classification-specific risks
        if classification.lower() in self.classification_patterns:
            pattern = self.classification_patterns[classification.lower()]
            for risk_area in pattern['risk_areas']:
                if coverage.get(risk_area, {}).get('status') != 'strong':
                    gaps.append({
                        'dimension': risk_area,
                        'type': 'classification_risk',  # 🔧 FIX: Single type field
                        'priority': 'high',
                        'current_score': coverage.get(risk_area, {}).get('score', 0),
                        'description': f"{classification.title()} policies typically need stronger {risk_area} measures",
                        'evidence': f"Classification pattern analysis indicates vulnerability",
                        'matched_items': coverage.get(risk_area, {}).get('matched_items', [])
                    })
        
        # Sort by priority and score (worst first)
        gaps.sort(key=lambda x: (x['priority'] != 'high', x['current_score']))
        
        return gaps


class RecommendationGenerator:
    """
    Enhanced recommendation generator with comprehensive academic-grade templates.
    
    Implements multi-dimensional matching approach based on:
    - Ethical dimension (accountability, transparency, human_agency, inclusiveness)
    - Institution type (research_university, teaching_focused, technical_institute)
    - Existing policy context (enhancement vs new implementation)
    - Priority level (critical gaps vs improvement opportunities)
    
    Academic sources: UNESCO 2023, JISC 2023, BERA 2018, Dabis & Csáki 2024
    """
    
    def __init__(self):
        """Initialise with comprehensive academic-sourced recommendation templates."""
        
        # Enhanced UNESCO 2023-based recommendations with specific implementation steps
        self.unesco_2023_templates = {
            'accountability': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Establish Multi-Stakeholder AI Governance Committee',
                            'description': 'Create institution-wide committee comprising faculty representatives, student body delegates, IT specialists, ethics experts, and senior administrators. Committee should meet monthly to review AI policy implementation, assess emerging risks, and update guidelines based on practical experience.',
                            'implementation_steps': [
                                'Identify and recruit diverse committee members with relevant expertise',
                                'Develop committee charter defining roles, responsibilities, and decision-making authority',
                                'Establish regular meeting schedule and reporting mechanisms to senior leadership',
                                'Create standardised incident reporting and policy violation review processes'
                            ],
                            'success_metrics': ['Committee established within 2 months', 'Monthly meeting attendance >80%', 'Quarterly policy reviews completed'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Implement Research Integrity AI Oversight Framework',
                            'description': 'Develop specialised oversight mechanisms for AI use in research contexts, including pre-approval processes for high-risk research applications, ongoing monitoring of AI-assisted research projects, and integration with existing research ethics review boards.',
                            'implementation_steps': [
                                'Extend research ethics board mandate to include AI governance oversight',
                                'Develop risk assessment matrix for AI applications in research contexts',
                                'Create streamlined approval process for low-risk AI research applications',
                                'Establish quarterly compliance audits for active research projects using AI'
                            ],
                            'success_metrics': ['Ethics board AI protocols adopted', '>90% research project compliance', 'Risk assessment completed for all new projects'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Strengthen Existing Governance with Formal Accountability Metrics',
                            'description': 'Enhance current governance structures by implementing quantitative accountability measures, establishing clear performance indicators for policy effectiveness, and creating systematic feedback loops from stakeholder communities.',
                            'implementation_steps': [
                                'Develop KPIs for current governance structure effectiveness',
                                'Implement quarterly stakeholder satisfaction surveys',
                                'Create public transparency reports on governance activities and outcomes',
                                'Establish formal escalation procedures for unresolved policy concerns'
                            ],
                            'success_metrics': ['KPI dashboard operational', 'Stakeholder satisfaction >75%', 'Response time to concerns <48 hours'],
                            'timeframe': '1-3 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Create Faculty-Led AI Teaching Excellence Network',
                            'description': 'Establish collaborative network of teaching-focused faculty to develop and share best practices for AI integration in educational contexts, provide peer support for policy implementation, and ensure accountability through professional community engagement.',
                            'implementation_steps': [
                                'Recruit volunteer faculty champions from each academic department',
                                'Organise monthly professional development sessions on AI pedagogy',
                                'Create shared resource repository for AI teaching materials and assessments',
                                'Develop peer review system for innovative AI-enhanced teaching approaches'
                            ],
                            'success_metrics': ['Network membership >50% of teaching faculty', 'Monthly session attendance >30', 'Resource repository with >100 materials'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                },
                'technical_institute': {
                    'new_implementation': [
                        {
                            'title': 'Implement Technical AI Safety and Security Oversight Board',
                            'description': 'Establish technically-sophisticated oversight body with expertise in AI systems, cybersecurity, and educational technology to provide specialised governance for complex AI implementations in technical education contexts.',
                            'implementation_steps': [
                                'Recruit board members with advanced technical AI expertise',
                                'Develop technical safety assessment protocols for AI educational tools',
                                'Create incident response procedures for AI system failures or security breaches',
                                'Establish integration protocols with existing IT security infrastructure'
                            ],
                            'success_metrics': ['Board operational with >5 technical experts', 'Safety protocols for all AI tools', 'Zero major security incidents'],
                            'timeframe': '1-3 months',
                            'priority': 'critical'
                        }
                    ]
                }
            },
            'transparency': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Develop Comprehensive AI Research Disclosure Framework',
                            'description': 'Create detailed disclosure requirements for AI use in research publications, grant applications, and academic presentations. Framework should include methodology transparency, dataset acknowledgment, and limitations documentation to maintain research integrity.',
                            'implementation_steps': [
                                'Draft disclosure templates for different research publication types',
                                'Integrate disclosure requirements into institutional publication guidelines',
                                'Provide training for researchers on proper AI methodology documentation',
                                'Create review checklist for research integrity office and journal submissions'
                            ],
                            'success_metrics': ['Disclosure templates adopted by all departments', '100% compliance in new publications', 'Training completed by >80% research-active faculty'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Establish Public AI Transparency Repository',
                            'description': 'Create publicly accessible repository documenting institutional AI policies, implementation decisions, outcome assessments, and stakeholder feedback. Repository should demonstrate institutional commitment to openness and enable external scrutiny of AI governance practices.',
                            'implementation_steps': [
                                'Develop web-based transparency portal with searchable policy database',
                                'Implement quarterly reporting cycle for AI policy implementation outcomes',
                                'Create stakeholder feedback mechanism with public response commitments',
                                'Establish annual third-party audit of transparency practices'
                            ],
                            'success_metrics': ['Portal launched with full policy documentation', 'Quarterly reports published on schedule', '>1000 annual portal visits'],
                            'timeframe': '4-8 months',
                            'priority': 'medium'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Expand Existing Disclosure Requirements with Methodological Detail',
                            'description': 'Enhance current disclosure practices by requiring detailed documentation of AI methodologies, decision-making processes, and outcome validation procedures. Focus on academic integrity and reproducibility standards.',
                            'implementation_steps': [
                                'Review and strengthen existing disclosure language for comprehensiveness',
                                'Add requirements for AI methodology documentation in research contexts',
                                'Create detailed examples and case studies for common disclosure scenarios',
                                'Implement compliance monitoring through existing academic integrity mechanisms'
                            ],
                            'success_metrics': ['Enhanced disclosure guidelines published', 'Compliance monitoring system operational', 'Faculty feedback rating >4/5'],
                            'timeframe': '1-2 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Create Student-Friendly AI Transparency Dashboard',
                            'description': 'Develop accessible, student-oriented transparency platform explaining institutional AI policies, providing clear examples of appropriate use, and offering easy access to support resources and feedback mechanisms.',
                            'implementation_steps': [
                                'Design user-friendly interface with clear navigation and search functionality',
                                'Create multimedia content explaining AI policies with practical examples',
                                'Implement live chat support for student questions about AI policy',
                                'Develop mobile-responsive design for accessible student engagement'
                            ],
                            'success_metrics': ['Dashboard launched with <2 second load times', 'Student satisfaction rating >4.2/5', '>500 monthly active users'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                }
            },
            'human_agency': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Implement Graduated Human Oversight Protocol for Research AI',
                            'description': 'Establish risk-based human oversight framework requiring different levels of human control based on AI application complexity, research sensitivity, and potential impact. Protocol should preserve human authority in critical research decisions while enabling efficient AI integration.',
                            'implementation_steps': [
                                'Develop risk assessment matrix categorising AI applications by oversight requirements',
                                'Create standard operating procedures for each oversight level',
                                'Train research supervisors on appropriate oversight implementation',
                                'Establish periodic review cycle for oversight level adjustments'
                            ],
                            'success_metrics': ['Risk matrix approved and implemented', 'All active research projects classified', 'Supervisor training >90% completion'],
                            'timeframe': '2-5 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Preserve Human Authority in Academic Assessment and Evaluation',
                            'description': 'Ensure human faculty maintain final decision-making authority over all academic assessments, grading decisions, and research evaluations. Implement safeguards preventing inappropriate delegation of academic judgment to AI systems.',
                            'implementation_steps': [
                                'Develop clear policy statements on human authority in academic evaluation',
                                'Create training programmes for faculty on appropriate AI-assisted assessment',
                                'Implement audit mechanisms to verify human oversight in grading processes',
                                'Establish appeals process for students concerned about AI influence on evaluations'
                            ],
                            'success_metrics': ['Policy statements distributed to all faculty', 'Assessment audit system operational', 'Zero substantiated complaints about inappropriate AI delegation'],
                            'timeframe': '1-3 months',
                            'priority': 'critical'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Strengthen Existing Human Oversight with Systematic Review Processes',
                            'description': 'Enhance current human oversight practices by implementing systematic review processes, establishing clear decision-making hierarchies, and creating documentation requirements for AI-assisted decisions.',
                            'implementation_steps': [
                                'Audit existing oversight practices for completeness and effectiveness',
                                'Implement standardised documentation requirements for AI-assisted decisions',
                                'Create clear escalation procedures for complex or ambiguous cases',
                                'Establish quarterly review meetings to assess oversight effectiveness'
                            ],
                            'success_metrics': ['Oversight audit completed', 'Documentation compliance >95%', 'Escalation procedures tested and functional'],
                            'timeframe': '1-2 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Empower Faculty with AI-Enhanced Teaching Authority',
                            'description': 'Provide faculty with clear authority and practical tools to make informed decisions about AI integration in their courses, including assessment design, student support, and pedagogical innovation while maintaining educational quality standards.',
                            'implementation_steps': [
                                'Develop faculty decision-making framework for AI integration in courses',
                                'Create practical toolkit with assessment examples and best practices',
                                'Provide professional development workshops on AI-enhanced pedagogy',
                                'Establish peer consultation network for complex teaching scenarios'
                            ],
                            'success_metrics': ['Decision framework adopted by >80% faculty', 'Workshop attendance >60% eligible faculty', 'Peer network membership >40 faculty'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                }
            },
            'inclusiveness': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Establish Comprehensive AI Accessibility Standards',
                            'description': 'Implement institution-wide accessibility requirements for all AI tools and platforms, ensuring compliance with disability rights legislation and promoting equitable access for students and faculty with diverse needs and capabilities.',
                            'implementation_steps': [
                                'Conduct accessibility audit of current AI tools and platforms',
                                'Develop procurement requirements including accessibility criteria for new AI tools',
                                'Create accommodation procedures for students unable to use standard AI tools',
                                'Implement regular accessibility testing and compliance monitoring'
                            ],
                            'success_metrics': ['Accessibility audit completed for all AI tools', 'Procurement standards updated', 'Accommodation procedures operational'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Address Digital Equity Gaps in AI Access',
                            'description': 'Develop comprehensive programme to ensure equitable access to AI tools across diverse student populations, addressing financial barriers, technical literacy gaps, and cultural considerations that may limit effective AI engagement.',
                            'implementation_steps': [
                                'Survey student population to identify access barriers and needs',
                                'Establish AI tool lending programme for students with financial constraints',
                                'Create multilingual support materials and culturally responsive training',
                                'Develop partnerships with community organisations to extend support reach'
                            ],
                            'success_metrics': ['Student needs assessment completed', 'Lending programme operational', 'Support materials available in >3 languages'],
                            'timeframe': '4-8 months',
                            'priority': 'high'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Expand Existing Accessibility Measures with Cultural Competency',
                            'description': 'Enhance current accessibility practices by incorporating cultural competency considerations, addressing diverse learning styles and preferences, and ensuring AI implementations respect varied cultural and linguistic backgrounds.',
                            'implementation_steps': [
                                'Review existing accessibility measures for cultural inclusivity gaps',
                                'Engage diverse student focus groups to identify additional needs',
                                'Develop cultural competency guidelines for AI tool selection and implementation',
                                'Create ongoing assessment mechanism for inclusive practice effectiveness'
                            ],
                            'success_metrics': ['Cultural inclusivity review completed', 'Focus group recommendations implemented', 'Assessment mechanism operational'],
                            'timeframe': '2-4 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Develop Alternative Assessment Pathways for Diverse Learning Needs',
                            'description': 'Create multiple assessment options accommodating different learning styles, technical capabilities, and cultural backgrounds while maintaining academic standards and ensuring fair evaluation of student learning outcomes.',
                            'implementation_steps': [
                                'Design alternative assessment formats for students who cannot or prefer not to use AI',
                                'Create flexibility guidelines for faculty to adapt assessments for diverse needs',
                                'Develop support resources for students navigating different assessment options',
                                'Implement quality assurance processes to ensure alternative assessments maintain academic rigour'
                            ],
                            'success_metrics': ['Alternative assessment options available in all courses', 'Student satisfaction with options >4/5', 'Academic standards maintained across all pathways'],
                            'timeframe': '3-5 months',
                            'priority': 'high'
                        }
                    ]
                }
            }
        }
        
        # JISC 2023-based practical implementation templates
        self.jisc_2023_templates = {
            'accountability': {
                'research_university': [
                    {
                        'title': 'Develop Research-Grade AI Competency Requirements',
                        'description': 'Establish mandatory AI literacy requirements for research-active faculty, including understanding of AI capabilities and limitations, ethical considerations in research contexts, and best practices for AI-assisted scholarly work.',
                        'implementation_steps': [
                            'Create competency framework specific to research contexts and methodologies',
                            'Develop assessment mechanism to verify faculty AI literacy levels',
                            'Provide targeted training programmes for different research disciplines',
                            'Implement continuing education requirements for faculty using AI in research'
                        ],
                        'success_metrics': ['Competency framework approved', 'Faculty assessment system operational', '>85% faculty meet basic competency requirements'],
                        'timeframe': '4-6 months',
                        'priority': 'high'
                    }
                ],
                'teaching_focused': [
                    {
                        'title': 'Create Teaching-Focused AI Professional Development Programme',
                        'description': 'Implement comprehensive professional development initiative specifically designed for teaching faculty, focusing on pedagogical applications of AI, assessment design in AI contexts, and student support strategies.',
                        'implementation_steps': [
                            'Design modular training programme addressing core teaching challenges with AI',
                            'Create peer mentoring system pairing experienced and novice AI users',
                            'Develop online resource library with practical teaching examples and case studies',
                            'Establish ongoing support network for faculty implementing AI-enhanced teaching'
                        ],
                        'success_metrics': ['Training programme launched', 'Mentoring system operational with >50 participants', 'Resource library with >200 materials'],
                        'timeframe': '3-5 months',
                        'priority': 'high'
                    }
                ]
            },
            'transparency': {
                'all_institutions': [
                    {
                        'title': 'Implement Comprehensive Stakeholder Communication Strategy',
                        'description': 'Develop multi-channel communication approach ensuring all institutional stakeholders understand AI policies, implementation decisions, and ongoing developments through accessible, regular, and meaningful engagement.',
                        'implementation_steps': [
                            'Create stakeholder mapping identifying all relevant community groups',
                            'Develop communication materials tailored to different audience needs and preferences',
                            'Establish regular communication schedule with predictable updates and opportunities for feedback',
                            'Implement feedback collection and response system with public accountability measures'
                        ],
                        'success_metrics': ['Communication strategy launched', 'All stakeholder groups receiving targeted updates', 'Feedback response rate >30%'],
                        'timeframe': '2-4 months',
                        'priority': 'medium'
                    }
                ]
            }
        }
        
        # BERA 2018 ethical principles adapted for AI contexts
        self.bera_2018_templates = {
            'human_agency': {
                'research_university': [
                    {
                        'title': 'Implement Informed Consent Framework for AI-Assisted Research',
                        'description': 'Develop comprehensive informed consent procedures for research involving AI tools, ensuring participants understand AI involvement, data usage, and potential implications while maintaining research ethics standards.',
                        'implementation_steps': [
                            'Update research ethics protocols to address AI-specific consent requirements',
                            'Create template consent forms with clear AI disclosure language',
                            'Train research ethics board members on AI-related ethical considerations',
                            'Implement ongoing consent verification for longitudinal studies using AI'
                        ],
                        'success_metrics': ['Updated ethics protocols approved', 'Template forms available', 'Ethics board training completed'],
                        'timeframe': '2-4 months',
                        'priority': 'high'
                    }
                ]
            },
            'inclusiveness': {
                'all_institutions': [
                    {
                        'title': 'Establish Participant Welfare Protection in AI Contexts',
                        'description': 'Create robust safeguards ensuring AI implementation does not harm student welfare, academic progress, or personal development, with particular attention to vulnerable populations and those who may be disadvantaged by AI adoption.',
                        'implementation_steps': [
                            'Conduct impact assessment identifying potential welfare risks from AI implementation',
                            'Develop early warning system to identify students experiencing difficulties with AI integration',
                            'Create support services specifically addressing AI-related academic challenges',
                            'Implement regular welfare monitoring and intervention protocols'
                        ],
                        'success_metrics': ['Impact assessment completed', 'Early warning system operational', 'Support services utilised by >5% student body'],
                        'timeframe': '3-6 months',
                        'priority': 'high'
                    }
                ]
            }
        }
        
        # Implementation timeframes based on complexity and urgency
        self.implementation_timeframes = {
            'critical': '1-2 months',
            'high': '2-4 months', 
            'medium': '3-6 months',
            'low': '6-12 months',
            'strategic': '12+ months'
        }
        
        # Institution type characteristics for contextual matching
        self.institution_characteristics = {
            'research_university': {
                'priorities': ['research_integrity', 'publication_ethics', 'graduate_supervision', 'grant_compliance'],
                'stakeholders': ['faculty', 'graduate_students', 'research_staff', 'external_collaborators'],
                'complexity_factors': ['multi_disciplinary', 'international_collaboration', 'high_risk_research']
            },
            'teaching_focused': {
                'priorities': ['student_learning', 'assessment_quality', 'pedagogical_innovation', 'student_support'],
                'stakeholders': ['undergraduate_students', 'teaching_faculty', 'academic_support_staff'],
                'complexity_factors': ['diverse_student_body', 'varying_technical_literacy', 'resource_constraints']
            },
            'technical_institute': {
                'priorities': ['technical_accuracy', 'industry_relevance', 'practical_skills', 'innovation'],
                'stakeholders': ['technical_faculty', 'industry_partners', 'technical_students'],
                'complexity_factors': ['rapid_technology_change', 'industry_integration', 'specialised_equipment']
            }
        }

    def generate_recommendations(self, gaps: List[Dict], classification: str, 
                               themes: List[Dict], text: str = "") -> List[Dict]:
        """
        Generate contextual, detailed recommendations using multi-dimensional matching approach.
        
        Produces academic-grade recommendations with implementation steps, success metrics,
        and contextual adaptations based on institution type and existing policies.
        
        Args:
            gaps: Identified gaps from EthicalFrameworkAnalyzer
            classification: Policy classification (restrictive/moderate/permissive)
            themes: Extracted themes for context
            text: Original text for existing policy detection
            
        Returns:
            List of detailed, contextual recommendations with implementation guidance
        """
        # Determine institution context for targeted recommendations
        institution_context = self._analyze_institution_context(themes, text)
        
        # Detect existing policies to determine enhancement vs new implementation
        existing_policies = self._detect_existing_policies(text) if text else {}
        
        recommendations = []
        used_combinations = set()  # Prevent exact duplicates
        
        # Process each gap with sophisticated matching logic
        for gap in gaps[:8]:  # Limit to top 8 gaps for quality over quantity
            dimension = gap['dimension']
            priority = gap.get('priority', 'medium')
            current_score = gap.get('current_score', 0)
            
            # Determine implementation approach based on existing policies
            has_existing = self._has_existing_provision(gap, existing_policies)
            implementation_type = 'enhancement' if has_existing else 'new_implementation'
            
            # Generate contextual recommendation using multi-dimensional matching
            recommendation = self._generate_contextual_recommendation(
                dimension=dimension,
                institution_context=institution_context,
                implementation_type=implementation_type,
                priority=priority,
                current_score=current_score,
                gap_details=gap
            )
            
            if recommendation:
                # Create unique identifier to prevent duplicates
                combo_key = f"{dimension}_{implementation_type}_{institution_context.get('type', 'general')}"
                if combo_key not in used_combinations:
                    recommendations.append(recommendation)
                    used_combinations.add(combo_key)
        
        # Sort by priority and potential impact
        recommendations.sort(key=lambda x: (
            x.get('priority') != 'critical',
            x.get('priority') != 'high', 
            -x.get('impact_score', 0)
        ))
        
        return recommendations

    def _analyze_institution_context(self, themes: List[Dict], text: str) -> Dict:
        """Determine institution type and characteristics for contextual recommendations."""
        context = {
            'type': 'research_university',  # Default assumption
            'focus_areas': [],
            'complexity_level': 'medium',
            'stakeholder_emphasis': []
        }
        
        if not themes and not text:
            return context
        
        # Combine theme names and text for analysis
        theme_text = ' '.join([t.get('name', '').lower() for t in themes])
        full_text = (text.lower() + ' ' + theme_text) if text else theme_text
        
        # Institution type detection based on content patterns
        research_indicators = ['research', 'publication', 'scholarly', 'graduate', 'phd', 'faculty research']
        teaching_indicators = ['teaching', 'student learning', 'undergraduate', 'classroom', 'pedagogy']
        technical_indicators = ['technical', 'engineering', 'technology', 'industry', 'applied']
        
        research_score = sum(1 for indicator in research_indicators if indicator in full_text)
        teaching_score = sum(1 for indicator in teaching_indicators if indicator in full_text)
        technical_score = sum(1 for indicator in technical_indicators if indicator in full_text)
        
        # Determine primary institution type
        if technical_score > max(research_score, teaching_score):
            context['type'] = 'technical_institute'
        elif teaching_score > research_score * 1.3:
            context['type'] = 'teaching_focused'
        else:
            context['type'] = 'research_university'
        
        # Identify focus areas based on theme analysis
        if any('privacy' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('data_governance')
        if any('integrity' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('academic_integrity')
        if any('research' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('research_excellence')
        
        return context

    def _detect_existing_policies(self, text: str) -> Dict:
        """Enhanced detection of existing policy elements."""
        if not text:
            return {}
            
        text_lower = text.lower()
        existing_policies = {}
        
        # Detection patterns for various policy types
        policy_patterns = {
            'disclosure_requirements': [
                'must disclose', 'require.*disclosure', 'acknowledge.*use', 'cite.*ai',
                'transparent.*about', 'declare.*use', 'must be transparent'
            ],
            'approval_processes': [
                'permission.*required', 'approval.*needed', 'instructor.*approval',
                'prior.*authorization', 'seek.*permission', 'faculty.*consent'
            ],
            'governance_structure': [
                'committee', 'working group', 'governance.*board', 'oversight.*body',
                'ai.*team', 'policy.*committee', 'steering.*group'
            ],
            'training_requirements': [
                'training.*required', 'professional.*development', 'competency.*requirements',
                'education.*programme', 'literacy.*training', 'skill.*development'
            ],
            'assessment_guidelines': [
                'assessment.*guidelines', 'evaluation.*criteria', 'grading.*standards',
                'academic.*evaluation', 'marking.*scheme', 'assessment.*policy'
            ],
            'research_protocols': [
                'research.*ethics', 'research.*integrity', 'scholarly.*standards',
                'publication.*requirements', 'research.*guidelines', 'ethics.*review'
            ]
        }
        
        import re
        for policy_type, patterns in policy_patterns.items():
            existing_policies[policy_type] = any(
                re.search(pattern, text_lower) for pattern in patterns
            )
        
        return existing_policies

    def _has_existing_provision(self, gap: Dict, existing_policies: Dict) -> bool:
        """Determine if gap area has existing policy coverage."""
        dimension = gap['dimension']
        current_score = gap.get('current_score', 0)
        
        # Mapping of dimensions to relevant existing policies
        dimension_policy_map = {
            'transparency': ['disclosure_requirements', 'assessment_guidelines'],
            'accountability': ['governance_structure', 'approval_processes', 'training_requirements'],
            'human_agency': ['approval_processes', 'assessment_guidelines'],
            'inclusiveness': ['assessment_guidelines', 'training_requirements']
        }
        
        if dimension in dimension_policy_map:
            relevant_policies = dimension_policy_map[dimension]
            if any(existing_policies.get(policy, False) for policy in relevant_policies):
                return True
        
        # Also consider score-based determination
        return current_score > 10  # Threshold for considering existing provision

    def _generate_contextual_recommendation(self, dimension: str, institution_context: Dict,
                                          implementation_type: str, priority: str,
                                          current_score: float, gap_details: Dict) -> Dict:
        """Generate contextual recommendation using multi-dimensional matching."""
        
        institution_type = institution_context.get('type', 'research_university')
        
        # Try UNESCO templates first (most comprehensive)
        if dimension in self.unesco_2023_templates:
            if institution_type in self.unesco_2023_templates[dimension]:
                if implementation_type in self.unesco_2023_templates[dimension][institution_type]:
                    templates = self.unesco_2023_templates[dimension][institution_type][implementation_type]
                    selected_template = templates[0]  # Take first as primary
                    
                    return self._build_recommendation_from_template(
                        selected_template, dimension, institution_context, 
                        implementation_type, current_score, gap_details
                    )
        
        # Fallback to JISC templates
        if dimension in self.jisc_2023_templates:
            if institution_type in self.jisc_2023_templates[dimension]:
                templates = self.jisc_2023_templates[dimension][institution_type]
                selected_template = templates[0]
                
                return self._build_recommendation_from_template(
                    selected_template, dimension, institution_context,
                    implementation_type, current_score, gap_details
                )
            elif 'all_institutions' in self.jisc_2023_templates[dimension]:
                templates = self.jisc_2023_templates[dimension]['all_institutions']
                selected_template = templates[0]
                
                return self._build_recommendation_from_template(
                    selected_template, dimension, institution_context,
                    implementation_type, current_score, gap_details
                )
        
        # Final fallback to BERA templates
        if dimension in self.bera_2018_templates:
            available_templates = self.bera_2018_templates[dimension].get(
                'all_institutions', 
                self.bera_2018_templates[dimension].get(institution_type, [])
            )
            if available_templates:
                selected_template = available_templates[0]
                
                return self._build_recommendation_from_template(
                    selected_template, dimension, institution_context,
                    implementation_type, current_score, gap_details
                )
        
        # Ultimate fallback - generate basic recommendation
        return self._generate_fallback_recommendation(
            dimension, institution_context, implementation_type, priority
        )

    def _build_recommendation_from_template(self, template: Dict, dimension: str,
                                          institution_context: Dict, implementation_type: str,
                                          current_score: float, gap_details: Dict) -> Dict:
        """Build comprehensive recommendation from selected template."""
        
        # Calculate impact score based on gap severity and template comprehensiveness
        impact_score = self._calculate_impact_score(current_score, template, institution_context)
        
        # Customise title based on implementation type
        base_title = template.get('title', f'Enhance {dimension.replace("_", " ").title()}')
        if implementation_type == 'enhancement':
            if not base_title.startswith('Enhance') and not base_title.startswith('Strengthen'):
                base_title = f"Enhance {base_title}"
        
        # Build comprehensive recommendation object
        recommendation = {
            'title': base_title,
            'description': template.get('description', ''),
            'dimension': dimension,
            'priority': self._adjust_priority_for_context(
                template.get('priority', 'medium'), 
                current_score, 
                institution_context
            ),
            'implementation_type': implementation_type,
            'timeframe': template.get('timeframe', self.implementation_timeframes.get('medium')),
            'impact_score': impact_score,
            'current_score': current_score,
            'expected_improvement': self._estimate_improvement(current_score, template),
            
            # Detailed implementation guidance
            'implementation_steps': template.get('implementation_steps', []),
            'success_metrics': template.get('success_metrics', []),
            'estimated_resources': self._estimate_resources(template, institution_context),
            
            # Academic sourcing and validation
            'source': self._determine_source(template),
            'academic_rationale': self._generate_academic_rationale(dimension, template, institution_context),
            'related_literature': self._get_related_literature(dimension),
            # Frontend expects a list of sources; fall back to related_literature if not provided
            'sources': template.get('sources', self._get_related_literature(dimension)),
            
            # Contextual adaptations
            'institution_specific_notes': self._generate_context_notes(institution_context, implementation_type),
            'stakeholder_considerations': self._identify_stakeholders(dimension, institution_context),
            'potential_challenges': self._identify_challenges(template, institution_context),
            'mitigation_strategies': self._suggest_mitigations(template, institution_context),
            
            # Quality and validation metadata
            'recommendation_confidence': self._calculate_confidence(template, institution_context),
            'evidence_strength': self._assess_evidence_strength(template),
            'implementation_complexity': self._assess_complexity(template, institution_context)
        }
        
        return recommendation

    def _calculate_impact_score(self, current_score: float, template: Dict, 
                               institution_context: Dict) -> float:
        """Calculate potential impact score for recommendation."""
        # Base impact from gap severity (lower current score = higher impact potential)
        gap_impact = max(0, 100 - current_score) / 100 * 40
        
        # Template comprehensiveness bonus
        template_bonus = len(template.get('implementation_steps', [])) * 2
        template_bonus += len(template.get('success_metrics', [])) * 3
        
        # Institution context multiplier
        context_multiplier = 1.0
        if institution_context.get('type') == 'research_university':
            context_multiplier = 1.2  # Research universities have higher impact potential
        elif institution_context.get('type') == 'technical_institute':
            context_multiplier = 1.1
        
        total_impact = (gap_impact + template_bonus) * context_multiplier
        return min(100, max(10, total_impact))  # Cap between 10-100

    def _adjust_priority_for_context(self, base_priority: str, current_score: float,
                                   institution_context: Dict) -> str:
        """Adjust recommendation priority based on context and gap severity."""
        # Critical gaps (score < 5%) get priority boost
        if current_score < 5:
            return 'critical'
        
        # Severe gaps (score < 15%) in important contexts get high priority
        if current_score < 15:
            if institution_context.get('type') == 'research_university':
                return 'high'
            elif base_priority == 'medium':
                return 'high'
        
        # Research universities get priority boost for accountability and transparency
        if (institution_context.get('type') == 'research_university' and 
            base_priority == 'medium'):
            return 'high'
        
        return base_priority

    def _estimate_improvement(self, current_score: float, template: Dict) -> str:
        """Estimate expected improvement from implementing recommendation."""
        # Base improvement from template comprehensiveness
        step_count = len(template.get('implementation_steps', []))
        metric_count = len(template.get('success_metrics', []))
        
        if step_count >= 4 and metric_count >= 3:
            expected_gain = 25 + (100 - current_score) * 0.3
        elif step_count >= 3:
            expected_gain = 20 + (100 - current_score) * 0.2
        else:
            expected_gain = 15 + (100 - current_score) * 0.1
        
        final_score = min(100, current_score + expected_gain)
        
        if expected_gain >= 25:
            return f"Significant improvement expected: {current_score:.1f}% → {final_score:.1f}%"
        elif expected_gain >= 15:
            return f"Moderate improvement expected: {current_score:.1f}% → {final_score:.1f}%"
        else:
            return f"Incremental improvement expected: {current_score:.1f}% → {final_score:.1f}%"

    def _estimate_resources(self, template: Dict, institution_context: Dict) -> Dict:
        """Estimate required resources for implementation."""
        step_count = len(template.get('implementation_steps', []))
        
        # Base resource estimates
        if step_count >= 4:
            staff_time = "Substantial (2-3 FTE months)"
            budget_requirement = "Medium (£10,000-£25,000)"
        elif step_count >= 3:
            staff_time = "Moderate (1-2 FTE months)"
            budget_requirement = "Low-Medium (£5,000-£15,000)"
        else:
            staff_time = "Light (0.5-1 FTE month)"
            budget_requirement = "Low (£1,000-£5,000)"
        
        # Adjust for institution type
        if institution_context.get('type') == 'research_university':
            budget_requirement = budget_requirement.replace('Low', 'Medium').replace('Medium', 'High')
        
        return {
            'staff_time': staff_time,
            'budget_requirement': budget_requirement,
            'specialist_expertise': self._identify_required_expertise(template),
            'external_support': self._assess_external_support_needs(template)
        }

    def _determine_source(self, template: Dict) -> str:
        """Determine primary academic source for recommendation."""
        if 'unesco' in str(template).lower():
            return 'UNESCO 2023'
        elif 'jisc' in str(template).lower():
            return 'JISC 2023'
        elif 'bera' in str(template).lower():
            return 'BERA 2018'
        else:
            return 'PolicyCraft Enhanced Framework'

    def _generate_academic_rationale(self, dimension: str, template: Dict,
                                   institution_context: Dict) -> str:
        """Generate academic rationale for recommendation."""
        rationale_map = {
            'accountability': f"Establishes clear governance structures essential for responsible AI integration in {institution_context.get('type', 'academic')} contexts, addressing institutional risk management and stakeholder trust requirements.",
            
            'transparency': f"Implements disclosure and communication frameworks critical for maintaining academic integrity and enabling informed decision-making by all institutional stakeholders.",
            
            'human_agency': f"Preserves human authority and oversight in educational processes, ensuring AI augments rather than replaces human judgment in critical academic decisions.",
            
            'inclusiveness': f"Addresses equity and accessibility requirements to ensure AI implementation does not create or exacerbate educational inequalities or exclude diverse student populations."
        }
        
        base_rationale = rationale_map.get(dimension, "Addresses critical gap in institutional AI governance.")
        
        # Add context-specific considerations
        if institution_context.get('type') == 'research_university':
            base_rationale += " Particularly important for research integrity and scholarly communication standards."
        elif institution_context.get('type') == 'teaching_focused':
            base_rationale += " Essential for maintaining educational quality and student support effectiveness."
        
        return base_rationale

    def _get_related_literature(self, dimension: str) -> List[str]:
        """Provide related academic literature references."""
        literature_map = {
            'accountability': [
                "Dabis & Csáki (2024) - AI Ethics in Higher Education Policy",
            ],
            'transparency': [
                "UNESCO (2023) - AI Transparency Guidelines",
                "JISC (2023) - Generative AI in Teaching and Learning",
                "Chen et al. (2024) - Global AI Policy Perspectives"            ],
            'human_agency': [
                "BERA (2018) - Ethical Guidelines for Educational Research",
                "Chan & Hu (2023) - Student Perspectives on Generative AI",
                "UNESCO (2023) - Human-Centric AI in Education",
                "Li et al. (2024) - NLP in Policy Research"            ],
            'inclusiveness': [
                "JISC (2023) - Inclusive AI Implementation",
                "Bond et al. (2024) - Equity Considerations in AI Education",
                "An et al. (2025) - Stakeholder Engagement in AI Policies"            ]
        }
        
        return literature_map.get(dimension, ["PolicyCraft Framework Documentation"])

    def _generate_context_notes(self, institution_context: Dict, implementation_type: str) -> str:
        """Generate institution-specific implementation notes."""
        notes = []
        
        institution_type = institution_context.get('type', 'general')
        
        if institution_type == 'research_university':
            notes.append("Consider integration with existing research ethics and integrity frameworks")
            if implementation_type == 'enhancement':
                notes.append("Build on established academic governance structures")
        elif institution_type == 'teaching_focused':
            notes.append("Prioritise student-facing aspects and teaching quality assurance")
            notes.append("Ensure alignment with student support and academic success initiatives")
        elif institution_type == 'technical_institute':
            notes.append("Leverage technical expertise within institution for implementation")
            notes.append("Consider industry partnership opportunities for practical implementation")
        
        if implementation_type == 'enhancement':
            notes.append("Builds on existing policy foundation - focus on strengthening and expanding current provisions")
        else:
            notes.append("New implementation required - establish foundation before building advanced features")
        
        return "; ".join(notes)

    def _identify_stakeholders(self, dimension: str, institution_context: Dict) -> List[str]:
        """Identify key stakeholders for recommendation implementation."""
        base_stakeholders = {
            'accountability': ['Senior Leadership', 'IT Services', 'Legal/Compliance'],
            'transparency': ['Communications Team', 'Student Services', 'Faculty Representatives'],
            'human_agency': ['Academic Affairs', 'Faculty Senate', 'Student Representatives'],
            'inclusiveness': ['Disability Services', 'Diversity & Inclusion Office', 'Student Support']
        }
        
        stakeholders = base_stakeholders.get(dimension, ['Policy Committee'])
        
        # Add institution-specific stakeholders
        if institution_context.get('type') == 'research_university':
            stakeholders.extend(['Research Office', 'Graduate School', 'Ethics Board'])
        elif institution_context.get('type') == 'teaching_focused':
            stakeholders.extend(['Teaching & Learning Centre', 'Academic Support'])
        
        return stakeholders

    def _identify_challenges(self, template: Dict, institution_context: Dict) -> List[str]:
        """Identify potential implementation challenges."""
        challenges = []
        
        step_count = len(template.get('implementation_steps', []))
        if step_count >= 4:
            challenges.append("Complex implementation requiring significant coordination")
        
        if institution_context.get('type') == 'research_university':
            challenges.extend([
                "Faculty autonomy considerations in research contexts",
                "Integration with existing research governance structures"
            ])
        elif institution_context.get('type') == 'teaching_focused':
            challenges.extend([
                "Diverse faculty technical literacy levels",
                "Student resistance to policy changes"
            ])
        
        challenges.extend([
            "Resource allocation and budget constraints",
            "Timeline coordination with academic calendar",
            "Change management and stakeholder buy-in"
        ])
        
        return challenges

    def _suggest_mitigations(self, template: Dict, institution_context: Dict) -> List[str]:
        """Suggest mitigation strategies for identified challenges."""
        mitigations = [
            "Establish clear project governance with defined roles and responsibilities",
            "Implement phased rollout approach to manage complexity and risk",
            "Provide comprehensive training and support for all stakeholders",
            "Create feedback mechanisms for continuous improvement during implementation"
        ]
        
        if institution_context.get('type') == 'research_university':
            mitigations.extend([
                "Engage faculty governance bodies early in planning process",
                "Align implementation with research ethics review cycles"
            ])
        elif institution_context.get('type') == 'teaching_focused':
            mitigations.extend([
                "Provide extensive faculty development and technical support",
                "Create student advisory group to guide policy development"
            ])
        
        return mitigations

    def _calculate_confidence(self, template: Dict, institution_context: Dict) -> str:
        """Calculate confidence level in recommendation effectiveness."""
        confidence_score = 0
        
        # Template quality indicators
        if len(template.get('implementation_steps', [])) >= 3:
            confidence_score += 25
        if len(template.get('success_metrics', [])) >= 2:
            confidence_score += 25
        if template.get('timeframe'):
            confidence_score += 15
        
        # Institution context match
        if institution_context.get('type') in ['research_university', 'teaching_focused']:
            confidence_score += 20
        
        # Source credibility
        source = self._determine_source(template)
        if source in ['UNESCO 2023', 'JISC 2023', 'BERA 2018']:
            confidence_score += 15
        
        if confidence_score >= 80:
            return 'High'
        elif confidence_score >= 60:
            return 'Medium-High'
        elif confidence_score >= 40:
            return 'Medium'
        else:
            return 'Medium-Low'

    def _assess_evidence_strength(self, template: Dict) -> str:
        """Assess strength of evidence supporting recommendation."""
        if 'research' in template.get('description', '').lower():
            return 'Strong - Research-based'
        elif len(template.get('success_metrics', [])) >= 3:
            return 'Good - Measurable outcomes defined'
        elif len(template.get('implementation_steps', [])) >= 4:
            return 'Moderate - Detailed implementation guidance'
        else:
            return 'Basic - General guidance provided'

    def _assess_complexity(self, template: Dict, institution_context: Dict) -> str:
        """Assess implementation complexity."""
        complexity_score = 0
        
        complexity_score += len(template.get('implementation_steps', [])) * 10
        complexity_score += len(template.get('success_metrics', [])) * 5
        
        if institution_context.get('type') == 'research_university':
            complexity_score += 15  # Higher complexity for research contexts
        
        if complexity_score >= 60:
            return 'High'
        elif complexity_score >= 40:
            return 'Medium'
        else:
            return 'Low'

    def _identify_required_expertise(self, template: Dict) -> List[str]:
        """Identify specialist expertise required for implementation."""
        expertise = []
        
        description = template.get('description', '').lower()
        steps = ' '.join(template.get('implementation_steps', [])).lower()
        
        if any(term in description + steps for term in ['technical', 'system', 'platform']):
            expertise.append('Technical/IT specialist')
        if any(term in description + steps for term in ['legal', 'compliance', 'governance']):
            expertise.append('Legal/Compliance expert')
        if any(term in description + steps for term in ['training', 'education', 'development']):
            expertise.append('Professional development specialist')
        if any(term in description + steps for term in ['assessment', 'evaluation', 'measurement']):
            expertise.append('Assessment design expert')
        
        return expertise if expertise else ['General project management']

    def _assess_external_support_needs(self, template: Dict) -> str:
        """Assess whether external support/consultation is needed."""
        complexity_indicators = len(template.get('implementation_steps', []))
        
        if complexity_indicators >= 4:
            return 'Recommended - Complex implementation benefits from external expertise'
        elif complexity_indicators >= 3:
            return 'Optional - Consider for specialised aspects'
        else:
            return 'Not required - Can be implemented with internal resources'

    def _generate_fallback_recommendation(self, dimension: str, institution_context: Dict,
                                        implementation_type: str, priority: str) -> Dict:
        """Generate basic recommendation when no specific template matches."""
        dimension_title = dimension.replace('_', ' ').title()
        
        fallback_recommendations = {
            'accountability': {
                'title': f'Strengthen {dimension_title} Framework',
                'description': f'Develop comprehensive {dimension_title.lower()} measures including clear governance structures, defined responsibilities, and regular compliance monitoring to ensure effective AI policy implementation.',
                'steps': [
                    'Establish governance committee with clear mandate and authority',
                    'Define roles and responsibilities for AI policy oversight',
                    'Implement regular monitoring and compliance assessment procedures',
                    'Create escalation procedures for policy violations or concerns'
                ],
                'sources': [
                    'BERA 2018 – Ethical Guidelines, Principle 2',
                    'UNESCO 2023 – Guidance for Generative AI, pp. 10–12'
                ]
            },
            'transparency': {
                'title': f'Implement {dimension_title} Requirements',
                'description': f'Create comprehensive {dimension_title.lower()} framework requiring clear disclosure of AI usage, accessible communication of policies, and regular stakeholder engagement.',
                'steps': [
                    'Develop clear disclosure requirements for AI usage',
                    'Create accessible policy communication materials',
                    'Establish regular stakeholder consultation processes',
                    'Implement feedback collection and response mechanisms'
                ],
                'sources': [
                    'Jisc 2023 – Generative AI Guide, Section 4.1',
                    'UNESCO 2023 – Guidance for Generative AI, pp. 8–9'
                ]
            },
            'human_agency': {
                'title': f'Preserve {dimension_title} in AI Implementation',
                'description': f'Ensure human authority and oversight remain central to AI-enhanced processes, maintaining human control over critical decisions and preserving educational relationships.',
                'steps': [
                    'Define areas requiring mandatory human oversight',
                    'Establish clear protocols for human authority in AI-assisted decisions',
                    'Train staff on appropriate human-AI collaboration approaches',
                    'Implement regular review of human oversight effectiveness'
                ],
                'sources': [
                    'UNESCO 2023 – Guidance for Generative AI, p. 22',
                    'Selwyn et al. 2020 – Machine Learning & Emotional Tenor'
                ]
            },
            'inclusiveness': {
                'title': f'Develop {dimension_title} Framework',
                'description': f'Create comprehensive {dimension_title.lower()} measures ensuring equitable AI access, addressing diverse needs, and preventing discriminatory outcomes.',
                'steps': [
                    'Conduct accessibility audit of AI tools and processes',
                    'Develop alternative pathways for diverse learning needs',
                    'Implement bias monitoring and mitigation procedures',
                    'Create support mechanisms for underrepresented groups'
                ],
                'sources': [
                    'UNESCO 2023 – Guidance for Generative AI, pp. 16–18',
                    'Corrigan et al. 2023 – ChatGPT Pedagogical Affordances'
                ]
            }
        }
        
        template = fallback_recommendations.get(dimension, fallback_recommendations['accountability'])
        
        return {
            'title': template['title'],
            'description': template['description'],
            'dimension': dimension,
            'priority': priority,
            'implementation_type': implementation_type,
            'timeframe': self.implementation_timeframes.get(priority, '3-6 months'),
            'implementation_steps': template['steps'],
            'source': 'PolicyCraft Fallback Framework',
            'sources': template.get('sources', []),
            'recommendation_confidence': 'Medium',
            'implementation_complexity': 'Medium'
        }


class RecommendationEngine:
    """
    🔧 ENHANCED: Main recommendation engine with improved error handling and debugging.
    
    Integration point for ethical framework analysis and recommendation generation.
    """
    
    def __init__(self):
        """Initialise recommendation engine components."""
        self.framework_analyzer = EthicalFrameworkAnalyzer()
        self.recommendation_generator = RecommendationGenerator()
        
        logger.info("Enhanced Recommendation Engine initialized with fixes")
        print("🔧 FIXED PolicyCraft Recommendation Engine loaded:")
        print("   ✅ Enhanced scoring algorithm (15-35% realistic range)")
        print("   ✅ Weighted keyword matching with phrase detection")
        print("   ✅ Existing policy recognition (disclosure, governance)")
        print("   ✅ Context-aware recommendations with deduplication")
        print("   ✅ Fixed gap_type errors and missing fields")

    """
Enhanced Recommendation Templates & Smart Matching Logic for PolicyCraft
Multi-dimensional recommendation matrix: dimension × institution type × existing policies
Based on UNESCO 2023, JISC 2023, BERA 2018, and Dabis & Csáki (2024) research

Replace the RecommendationGenerator class in engine.py with this enhanced version
"""
    def generate_recommendations(self, themes: List[Dict], classification: Dict, 
                               text: str, analysis_id: str = None) -> Dict:
        """
        Main entry point for comprehensive recommendation generation.
        
        Integrates ethical framework analysis with contextual recommendation generation
        to produce detailed, academic-grade recommendations with implementation guidance.
        
        Args:
            themes: Extracted themes from NLP pipeline
            classification: Policy classification results
            text: Original policy text (crucial for existing policy detection)
            analysis_id: Optional analysis identifier
            
        Returns:
            Complete recommendation package with coverage analysis and detailed recommendations
        """
        try:
            logger.info(f"Generating comprehensive recommendations for analysis: {analysis_id}")
            print(f"\n🔍 Analysing policy against enhanced ethical framework...")
            
            # Step 1: Enhanced coverage analysis with weighted scoring
            coverage_analysis = self.framework_analyzer.analyze_coverage(themes, text)
            
            print(f"📊 Enhanced Coverage Analysis (Fixed Scoring):")
            for dimension, analysis in coverage_analysis.items():
                status_emoji = "🟢" if analysis['status'] == 'strong' else "🟡" if analysis['status'] == 'moderate' else "🔴"
                matched_count = analysis.get('item_count', 0)
                phrase_count = len([i for i in analysis.get('matched_items', []) if 'PHRASE:' in i])
                print(f"   {status_emoji} {dimension.replace('_', ' ').title()}: {analysis['score']}% ({analysis['status']}) - {matched_count} indicators, {phrase_count} phrases")
            
            # Step 2: Detect existing policies to inform recommendations
            existing_policies = self.framework_analyzer.detect_existing_policies(text)
            existing_count = sum(1 for v in existing_policies.values() if v)
            print(f"\n🏛️ Detected {existing_count} existing policy elements:")
            for policy, exists in existing_policies.items():
                if exists:
                    print(f"   ✅ {policy.replace('_', ' ').title()}")
            
            # Step 3: Identify gaps with proper field mapping
            gaps = self.framework_analyzer.identify_gaps(
                coverage_analysis, 
                classification.get('classification', 'Unknown')
            )
            
            print(f"\n🎯 Identified {len(gaps)} improvement areas:")
            for gap in gaps[:3]:  # Show top 3
                print(f"   📍 {gap['dimension'].replace('_', ' ').title()}: {gap['current_score']:.1f}% ({gap['type']})")
            
            # Step 4: Generate contextual, non-duplicate recommendations using enhanced templates
            recommendations = self.recommendation_generator.generate_recommendations(
                gaps, 
                classification.get('classification', 'Unknown'),
                themes,
                text  # Crucial: Pass text for existing policy detection
            )
            
            enhancement_count = len([r for r in recommendations if r.get('implementation_type') == 'enhancement'])
            new_count = len([r for r in recommendations if r.get('implementation_type') == 'new'])
            
            print(f"💡 Generated {len(recommendations)} context-aware recommendations:")
            print(f"   🔧 {enhancement_count} enhancements to existing policies")
            print(f"   🆕 {new_count} new implementations")
            
            # Step 5: Compile comprehensive recommendation package
            recommendation_package = {
                'analysis_metadata': {
                    'analysis_id': analysis_id,
                    'generated_date': datetime.now().isoformat(),
                    'framework_version': '2.0-enhanced',
                    'academic_sources': ['UNESCO 2023', 'JISC 2023', 'BERA 2018'],
                    'methodology': 'Enhanced Ethical Framework Gap Analysis with Multi-Dimensional Matching'
                },
                'coverage_analysis': coverage_analysis,
                'existing_policies': existing_policies,
                'identified_gaps': gaps,
                'recommendations': recommendations,
                'summary': {
                    'total_recommendations': len(recommendations),
                    'enhancement_recommendations': enhancement_count,
                    'new_implementations': new_count,
                    'high_priority_count': len([r for r in recommendations if r.get('priority') == 'high']),
                    'coverage_scores': {dim: analysis['score'] for dim, analysis in coverage_analysis.items()},
                    'overall_coverage': round(sum(a['score'] for a in coverage_analysis.values()) / len(coverage_analysis), 1) if coverage_analysis else 0,
                    'existing_policy_count': existing_count,
                    'recommendations_by_dimension': {
                        dim: len([r for r in recommendations if r.get('dimension') == dim])
                        for dim in coverage_analysis.keys()
                    },
                    'recommendations_by_priority': {
                        'critical': len([r for r in recommendations if r.get('priority') == 'critical']),
                        'high': len([r for r in recommendations if r.get('priority') == 'high']),
                        'medium': len([r for r in recommendations if r.get('priority') == 'medium']),
                        'low': len([r for r in recommendations if r.get('priority') == 'low'])
                    }
                }
            }
            
            # Validation: Check if fixes worked for enhanced recommendations
            transparency_score = coverage_analysis.get('transparency', {}).get('score', 0)
            has_disclosure = existing_policies.get('disclosure_requirements', False)
            
            if transparency_score > 0 and has_disclosure:
                print(f"✅ Fix validation: Transparency score {transparency_score}% with disclosure detected")
            elif transparency_score == 0:
                print(f"⚠️ Warning: Transparency still scoring 0% - may need further debugging")
            
            logger.info(f"Enhanced recommendation generation completed successfully")
            return recommendation_package
            
        except Exception as e:
            logger.error(f"Error in enhanced recommendation generation: {str(e)}")
            print(f"❌ Error in enhanced recommendation generation: {str(e)}")
            
            # Enhanced fallback with debug info
            return self._generate_enhanced_fallback(classification, themes, str(e))

    def _generate_enhanced_fallback(self, classification: Dict, themes: List[Dict], error_msg: str) -> Dict:
        """
        Generate informative fallback when main process fails.
        
        Provides basic recommendations while preserving error information for debugging.
        """
        
        basic_recommendations = [
            {
                'title': 'Policy Review and Enhancement',
                'description': 'Conduct comprehensive review of current AI policy to ensure alignment with best practices and address identified gaps.',
                'priority': 'high',
                'source': 'Fallback',
                'timeframe': '3-6 months',
                'implementation_type': 'review',
                'dimension': 'general'
            },
            {
                'title': 'Stakeholder Consultation Process',
                'description': 'Establish systematic consultation with faculty, students, and staff to gather feedback on AI policy effectiveness.',
                'priority': 'medium', 
                'source': 'Fallback',
                'timeframe': '1-3 months',
                'implementation_type': 'new',
                'dimension': 'engagement'
            }
        ]
        
        return {
            'analysis_metadata': {
                'generated_date': datetime.now().isoformat(),
                'framework_version': 'fallback-2.0',
                'methodology': 'Enhanced Fallback Template',
                'error_info': {
                    'error_message': error_msg,
                    'fallback_reason': 'Main analysis failed, using enhanced fallback'
                }
            },
            'recommendations': basic_recommendations,
            'summary': {
                'total_recommendations': len(basic_recommendations),
                'note': 'Enhanced fallback recommendations due to processing error',
                'debug_available': True
            },
            'debug_info': {
                'classification': classification,
                'theme_count': len(themes) if themes else 0,
                'error_occurred': True
            }
        }
class EnhancedRecommendationGenerator:
    """
    Enhanced recommendation generator with comprehensive academic-grade templates.
    
    Implements multi-dimensional matching:
    - Ethical dimension (accountability, transparency, human_agency, inclusiveness)
    - Institution type (research_university, teaching_focused, technical_institute)
    - Existing policy context (enhancement vs new implementation)
    - Priority level (critical gaps vs improvement opportunities)
    """
    
    def __init__(self):
        """Initialise with comprehensive academic-sourced recommendation templates."""
        
        # Enhanced UNESCO 2023-based recommendations with specific implementation steps
        self.unesco_2023_templates = {
            'accountability': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Establish Multi-Stakeholder AI Governance Committee',
                            'description': 'Create institution-wide committee comprising faculty representatives, student body delegates, IT specialists, ethics experts, and senior administrators. Committee should meet monthly to review AI policy implementation, assess emerging risks, and update guidelines based on practical experience.',
                            'implementation_steps': [
                                'Identify and recruit diverse committee members with relevant expertise',
                                'Develop committee charter defining roles, responsibilities, and decision-making authority',
                                'Establish regular meeting schedule and reporting mechanisms to senior leadership',
                                'Create standardised incident reporting and policy violation review processes'
                            ],
                            'success_metrics': ['Committee established within 2 months', 'Monthly meeting attendance >80%', 'Quarterly policy reviews completed'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Implement Research Integrity AI Oversight Framework',
                            'description': 'Develop specialised oversight mechanisms for AI use in research contexts, including pre-approval processes for high-risk research applications, ongoing monitoring of AI-assisted research projects, and integration with existing research ethics review boards.',
                            'implementation_steps': [
                                'Extend research ethics board mandate to include AI governance oversight',
                                'Develop risk assessment matrix for AI applications in research contexts',
                                'Create streamlined approval process for low-risk AI research applications',
                                'Establish quarterly compliance audits for active research projects using AI'
                            ],
                            'success_metrics': ['Ethics board AI protocols adopted', '>90% research project compliance', 'Risk assessment completed for all new projects'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Strengthen Existing Governance with Formal Accountability Metrics',
                            'description': 'Enhance current governance structures by implementing quantitative accountability measures, establishing clear performance indicators for policy effectiveness, and creating systematic feedback loops from stakeholder communities.',
                            'implementation_steps': [
                                'Develop KPIs for current governance structure effectiveness',
                                'Implement quarterly stakeholder satisfaction surveys',
                                'Create public transparency reports on governance activities and outcomes',
                                'Establish formal escalation procedures for unresolved policy concerns'
                            ],
                            'success_metrics': ['KPI dashboard operational', 'Stakeholder satisfaction >75%', 'Response time to concerns <48 hours'],
                            'timeframe': '1-3 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Create Faculty-Led AI Teaching Excellence Network',
                            'description': 'Establish collaborative network of teaching-focused faculty to develop and share best practices for AI integration in educational contexts, provide peer support for policy implementation, and ensure accountability through professional community engagement.',
                            'implementation_steps': [
                                'Recruit volunteer faculty champions from each academic department',
                                'Organise monthly professional development sessions on AI pedagogy',
                                'Create shared resource repository for AI teaching materials and assessments',
                                'Develop peer review system for innovative AI-enhanced teaching approaches'
                            ],
                            'success_metrics': ['Network membership >50% of teaching faculty', 'Monthly session attendance >30', 'Resource repository with >100 materials'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                },
                'technical_institute': {
                    'new_implementation': [
                        {
                            'title': 'Implement Technical AI Safety and Security Oversight Board',
                            'description': 'Establish technically-sophisticated oversight body with expertise in AI systems, cybersecurity, and educational technology to provide specialised governance for complex AI implementations in technical education contexts.',
                            'implementation_steps': [
                                'Recruit board members with advanced technical AI expertise',
                                'Develop technical safety assessment protocols for AI educational tools',
                                'Create incident response procedures for AI system failures or security breaches',
                                'Establish integration protocols with existing IT security infrastructure'
                            ],
                            'success_metrics': ['Board operational with >5 technical experts', 'Safety protocols for all AI tools', 'Zero major security incidents'],
                            'timeframe': '1-3 months',
                            'priority': 'critical'
                        }
                    ]
                }
            },
            'transparency': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Develop Comprehensive AI Research Disclosure Framework',
                            'description': 'Create detailed disclosure requirements for AI use in research publications, grant applications, and academic presentations. Framework should include methodology transparency, dataset acknowledgment, and limitations documentation to maintain research integrity.',
                            'implementation_steps': [
                                'Draft disclosure templates for different research publication types',
                                'Integrate disclosure requirements into institutional publication guidelines',
                                'Provide training for researchers on proper AI methodology documentation',
                                'Create review checklist for research integrity office and journal submissions'
                            ],
                            'success_metrics': ['Disclosure templates adopted by all departments', '100% compliance in new publications', 'Training completed by >80% research-active faculty'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Establish Public AI Transparency Repository',
                            'description': 'Create publicly accessible repository documenting institutional AI policies, implementation decisions, outcome assessments, and stakeholder feedback. Repository should demonstrate institutional commitment to openness and enable external scrutiny of AI governance practices.',
                            'implementation_steps': [
                                'Develop web-based transparency portal with searchable policy database',
                                'Implement quarterly reporting cycle for AI policy implementation outcomes',
                                'Create stakeholder feedback mechanism with public response commitments',
                                'Establish annual third-party audit of transparency practices'
                            ],
                            'success_metrics': ['Portal launched with full policy documentation', 'Quarterly reports published on schedule', '>1000 annual portal visits'],
                            'timeframe': '4-8 months',
                            'priority': 'medium'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Expand Existing Disclosure Requirements with Methodological Detail',
                            'description': 'Enhance current disclosure practices by requiring detailed documentation of AI methodologies, decision-making processes, and outcome validation procedures. Focus on academic integrity and reproducibility standards.',
                            'implementation_steps': [
                                'Review and strengthen existing disclosure language for comprehensiveness',
                                'Add requirements for AI methodology documentation in research contexts',
                                'Create detailed examples and case studies for common disclosure scenarios',
                                'Implement compliance monitoring through existing academic integrity mechanisms'
                            ],
                            'success_metrics': ['Enhanced disclosure guidelines published', 'Compliance monitoring system operational', 'Faculty feedback rating >4/5'],
                            'timeframe': '1-2 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Create Student-Friendly AI Transparency Dashboard',
                            'description': 'Develop accessible, student-oriented transparency platform explaining institutional AI policies, providing clear examples of appropriate use, and offering easy access to support resources and feedback mechanisms.',
                            'implementation_steps': [
                                'Design user-friendly interface with clear navigation and search functionality',
                                'Create multimedia content explaining AI policies with practical examples',
                                'Implement live chat support for student questions about AI policy',
                                'Develop mobile-responsive design for accessible student engagement'
                            ],
                            'success_metrics': ['Dashboard launched with <2 second load times', 'Student satisfaction rating >4.2/5', '>500 monthly active users'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                }
            },
            'human_agency': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Implement Graduated Human Oversight Protocol for Research AI',
                            'description': 'Establish risk-based human oversight framework requiring different levels of human control based on AI application complexity, research sensitivity, and potential impact. Protocol should preserve human authority in critical research decisions while enabling efficient AI integration.',
                            'implementation_steps': [
                                'Develop risk assessment matrix categorising AI applications by oversight requirements',
                                'Create standard operating procedures for each oversight level',
                                'Train research supervisors on appropriate oversight implementation',
                                'Establish periodic review cycle for oversight level adjustments'
                            ],
                            'success_metrics': ['Risk matrix approved and implemented', 'All active research projects classified', 'Supervisor training >90% completion'],
                            'timeframe': '2-5 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Preserve Human Authority in Academic Assessment and Evaluation',
                            'description': 'Ensure human faculty maintain final decision-making authority over all academic assessments, grading decisions, and research evaluations. Implement safeguards preventing inappropriate delegation of academic judgment to AI systems.',
                            'implementation_steps': [
                                'Develop clear policy statements on human authority in academic evaluation',
                                'Create training programmes for faculty on appropriate AI-assisted assessment',
                                'Implement audit mechanisms to verify human oversight in grading processes',
                                'Establish appeals process for students concerned about AI influence on evaluations'
                            ],
                            'success_metrics': ['Policy statements distributed to all faculty', 'Assessment audit system operational', 'Zero substantiated complaints about inappropriate AI delegation'],
                            'timeframe': '1-3 months',
                            'priority': 'critical'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Strengthen Existing Human Oversight with Systematic Review Processes',
                            'description': 'Enhance current human oversight practices by implementing systematic review processes, establishing clear decision-making hierarchies, and creating documentation requirements for AI-assisted decisions.',
                            'implementation_steps': [
                                'Audit existing oversight practices for completeness and effectiveness',
                                'Implement standardised documentation requirements for AI-assisted decisions',
                                'Create clear escalation procedures for complex or ambiguous cases',
                                'Establish quarterly review meetings to assess oversight effectiveness'
                            ],
                            'success_metrics': ['Oversight audit completed', 'Documentation compliance >95%', 'Escalation procedures tested and functional'],
                            'timeframe': '1-2 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Empower Faculty with AI-Enhanced Teaching Authority',
                            'description': 'Provide faculty with clear authority and practical tools to make informed decisions about AI integration in their courses, including assessment design, student support, and pedagogical innovation while maintaining educational quality standards.',
                            'implementation_steps': [
                                'Develop faculty decision-making framework for AI integration in courses',
                                'Create practical toolkit with assessment examples and best practices',
                                'Provide professional development workshops on AI-enhanced pedagogy',
                                'Establish peer consultation network for complex teaching scenarios'
                            ],
                            'success_metrics': ['Decision framework adopted by >80% faculty', 'Workshop attendance >60% eligible faculty', 'Peer network membership >40 faculty'],
                            'timeframe': '2-4 months',
                            'priority': 'high'
                        }
                    ]
                }
            },
            'inclusiveness': {
                'research_university': {
                    'new_implementation': [
                        {
                            'title': 'Establish Comprehensive AI Accessibility Standards',
                            'description': 'Implement institution-wide accessibility requirements for all AI tools and platforms, ensuring compliance with disability rights legislation and promoting equitable access for students and faculty with diverse needs and capabilities.',
                            'implementation_steps': [
                                'Conduct accessibility audit of current AI tools and platforms',
                                'Develop procurement requirements including accessibility criteria for new AI tools',
                                'Create accommodation procedures for students unable to use standard AI tools',
                                'Implement regular accessibility testing and compliance monitoring'
                            ],
                            'success_metrics': ['Accessibility audit completed for all AI tools', 'Procurement standards updated', 'Accommodation procedures operational'],
                            'timeframe': '3-6 months',
                            'priority': 'high'
                        },
                        {
                            'title': 'Address Digital Equity Gaps in AI Access',
                            'description': 'Develop comprehensive programme to ensure equitable access to AI tools across diverse student populations, addressing financial barriers, technical literacy gaps, and cultural considerations that may limit effective AI engagement.',
                            'implementation_steps': [
                                'Survey student population to identify access barriers and needs',
                                'Establish AI tool lending programme for students with financial constraints',
                                'Create multilingual support materials and culturally responsive training',
                                'Develop partnerships with community organisations to extend support reach'
                            ],
                            'success_metrics': ['Student needs assessment completed', 'Lending programme operational', 'Support materials available in >3 languages'],
                            'timeframe': '4-8 months',
                            'priority': 'high'
                        }
                    ],
                    'enhancement': [
                        {
                            'title': 'Expand Existing Accessibility Measures with Cultural Competency',
                            'description': 'Enhance current accessibility practices by incorporating cultural competency considerations, addressing diverse learning styles and preferences, and ensuring AI implementations respect varied cultural and linguistic backgrounds.',
                            'implementation_steps': [
                                'Review existing accessibility measures for cultural inclusivity gaps',
                                'Engage diverse student focus groups to identify additional needs',
                                'Develop cultural competency guidelines for AI tool selection and implementation',
                                'Create ongoing assessment mechanism for inclusive practice effectiveness'
                            ],
                            'success_metrics': ['Cultural inclusivity review completed', 'Focus group recommendations implemented', 'Assessment mechanism operational'],
                            'timeframe': '2-4 months',
                            'priority': 'medium'
                        }
                    ]
                },
                'teaching_focused': {
                    'new_implementation': [
                        {
                            'title': 'Develop Alternative Assessment Pathways for Diverse Learning Needs',
                            'description': 'Create multiple assessment options accommodating different learning styles, technical capabilities, and cultural backgrounds while maintaining academic standards and ensuring fair evaluation of student learning outcomes.',
                            'implementation_steps': [
                                'Design alternative assessment formats for students who cannot or prefer not to use AI',
                                'Create flexibility guidelines for faculty to adapt assessments for diverse needs',
                                'Develop support resources for students navigating different assessment options',
                                'Implement quality assurance processes to ensure alternative assessments maintain academic rigour'
                            ],
                            'success_metrics': ['Alternative assessment options available in all courses', 'Student satisfaction with options >4/5', 'Academic standards maintained across all pathways'],
                            'timeframe': '3-5 months',
                            'priority': 'high'
                        }
                    ]
                }
            }
        }
        
        # JISC 2023-based practical implementation templates
        self.jisc_2023_templates = {
            'accountability': {
                'research_university': [
                    {
                        'title': 'Develop Research-Grade AI Competency Requirements',
                        'description': 'Establish mandatory AI literacy requirements for research-active faculty, including understanding of AI capabilities and limitations, ethical considerations in research contexts, and best practices for AI-assisted scholarly work.',
                        'implementation_steps': [
                            'Create competency framework specific to research contexts and methodologies',
                            'Develop assessment mechanism to verify faculty AI literacy levels',
                            'Provide targeted training programmes for different research disciplines',
                            'Implement continuing education requirements for faculty using AI in research'
                        ],
                        'success_metrics': ['Competency framework approved', 'Faculty assessment system operational', '>85% faculty meet basic competency requirements'],
                        'timeframe': '4-6 months',
                        'priority': 'high'
                    }
                ],
                'teaching_focused': [
                    {
                        'title': 'Create Teaching-Focused AI Professional Development Programme',
                        'description': 'Implement comprehensive professional development initiative specifically designed for teaching faculty, focusing on pedagogical applications of AI, assessment design in AI contexts, and student support strategies.',
                        'implementation_steps': [
                            'Design modular training programme addressing core teaching challenges with AI',
                            'Create peer mentoring system pairing experienced and novice AI users',
                            'Develop online resource library with practical teaching examples and case studies',
                            'Establish ongoing support network for faculty implementing AI-enhanced teaching'
                        ],
                        'success_metrics': ['Training programme launched', 'Mentoring system operational with >50 participants', 'Resource library with >200 materials'],
                        'timeframe': '3-5 months',
                        'priority': 'high'
                    }
                ]
            },
            'transparency': {
                'all_institutions': [
                    {
                        'title': 'Implement Comprehensive Stakeholder Communication Strategy',
                        'description': 'Develop multi-channel communication approach ensuring all institutional stakeholders understand AI policies, implementation decisions, and ongoing developments through accessible, regular, and meaningful engagement.',
                        'implementation_steps': [
                            'Create stakeholder mapping identifying all relevant community groups',
                            'Develop communication materials tailored to different audience needs and preferences',
                            'Establish regular communication schedule with predictable updates and opportunities for feedback',
                            'Implement feedback collection and response system with public accountability measures'
                        ],
                        'success_metrics': ['Communication strategy launched', 'All stakeholder groups receiving targeted updates', 'Feedback response rate >30%'],
                        'timeframe': '2-4 months',
                        'priority': 'medium'
                    }
                ]
            }
        }
        
        # BERA 2018 ethical principles adapted for AI contexts
        self.bera_2018_templates = {
            'human_agency': {
                'research_university': [
                    {
                        'title': 'Implement Informed Consent Framework for AI-Assisted Research',
                        'description': 'Develop comprehensive informed consent procedures for research involving AI tools, ensuring participants understand AI involvement, data usage, and potential implications while maintaining research ethics standards.',
                        'implementation_steps': [
                            'Update research ethics protocols to address AI-specific consent requirements',
                            'Create template consent forms with clear AI disclosure language',
                            'Train research ethics board members on AI-related ethical considerations',
                            'Implement ongoing consent verification for longitudinal studies using AI'
                        ],
                        'success_metrics': ['Updated ethics protocols approved', 'Template forms available', 'Ethics board training completed'],
                        'timeframe': '2-4 months',
                        'priority': 'high'
                    }
                ]
            },
            'inclusiveness': {
                'all_institutions': [
                    {
                        'title': 'Establish Participant Welfare Protection in AI Contexts',
                        'description': 'Create robust safeguards ensuring AI implementation does not harm student welfare, academic progress, or personal development, with particular attention to vulnerable populations and those who may be disadvantaged by AI adoption.',
                        'implementation_steps': [
                            'Conduct impact assessment identifying potential welfare risks from AI implementation',
                            'Develop early warning system to identify students experiencing difficulties with AI integration',
                            'Create support services specifically addressing AI-related academic challenges',
                            'Implement regular welfare monitoring and intervention protocols'
                        ],
                        'success_metrics': ['Impact assessment completed', 'Early warning system operational', 'Support services utilised by >5% student body'],
                        'timeframe': '3-6 months',
                        'priority': 'high'
                    }
                ]
            }
        }
        
        # Implementation timeframes based on complexity and urgency
        self.implementation_timeframes = {
            'critical': '1-2 months',
            'high': '2-4 months', 
            'medium': '3-6 months',
            'low': '6-12 months',
            'strategic': '12+ months'
        }
        
        # Institution type characteristics for contextual matching
        self.institution_characteristics = {
            'research_university': {
                'priorities': ['research_integrity', 'publication_ethics', 'graduate_supervision', 'grant_compliance'],
                'stakeholders': ['faculty', 'graduate_students', 'research_staff', 'external_collaborators'],
                'complexity_factors': ['multi_disciplinary', 'international_collaboration', 'high_risk_research']
            },
            'teaching_focused': {
                'priorities': ['student_learning', 'assessment_quality', 'pedagogical_innovation', 'student_support'],
                'stakeholders': ['undergraduate_students', 'teaching_faculty', 'academic_support_staff'],
                'complexity_factors': ['diverse_student_body', 'varying_technical_literacy', 'resource_constraints']
            },
            'technical_institute': {
                'priorities': ['technical_accuracy', 'industry_relevance', 'practical_skills', 'innovation'],
                'stakeholders': ['technical_faculty', 'industry_partners', 'technical_students'],
                'complexity_factors': ['rapid_technology_change', 'industry_integration', 'specialised_equipment']
            }
        }

    def generate_recommendations(self, gaps: List[Dict], classification: str, 
                               themes: List[Dict], text: str = "") -> List[Dict]:
        """
        Generate contextual, detailed recommendations using multi-dimensional matching.
        
        Args:
            gaps: Identified gaps from EthicalFrameworkAnalyzer
            classification: Policy classification (restrictive/moderate/permissive)
            themes: Extracted themes for context
            text: Original text for existing policy detection
            
        Returns:
            List of detailed, contextual recommendations with implementation guidance
        """
        # Determine institution context for targeted recommendations
        institution_context = self._analyze_institution_context(themes, text)
        
        # Detect existing policies to determine enhancement vs new implementation
        existing_policies = self._detect_existing_policies(text) if text else {}
        
        recommendations = []
        used_combinations = set()  # Prevent exact duplicates
        
        # Process each gap with sophisticated matching logic
        for gap in gaps[:8]:  # Limit to top 8 gaps for quality over quantity
            dimension = gap['dimension']
            priority = gap.get('priority', 'medium')
            current_score = gap.get('current_score', 0)
            
            # Determine implementation approach based on existing policies
            has_existing = self._has_existing_provision(gap, existing_policies)
            implementation_type = 'enhancement' if has_existing else 'new_implementation'
            
            # Generate contextual recommendation using multi-dimensional matching
            recommendation = self._generate_contextual_recommendation(
                dimension=dimension,
                institution_context=institution_context,
                implementation_type=implementation_type,
                priority=priority,
                current_score=current_score,
                gap_details=gap
            )
            
            if recommendation:
                # Create unique identifier to prevent duplicates
                combo_key = f"{dimension}_{implementation_type}_{institution_context.get('type', 'general')}"
                if combo_key not in used_combinations:
                    recommendations.append(recommendation)
                    used_combinations.add(combo_key)
        
        # Sort by priority and potential impact
        recommendations.sort(key=lambda x: (
            x.get('priority') != 'critical',
            x.get('priority') != 'high', 
            -x.get('impact_score', 0)
        ))
        
        return recommendations

    def _analyze_institution_context(self, themes: List[Dict], text: str) -> Dict:
        """Determine institution type and characteristics for contextual recommendations."""
        context = {
            'type': 'research_university',  # Default assumption
            'focus_areas': [],
            'complexity_level': 'medium',
            'stakeholder_emphasis': []
        }
        
        if not themes and not text:
            return context
        
        # Combine theme names and text for analysis
        theme_text = ' '.join([t.get('name', '').lower() for t in themes])
        full_text = (text.lower() + ' ' + theme_text) if text else theme_text
        
        # Institution type detection based on content patterns
        research_indicators = ['research', 'publication', 'scholarly', 'graduate', 'phd', 'faculty research']
        teaching_indicators = ['teaching', 'student learning', 'undergraduate', 'classroom', 'pedagogy']
        technical_indicators = ['technical', 'engineering', 'technology', 'industry', 'applied']
        
        research_score = sum(1 for indicator in research_indicators if indicator in full_text)
        teaching_score = sum(1 for indicator in teaching_indicators if indicator in full_text)
        technical_score = sum(1 for indicator in technical_indicators if indicator in full_text)
        
        # Determine primary institution type
        if technical_score > max(research_score, teaching_score):
            context['type'] = 'technical_institute'
        elif teaching_score > research_score * 1.3:
            context['type'] = 'teaching_focused'
        else:
            context['type'] = 'research_university'
        
        # Identify focus areas based on theme analysis
        if any('privacy' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('data_governance')
        if any('integrity' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('academic_integrity')
        if any('research' in t.get('name', '').lower() for t in themes):
            context['focus_areas'].append('research_excellence')
        
        return context

    def _detect_existing_policies(self, text: str) -> Dict:
        """Enhanced detection of existing policy elements."""
        if not text:
            return {}
            
        text_lower = text.lower()
        existing_policies = {}
        
        # Detection patterns for various policy types
        policy_patterns = {
            'disclosure_requirements': [
                'must disclose', 'require.*disclosure', 'acknowledge.*use', 'cite.*ai',
                'transparent.*about', 'declare.*use', 'must be transparent'
            ],
            'approval_processes': [
                'permission.*required', 'approval.*needed', 'instructor.*approval',
                'prior.*authorization', 'seek.*permission', 'faculty.*consent'
            ],
            'governance_structure': [
                'committee', 'working group', 'governance.*board', 'oversight.*body',
                'ai.*team', 'policy.*committee', 'steering.*group'
            ],
            'training_requirements': [
                'training.*required', 'professional.*development', 'competency.*requirements',
                'education.*programme', 'literacy.*training', 'skill.*development'
            ],
            'assessment_guidelines': [
                'assessment.*guidelines', 'evaluation.*criteria', 'grading.*standards',
                'academic.*evaluation', 'marking.*scheme', 'assessment.*policy'
            ],
            'research_protocols': [
                'research.*ethics', 'research.*integrity', 'scholarly.*standards',
                'publication.*requirements', 'research.*guidelines', 'ethics.*review'
            ]
        }
        
        for policy_type, patterns in policy_patterns.items():
            existing_policies[policy_type] = any(
                re.search(pattern, text_lower) for pattern in patterns
            )
        
        return existing_policies

    def _has_existing_provision(self, gap: Dict, existing_policies: Dict) -> bool:
        """Determine if gap area has existing policy coverage."""
        dimension = gap['dimension']
        current_score = gap.get('current_score', 0)
        
        # Mapping of dimensions to relevant existing policies
        dimension_policy_map = {
            'transparency': ['disclosure_requirements', 'assessment_guidelines'],
            'accountability': ['governance_structure', 'approval_processes', 'training_requirements'],
            'human_agency': ['approval_processes', 'assessment_guidelines'],
            'inclusiveness': ['assessment_guidelines', 'training_requirements']
        }
        
        if dimension in dimension_policy_map:
            relevant_policies = dimension_policy_map[dimension]
            if any(existing_policies.get(policy, False) for policy in relevant_policies):
                return True
        
        # Also consider score-based determination
        return current_score > 10  # Threshold for considering existing provision

    def _generate_contextual_recommendation(self, dimension: str, institution_context: Dict,
                                          implementation_type: str, priority: str,
                                          current_score: float, gap_details: Dict) -> Dict:
        """Generate contextual recommendation using multi-dimensional matching."""
        
        institution_type = institution_context.get('type', 'research_university')
        
        # Try UNESCO templates first (most comprehensive)
        if dimension in self.unesco_2023_templates:
            if institution_type in self.unesco_2023_templates[dimension]:
                if implementation_type in self.unesco_2023_templates[dimension][institution_type]:
                    templates = self.unesco_2023_templates[dimension][institution_type][implementation_type]
                    selected_template = templates[0]  # Take first as primary
                    
                    return self._build_recommendation_from_template(
                        selected_template, dimension, institution_context, 
                        implementation_type, current_score, gap_details
                    )
        
        # Fallback to JISC templates
        if dimension in self.jisc_2023_templates:
            if institution_type in self.jisc_2023_templates[dimension]:
                templates = self.jisc_2023_templates[dimension][institution_type]
                selected_template = templates[0]
                
                return self._build_recommendation_from_template(
                    selected_template, dimension, institution_context,
                    implementation_type, current_score, gap_details
                )
        
        # Final fallback to BERA templates
        if dimension in self.bera_2018_templates:
            available_templates = self.bera_2018_templates[dimension].get(
                'all_institutions', 
                self.bera_2018_templates[dimension].get(institution_type, [])
            )
            if available_templates:
                selected_template = available_templates[0]
                
                return self._build_recommendation_from_template(
                    selected_template, dimension, institution_context,
                    implementation_type, current_score, gap_details
                )
        
        # Ultimate fallback - generate basic recommendation
        return self._generate_fallback_recommendation(
            dimension, institution_context, implementation_type, priority
        )

    def _build_recommendation_from_template(self, template: Dict, dimension: str,
                                          institution_context: Dict, implementation_type: str,
                                          current_score: float, gap_details: Dict) -> Dict:
        """Build comprehensive recommendation from selected template."""
        
        # Calculate impact score based on gap severity and template comprehensiveness
        impact_score = self._calculate_impact_score(current_score, template, institution_context)
        
        # Customise title based on implementation type
        base_title = template.get('title', f'Enhance {dimension.replace("_", " ").title()}')
        if implementation_type == 'enhancement':
            if not base_title.startswith('Enhance') and not base_title.startswith('Strengthen'):
                base_title = f"Enhance {base_title}"
        
        # Build comprehensive recommendation object
        recommendation = {
            'title': base_title,
            'description': template.get('description', ''),
            'dimension': dimension,
            'priority': self._adjust_priority_for_context(
                template.get('priority', 'medium'), 
                current_score, 
                institution_context
            ),
            'implementation_type': implementation_type,
            'timeframe': template.get('timeframe', self.implementation_timeframes.get('medium')),
            'impact_score': impact_score,
            'current_score': current_score,
            'expected_improvement': self._estimate_improvement(current_score, template),
            
            # Detailed implementation guidance
            'implementation_steps': template.get('implementation_steps', []),
            'success_metrics': template.get('success_metrics', []),
            'estimated_resources': self._estimate_resources(template, institution_context),
            
            # Academic sourcing and validation
            'source': self._determine_source(template),
            'academic_rationale': self._generate_academic_rationale(dimension, template, institution_context),
            'related_literature': self._get_related_literature(dimension),
            # Frontend expects a list of sources; fall back to related_literature if not provided
            'sources': template.get('sources', self._get_related_literature(dimension)),
            
            # Contextual adaptations
            'institution_specific_notes': self._generate_context_notes(institution_context, implementation_type),
            'stakeholder_considerations': self._identify_stakeholders(dimension, institution_context),
            'potential_challenges': self._identify_challenges(template, institution_context),
            'mitigation_strategies': self._suggest_mitigations(template, institution_context),
            
            # Quality and validation metadata
            'recommendation_confidence': self._calculate_confidence(template, institution_context),
            'evidence_strength': self._assess_evidence_strength(template),
            'implementation_complexity': self._assess_complexity(template, institution_context)
        }
        
        return recommendation

    def _calculate_impact_score(self, current_score: float, template: Dict, 
                               institution_context: Dict) -> float:
        """Calculate potential impact score for recommendation."""
        # Base impact from gap severity (lower current score = higher impact potential)
        gap_impact = max(0, 100 - current_score) / 100 * 40
        
        # Template comprehensiveness bonus
        template_bonus = len(template.get('implementation_steps', [])) * 2
        template_bonus += len(template.get('success_metrics', [])) * 3
        
        # Institution context multiplier
        context_multiplier = 1.0
        if institution_context.get('type') == 'research_university':
            context_multiplier = 1.2  # Research universities have higher impact potential
        elif institution_context.get('type') == 'technical_institute':
            context_multiplier = 1.1
        
        total_impact = (gap_impact + template_bonus) * context_multiplier
        return min(100, max(10, total_impact))  # Cap between 10-100

    def _adjust_priority_for_context(self, base_priority: str, current_score: float,
                                   institution_context: Dict) -> str:
        """Adjust recommendation priority based on context and gap severity."""
        # Critical gaps (score < 5%) get priority boost
        if current_score < 5:
            return 'critical'
        
        # Severe gaps (score < 15%) in important contexts get high priority
        if current_score < 15:
            if institution_context.get('type') == 'research_university':
                return 'high'
            elif base_priority == 'medium':
                return 'high'
        
        # Research universities get priority boost for accountability and transparency
        if (institution_context.get('type') == 'research_university' and 
            base_priority == 'medium'):
            return 'high'
        
        return base_priority

    def _estimate_improvement(self, current_score: float, template: Dict) -> str:
        """Estimate expected improvement from implementing recommendation."""
        # Base improvement from template comprehensiveness
        step_count = len(template.get('implementation_steps', []))
        metric_count = len(template.get('success_metrics', []))
        
        if step_count >= 4 and metric_count >= 3:
            expected_gain = 25 + (100 - current_score) * 0.3
        elif step_count >= 3:
            expected_gain = 20 + (100 - current_score) * 0.2
        else:
            expected_gain = 15 + (100 - current_score) * 0.1
        
        final_score = min(100, current_score + expected_gain)
        
        if expected_gain >= 25:
            return f"Significant improvement expected: {current_score:.1f}% → {final_score:.1f}%"
        elif expected_gain >= 15:
            return f"Moderate improvement expected: {current_score:.1f}% → {final_score:.1f}%"
        else:
            return f"Incremental improvement expected: {current_score:.1f}% → {final_score:.1f}%"

    def _estimate_resources(self, template: Dict, institution_context: Dict) -> Dict:
        """Estimate required resources for implementation."""
        step_count = len(template.get('implementation_steps', []))
        
        # Base resource estimates
        if step_count >= 4:
            staff_time = "Substantial (2-3 FTE months)"
            budget_requirement = "Medium (£10,000-£25,000)"
        elif step_count >= 3:
            staff_time = "Moderate (1-2 FTE months)"
            budget_requirement = "Low-Medium (£5,000-£15,000)"
        else:
            staff_time = "Light (0.5-1 FTE month)"
            budget_requirement = "Low (£1,000-£5,000)"
        
        # Adjust for institution type
        if institution_context.get('type') == 'research_university':
            budget_requirement = budget_requirement.replace('Low', 'Medium').replace('Medium', 'High')
        
        return {
            'staff_time': staff_time,
            'budget_requirement': budget_requirement,
            'specialist_expertise': self._identify_required_expertise(template),
            'external_support': self._assess_external_support_needs(template)
        }

    def _determine_source(self, template: Dict) -> str:
        """Determine primary academic source for recommendation."""
        if 'unesco' in str(template).lower():
            return 'UNESCO 2023'
        elif 'jisc' in str(template).lower():
            return 'JISC 2023'
        elif 'bera' in str(template).lower():
            return 'BERA 2018'
        else:
            return 'PolicyCraft Enhanced Framework'

    def _generate_academic_rationale(self, dimension: str, template: Dict,
                                   institution_context: Dict) -> str:
        """Generate academic rationale for recommendation."""
        rationale_map = {
            'accountability': f"Establishes clear governance structures essential for responsible AI integration in {institution_context.get('type', 'academic')} contexts, addressing institutional risk management and stakeholder trust requirements.",
            
            'transparency': f"Implements disclosure and communication frameworks critical for maintaining academic integrity and enabling informed decision-making by all institutional stakeholders.",
            
            'human_agency': f"Preserves human authority and oversight in educational processes, ensuring AI augments rather than replaces human judgment in critical academic decisions.",
            
            'inclusiveness': f"Addresses equity and accessibility requirements to ensure AI implementation does not create or exacerbate educational inequalities or exclude diverse student populations."
        }
        
        base_rationale = rationale_map.get(dimension, "Addresses critical gap in institutional AI governance.")
        
        # Add context-specific considerations
        if institution_context.get('type') == 'research_university':
            base_rationale += " Particularly important for research integrity and scholarly communication standards."
        elif institution_context.get('type') == 'teaching_focused':
            base_rationale += " Essential for maintaining educational quality and student support effectiveness."
        
        return base_rationale

    def _get_related_literature(self, dimension: str) -> List[str]:
        """Provide related academic literature references."""
        literature_map = {
            'accountability': [
                "Dabis & Csáki (2024) - AI Ethics in Higher Education Policy",
            ],
            'transparency': [
                "UNESCO (2023) - AI Transparency Guidelines",
                "JISC (2023) - Generative AI in Teaching and Learning",
                "Chen et al. (2024) - Global AI Policy Perspectives"            ],
            'human_agency': [
                "BERA (2018) - Ethical Guidelines for Educational Research",
                "Chan & Hu (2023) - Student Perspectives on Generative AI",
                "UNESCO (2023) - Human-Centric AI in Education",
                "Li et al. (2024) - NLP in Policy Research"            ],
            'inclusiveness': [
                "JISC (2023) - Inclusive AI Implementation",
                "Bond et al. (2024) - Equity Considerations in AI Education",
                "An et al. (2025) - Stakeholder Engagement in AI Policies"            ]
        }
        
        return literature_map.get(dimension, ["PolicyCraft Framework Documentation"])

    def _generate_context_notes(self, institution_context: Dict, implementation_type: str) -> str:
        """Generate institution-specific implementation notes."""
        notes = []
        
        institution_type = institution_context.get('type', 'general')
        
        if institution_type == 'research_university':
            notes.append("Consider integration with existing research ethics and integrity frameworks")
            if implementation_type == 'enhancement':
                notes.append("Build on established academic governance structures")
        elif institution_type == 'teaching_focused':
            notes.append("Prioritise student-facing aspects and teaching quality assurance")
            notes.append("Ensure alignment with student support and academic success initiatives")
        elif institution_type == 'technical_institute':
            notes.append("Leverage technical expertise within institution for implementation")
            notes.append("Consider industry partnership opportunities for practical implementation")
        
        if implementation_type == 'enhancement':
            notes.append("Builds on existing policy foundation - focus on strengthening and expanding current provisions")
        else:
            notes.append("New implementation required - establish foundation before building advanced features")
        
        return "; ".join(notes)

    def _identify_stakeholders(self, dimension: str, institution_context: Dict) -> List[str]:
        """Identify key stakeholders for recommendation implementation."""
        base_stakeholders = {
            'accountability': ['Senior Leadership', 'IT Services', 'Legal/Compliance'],
            'transparency': ['Communications Team', 'Student Services', 'Faculty Representatives'],
            'human_agency': ['Academic Affairs', 'Faculty Senate', 'Student Representatives'],
            'inclusiveness': ['Disability Services', 'Diversity & Inclusion Office', 'Student Support']
        }
        
        stakeholders = base_stakeholders.get(dimension, ['Policy Committee'])
        
        # Add institution-specific stakeholders
        if institution_context.get('type') == 'research_university':
            stakeholders.extend(['Research Office', 'Graduate School', 'Ethics Board'])
        elif institution_context.get('type') == 'teaching_focused':
            stakeholders.extend(['Teaching & Learning Centre', 'Academic Support'])
        
        return stakeholders

    def _identify_challenges(self, template: Dict, institution_context: Dict) -> List[str]:
        """Identify potential implementation challenges."""
        challenges = []
        
        step_count = len(template.get('implementation_steps', []))
        if step_count >= 4:
            challenges.append("Complex implementation requiring significant coordination")
        
        if institution_context.get('type') == 'research_university':
            challenges.extend([
                "Faculty autonomy considerations in research contexts",
                "Integration with existing research governance structures"
            ])
        elif institution_context.get('type') == 'teaching_focused':
            challenges.extend([
                "Diverse faculty technical literacy levels",
                "Student resistance to policy changes"
            ])
        
        challenges.extend([
            "Resource allocation and budget constraints",
            "Timeline coordination with academic calendar",
            "Change management and stakeholder buy-in"
        ])
        
        return challenges

    def _suggest_mitigations(self, template: Dict, institution_context: Dict) -> List[str]:
        """Suggest mitigation strategies for identified challenges."""
        mitigations = [
            "Establish clear project governance with defined roles and responsibilities",
            "Implement phased rollout approach to manage complexity and risk",
            "Provide comprehensive training and support for all stakeholders",
            "Create feedback mechanisms for continuous improvement during implementation"
        ]
        
        if institution_context.get('type') == 'research_university':
            mitigations.extend([
                "Engage faculty governance bodies early in planning process",
                "Align implementation with research ethics review cycles"
            ])
        elif institution_context.get('type') == 'teaching_focused':
            mitigations.extend([
                "Provide extensive faculty development and technical support",
                "Create student advisory group to guide policy development"
            ])
        
        return mitigations

    def _calculate_confidence(self, template: Dict, institution_context: Dict) -> str:
        """Calculate confidence level in recommendation effectiveness."""
        confidence_score = 0
        
        # Template quality indicators
        if len(template.get('implementation_steps', [])) >= 3:
            confidence_score += 25
        if len(template.get('success_metrics', [])) >= 2:
            confidence_score += 25
        if template.get('timeframe'):
            confidence_score += 15
        
        # Institution context match
        if institution_context.get('type') in ['research_university', 'teaching_focused']:
            confidence_score += 20
        
        # Source credibility
        source = self._determine_source(template)
        if source in ['UNESCO 2023', 'JISC 2023', 'BERA 2018']:
            confidence_score += 15
        
        if confidence_score >= 80:
            return 'High'
        elif confidence_score >= 60:
            return 'Medium-High'
        elif confidence_score >= 40:
            return 'Medium'
        else:
            return 'Medium-Low'

    def _assess_evidence_strength(self, template: Dict) -> str:
        """Assess strength of evidence supporting recommendation."""
        if 'research' in template.get('description', '').lower():
            return 'Strong - Research-based'
        elif len(template.get('success_metrics', [])) >= 3:
            return 'Good - Measurable outcomes defined'
        elif len(template.get('implementation_steps', [])) >= 4:
            return 'Moderate - Detailed implementation guidance'
        else:
            return 'Basic - General guidance provided'

    def _assess_complexity(self, template: Dict, institution_context: Dict) -> str:
        """Assess implementation complexity."""
        complexity_score = 0
        
        complexity_score += len(template.get('implementation_steps', [])) * 10
        complexity_score += len(template.get('success_metrics', [])) * 5
        
        if institution_context.get('type') == 'research_university':
            complexity_score += 15  # Higher complexity for research contexts
        
        if complexity_score >= 60:
            return 'High'
        elif complexity_score >= 40:
            return 'Medium'
        else:
            return 'Low'

    def _identify_required_expertise(self, template: Dict) -> List[str]:
        """Identify specialist expertise required for implementation."""
        expertise = []
        
        description = template.get('description', '').lower()
        steps = ' '.join(template.get('implementation_steps', [])).lower()
        
        if any(term in description + steps for term in ['technical', 'system', 'platform']):
            expertise.append('Technical/IT specialist')
        if any(term in description + steps for term in ['legal', 'compliance', 'governance']):
            expertise.append('Legal/Compliance expert')
        if any(term in description + steps for term in ['training', 'education', 'development']):
            expertise.append('Professional development specialist')
        if any(term in description + steps for term in ['assessment', 'evaluation', 'measurement']):
            expertise.append('Assessment design expert')
        
        return expertise if expertise else ['General project management']

    def _assess_external_support_needs(self, template: Dict) -> str:
        """Assess whether external support/consultation is needed."""
        complexity_indicators = len(template.get('implementation_steps', []))
        
        if complexity_indicators >= 4:
            return 'Recommended - Complex implementation benefits from external expertise'
        elif complexity_indicators >= 3:
            return 'Optional - Consider for specialised aspects'
        else:
            return 'Not required - Can be implemented with internal resources'

    def _generate_fallback_recommendation(self, dimension: str, institution_context: Dict,
                                        implementation_type: str, priority: str) -> Dict:
        """Generate basic recommendation when no specific template matches."""
        dimension_title = dimension.replace('_', ' ').title()
        
        fallback_recommendations = {
            'accountability': {
                'title': f'Strengthen {dimension_title} Framework',
                'description': f'Develop comprehensive {dimension_title.lower()} measures including clear governance structures, defined responsibilities, and regular compliance monitoring to ensure effective AI policy implementation.',
                'steps': [
                    'Establish governance committee with clear mandate and authority',
                    'Define roles and responsibilities for AI policy oversight',
                    'Implement regular monitoring and compliance assessment procedures',
                    'Create escalation procedures for policy violations or concerns'
                ],
                'sources': [
                    'BERA 2018 – Ethical Guidelines, Principle 2',
                    'UNESCO 2023 – Guidance for Generative AI, pp. 10–12'
                ]
            },
            'transparency': {
                'title': f'Implement {dimension_title} Requirements',
                'description': f'Create comprehensive {dimension_title.lower()} framework requiring clear disclosure of AI usage, accessible communication of policies, and regular stakeholder engagement.',
                'steps': [
                    'Develop clear disclosure requirements for AI usage',
                    'Create accessible policy communication materials',
                    'Establish regular stakeholder consultation processes',
                    'Implement feedback collection and response mechanisms'
                ],
                'sources': [
                    'Jisc 2023 – Generative AI Guide, Section 4.1',
                    'UNESCO 2023 – Guidance for Generative AI, pp. 8–9'
                ]
            },
            'human_agency': {
                'title': f'Preserve {dimension_title} in AI Implementation',
                'description': f'Ensure human authority and oversight remain central to AI-enhanced processes, maintaining human control over critical decisions and preserving educational relationships.',
                'steps': [
                    'Define areas requiring mandatory human oversight',
                    'Establish clear protocols for human authority in AI-assisted decisions',
                    'Train staff on appropriate human-AI collaboration approaches',
                    'Implement regular review of human oversight effectiveness'
                ],
                'sources': [
                    'UNESCO 2023 – Guidance for Generative AI, p. 22',
                    'Selwyn et al. 2020 – Machine Learning & Emotional Tenor'
                ]
            },
            'inclusiveness': {
                'title': f'Develop {dimension_title} Framework',
                'description': f'Create comprehensive {dimension_title.lower()} measures ensuring equitable AI access, addressing diverse needs, and preventing discriminatory outcomes.',
                'steps': [
                    'Conduct accessibility audit of AI tools and processes',
                    'Develop alternative pathways for diverse learning needs',
                    'Implement bias monitoring and mitigation procedures',
                    'Create support mechanisms for underrepresented groups'
                ],
                'sources': [
                    'UNESCO 2023 – Guidance for Generative AI, pp. 16–18',
                    'Corrigan et al. 2023 – ChatGPT Pedagogical Affordances'
                ]
            }
        }
        
        template = fallback_recommendations.get(dimension, fallback_recommendations['accountability'])
        
        return {
            'title': template['title'],
            'description': template['description'],
            'dimension': dimension,
            'priority': priority,
            'implementation_type': implementation_type,
            'timeframe': self.implementation_timeframes.get(priority, '3-6 months'),
            'implementation_steps': template['steps'],
            'source': 'PolicyCraft Fallback Framework',
            'sources': template.get('sources', []),
            'recommendation_confidence': 'Medium',
            'implementation_complexity': 'Medium'
        }

    def _generate_enhanced_fallback(self, classification: Dict, themes: List[Dict], error_msg: str) -> Dict:
        """
        🔧 ENHANCED: Generate informative fallback when main process fails.
        
        Provides basic recommendations while preserving error information for debugging.
        """
        
        basic_recommendations = [
            {
                'title': 'Policy Review and Enhancement',
                'description': 'Conduct comprehensive review of current AI policy to ensure alignment with best practices and address identified gaps.',
                'priority': 'high',
                'source': 'Fallback',
                'timeframe': '3-6 months',
                'implementation_type': 'review',
                'dimension': 'general'
            },
            {
                'title': 'Stakeholder Consultation Process',
                'description': 'Establish systematic consultation with faculty, students, and staff to gather feedback on AI policy effectiveness.',
                'priority': 'medium', 
                'source': 'Fallback',
                'timeframe': '1-3 months',
                'implementation_type': 'new',
                'dimension': 'engagement'
            }
        ]
        
        return {
            'analysis_metadata': {
                'generated_date': datetime.now().isoformat(),
                'framework_version': 'fallback-2.0',
                'methodology': 'Enhanced Fallback Template',
                'error_info': {
                    'error_message': error_msg,
                    'fallback_reason': 'Main analysis failed, using enhanced fallback'
                }
            },
            'recommendations': basic_recommendations,
            'summary': {
                'total_recommendations': len(basic_recommendations),
                'note': 'Enhanced fallback recommendations due to processing error',
                'debug_available': True
            },
            'debug_info': {
                'classification': classification,
                'theme_count': len(themes) if themes else 0,
                'error_occurred': True
            }
        }

# End of production code
