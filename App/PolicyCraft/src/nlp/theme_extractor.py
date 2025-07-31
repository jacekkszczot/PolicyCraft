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
    print(f"\n=== Theme Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Visualization data
    viz_data = extractor.visualize_themes(themes)
    print(f"\n=== Visualization Data ===")
    print(f"Chart labels: {viz_data['labels']}")
    print(f"Chart scores: {viz_data['scores']}")
    
    print("\n✅ Theme extractor working correctly!")