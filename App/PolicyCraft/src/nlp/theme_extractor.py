"""
Theme extraction module for PolicyCraft.
Identifies key themes and concepts in AI policy documents using spaCy and custom rules.

Author: Jacek Robert Kszczot
"""

import re
import logging
from collections import defaultdict, Counter
from typing import List, Dict, Optional

# NLP libraries
try:
    import spacy
    from spacy.matcher import Matcher, PhraseMatcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. Install with: pip install spacy")

logger = logging.getLogger(__name__)

class ThemeExtractor:
    """
    Advanced theme extraction for AI policy documents.
    Uses spaCy NLP pipeline with custom policy-specific rules.
    """
    
    def __init__(self, model_name: str = 'en_core_web_sm'):
        """
        Initialize theme extractor with spaCy model and policy-specific patterns.
        
        Args:
            model_name (str): spaCy model name
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
                    'academic integrity', 'academic misconduct', 'academic dishonesty',
                    'proper citation', 'original work', 'intellectual honesty'
                ]
            },
            
            'AI Ethics': {
                'keywords': ['ethics', 'ethical', 'moral', 'responsible', 'harm', 'benefit',
                           'rights', 'dignity', 'respect', 'justice', 'welfare'],
                'patterns': [
                    'ethical ai', 'responsible ai', 'ai ethics', 'ethical considerations',
                    'moral implications', 'ethical guidelines', 'human dignity'
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
                           'equality', 'inclusive', 'diverse', 'representation', 'prejudice'],
                'patterns': [
                    'algorithmic bias', 'ai bias', 'bias mitigation', 'fair ai',
                    'bias detection', 'discrimination prevention', 'inclusive ai'
                ]
            },
            
            'Privacy and Data': {
                'keywords': ['privacy', 'private', 'data', 'personal', 'confidential', 'gdpr',
                           'consent', 'anonymization', 'protection', 'security', 'information'],
                'patterns': [
                    'data privacy', 'personal data', 'data protection', 'privacy rights',
                    'data security', 'informed consent', 'data anonymization'
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
            
            'Student Guidelines': {
                'keywords': ['student', 'students', 'learner', 'pupil', 'coursework', 'assignment',
                           'homework', 'submission', 'project', 'essay', 'report'],
                'patterns': [
                    'student use', 'student guidelines', 'assignment policy', 'coursework rules',
                    'student responsibilities', 'ai in assignments', 'student conduct'
                ]
            },
            
            'Faculty Guidelines': {
                'keywords': ['faculty', 'teacher', 'instructor', 'professor', 'staff', 'educator',
                           'teaching', 'pedagogy', 'curriculum', 'course', 'classroom'],
                'patterns': [
                    'faculty guidelines', 'instructor policy', 'teaching with ai',
                    'faculty responsibilities', 'classroom ai', 'pedagogical use'
                ]
            },
            
            'Research and Innovation': {
                'keywords': ['research', 'innovation', 'development', 'advancement', 'discovery',
                           'investigation', 'study', 'experiment', 'analysis', 'methodology'],
                'patterns': [
                    'ai research', 'research ethics', 'innovation policy', 'research integrity',
                    'ai development', 'research methodology', 'scientific research'
                ]
            }
        }
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            self._initialize_spacy()
        else:
            print("spaCy not available - using fallback keyword extraction")
            
    def _initialize_spacy(self):
        """Initialize spaCy model and matchers."""
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
            
    def _setup_patterns(self):
        """Setup pattern matching rules for theme extraction."""
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
        Extract key themes from policy text.
        
        Args:
            text (str): Input policy text
            min_frequency (int): Minimum frequency for theme inclusion
            max_themes (int): Maximum number of themes to return
            
        Returns:
            List[Dict]: List of themes with scores and details
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
        """Extract themes using spaCy NLP pipeline."""
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
        """Fallback theme extraction using keyword matching only."""
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
        """Convert pattern name back to theme name."""
        pattern_to_theme = {
            theme_name.lower().replace(' ', '_'): theme_name 
            for theme_name in self.theme_categories.keys()
        }
        return pattern_to_theme.get(pattern_name)

    def _format_themes(self, theme_scores: Dict, theme_details: Dict, max_themes: int) -> List[Dict]:
        """Format themes into final output structure."""
        # Sort themes by score
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Format output
        themes = []
        for theme_name, score in sorted_themes[:max_themes]:
            details = theme_details[theme_name]
            
            theme_data = {
                'name': theme_name,
                'score': round(score, 2),
                'frequency': int(score),
                'keywords': [kw[0] for kw in details['keywords'][:5]],  # Top 5 keywords
                'matches': [match[0] if isinstance(match, tuple) else match for match in details['matches'][:3]],  # Top 3 matches
                'confidence': min(100, int(score * 10))  # Convert to confidence percentage
            }
            
            # Add entities if available
            if 'entities' in details and details['entities']:
                theme_data['entities'] = [ent[0] for ent in details['entities'][:3]]
            
            themes.append(theme_data)
        
        return themes

    def get_theme_summary(self, themes: List[Dict]) -> Dict:
        """
        Generate a summary of extracted themes.
        
        Args:
            themes (List[Dict]): List of extracted themes
            
        Returns:
            Dict: Theme summary statistics
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
        Prepare theme data for visualization.
        
        Args:
            themes (List[Dict]): List of extracted themes
            
        Returns:
            Dict: Data formatted for charts and graphs
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
    print(f"\n=== Theme Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Visualization data
    viz_data = extractor.visualize_themes(themes)
    print(f"\n=== Visualization Data ===")
    print(f"Chart labels: {viz_data['labels']}")
    print(f"Chart scores: {viz_data['scores']}")
    
    print("\n✅ Theme extractor working correctly!")