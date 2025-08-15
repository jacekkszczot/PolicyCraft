"""
Theme extraction module for PolicyCraft.
Identifies key themes and concepts in AI policy documents using spaCy and custom rules.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import re
import logging
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

# Common repeated literals extracted as constants to reduce duplication
PROFESSIONAL_DEVELOPMENT = 'professional development'
RISK_ASSESSMENT = 'risk assessment'

# NLP libraries
try:
    import spacy
    from spacy.matcher import Matcher, PhraseMatcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. Install with: pip install spacy")

logger = logging.getLogger(__name__)

# String constants for theme categories and patterns
ACADEMIC_INTEGRITY = "academic integrity"
RESEARCH_ETHICS = "research ethics"
INFORMED_CONSENT = "informed consent"
ETHICAL_GUIDELINES = "ethical guidelines"
DATA_PROTECTION = "data protection"
STAKEHOLDER_ENGAGEMENT = "stakeholder engagement"
ETHICAL_FRAMEWORK = "ethical framework"
RESEARCH_INTEGRITY = "research integrity"
RESPONSIBLE_AI = "responsible ai"
ETHICAL_AI = "ethical ai"


class ThemeExtractor:
    """
    Advanced theme extraction and analysis for AI policy documents.
    
    This class provides comprehensive theme extraction capabilities specifically
    designed for analysing AI policy documents in higher education contexts. It
    combines multiple natural language processing techniques to identify and
    categorise key themes, including:
    
    - Pattern matching for policy-specific phrases and terminology
    - Keyword frequency analysis across predefined theme categories
    - Named entity recognition for policy-relevant entities
    
    The extractor is pre-configured with common AI policy themes such as academic
    integrity, AI ethics, transparency, bias and fairness, privacy, and more.
    
    Note:
        For optimal performance, the spaCy library should be installed. If not
        available, the class will fall back to a simpler keyword-based approach.
    """
    
    def __init__(self, model_name: str = 'en_core_web_sm'):
        """
        Initialise a new ThemeExtractor instance with the specified spaCy model.
        
        This constructor sets up the theme extraction pipeline, including:
        - Loading the specified spaCy language model
        - Initialising pattern matchers for policy themes
        - Configuring theme categories and their associated keywords
        
        Args:
            model_name: The name of the spaCy language model to use.
                      Defaults to 'en_core_web_sm' (small English model).
                      
        Note:
            If the specified spaCy model is not available, the extractor will
            automatically fall back to a keyword-based approach with reduced
            functionality. A warning will be printed in this case.
        """
        self.model_name = model_name
        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None
        
        # Policy theme categories with keywords
        self.theme_categories = {
            'Academic Integrity': {
                'keywords': ['plagiarism', 'cheating', 'academic', 'integrity', 'dishonesty', 'misconduct', 
                           'citation', 'attribution', 'originality', 'authorship', 'collaboration'],
                'patterns': [
                    ACADEMIC_INTEGRITY, 'academic misconduct', 'academic dishonesty',
                    'proper citation', 'original work', 'intellectual honesty'
                ]
            },
            
            'Research Ethics in AI': {
                'keywords': [RESEARCH_ETHICS, ETHICAL_GUIDELINES, INFORMED_CONSENT, 'participant rights',
                           DATA_PROTECTION, 'privacy', 'confidentiality', 'anonymity', 'transparency',
                           'integrity', 'accountability', 'responsibility', 'beneficence', 'non-maleficence',
                           'justice', 'fairness', 'equity', 'respect', 'dignity', 'autonomy', 'trust',
                           STAKEHOLDER_ENGAGEMENT, 'participant involvement', 'ethical oversight',
                           'institutional review', 'research governance', 'ethical approval', 'ethical review',
                           'ethical principles', ETHICAL_FRAMEWORK, 'ethical standards', 'ethical practices',
                           'cross-institutional research', 'interdisciplinary collaboration', 'methodological rigor',
                           'empirical validation', 'systematic reviews', 'meta-analysis', 'research gaps',
                           'collaboration needs', 'methodological issues', 'rigor improvement', 'longitudinal studies',
                           'mixed-methods approaches', 'transparent reporting', 'reproducible research'],
                'patterns': [
                    'ethical research', RESEARCH_INTEGRITY, 'ethical approval process',
                    f'{INFORMED_CONSENT} process', 'participant information sheet', 'ethical considerations',
                    'research governance framework', 'ethical review board', 'institutional review board',
                    'research ethics committee', f'{ETHICAL_GUIDELINES} for research', 'responsible research',
                    'ethical data collection', f'{DATA_PROTECTION} in research', 'privacy in research',
                    'confidentiality agreement', 'anonymization of data', 'pseudonymization of data',
                    'participant confidentiality', 'data security measures', 'ethical data sharing',
                    'research data management', 'ethical implications', 'risk benefit analysis',
                    'vulnerable participants', f'{INFORMED_CONSENT} form', 'voluntary participation',
                    'right to withdraw', 'debriefing participants', 'ethical decision making',
                    'cross-institutional collaboration', 'interdisciplinary research teams',
                    'methodological rigor in ai research', 'empirical validation of ai tools',
                    'systematic review of ai applications', 'meta-analysis of ai in education',
                    'identifying research gaps in ai', 'collaboration in ai research',
                    'methodological challenges in ai studies', 'improving rigor in ai research',
                    'longitudinal ai research studies', 'mixed-methods ai research',
                    'transparent research reporting', 'reproducible ai research',
                    f'{ETHICAL_AI} research practices'
                ]
            },
            
            'AI Ethics': {
                'keywords': ['ethics', 'ethical', 'moral', 'responsible', 'harm', 'benefit',
                           'rights', 'dignity', 'respect', 'justice', 'welfare',
                           'manipulation', 'deception', 'exploitation', 'vulnerability', 'autonomy',
                           RESEARCH_ETHICS, INFORMED_CONSENT, 'participant rights', DATA_PROTECTION,
                           'privacy', 'confidentiality', 'anonymity', 'integrity', 'accountability',
                           'beneficence', 'non-maleficence', STAKEHOLDER_ENGAGEMENT, 'ethical oversight'],
                'patterns': [
                    ETHICAL_AI, RESPONSIBLE_AI, 'ai ethics', 'ethical considerations',
                    'moral implications', ETHICAL_GUIDELINES, 'human dignity',
                    'human manipulation', 'behavioral manipulation', 'exploitation prevention',
                    'vulnerable groups protection', 'human autonomy', f'{RESEARCH_ETHICS} in ai',
                    f'{ETHICAL_AI} research', 'ai research governance', f'{ETHICAL_AI} development',
                    f'ai and {RESEARCH_INTEGRITY}', f'{RESPONSIBLE_AI} research'
                ]
            },
            
            'Transparency': {
                'keywords': ['transparency', 'transparent', 'disclosure', 'open', 'clarity',
                           'explainable', 'interpretable', 'understandable', 'visible'],
                'patterns': [
                    'ai transparency', 'algorithmic transparency', 'model transparency',
                    'explainable ai', 'interpretable ai', 'black box', 'ai disclosure'
                ]
            },
            
            'Bias and Fairness': {
                'keywords': ['bias', 'biased', 'fairness', 'fair', 'discrimination', 'equity',
                           'equality', 'inclusive', 'diverse', 'representation', 'prejudice',
                           'social scoring', 'biometric categorization', 'protected characteristics',
                           'demographic bias', 'algorithmic fairness', 'bias mitigation', 'equitable outcomes',
                           'cultural bias', 'gender bias', 'socioeconomic bias', 'fairness gaps', 'bias audits',
                           'disparate impact', 'equity in education', 'inclusive design', 'bias awareness',
                           'fairness metrics', 'bias detection', 'unconscious bias', 'systemic bias'],
                'patterns': [
                    'algorithmic bias', 'ai bias', 'bias mitigation strategies', 'fair ai',
                    'bias detection', 'discrimination prevention', 'inclusive ai',
                    'social credit system', 'biometric identification', 'protected groups',
                    'fairness in ai', 'equity in algorithms', 'bias in ai tools',
                    'mitigating bias in education', 'ai fairness framework', 'bias audit protocols',
                    'continuous bias monitoring', 'ai equity assessment', 'bias risk assessment',
                    'fairness in automated decisions', 'bias in student assessment',
                    'ai transparency and fairness', 'bias in machine learning',
                    'fairness in educational technology', 'bias in ai training data',
                    'algorithmic fairness standards', 'bias in educational ai',
                    'fairness in automated grading', 'bias in ai recommendations'
                ]
            },
            
            'AI Ethics and Governance': {
                'keywords': ['ethics', 'ethical', 'governance', 'accountability', 'transparency',
                           'responsible ai', 'ethical ai', 'ai policy', 'regulation', 'compliance',
                           'ethical guidelines', 'ai oversight', 'responsible innovation', 'trustworthy ai',
                           'ai ethics board', 'ethical framework', 'ai governance framework',
                           'ethical decision making', 'ai risk management', 'stakeholder engagement',
                           'institutional strategies', 'policy enforcement', 'monitoring mechanisms',
                           'sanctioning mechanisms', 'policy adoption', 'draft policies', 'formal policies',
                           'enforcement mechanisms', 'policy development', 'standardized guidelines',
                           'policy templates', 'policy compliance', 'institutional variation', 'regional contexts'],
                'patterns': [
                    'ethical ai development', 'ai governance model', 'responsible ai practices',
                    'ai ethics framework', 'transparent ai systems', 'accountable ai',
                    'ai policy development', 'ethical guidelines for ai', 'ai oversight committee',
                    'trust in ai systems', 'ai risk assessment', 'stakeholder involvement in ai',
                    'ethical ai implementation', 'ai governance structure', 'ai policy compliance',
                    'ethical ai use in education', 'ai decision making process', 'ai impact assessment',
                    'ai transparency standards', 'ai accountability framework',
                    'institutional ai strategies', 'ai policy enforcement', 'monitoring ai compliance',
                    'sanctioning ai misuse', 'ai policy adoption rates', 'draft ai policies',
                    'formal ai policies', 'enforcing ai policies', 'developing ai policies',
                    'standardized ai guidelines', 'ai policy templates', 'ensuring policy compliance',
                    'institutional variations in ai policy', 'regional ai policy contexts',
                    'faculty involvement in ai policy', 'student input in ai policy',
                    'ai policy implementation gaps', 'ai policy monitoring tools'
                ]
            },
            
            'Privacy and Data': {
                'keywords': ['privacy', 'private', 'data', 'personal', 'confidential', 'gdpr',
                           'consent', 'anonymization', 'protection', 'security', 'information',
                           'biometric', 'surveillance', 'monitoring', 'tracking', 'identification',
                           'data retention', 'data minimization', 'purpose limitation'],
                'patterns': [
                    'data privacy', 'personal data', 'data protection', 'privacy rights',
                    'data security', 'informed consent', 'data anonymization',
                    'biometric data', 'real-time identification', 'public surveillance',
                    'data retention policy', 'purpose limitation principle'
                ]
            },
            
            'GenAI in Learning and Assessment': {
                'keywords': ['generative ai', 'genai', 'ai-assisted learning', 'ai in assessment', 'automated grading',
                           'personalized learning', 'adaptive learning', 'learning analytics', 'formative assessment',
                           'summative assessment', 'proctoring', 'exam integrity', 'plagiarism detection', 'ai grading',
                           'automated feedback', 'learning analytics', 'student performance prediction', 'early warning',
                           'learning design', 'curriculum development', 'content generation', 'automated question generation',
                           'automated essay scoring', 'automated coding assessment', 'automated math assessment',
                           'automated language assessment', 'automated science assessment', 'automated art assessment',
                           'automated music assessment', 'automated design assessment', 'automated engineering assessment',
                           'chatgpt', 'assignment', 'prompt', 'class', 'design', 'visual media', 'interactive', 'multimodal',
                           'image generation', 'code generation', 'academic integrity', 'authentic assessment',
                           'process-oriented', 'higher-order thinking', 'alternative formats', 'oral exams',
                           'collaborative projects', 'in-person assessments', 'assignment design', 'prompt engineering',
                           'visual generation', 'interactive media', 'multimodal learning', 'academic honesty',
                           'policy enforcement', 'educational standards', 'assignment submission', 'policy compliance',
                           'academic conduct', 'syllabus statements', 'writing expectations', 'academic violations'],
                'patterns': [
                    'ai in learning and assessment', 'generative ai in education', 'ai-assisted assessment',
                    'automated grading systems', 'personalized learning with ai', 'adaptive learning technologies',
                    'learning analytics dashboard', 'formative assessment with ai', 'summative assessment with ai',
                    'ai proctoring solutions', 'exam integrity with ai', 'plagiarism detection using ai',
                    'ai-powered feedback', 'student performance analytics', 'early warning systems in education',
                    'learning design with ai', 'ai in curriculum development', 'automated content generation',
                    'ai for question generation', 'automated essay evaluation', 'ai in coding assessment',
                    'automated math problem solving', 'language learning with ai', 'ai in science education',
                    'ai in arts education', 'music education with ai', 'design education with ai',
                    'engineering education with ai', 'ai in medical education', 'ai in legal education',
                    'ai in business education', 'ai in social sciences', 'ai in humanities',
                    'ai in stem education', 'ai in steam education', 'automated assessment systems',
                    'ai in evaluation methods', 'automated marking systems', 'ai in scoring rubrics',
                    'genai in assignments', 'ai-assisted learning', 'automated grading', 'personalized learning with ai',
                    'adaptive learning technologies', 'ai in formative assessment', 'ai for summative assessment',
                    'intelligent tutoring systems', 'ai-generated feedback', 'assignment redesign with ai',
                    'competency-based assessment', 'ai and learning analytics', 'visual media generation',
                    'interactive ai tools', 'multimodal learning experiences', 'ai in visual arts',
                    'ai for code generation', 'ai in programming education', 'ai and academic integrity',
                    'detecting ai-generated content', 'authentic assessment design', 'process-oriented assessment',
                    'higher-order thinking skills', 'alternative assessment formats', 'oral examination with ai',
                    'collaborative ai projects', 'in-person assessment methods', 'ai in assignment design',
                    'effective prompt engineering', 'visual content creation', 'interactive learning tools',
                    'multimodal content generation', 'ai and academic honesty', 'enforcing ai policies',
                    'academic standards with ai', 'ai in assignment submission', 'ai policy compliance',
                    'ai in academic conduct', 'syllabus statements on ai', 'writing expectations with ai',
                    'preventing ai violations', 'ai in academic integrity'
                    'ai policy compliance', 'ai in academic conduct', 'syllabus statements on ai',
                    'writing expectations with ai', 'preventing ai violations', 'ai in academic integrity',
                    'course-specific ai policies', 'ai detection in education', 'ferpa and ai tools',
                    'ai use disclosure', 'proper attribution of ai', 'faculty autonomy in ai use',
                    'university ai guidelines', 'ai policy templates', 'ai in higher education'
                ]
            },
            
            'Accountability': {
                'keywords': ['accountability', 'accountable', 'responsibility', 'responsible',
                           'liable', 'liability', 'oversight', 'governance', 'control'],
                'patterns': [
                    'ai accountability', 'algorithmic accountability', 'responsible ai',
                    'ai governance', 'human oversight', 'ai responsibility'
                ]
            },
            
            'Assessment and Evaluation': {
                'keywords': ['assessment', 'evaluation', 'testing', 'validation', 'verification',
                           'audit', 'review', 'examination', 'grading', 'marking'],
                'patterns': [
                    'ai assessment', 'automated grading', 'ai evaluation', 'algorithm testing',
                    'ai-assisted assessment', 'automated marking', 'evaluation criteria'
                ]
            },
            
            'Student Perspectives on AI': {
                'keywords': ['student perspective', 'student voice', 'learner experience', 'student feedback',
                           'student perceptions', 'student concerns', 'student benefits', 'student challenges',
                           'academic integrity', 'ai literacy', 'policy awareness', 'student needs',
                           'learning enhancement', 'creativity support', 'personalized learning', 'academic support',
                           'misuse concerns', 'over-reliance', 'skill development', 'student empowerment'],
                'patterns': [
                    'student views on ai', 'ai in student learning', 'ai for academic support',
                    'student ai literacy', 'ethical ai use by students', 'ai and academic integrity',
                    'student ai policy awareness', 'ai for personalized learning', 'ai in coursework',
                    'student research with ai', 'ai for student productivity', 'ai and student creativity',
                    'student concerns about ai', 'ai policy for students', 'student centered ai policies',
                    'ai in higher education', 'student ai training', 'ai for student success',
                    'student engagement with ai', 'ai and student assessment'
                ]
            },
            
            'Student Guidelines': {
                'keywords': ['student', 'students', 'learner', 'pupil', 'coursework', 'assignment',
                           'homework', 'submission', 'project', 'essay', 'report',
                           'ai literacy', 'academic integrity', 'responsible use', 'policy awareness',
                           'skill development', 'learning enhancement', 'creativity support', 'personalization'],
                'patterns': [
                    'student use', 'student guidelines', 'assignment policy', 'coursework rules',
                    'student responsibilities', 'ai in assignments', 'student conduct',
                    'ai literacy for students', 'responsible ai use', 'academic integrity with ai',
                    'student ai policy', 'ai for learning enhancement', 'ai in student work',
                    'student ai training', 'ai for academic success', 'student ai best practices'
                ]
            },
            
            'Socio-Emotional Impact of AI': {
                'keywords': ['emotional impact', 'teacher emotions', 'student emotions', 'classroom dynamics',
                           'human agency', 'autonomy', 'trust', 'anxiety', 'excitement', 'adaptation',
                           'teacher-student relationship', 'emotional labor', 'wellbeing', 'stress',
                           'emotional adaptation', 'emotional readiness', 'emotional intelligence',
                           'socio-emotional learning', 'emotional response', 'psychological impact'],
                'patterns': [
                    'socio-emotional impact', 'emotional dynamics of ai', 'ai and teacher emotions',
                    'human agency in ai', 'teacher autonomy with ai', 'ai and classroom dynamics',
                    'emotional labor of teaching with ai', 'ai and student wellbeing',
                    'emotional adaptation to technology', 'ai and teacher stress',
                    'trust in ai systems', 'ai and emotional intelligence',
                    'psychological impact of ai', 'ai and socio-emotional learning',
                    'emotional responses to automation', 'ai and human connection'
                ]
            },
            
            'Faculty Guidelines': {
                'keywords': ['faculty', 'teacher', 'instructor', 'professor', 'staff', 'educator',
                            'teaching', 'pedagogy', 'curriculum', 'course', 'classroom',
                            'emotional impact', 'autonomy', 'trust', 'agency', 'decision-making',
                            PROFESSIONAL_DEVELOPMENT, 'training', 'support', 'guidance'],
                'patterns': [
                    'faculty guidelines', 'instructor policy', 'teaching with ai',
                    'faculty responsibilities', 'classroom ai', 'pedagogical use',
                    'ai and teacher autonomy', 'faculty training on ai', 'ai in teaching practice',
                    'educator support for ai', 'ai decision-making in education',
                    'faculty ai literacy', 'ai and teaching methods', 'educator ai resources'
                ]
            },
            
            'NLP and Text Analysis': {
                'keywords': ['text mining', 'natural language processing', 'nlp', 'topic modeling', 'sentiment analysis',
                           'text classification', 'keyword extraction', 'document analysis', 'text preprocessing',
                           'feature extraction', 'machine learning', 'deep learning', 'text analytics', 'corpus analysis',
                           'semantic analysis', 'syntactic analysis', 'discourse analysis', 'content analysis',
                           'information retrieval', 'text summarization', 'named entity recognition', 'part-of-speech tagging'],
                'patterns': [
                    'natural language processing', 'text mining techniques', 'topic modeling with lda',
                    'sentiment analysis of text', 'document classification', 'keyword extraction methods',
                    'text preprocessing pipeline', 'feature extraction from text', 'machine learning for nlp',
                    'deep learning in text analysis', 'text analytics pipeline', 'corpus linguistics',
                    'semantic text analysis', 'syntactic parsing', 'discourse analysis methods',
                    'content analysis framework', 'information retrieval systems', 'automated text summarization',
                    'named entity recognition', 'part-of-speech tagging', 'text classification algorithms',
                    'bias detection in text', 'text data visualization', 'text mining applications', 'nlp in policy analysis'
                ]
            },
            
            'Research and Innovation': {
                'keywords': ['research', 'innovation', 'development', 'advancement', 'discovery',
                           'investigation', 'study', 'experiment', 'analysis', 'methodology',
                           'text mining', 'nlp', 'topic modeling', 'sentiment analysis', 'machine learning',
                           'data science', 'artificial intelligence', 'computational methods', 'quantitative analysis',
                           'qualitative analysis', 'mixed methods', 'empirical research', 'theoretical framework'],
                'patterns': [
                    'ai research', 'research ethics', 'innovation policy', 'research integrity',
                    'ai development', 'research methodology', 'scientific research', 'nlp in research',
                    'text mining for research', 'machine learning applications', 'data science methods',
                    'computational social science', 'quantitative text analysis', 'qualitative text analysis',
                    'mixed methods research', 'empirical study', 'theoretical framework', 'research design',
                    'experimental methods', 'case study research', 'longitudinal study', 'cross-sectional analysis',
                    'systematic literature review', 'meta-analysis', 'research validation', 'reproducible research'
                ]
            },
            
            'Regulatory Compliance': {
                'keywords': ['regulation', 'compliance', 'legislation', 'law', 'act', 'directive',
                           'standard', 'requirement', 'obligation', 'certification', 'audit',
                           'enforcement', 'conformity', 'assessment', 'prohibition', 'ban',
                           'high-risk', 'unacceptable risk', 'limited risk', 'minimal risk'],
                'patterns': [
                    'ai regulation', 'regulatory framework', 'compliance requirements',
                    'legal obligations', 'risk classification', 'prohibited practices',
                    'high-risk ai', 'ai act', 'eu ai act', 'regulatory compliance',
                    'conformity assessment', 'certification process'
                ]
            },
            
            'AI in Higher Education': {
                'keywords': ['higher education', 'university', 'college', 'campus', 'academic',
                           'tertiary education', 'post-secondary', 'undergraduate', 'graduate',
                           'faculty', 'professor', 'lecturer', 'researcher', 'scholar',
                           'academic integrity', 'plagiarism', 'cheating', 'exam proctoring',
                           'admissions', 'enrollment', 'student records', 'academic advising',
                           'research ethics', 'publication ethics', 'research integrity',
                           'campus safety', 'student life', 'extracurricular', 'student services'],
                'patterns': [
                    'ai in higher education', 'university ai policy', 'college ai guidelines',
                    'ai for academic research', 'ai in academic publishing', 'ai and academic integrity',
                    'ai in student admissions', 'automated exam proctoring', 'ai for student support',
                    'ai in academic advising', 'research ethics ai', 'ai in campus security',
                    'ai for student retention', 'learning analytics in higher education',
                    'ai for faculty support', 'ai in academic administration', 'ai for research assessment',
                    'ai in student assessment', 'ai for curriculum development', 'ai in academic libraries'
                ]
            },
            
            'AI in Education': {
                'keywords': ['education', 'learning', 'teaching', 'pedagogy', 'curriculum',
                           'classroom', 'student', 'teacher', 'instructor', 'faculty',
                           'academic', 'university', 'school', 'higher education', 'lifelong learning',
                           'personalized learning', 'adaptive learning', 'educational technology',
                           'coursework', 'academic work', 'learning management', 'lms', 'vle',
                           'intelligent tutoring', 'learning analytics', 'automated feedback',
                           'collaborative learning', 'educational management', 'student services',
                           'quality assurance', 'remote learning', 'cultural adaptation', 'sdg 4',
                           'k-12', 'primary education', 'secondary education', 'vocational training',
                           'llms', 'ai literacy', 'ai policy', 'ai governance',
                           'ai ethics', 'ai implementation', 'ai adoption', 'ai challenges', 'ai opportunities'],
                'patterns': [
                    'ai in education', 'educational technology', 'digital learning', 'smart classroom',
                    'personalized learning', 'adaptive learning', 'learning analytics', 'edtech',
                    'ai for education', 'education technology', 'digital education', 'ai in teaching',
                    'ai in learning', 'ai in higher education', 'ai in schools', 'ai in universities',
                    'llm applications', 'generative ai in education', 'ai policy in education',
                    'ai governance in academia', 'ai literacy programs', 'ai implementation strategies',
                    'ai adoption challenges', 'ai in curriculum development', 'ai for student success'
                    'academic integrity', 'learning management system', 'virtual learning environment',
                    'intelligent tutoring systems', 'personalized learning', 'learning analytics',
                    'administrative efficiency', 'educational management', 'resource allocation',
                    'student support services', 'quality assurance in education', 'sustainable development goal 4',
                    'inclusive education', 'equitable access', 'lifelong learning opportunities',
                    'ai in k-12 education', 'ai in primary schools', 'ai in secondary education',
                    'vocational training with ai', 'ai for special education', 'inclusive learning with ai'
                ]
            },
            
            'Human-Centric AI in Education': {
                'keywords': ['human rights', 'human-centric', 'ethical ai', 'inclusion', 'equity',
                           'sustainability', 'transparency', 'non-discrimination', 'auditability',
                           'human dignity', 'human agency', 'human oversight', 'human control',
                           'ethical framework', 'human values', 'human wellbeing', 'human development',
                           'social impact', 'cultural sensitivity', 'context awareness'],
                'patterns': [
                    'human rights based approach', 'human centric ai', 'ethical artificial intelligence',
                    'inclusive education', 'equitable ai', 'sustainable development',
                    'transparent algorithms', 'non-discriminatory ai', 'auditable ai systems',
                    'human dignity in ai', 'human agency in education', 'human oversight of ai',
                    'human control over ai', 'ethical framework for ai', 'human values in technology',
                    'human wellbeing and ai', 'human development through ai', 'social impact of ai',
                    'culturally sensitive ai', 'context aware education'
                ]
            },
            
            'AI Implementation in Institutions': {
                'keywords': ['implementation', 'adoption', 'integration', 'deployment', 'rollout',
                           'institutional', 'strategy', 'roadmap', 'stakeholder', 'adoption stages',
                           'exploratory', 'pilot', 'scaling', 'institutional policy', 'governance',
                           'compliance', 'oversight', 'committee', 'steering group', 'working group'],
                'patterns': [
                    'ai implementation', 'institutional adoption', 'ai strategy', 'adoption roadmap',
                    'stakeholder engagement', 'implementation phases', 'pilot program', 'scaling ai',
                    'institutional policy', 'ai governance', 'oversight committee', 'technical integration',
                    'system compatibility', 'lms integration', 'infrastructure requirements', 'resource allocation'
                ]
            },
            
            'AI Literacy and Training': {
                'keywords': ['literacy', 'training', 'skills', 'competencies', 'capacity',
                            PROFESSIONAL_DEVELOPMENT, 'workshop', 'seminar', 'course', 'program',
                            'pedagogical', 'didactic', 'instructional', 'faculty development',
                            'student training', 'digital skills', 'ai competencies', 'workshop',
                            'tutorial', 'handbook', 'guide', 'resource', 'toolkit', 'workshop series',
                            'certification', 'microcredentials', 'upskilling', 'reskilling',
                            'faculty resources', 'staff development', 'continuous learning', 'capacity building'],
                'patterns': [
                    'ai literacy', 'digital literacy', 'ai training', PROFESSIONAL_DEVELOPMENT,
                    'faculty training', 'student training', 'ai skills', 'digital competencies',
                    'ai education program', 'teacher training in ai', 'ai curriculum',
                    'pedagogical training', 'digital upskilling', 'ai workshops', 'training materials',
                    'faculty resources', 'staff development', 'ai certification', 'microcredentials',
                    'continuous learning', 'capacity building', 'training resources', 'faculty guide',
                    'ai toolkit', 'professional learning community', 'faculty learning community'
                ]
            },
            
            'AI Risk Management': {
                'keywords': ['risk', 'safety', 'compliance', 'assessment', 'mitigation',
                           'unacceptable risk', 'high risk', 'limited risk', 'minimal risk',
                           'manipulation', 'deception', 'exploitation', 'vulnerability',
                           'social scoring', 'emotion recognition', 'biometric identification',
                           'biometric categorization', 'critical infrastructure', 'essential services',
                           'law enforcement', 'justice', 'democracy', 'cybersecurity', 'robustness',
                           'transparency', 'disclosure', 'labeling', 'deepfake', 'synthetic media'],
                'patterns': [
                    RISK_ASSESSMENT, 'risk mitigation', 'safety evaluations', 'compliance requirements',
                    'unacceptable risk ai', 'banned ai practices', 'harmful manipulation', 'deceptive ai',
                    'exploitation of vulnerabilities', 'social credit system', 'emotion recognition ban',
                    'real-time biometric identification', 'biometric categorization ban', 'high risk ai systems',
                    'critical infrastructure ai', 'essential services ai', 'law enforcement ai',
                    'ai in justice system', 'ai in democratic processes', 'cybersecurity requirements',
                    'ai robustness standards', 'transparency obligations', 'ai disclosure requirements',
                    'ai content labeling', 'deepfake identification', 'synthetic media labeling'
                ]
            },
            
            'AI Policy and Governance': {
                'keywords': ['policy', 'governance', 'framework', 'guidelines', 'standards',
                           'regulation', 'compliance', 'oversight', 'accountability', 'stewardship',
                           'ethics committee', 'review board', 'policy development', 'implementation',
                           'interdisciplinary', 'intersectoral', 'multistakeholder', 'global coordination',
                           'strategic planning', 'master plan', 'roadmap', 'implementation strategy',
                           'monitoring', 'evaluation', 'impact assessment', 'equity monitoring',
                           'effectiveness evaluation', 'continuous improvement', 'sdg 4', 'sustainable development',
                           'eu ai act', 'artificial intelligence act', 'ai regulation', 'legal framework'],
                'patterns': [
                    'ai policy framework', 'governance structure', 'policy development',
                    'compliance monitoring', 'ethics review', RISK_ASSESSMENT,
                    'stakeholder consultation', 'decision-making framework', 'transparency in ai',
                    'policy implementation', 'monitoring and evaluation', 'interdisciplinary planning',
                    'intersectoral governance', 'multistakeholder collaboration', 'global coordination',
                    'strategic vision', 'master plan development', 'implementation roadmap',
                    'monitoring framework', 'evaluation framework', 'impact assessment',
                    'equity monitoring', 'effectiveness evaluation', 'continuous improvement',
                    'sustainable development goal 4', 'inclusive policy making', 'evidence-based policy',
                    'eu artificial intelligence act', 'ai legal framework', 'ai regulatory requirements',
                    'ai compliance framework', 'ai governance model', 'ai policy development'
                ]
            },
            
            'Institutional Governance and Policy': {
                'keywords': ['governance', 'policy', 'framework', 'guidelines', 'standards',
                           'regulation', 'compliance', 'oversight', 'accountability', 'stewardship',
                           'ethics committee', 'review board', 'policy development', 'implementation'],
                'patterns': [
                    'institutional governance', 'ai policy framework', 'governance structure',
                    'policy development', 'compliance monitoring', 'ethics review',
                    RISK_ASSESSMENT, 'stakeholder consultation', 'decision-making framework',
                    'transparency in ai', 'policy implementation', 'monitoring and evaluation'
                ]
            },
            
            'Academic Integrity and AI': {
                'keywords': ['integrity', 'honesty', 'plagiarism', 'cheating', 'misconduct',
                           'originality', 'authorship', 'attribution', 'citation', 'referencing',
                           'authenticity', 'academic dishonesty', 'contract cheating', 'ghostwriting',
                           'ai-generated content', 'ai-assisted writing'],
                'patterns': [
                    'academic integrity', 'ai and plagiarism', 'ai in academic writing',
                    'ai-generated assignments', 'contract cheating', 'ghostwriting services',
                    'academic honesty', 'original work', 'authorship attribution',
                    'ai detection', 'plagiarism detection', 'citation ethics'
                ]
            }
        }
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            self._initialize_spacy()
        else:
            print("spaCy not available - using fallback keyword extraction")
            
    def _initialize_spacy(self) -> None:
        """
        Initialise the spaCy NLP pipeline and configure pattern matchers.
        
        This private method loads the specified spaCy language model and sets up
        the necessary components for theme extraction, including:
        - Loading the language model
        - Initialising phrase and pattern matchers
        - Configuring theme-specific patterns
        
        Note:
            If the specified model is not available, this method will print an
            error message and leave the nlp attribute as None. The class will
            automatically fall back to keyword-based extraction in this case.
        """
        try:
            self.nlp = spacy.load(self.model_name)
            print(f"spaCy model '{self.model_name}' loaded successfully")
            
            # Initialize matchers
            self.matcher = Matcher(self.nlp.vocab)
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            
            # Add patterns to matchers
            self._setup_patterns()
            
        except OSError:
            print(f"spaCy model '{self.model_name}' not found. Install with: python -m spacy download {self.model_name}")
            self.nlp = None
        except Exception as e:
            print(f"Error initializing spaCy: {e}")
            self.nlp = None
            
    def _setup_patterns(self) -> None:
        """
        Configure pattern matching rules for theme extraction.
        
        This private method sets up the phrase patterns for each theme category
        in the PhraseMatcher. It converts the human-readable theme patterns into
        a format suitable for efficient pattern matching by spaCy.
        
        Note:
            This method requires the spaCy NLP pipeline to be initialised first.
            If nlp is None, this method will return without making any changes.
        """
        if not self.nlp:
            return
            
        # Add phrase patterns for each theme
        for theme_name, theme_data in self.theme_categories.items():
            # Create pattern name
            pattern_name = theme_name.lower().replace(' ', '_')
            
            # Add phrase patterns
            patterns = [self.nlp(phrase) for phrase in theme_data['patterns']]
            self.phrase_matcher.add(pattern_name, patterns)
            
        print(f"Pattern matching setup complete with {len(self.theme_categories)} theme categories")

    def extract_themes(self, text: str, min_frequency: int = 1, max_themes: int = 15) -> List[Dict]:
        """
        Extract and analyse key themes from policy text.
        
        This is the main method for theme extraction. It processes the input text
        to identify and score themes based on the configured theme categories.
        The method automatically selects the appropriate extraction strategy
        (spaCy or keyword-based) based on availability.
        
        Args:
            text: The policy text to analyse. Should be in plain text format.
            min_frequency: Minimum number of keyword matches required for a theme
                         to be included in the results. Defaults to 1.
            max_themes: Maximum number of themes to return, sorted by relevance.
                      Defaults to 15.
                      
        Returns:
            A list of dictionaries, where each dictionary contains information
            about a detected theme, including its name, score, frequency,
            keywords, and example matches.
            
        Example:
            >>> extractor = ThemeExtractor()
            >>> themes = extractor.extract_themes("AI ethics is crucial for...")
            >>> for theme in themes:
            ...     print(f"{theme['name']}: {theme['score']}")
        """
        if not text:
            return []
            
        print(f"Extracting themes from text ({len(text)} characters)")
        
        # Use spaCy if available, otherwise fallback to keyword extraction
        if self.nlp:
            themes = self._extract_themes_spacy(text, min_frequency, max_themes)
        else:
            themes = self._extract_themes_keywords(text, min_frequency, max_themes)
            
        print(f"Extracted {len(themes)} themes")
        return themes

    def _extract_themes_spacy(self, text: str, min_frequency: int, max_themes: int) -> List[Dict]:
        """
        Extract themes from text using the spaCy NLP pipeline.
        
        This private method implements the core theme extraction logic when spaCy
        is available. It uses multiple techniques to identify themes:
        
        1. Pattern matching using pre-configured phrase patterns
        2. Keyword frequency analysis across theme categories
        3. Named entity recognition for policy-relevant entities
        
        Args:
            text: The input text to analyse.
            min_frequency: Minimum number of keyword matches required for a theme.
            max_themes: Maximum number of themes to return.
            
        Returns:
            A list of theme dictionaries, each containing the theme name, score,
            frequency, and related information.
            
        Note:
            This is an internal method and should not be called directly.
            Use the public extract_themes() method instead.
        """
        doc = self.nlp(text)
        
        # Theme scores
        theme_scores = defaultdict(float)
        theme_details = defaultdict(lambda: {'matches': [], 'entities': [], 'keywords': []})
        
        # 1. Pattern matching
        matches = self.phrase_matcher(doc)
        for match_id, start, end in matches:
            theme_name = self._get_theme_from_pattern(self.nlp.vocab.strings[match_id])
            if theme_name:
                matched_text = doc[start:end].text
                theme_scores[theme_name] += 2.0  # Higher weight for exact patterns
                theme_details[theme_name]['matches'].append(matched_text)
        
        # 2. Keyword frequency analysis
        for theme_name, theme_data in self.theme_categories.items():
            keyword_count = 0
            found_keywords = []
            
            for keyword in theme_data['keywords']:
                # Count occurrences (case-insensitive)
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text.lower()))
                if count > 0:
                    keyword_count += count
                    found_keywords.append((keyword, count))
            
            if keyword_count >= min_frequency:
                theme_scores[theme_name] += keyword_count * 0.5  # Lower weight for individual keywords
                theme_details[theme_name]['keywords'] = found_keywords
        
        # 3. Named entity recognition
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'PRODUCT', 'EVENT']:
                # Check if entity relates to AI/technology
                if any(tech_word in ent.text.lower() for tech_word in ['ai', 'artificial', 'algorithm', 'machine', 'data']):
                    theme_scores['AI Technology'] += 0.5
                    theme_details['AI Technology']['entities'].append((ent.text, ent.label_))
        
        # 4. Create final theme list
        return self._format_themes(theme_scores, theme_details, max_themes)

    def _extract_themes_keywords(self, text: str, min_frequency: int, max_themes: int) -> List[Dict]:
        """
        Fallback theme extraction using basic keyword matching.
        
        This method is used when spaCy is not available. It performs a simpler
        form of theme extraction using regular expressions to count keyword
        occurrences and pattern matches in the text.
        
        Args:
            text: The input text to analyse (converted to lowercase).
            min_frequency: Minimum number of keyword matches required for a theme.
            max_themes: Maximum number of themes to return.
            
        Returns:
            A list of theme dictionaries with basic scoring based on keyword
            and pattern frequencies.
            
        Note:
            This method provides reduced functionality compared to the spaCy-based
            approach and is used as a fallback when spaCy is not available.
        """
        text_lower = text.lower()
        theme_scores = defaultdict(int)
        theme_details = defaultdict(lambda: {'keywords': [], 'matches': []})
        
        # Keyword frequency analysis
        for theme_name, theme_data in self.theme_categories.items():
            keyword_count = 0
            found_keywords = []
            
            # Check keywords
            for keyword in theme_data['keywords']:
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                if count > 0:
                    keyword_count += count
                    found_keywords.append((keyword, count))
            
            # Check patterns
            for pattern in theme_data['patterns']:
                count = len(re.findall(r'\b' + re.escape(pattern.lower()) + r'\b', text_lower))
                if count > 0:
                    keyword_count += count * 2  # Higher weight for patterns
                    theme_details[theme_name]['matches'].append((pattern, count))
            
            if keyword_count >= min_frequency:
                theme_scores[theme_name] = keyword_count
                theme_details[theme_name]['keywords'] = found_keywords
        
        return self._format_themes(theme_scores, theme_details, max_themes)

    def _get_theme_from_pattern(self, pattern_name: str) -> Optional[str]:
        """
        Convert a pattern name back to its corresponding theme name.
        
        This helper method maps the internal pattern names used by the matcher
        back to the human-readable theme names defined in the theme categories.
        
        Args:
            pattern_name: The internal pattern name used by the matcher.
            
        Returns:
            The human-readable theme name if a match is found, or None if no
            matching theme is found.
            
        Example:
            >>> self._get_theme_from_pattern('academic_integrity')
            'Academic Integrity'
        """
        pattern_to_theme = {
            theme_name.lower().replace(' ', '_'): theme_name 
            for theme_name in self.theme_categories.keys()
        }
        return pattern_to_theme.get(pattern_name)

    def _format_themes(self, theme_scores: Dict, theme_details: Dict, max_themes: int) -> List[Dict]:
        """
        Format and structure the extracted theme data for output.
        
        This internal method processes the raw theme scores and details into
        a structured format suitable for consumption by other methods. It:
        
        1. Sorts themes by their calculated scores
        2. Limits results to the specified maximum number of themes
        3. Structures the output with consistent field names and types
        
        Args:
            theme_scores: Dictionary mapping theme names to their raw scores.
            theme_details: Dictionary containing detailed information about each theme.
            max_themes: Maximum number of themes to include in the output.
            
        Returns:
            A list of theme dictionaries, each containing:
            - name: The human-readable theme name
            - score: Normalised theme score (float)
            - frequency: Integer count of theme occurrences
            - keywords: List of top keywords associated with the theme
            - matches: List of example text matches
            - confidence: Confidence percentage (0-100)
            
        Note:
            This method normalises scores and ensures consistent output formatting
            across different extraction methods.
        """
        # Sort themes by score
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)

        # Compute document-specific scaling to prevent flat 10/100 values
        raw_values = [float(s) for _, s in sorted_themes] or [0.0]
        max_raw = max(raw_values) if raw_values else 0.0
        if max_raw <= 0:
            return []

        # Format output
        themes = []
        for theme_name, score in sorted_themes[:max_themes]:
            details = theme_details[theme_name]

            raw_score = float(score)
            # Scale relative to the strongest theme in this document
            rel = raw_score / max_raw
            normalised_score = round(rel * 10.0, 2)

            # Confidence mirrors relative strength in [0,100]
            confidence = max(0, min(100, int(rel * 100)))

            theme_data = {
                'name': theme_name,
                'score': normalised_score,
                'frequency': int(raw_score),
                'keywords': [kw[0] for kw in details['keywords'][:5]],  # Top 5 keywords
                'matches': [match[0] if isinstance(match, tuple) else match for match in details['matches'][:3]],  # Top 3 matches
                'confidence': confidence
            }
            
            # Add entities if available
            if 'entities' in details and details['entities']:
                theme_data['entities'] = [ent[0] for ent in details['entities'][:3]]
            
            themes.append(theme_data)
        
        return themes

    def identify_keywords(self, text: Optional[str], top_n: int = 10) -> List[str]:
        """
        Identify prominent keywords from text using configured theme vocab.
        
        This lightweight implementation counts occurrences of all configured
        theme keywords and returns the most frequent unique tokens.
        Falls back to simple tokenisation when no configured keyword matches.
        """
        if not text:
            return []
        text_lower = text.lower()
        counts = Counter()
        # Count configured keywords
        for theme in self.theme_categories.values():
            for kw in theme.get('keywords', []):
                n = len(re.findall(r"\b" + re.escape(kw) + r"\b", text_lower))
                if n:
                    counts[kw] += n
        # Fallback: simple tokenisation if nothing matched
        if not counts:
            tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text_lower)
            counts.update(tokens)
        return [w for w, _ in counts.most_common(max(1, top_n))]

    def calculate_theme_confidence(self, theme: str, text: Optional[str]) -> float:
        """
        Calculate a simple confidence score in [0,1] for a theme within text.
        
        Heuristic: ratio of matched keywords/pattern occurrences to a capped
        denominator to ensure stable values.
        """
        if not text or not theme:
            return 0.0
        text_lower = text.lower()
        theme_def = self._match_theme_def(theme)
        if theme_def is None:
            # Unknown theme: estimate via generic keyword presence
            occurrences = self._count_word_occurrences(text_lower, theme.lower())
            return min(1.0, occurrences / 5.0)
        # Count keyword and pattern occurrences (patterns weighted x2)
        occ = sum(self._count_word_occurrences(text_lower, kw) for kw in theme_def.get('keywords', []))
        occ += 2 * sum(self._count_word_occurrences(text_lower, patt.lower()) for patt in theme_def.get('patterns', []))
        # Normalise with a soft cap
        return min(1.0, occ / 10.0)

    def _match_theme_def(self, theme: str) -> Optional[dict]:
        """Find theme definition by case-insensitive substring name match."""
        t = (theme or '').lower()
        for name, data in self.theme_categories.items():
            if t in name.lower():
                return data
        return None

    @staticmethod
    def _count_word_occurrences(text_lower: str, token: str) -> int:
        """Count whole-word occurrences of token within pre-lowered text."""
        if not token:
            return 0
        return len(re.findall(r"\b" + re.escape(token) + r"\b", text_lower))

    def categorise_themes(self, themes: List[str]) -> Dict[str, Any]:
        """
        Categorise a list of theme names into primary/secondary buckets and groups.
        
        Deterministic rule: first two are primary, rest are secondary. Also
        provide a simple grouping by whether the theme name contains common
        governance/economic hints to aid UI.
        """
        themes = themes or []
        primary = themes[:2]
        secondary = themes[2:]
        categories = {
            'governance': [t for t in themes if any(k in t.lower() for k in ['ethic', 'integrity', 'transparen'])],
            'economic': [t for t in themes if any(k in t.lower() for k in ['econom', 'market', 'fund'])],
            'domestic': []  # keep key present explicitly
        }
        return {
            'primary_themes': primary,
            'secondary_themes': secondary,
            'categories': categories
        }

    def get_theme_summary(self, themes: List[Dict]) -> Dict:
        """
        Generate a comprehensive summary of extracted themes.
        
        This method analyses the list of extracted themes and computes various
        statistics and metrics, including:
        - Total number of themes identified
        - Most prominent theme
        - Average confidence score across all themes
        - Coverage score indicating diversity of theme categories
        - Dominant category based on theme distribution
        
        Args:
            themes: List of theme dictionaries as returned by extract_themes().
                  Each dictionary should contain at least 'name', 'score', and
                  'confidence' keys.
                  
        Returns:
            A dictionary containing summary statistics with the following keys:
            - total_themes: Total number of themes identified
            - top_theme: Name of the highest-scoring theme
            - theme_categories: List of all theme categories found
            - avg_confidence: Average confidence score (0-100)
            - coverage_score: Percentage of theme categories represented (0-100)
            - total_score: Sum of all theme scores
            - dominant_category: Most frequently occurring theme category
            
        Example:
            >>> extractor = ThemeExtractor()
            >>> themes = extractor.extract_themes(some_text)
            >>> summary = extractor.get_theme_summary(themes)
            >>> print(f"Found {summary['total_themes']} themes")
            >>> print(f"Top theme: {summary['top_theme']}")
        """
        if not themes:
            return {
                'total_themes': 0,
                'top_theme': None,
                'theme_categories': [],
                'avg_confidence': 0,
                'coverage_score': 0
            }
        
        total_score = sum(theme['score'] for theme in themes)
        avg_confidence = sum(theme['confidence'] for theme in themes) / len(themes)
        
        # Calculate coverage score (how many different categories covered)
        unique_categories = set()
        for theme in themes:
            for category in self.theme_categories.keys():
                if category.lower() in theme['name'].lower():
                    unique_categories.add(category)
        
        coverage_score = (len(unique_categories) / len(self.theme_categories)) * 100
        
        summary = {
            'total_themes': len(themes),
            'top_theme': themes[0]['name'] if themes else None,
            'theme_categories': [theme['name'] for theme in themes],
            'avg_confidence': round(avg_confidence, 1),
            'coverage_score': round(coverage_score, 1),
            'total_score': round(total_score, 2),
            'dominant_category': (lambda c: c[0][0] if c else None)(Counter([cat for theme in themes for cat in self.theme_categories.keys() if cat.lower() in theme['name'].lower()]).most_common(1))
        }
        
        return summary

    def visualize_themes(self, themes: List[Dict]) -> Dict:
        """
        Prepare theme data for visualisation in charts and graphs.
        
        This method transforms the extracted theme data into a format suitable
        for visualisation in the frontend. It structures the data with consistent
        ordering and assigns a colour palette to ensure visual consistency.
        
        Args:
            themes: List of theme dictionaries as returned by extract_themes().
                  Each dictionary should contain at least 'name', 'score', and
                  'frequency' keys.
                  
        Returns:
            A dictionary containing visualisation-ready data with the following keys:
            - labels: List of theme names
            - scores: List of theme scores (normalised)
            - frequencies: List of theme frequencies (raw counts)
            - confidences: List of confidence scores (0-100)
            - colors: List of hex colour codes for consistent theming
            
        Example:
            >>> extractor = ThemeExtractor()
            >>> themes = extractor.extract_themes(some_text)
            >>> viz_data = extractor.visualize_themes(themes)
            >>> # Use with a charting library like Chart.js or Matplotlib
            >>> # plt.bar(viz_data['labels'], viz_data['scores'], color=viz_data['colors'])
            
        Note:
            The colour palette is fixed to ensure consistency across visualisations.
            If you have more than 10 themes, the colours will repeat.
        """
        if not themes:
            return {'labels': [], 'scores': [], 'colors': []}
        
        # Color palette for themes
        colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'
        ]
        
        viz_data = {
            'labels': [theme['name'] for theme in themes],
            'scores': [theme['score'] for theme in themes],
            'frequencies': [theme['frequency'] for theme in themes],
            'confidences': [theme['confidence'] for theme in themes],
            'colors': colors[:len(themes)]
        }
        
        return viz_data


# Test the theme extractor
if __name__ == "__main__":
    print("Starting theme extractor test...")
    
    # Test text - sample AI policy content
    test_text = """
    This university AI policy establishes guidelines for the ethical use of artificial intelligence 
    in academic settings. Students must maintain academic integrity when using AI tools for assignments. 
    All AI usage must be disclosed and properly attributed to ensure transparency and accountability.
    
    Faculty should consider potential bias in AI systems when implementing them in coursework evaluation. 
    Data privacy and student confidentiality must be protected when using AI for assessment purposes.
    The institution emphasizes responsible AI development and fair access to AI technologies.
    
    Research involving AI must follow ethical guidelines and consider the broader implications for society.
    AI transparency is crucial for maintaining trust in automated decision-making processes.
    """
    
    extractor = ThemeExtractor()
    
    print("\n=== Theme Extraction Test ===")
    print(f"Analyzing text ({len(test_text)} characters)...")
    
    # Extract themes
    themes = extractor.extract_themes(test_text, min_frequency=1, max_themes=10)
    
    print(f"\nExtracted {len(themes)} themes:")
    for i, theme in enumerate(themes, 1):
        print(f"\n{i}. {theme['name']} (Score: {theme['score']}, Confidence: {theme['confidence']}%)")
        if theme['keywords']:
            print(f"   Keywords: {', '.join(theme['keywords'])}")
        if theme['matches']:
            print(f"   Matches: {', '.join(theme['matches'])}")
    
    # Generate summary
    summary = extractor.get_theme_summary(themes)
    print("\n=== Theme Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Visualisation data
    viz_data = extractor.visualize_themes(themes)
    print("\n=== Visualisation Data ===")
    print(f"Chart labels: {viz_data['labels']}")
    print(f"Chart scores: {viz_data['scores']}")
    
    print("\n✅ Theme extractor working correctly!")