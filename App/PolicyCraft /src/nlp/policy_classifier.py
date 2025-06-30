"""
Policy classification module for PolicyCraft.
Classifies AI policies as Restrictive, Permissive, or Moderate using ML and rule-based approaches.

Author: Jacek Robert Kszczot
"""

import re
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional

# ML libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using rule-based classification only.")

logger = logging.getLogger(__name__)

class PolicyClassifier:
    """
    AI Policy classifier using hybrid ML and rule-based approaches.
    Classifies policies as Restrictive, Permissive, or Moderate.
    """
    
    def __init__(self):
        """Initialize the policy classifier with predefined rules and training data."""
        
        # Classification categories
        self.categories = ['Restrictive', 'Moderate', 'Permissive']
        
        # Rule-based classification keywords
        self.classification_keywords = {
            'Restrictive': {
                'prohibition': ['prohibited', 'forbidden', 'banned', 'not allowed', 'strictly forbidden',
                               'must not', 'shall not', 'cannot', 'strictly prohibited', 'zero tolerance'],
                'control': ['controlled', 'restricted', 'limited', 'monitored', 'supervised',
                           'approval required', 'prior approval', 'explicit permission', 'strict oversight'],
                'penalties': ['penalty', 'penalties', 'disciplinary', 'sanctions', 'violations',
                             'consequences', 'academic misconduct', 'expelled', 'suspended'],
                'mandatory': ['mandatory', 'required', 'must', 'compulsory', 'obligatory',
                             'essential', 'necessary', 'enforce', 'compliance']
            },
            
            'Permissive': {
                'encouragement': ['encouraged', 'welcome', 'embrace', 'promote', 'support',
                                 'foster', 'facilitate', 'enable', 'empowered', 'innovative'],
                'flexibility': ['flexible', 'adaptable', 'customizable', 'optional', 'choice',
                               'discretion', 'judgment', 'freedom', 'autonomy', 'creative'],
                'benefits': ['benefits', 'advantages', 'opportunities', 'enhance', 'improve',
                            'efficiency', 'productivity', 'innovation', 'advancement', 'progress'],
                'guidance': ['guidance', 'suggestions', 'recommendations', 'best practices',
                            'tips', 'advice', 'support', 'assistance', 'resources']
            },
            
            'Moderate': {
                'balance': ['balanced', 'moderate', 'reasonable', 'appropriate', 'proportionate',
                           'thoughtful', 'careful', 'considered', 'measured', 'prudent'],
                'conditions': ['conditions', 'guidelines', 'framework', 'principles', 'standards',
                              'criteria', 'requirements', 'considerations', 'factors'],
                'responsibility': ['responsible', 'responsibly', 'accountability', 'ethical',
                                 'integrity', 'transparency', 'fairness', 'respect'],
                'evaluation': ['case-by-case', 'context', 'circumstances', 'situation',
                              'individual', 'specific', 'particular', 'depending']
            }
        }
        
        # Weight multipliers for different keyword categories
        self.category_weights = {
            'Restrictive': {'prohibition': 2.0, 'control': 1.5, 'penalties': 2.0, 'mandatory': 1.3},
            'Permissive': {'encouragement': 1.8, 'flexibility': 1.5, 'benefits': 1.2, 'guidance': 1.0},
            'Moderate': {'balance': 1.5, 'conditions': 1.2, 'responsibility': 1.3, 'evaluation': 1.4}
        }
        
        # ML pipeline
        self.ml_pipeline = None
        if SKLEARN_AVAILABLE:
            self._initialize_ml_model()
        
        print("PolicyClassifier initialized successfully")

    def _initialize_ml_model(self):
        """Initialize and train the ML model with sample data."""
        # Sample training data for AI policies
        training_data = [
            # Restrictive examples
            ("AI tools are strictly prohibited in all assignments and examinations. Students found using AI will face disciplinary action.", "Restrictive"),
            ("The use of artificial intelligence is banned for academic work. Zero tolerance policy applies.", "Restrictive"),
            ("Students must not use AI assistance. All work must be entirely original. Violations result in course failure.", "Restrictive"),
            ("AI usage is forbidden in this course. Manual approval required for any exceptions.", "Restrictive"),
            ("Strictly prohibited to use AI tools. Academic misconduct charges will apply.", "Restrictive"),
            
            # Permissive examples
            ("Students are encouraged to explore AI tools as learning aids. Creative use is welcomed.", "Permissive"),
            ("AI assistance is permitted and can enhance your learning experience. Feel free to experiment.", "Permissive"),
            ("We embrace AI technology as a valuable educational resource. Students have freedom to use it.", "Permissive"),
            ("AI tools are allowed and can improve productivity. Innovation is encouraged.", "Permissive"),
            ("Open use of AI is supported. Students should explore these beneficial technologies.", "Permissive"),
            
            # Moderate examples
            ("AI use is permitted with proper disclosure and citation of sources.", "Moderate"),
            ("Students may use AI tools responsibly, following ethical guidelines and transparency requirements.", "Moderate"),
            ("AI assistance is allowed when used appropriately and with instructor guidance.", "Moderate"),
            ("Balanced approach to AI - permitted for research but not for final submissions without approval.", "Moderate"),
            ("AI tools may be used thoughtfully, considering academic integrity and learning objectives.", "Moderate"),
            ("Responsible AI use is acceptable when following established guidelines and principles.", "Moderate")
        ]
        
        # Extract texts and labels
        texts = [item[0] for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Create ML pipeline
        self.ml_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Train the model
        try:
            self.ml_pipeline.fit(texts, labels)
            print("ML model trained successfully with sample data")
        except Exception as e:
            print(f"Error training ML model: {e}")
            self.ml_pipeline = None

    def classify_policy(self, text: str) -> Dict:
        """
        Classify policy text using hybrid approach.
        
        Args:
            text (str): Policy text to classify
            
        Returns:
            Dict: Classification results with confidence scores
        """
        if not text:
            return {
                'classification': 'Unknown',
                'confidence': 0,
                'method': 'none',
                'scores': {},
                'reasoning': 'No text provided'
            }
        
        print(f"Classifying policy text ({len(text)} characters)")
        
        # Get rule-based classification
        rule_result = self._classify_rule_based(text)
        
        # Get ML classification if available
        ml_result = None
        if self.ml_pipeline:
            ml_result = self._classify_ml_based(text)
        
        # Combine results
        final_result = self._combine_classifications(rule_result, ml_result, text)
        
        print(f"Classification: {final_result['classification']} ({final_result['confidence']}% confidence)")
        return final_result

    def _classify_rule_based(self, text: str) -> Dict:
        """Classify using rule-based keyword matching."""
        text_lower = text.lower()
        category_scores = {category: 0.0 for category in self.categories}
        keyword_matches = {category: [] for category in self.categories}
        
        # Calculate scores for each category
        for category in self.categories:
            for subcategory, keywords in self.classification_keywords[category].items():
                weight = self.category_weights[category][subcategory]
                
                for keyword in keywords:
                    # Count keyword occurrences
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    if count > 0:
                        score = count * weight
                        category_scores[category] += score
                        keyword_matches[category].append((keyword, count, score))
        
        # Determine classification
        if max(category_scores.values()) == 0:
            classification = 'Moderate'  # Default if no strong signals
            confidence = 30
        else:
            classification = max(category_scores, key=category_scores.get)
            total_score = sum(category_scores.values())
            confidence = min(95, int((category_scores[classification] / total_score) * 100)) if total_score > 0 else 30
        
        return {
            'classification': classification,
            'confidence': confidence,
            'scores': category_scores,
            'keyword_matches': keyword_matches,
            'method': 'rule_based'
        }

    def _classify_ml_based(self, text: str) -> Optional[Dict]:
        """Classify using ML model."""
        if not self.ml_pipeline:
            return None
        
        try:
            # Get prediction probabilities
            probabilities = self.ml_pipeline.predict_proba([text])[0]
            classes = self.ml_pipeline.classes_
            
            # Create scores dictionary
            ml_scores = {classes[i]: float(probabilities[i]) for i in range(len(classes))}
            
            # Get classification
            classification = max(ml_scores, key=ml_scores.get)
            confidence = int(ml_scores[classification] * 100)
            
            return {
                'classification': classification,
                'confidence': confidence,
                'scores': ml_scores,
                'method': 'ml_based'
            }
        except Exception as e:
            print(f"ML classification error: {e}")
            return None

    def _combine_classifications(self, rule_result: Dict, ml_result: Optional[Dict], text: str) -> Dict:
        """Combine rule-based and ML classifications."""
        # If only rule-based available
        if not ml_result:
            return {
                'classification': rule_result['classification'],
                'confidence': rule_result['confidence'],
                'method': 'rule_based',
                'scores': rule_result['scores'],
                'reasoning': self._generate_reasoning(rule_result, text),
                'details': {
                    'rule_based': rule_result,
                    'ml_based': None
                }
            }
        
        # If both methods available - weighted combination
        rule_weight = 0.6  # Prefer rule-based for interpretability
        ml_weight = 0.4
        
        # Combine scores
        combined_scores = {}
        for category in self.categories:
            rule_score = rule_result['scores'].get(category, 0)
            ml_score = ml_result['scores'].get(category, 0) * 10  # Scale ML scores
            combined_scores[category] = (rule_score * rule_weight + ml_score * ml_weight)
        
        # Determine final classification
        if max(combined_scores.values()) == 0:
            final_classification = 'Moderate'
            final_confidence = 40
        else:
            final_classification = max(combined_scores, key=combined_scores.get)
            
            # Calculate confidence based on agreement
            rule_class = rule_result['classification']
            ml_class = ml_result['classification']
            
            if rule_class == ml_class == final_classification:
                # Both methods agree
                final_confidence = min(95, int((rule_result['confidence'] + ml_result['confidence']) / 2 * 1.2))
            else:
                # Methods disagree
                final_confidence = min(85, int((rule_result['confidence'] + ml_result['confidence']) / 2 * 0.8))
        
        return {
            'classification': final_classification,
            'confidence': final_confidence,
            'method': 'hybrid',
            'scores': combined_scores,
            'reasoning': self._generate_reasoning(rule_result, text),
            'details': {
                'rule_based': rule_result,
                'ml_based': ml_result,
                'agreement': rule_result['classification'] == ml_result['classification']
            }
        }

    def _generate_reasoning(self, rule_result: Dict, text: str) -> str:
        """Generate human-readable reasoning for the classification."""
        classification = rule_result['classification']
        keyword_matches = rule_result.get('keyword_matches', {})
        
        reasoning_parts = [f"Classified as {classification} based on:"]
        
        # Add top keyword matches
        if classification in keyword_matches and keyword_matches[classification]:
            top_matches = sorted(keyword_matches[classification], key=lambda x: x[2], reverse=True)[:3]
            for keyword, count, score in top_matches:
                reasoning_parts.append(f"- '{keyword}' appears {count} time(s)")
        
        # Add contextual reasoning
        text_lower = text.lower()
        if classification == 'Restrictive':
            if 'prohibited' in text_lower or 'banned' in text_lower:
                reasoning_parts.append("- Strong prohibition language detected")
            if 'penalty' in text_lower or 'misconduct' in text_lower:
                reasoning_parts.append("- Penalty/consequence language present")
        elif classification == 'Permissive':
            if 'encouraged' in text_lower or 'welcome' in text_lower:
                reasoning_parts.append("- Encouraging language detected")
            if 'freedom' in text_lower or 'optional' in text_lower:
                reasoning_parts.append("- Flexible approach indicated")
        elif classification == 'Moderate':
            if 'responsible' in text_lower or 'ethical' in text_lower:
                reasoning_parts.append("- Emphasis on responsible use")
            if 'guidelines' in text_lower or 'framework' in text_lower:
                reasoning_parts.append("- Structured approach with guidelines")
        
        return ' '.join(reasoning_parts)

    def get_classification_details(self, text: str) -> Dict:
        """
        Get detailed classification analysis including word frequency and patterns.
        
        Args:
            text (str): Policy text to analyze
            
        Returns:
            Dict: Detailed analysis results
        """
        result = self.classify_policy(text)
        
        # Add additional analysis
        text_lower = text.lower()
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Analyze sentence structure
        strong_statements = len(re.findall(r'\b(must|shall|required|mandatory|prohibited)\b', text_lower))
        conditional_statements = len(re.findall(r'\b(may|might|could|should|recommended)\b', text_lower))
        
        # Calculate policy tone
        if strong_statements > conditional_statements:
            tone = 'Authoritative'
        elif conditional_statements > strong_statements:
            tone = 'Suggestive'
        else:
            tone = 'Balanced'
        
        details = {
            'classification_result': result,
            'text_analysis': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_sentence_length': round(word_count / sentence_count, 1) if sentence_count > 0 else 0,
                'strong_statements': strong_statements,
                'conditional_statements': conditional_statements,
                'policy_tone': tone
            },
            'keyword_density': self._calculate_keyword_density(text),
            'classification_confidence_factors': self._analyze_confidence_factors(result)
        }
        
        return details

    def _calculate_keyword_density(self, text: str) -> Dict:
        """Calculate density of classification keywords."""
        text_lower = text.lower()
        total_words = len(text.split())
        
        density = {}
        for category in self.categories:
            category_keywords = []
            for subcategory, keywords in self.classification_keywords[category].items():
                category_keywords.extend(keywords)
            
            keyword_count = sum(len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower)) 
                               for kw in category_keywords)
            density[category] = round((keyword_count / total_words) * 100, 2) if total_words > 0 else 0
        
        return density

    def _analyze_confidence_factors(self, result: Dict) -> List[str]:
        """Analyze factors affecting classification confidence."""
        factors = []
        confidence = result['confidence']
        
        if confidence >= 80:
            factors.append("High confidence due to clear keyword indicators")
        elif confidence >= 60:
            factors.append("Moderate confidence with some ambiguity")
        else:
            factors.append("Low confidence - mixed or unclear signals")
        
        if result['method'] == 'hybrid' and result['details']['agreement']:
            factors.append("Rule-based and ML methods agree")
        elif result['method'] == 'hybrid' and not result['details']['agreement']:
            factors.append("Rule-based and ML methods disagree")
        
        return factors


# Test the classifier
if __name__ == "__main__":
    print("Starting policy classifier test...")
    
    classifier = PolicyClassifier()
    
    # Test cases
    test_cases = [
        {
            'name': 'Restrictive Policy',
            'text': 'AI tools are strictly prohibited in all assignments. Students found using AI will face disciplinary action and course failure.'
        },
        {
            'name': 'Permissive Policy', 
            'text': 'Students are encouraged to explore AI tools as learning aids. Creative use is welcomed and can enhance your educational experience.'
        },
        {
            'name': 'Moderate Policy',
            'text': 'AI use is permitted with proper disclosure and citation. Students should use AI tools responsibly following ethical guidelines.'
        }
    ]
    
    print("\n=== Policy Classification Tests ===")
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"Text: {test_case['text'][:100]}...")
        
        result = classifier.classify_policy(test_case['text'])
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']}%")
        print(f"Method: {result['method']}")
        print(f"Reasoning: {result['reasoning']}")
        
        # Get detailed analysis
        details = classifier.get_classification_details(test_case['text'])
        print(f"Policy Tone: {details['text_analysis']['policy_tone']}")
        print(f"Keyword Density: {details['keyword_density']}")
    
    print("\n✅ Policy classifier working correctly!")