"""
Policy classification module for PolicyCraft.
Classifies AI policies as Restrictive, Permissive, or Moderate using ML and rule-based approaches.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import re
import logging

from typing import Dict, List, Tuple, Optional

# ML libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline


    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using rule-based classification only.")

logger = logging.getLogger(__name__)

class PolicyClassifier:
    """
    Advanced AI policy classifier using hybrid machine learning and rule-based approaches.
    
    This classifier analyses policy documents related to AI usage in academic settings
    and classifies them into one of three categories:
    - Restrictive: Policies that prohibit or strictly limit AI usage
    - Permissive: Policies that encourage or allow broad AI usage
    - Moderate: Policies that allow AI usage with specific guidelines or conditions
    
    The classifier employs a hybrid approach that combines:
    - Rule-based keyword matching for interpretability
    - Machine learning for contextual understanding
    - Confidence scoring for result reliability
    
    Note:
        For optimal performance, the scikit-learn library should be installed.
        If not available, the classifier will fall back to rule-based classification.
    """
    
    def __init__(self):
        """
        Initialise the policy classifier with predefined rules and training data.
        
        This constructor sets up the classification pipeline, including:
        - Defining policy classification categories
        - Configuring keyword patterns and weights for rule-based classification
        - Initialising the machine learning model (if dependencies are available)
        
        The classifier is pre-configured with domain-specific knowledge about
        AI policy language and common patterns in academic policy documents.
        """
        
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
                'balance': ['moderate', 'reasonable', 'appropriate', 'proportionate',
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
        
        # === Explainability parameters ===
        self.top_explain_terms = 10  # default number of terms returned by explain_classification
        
        self.ml_pipeline = None
        if SKLEARN_AVAILABLE:
            self._initialize_ml_model()
        
        print("PolicyClassifier initialized successfully")

    # ------------------------------------------------------------------
    # Explainability helper
    # ------------------------------------------------------------------
    def explain_classification(self, text: str, top_n: int = None) -> List[Tuple[str, str, float]]:
        """
        Analyse and return the most influential keywords contributing to classification.
        
        This method provides explainability by identifying which specific keywords and
        phrases in the input text had the most significant impact on the classification
        decision, along with their associated categories and weights.
        
        Args:
            text: The policy text to analyse. Should be pre-cleaned for best results.
            top_n: Maximum number of terms to return. If None, uses the default value
                  specified in self.top_explain_terms (default: 10).
                  
        Returns:
            A list of tuples, where each tuple contains:
            - keyword: The matched term from the text
            - category: The classification category it contributed to
            - score: The weighted score indicating its influence
            
            The list is sorted by score in descending order.
            
        Example:
            >>> classifier = PolicyClassifier()
            >>> explanation = classifier.explain_classification("AI tools are strictly prohibited")
            >>> for keyword, category, score in explanation:
            ...     print(f"{keyword} ({category}): {score:.2f}")
        """
        if top_n is None:
            top_n = self.top_explain_terms

        text_lower = text.lower()
        scores: List[Tuple[str, str, float]] = []
        # Calculate rule-based keyword contributions
        for category, groups in self.classification_keywords.items():
            for group_name, keywords in groups.items():
                weight = self.category_weights[category].get(group_name, 1.0)
                for kw in keywords:
                    if kw in text_lower:
                        # simple frequency * weight
                        freq = text_lower.count(kw)
                        score = freq * weight
                        if score > 0:
                            scores.append((kw, category, score))

        # Sort and truncate
        scores.sort(key=lambda x: x[2], reverse=True)
        return scores[:top_n]

    def _initialize_ml_model(self) -> None:
        """
        Initialise and train the machine learning model with sample policy data.
        
        This private method sets up a scikit-learn pipeline for text classification
        using TF-IDF vectorization and Multinomial Naive Bayes. It trains the model
        on a curated dataset of example policies representing different classification
        categories.
        
        The training data includes:
        - Restrictive policies with strong prohibitive language
        - Permissive policies with encouraging language
        - Moderate policies with conditional guidelines
        
        Note:
            This method is automatically called during class initialisation if
            scikit-learn is available. If the training fails, the classifier
            will fall back to rule-based classification.
            
        Raises:
            ImportError: If required ML dependencies are not installed
            Exception: For any errors during model training
        """
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
            ("Moderate approach to AI - permitted for research but not for final submissions without approval.", "Moderate"),
            ("AI tools may be used thoughtfully, considering academic integrity and learning objectives.", "Moderate"),
            ("Responsible AI use is acceptable when following established guidelines and principles.", "Moderate")
        ]
        
        # Extract texts and labels
        texts = [item[0] for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Create ML pipeline (deterministic with consistent input ordering)
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
        Classify policy text using a hybrid rule-based and machine learning approach.
        
        This is the primary method for classifying AI policy documents. It combines:
        - Rule-based keyword matching for interpretability
        - Machine learning for contextual understanding (if available)
        - Confidence scoring to indicate result reliability
        
        Args:
            text: The policy text to classify. Should be a complete policy or policy section.
                For best results, pre-process the text to remove irrelevant content.
                
        Returns:
            A dictionary containing:
            - classification: The predicted category ('Restrictive', 'Moderate', or 'Permissive')
            - confidence: Integer score (0-100) indicating prediction confidence
            - method: The classification method used ('rule_based', 'ml_based', or 'hybrid')
            - scores: Dictionary of scores for each category
            - reasoning: Human-readable explanation of the classification
            - details: Additional metadata including individual classifier results
            
        Example:
            >>> classifier = PolicyClassifier()
            >>> result = classifier.classify_policy(
            ...     "AI tools are strictly prohibited in all academic work."
            ... )
            >>> print(f"Classification: {result['classification']}")
            >>> print(f"Confidence: {result['confidence']}%")
            >>> print(f"Reasoning: {result['reasoning']}")
            
        Note:
            If the input text is empty or contains no classifiable content,
            the method will return 'Unknown' classification with 0% confidence.
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
        """
        Classify policy text using rule-based keyword matching.
        
        This internal method implements the rule-based classification strategy,
        which identifies policy categories by matching keywords and phrases
        against predefined patterns with associated weights.
        
        The classification process involves:
        1. Tokenizing and normalizing the input text
        2. Matching against category-specific keyword patterns
        3. Applying category weights to calculate scores
        4. Determining the most likely category based on weighted scores
        
        Args:
            text: The policy text to classify. Should be pre-processed and
                 in lowercase for consistent matching.
                 
        Returns:
            A dictionary containing:
            - classification: The predicted category
            - confidence: Confidence score (0-100)
            - scores: Raw scores for each category
            - keyword_matches: Detailed information about matched keywords
            - method: Always 'rule_based'
            
        Note:
            This method is used as a fallback when ML classification is not available
            and as part of the hybrid classification approach. It provides good
            interpretability due to its rule-based nature.
        """
        text_lower = text.lower()
        category_scores, keyword_matches = self._compute_rule_scores(text_lower)
        
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

    def _compute_rule_scores(self, text_lower: str) -> Tuple[Dict[str, float], Dict[str, List[Tuple[str, int, float]]]]:
        """Compute rule-based category scores and keyword matches for a lowercased text.

        Preserves the original scoring logic exactly.
        """
        category_scores: Dict[str, float] = {category: 0.0 for category in self.categories}
        keyword_matches: Dict[str, List[Tuple[str, int, float]]] = {category: [] for category in self.categories}

        for category in self.categories:
            for subcategory, keywords in self.classification_keywords[category].items():
                weight = self.category_weights[category][subcategory]
                for keyword in keywords:
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    if count > 0:
                        score = count * weight
                        category_scores[category] += score
                        keyword_matches[category].append((keyword, count, score))

        return category_scores, keyword_matches

    def _classify_ml_based(self, text: str) -> Optional[Dict]:
        """
        Classify policy text using the pre-trained machine learning model.
        
        This internal method applies the scikit-learn pipeline to predict
        the policy category based on learned patterns from the training data.
        The ML model uses TF-IDF features to capture important n-gram patterns
        that distinguish between different policy types.
        
        Args:
            text: The policy text to classify. No pre-processing is required
                 as the model's pipeline handles text cleaning and normalization.
                 
        Returns:
            A dictionary containing classification results with the following keys:
            - classification: The predicted policy category
            - confidence: Confidence score (0-100)
            - scores: Probability distribution over all categories
            - method: Always 'ml_based'
            
            Returns None if the ML model is not available or if an error occurs.
            
        Note:
            This method is part of the hybrid classification approach and provides
            better generalization to unseen patterns compared to rule-based methods.
            It requires the scikit-learn package to be installed.
        """
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
        """
        Combine results from rule-based and ML classifiers into a final prediction.
        
        This internal method implements an ensemble approach that leverages the
        strengths of both classification methods:
        - Rule-based: High precision with clear interpretability
        - ML-based: Better handling of complex patterns and unseen cases
        
        The combination uses a weighted average where rule-based results have
        slightly higher influence (60%) than ML results (40%) by default,
        prioritizing interpretability while benefiting from ML's generalization.
        
        Args:
            rule_result: Results from the rule-based classifier
            ml_result: Results from the ML classifier, or None if not available
            text: The original policy text (used for reasoning generation)
            
        Returns:
            A dictionary containing the combined classification results:
            - classification: Final predicted category
            - confidence: Combined confidence score (0-100)
            - method: 'hybrid' if both methods used, otherwise the single method
            - scores: Combined scores for each category
            - reasoning: Human-readable explanation of the classification
            - details: Complete results from both classifiers
            
        Note:
            If the ML classifier is not available or fails, this method falls back
            to using only the rule-based results. The confidence score is adjusted
            based on the agreement between the two methods.
        """
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
        combined_scores = self._combine_hybrid_scores(rule_result, ml_result)

        # Determine final classification and confidence
        final_classification, final_confidence = self._finalise_hybrid_decision(
            combined_scores, rule_result, ml_result
        )

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

    def _combine_hybrid_scores(self, rule_result: Dict, ml_result: Dict) -> Dict[str, float]:
        """Combine rule-based and ML scores using original weights and scaling."""
        rule_weight = 0.6  # Prefer rule-based for interpretability
        ml_weight = 0.4
        combined_scores: Dict[str, float] = {}
        for category in self.categories:
            rule_score = rule_result['scores'].get(category, 0)
            ml_score = ml_result['scores'].get(category, 0) * 10  # Scale ML scores
            combined_scores[category] = (rule_score * rule_weight + ml_score * ml_weight)
        return combined_scores

    def _finalise_hybrid_decision(self, combined_scores: Dict[str, float], rule_result: Dict, ml_result: Dict) -> Tuple[str, int]:
        """Determine final class and confidence preserving original logic."""
        if max(combined_scores.values()) == 0:
            return 'Moderate', 40

        final_classification = max(combined_scores, key=combined_scores.get)
        rule_class = rule_result['classification']
        ml_class = ml_result['classification']

        if rule_class == ml_class == final_classification:
            raw_conf = int((rule_result['confidence'] + ml_result['confidence']) / 2 * 1.2)
        else:
            raw_conf = int((rule_result['confidence'] + ml_result['confidence']) / 2 * 0.8)

        # Clamp only to [0, 100] to avoid unrealistic values, no artificial 85/95 caps
        final_confidence = max(0, min(100, raw_conf))

        return final_classification, final_confidence

    def _generate_reasoning(self, rule_result: Dict, text: str) -> str:
        """
        Generate a human-readable explanation for the classification decision.
        
        This method creates a natural language explanation of why a particular
        classification was made, based on the rule-based analysis of the text.
        The reasoning highlights the most influential keywords and patterns
        that contributed to the classification decision.
        
        Args:
            rule_result: Results from the rule-based classifier, containing
                       keyword matches and scores.
            text: The original policy text being classified (used for context).
                 
        Returns:
            A string containing a clear, concise explanation of the classification
            in natural language, suitable for end-users. The explanation includes:
            - The predicted classification
            - Key terms that influenced the decision
            - Contextual patterns that support the classification
            
        Example:
            "Classified as Restrictive based on:
             - 'prohibited' appears 3 time(s)
             - Strong prohibition language detected
             - Penalty/consequence language present"
        """
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
        Generate a comprehensive analysis of the policy text with detailed metrics.
        
        This method provides an in-depth examination of the policy document,
        including classification results, text statistics, and linguistic patterns.
        It's designed to give users rich insights into both the classification
        decision and the characteristics of the policy text.
        
        The analysis includes:
        - Full classification results with confidence scores
        - Text statistics (word count, sentence count, etc.)
        - Analysis of policy tone and statement types
        - Keyword density by category
        - Confidence factors affecting the classification
        
        Args:
            text: The policy text to analyze. Should be a complete policy document
                 or a substantial excerpt for meaningful analysis.
                 
        Returns:
            A dictionary containing detailed analysis with the following structure:
            {
                'classification_result': Dict,  # Full classification results
                'text_analysis': {             # Text statistics
                    'word_count': int,          # Total words
                    'sentence_count': int,      # Total sentences
                    'avg_sentence_length': float,# Average words per sentence
                    'strong_statements': int,    # Count of strong/mandatory statements
                    'conditional_statements': int, # Count of conditional statements
                    'policy_tone': str           # Overall tone (Authoritative/Suggestive/Moderate)
                },
                'keyword_density': Dict,        # Percentage of keywords by category
                'classification_confidence_factors': List[str]  # Factors affecting confidence
            }
            
        Example:
            >>> classifier = PolicyClassifier()
            >>> details = classifier.get_classification_details(
            ...     "AI tools are strictly prohibited in all academic work..."
            ... )
            >>> print(f"Word count: {details['text_analysis']['word_count']}")
            >>> print(f"Policy tone: {details['text_analysis']['policy_tone']}")
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
            tone = 'Moderate'
        
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
        """
        Calculate the relative frequency of classification keywords in the text.
        
        This helper method computes the percentage of words in the input text
        that match the predefined classification keywords for each policy category.
        The density values are normalised by the total word count and can be used
        to understand the prominence of different policy-related terms.
        
        Args:
            text: The policy text to analyse. The text will be converted to
                 lowercase for case-insensitive matching.
                 
        Returns:
            A dictionary mapping each policy category to its keyword density
            as a percentage of total words. For example:
            {
                'Restrictive': 2.5,  # 2.5% of words are restrictive keywords
                'Moderate': 1.8,     # 1.8% of words are moderate keywords
                'Permissive': 1.2    # 1.2% of words are permissive keywords
            }
            
        Note:
            The density calculation is based on simple word matching and does not
            account for word context or multi-word expressions. It's primarily
            useful as a relative measure between categories rather than an
            absolute metric.
        """
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
        """
        Analyse and describe the key factors influencing the classification confidence.
        
        This method examines the classification results to identify and explain
        the main factors that contributed to the confidence level of the prediction.
        It provides human-readable insights into why a particular confidence
        score was assigned to the classification.
        
        Args:
            result: The classification result dictionary containing at least
                   'confidence' and 'method' keys, and optionally 'details'
                   with information about the classification process.
                   
        Returns:
            A list of strings, where each string describes a factor that
            influenced the confidence score. Example factors include:
            - "High confidence due to clear keyword indicators"
            - "Rule-based and ML methods agree"
            - "Low confidence - mixed or unclear signals"
            
        Note:
            The factors are intended to help users understand the reliability
            of the classification and should be presented as part of the
            classification details rather than as standalone metrics.
        """
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