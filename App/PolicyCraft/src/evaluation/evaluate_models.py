#!/usr/bin/env python3
"""
Model Evaluation Module for PolicyCraft AI Policy Analysis Platform.

This module provides comprehensive evaluation of policy classification models,
comparing a baseline TF-IDF + Logistic Regression approach against the custom
PolicyCraft spaCy/rule-based hybrid classifier. It includes functionality for
performance measurement, fairness analysis, and detailed reporting.

Key Features:
- Comparative evaluation of multiple classification approaches
- Detailed performance metrics (precision, recall, F1-score, confusion matrix)
- Fairness analysis across different demographic or institutional groups
- Command-line interface for easy integration into workflows
- Support for custom datasets and column mappings

Usage:
    python -m src.evaluation.evaluate_models \
        --data_path data/policy_dataset.csv \
        [--text_col text] \
        [--label_col label] \
        [--group_col institution_type] \
        [--test_size 0.2] \
        [--random_state 42]

Parameters:
    --data_path    Path to the CSV file containing the policy documents and labels
    --text_col     Name of the column containing policy text (default: 'text')
    --label_col    Name of the column containing classification labels (default: 'label')
    --group_col    Optional column for group-wise fairness analysis
    --test_size    Proportion of data to use for testing (default: 0.2)
    --random_state Random seed for reproducibility (default: 42)

Output:
    - Classification report for each model
    - Confusion matrices
    - Fairness metrics (if group column provided)
    - Comparative analysis of model performance

Note:
    The evaluation includes both statistical metrics and practical considerations
    for deployment in the PolicyCraft platform. The fairness analysis helps
    identify potential biases in model performance across different groups.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""
import argparse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split


from src.nlp.policy_classifier import PolicyClassifier

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def build_baseline_model():
    """
    Construct and return a baseline text classification pipeline.
    
    This function creates a simple yet effective text classification pipeline
    combining TF-IDF vectorisation with Logistic Regression. The pipeline is
    configured with sensible defaults for policy document classification.
    
    Pipeline Components:
        1. TF-IDF Vectorizer:
           - Maximum document frequency: 0.9 (ignores terms that appear in >90% of docs)
           - N-gram range: (1, 2) (includes both unigrams and bigrams)
           
        2. Logistic Regression Classifier:
           - Maximum iterations: 1000 (for convergence)
           - Class weights: 'balanced' (handles imbalanced classes)
    
    Returns:
        sklearn.pipeline.Pipeline: A scikit-learn pipeline object ready for training
        
    Example:
        >>> model = build_baseline_model()
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
        
    Note:
        This baseline model serves as a reference point for comparing the performance
        of more sophisticated approaches. It's particularly useful for establishing
        a minimum performance threshold and for quick prototyping.
    """
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_df=0.9, ngram_range=(1,2))),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    return pipeline


def evaluate(clf, X_test, y_test, name: str) -> float:
    """
    Evaluate and print classification metrics for a given model.
    
    This function provides a comprehensive evaluation of a classification model's
    performance, including precision, recall, F1-score, and a confusion matrix.
    The results are formatted for easy interpretation and analysis.
    
    Parameters:
        clf: A trained classifier implementing the scikit-learn interface
        X_test: Test feature set (list of texts or feature vectors)
        y_test: True labels for the test set
        name: Identifier for the model (used in output headers)
        
    Returns:
        float: The macro-averaged F1 score for the model
        
    Outputs:
        - Model name header
        - Classification report with precision, recall, and F1-score
        - Confusion matrix showing true vs. predicted labels
        
    Example:
        >>> model = build_baseline_model()
        >>> model.fit(X_train, y_train)
        >>> f1 = evaluate(model, X_test, y_test, "Baseline Model")
        
    Note:
        - Uses macro-averaging for F1 score to handle class imbalance
        - Prints results to stdout for immediate feedback
        - Returns the F1 score for further processing if needed
    """
    print("\n===", name, "===")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
    return f1_score(y_test, y_pred, average="macro")


def evaluate_policy_classifier(model: PolicyClassifier, X, y) -> float:
    """
    Evaluate a PolicyClassifier model on the given test data.
    
    This function evaluates a custom PolicyClassifier instance by generating
    predictions for the input texts and comparing them against the true labels.
    It provides a detailed classification report and confusion matrix.
    
    Parameters:
        model: An instance of PolicyClassifier with a classify_policy method
        X: Iterable of input texts to be classified
        y: True labels corresponding to the input texts
        
    Returns:
        float: The macro-averaged F1 score for the classifier
        
    Outputs:
        - Classification report showing precision, recall, and F1-score
        - Confusion matrix showing true vs. predicted labels
        
    Example:
        >>> classifier = PolicyClassifier()
        >>> f1 = evaluate_policy_classifier(classifier, test_texts, test_labels)
        
    Note:
        - Assumes the model's classify_policy method returns a dictionary
          with a 'classification' key containing the predicted label
        - Uses macro-averaging for F1 score to handle class imbalance
        - Prints evaluation metrics to stdout
    """
    y_pred = [model.classify_policy(text)["classification"] for text in X]
    print(classification_report(y, y_pred, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y, y_pred))
    return f1_score(y, y_pred, average="macro")


def group_fairness(y_true, y_pred, groups):
    """
    Calculate fairness metrics across different demographic or institutional groups.
    
    This function computes the fairness of a classification model by analysing performance
    disparities across different groups. It returns both the maximum F1 score difference
    between any two groups and the detailed F1 scores per group.
    
    Parameters:
        y_true: Array-like of true labels
        y_pred: Array-like of predicted labels
        groups: Array-like of group identifiers corresponding to each prediction
        
    Returns:
        tuple: A tuple containing:
            - float: The difference between maximum and minimum group F1 scores
            - dict: A dictionary mapping each group to its F1 score
            
    Example:
        >>> y_true = [1, 0, 1, 0, 1, 0]
        >>> y_pred = [1, 0, 1, 0, 0, 1]
        >>> groups = ['A', 'A', 'B', 'B', 'C', 'C']
        >>> diff, scores = group_fairness(y_true, y_pred, groups)
        
    Note:
        - Uses macro-averaged F1 score for each group
        - Skips groups with fewer than 2 samples
        - Returns 0.0 if fewer than 2 valid groups are found
        - Lower difference values indicate more equitable performance across groups
    """
    group_scores = {}
    for g in sorted(set(groups)):
        mask = groups == g
        if mask.sum() < 2:
            continue
        group_scores[g] = f1_score(y_true[mask], y_pred[mask], average="macro")
    if len(group_scores) < 2:
        return 0.0
    diff = max(group_scores.values()) - min(group_scores.values())
    return diff, group_scores


if __name__ == "__main__":
    # Set up command-line argument parser with detailed help messages
    parser = argparse.ArgumentParser(
        description="Evaluate and compare PolicyCraft classification models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--data_path",
        required=True,
        help="Path to the CSV file containing policy documents and labels"
    )
    parser.add_argument(
        "--text_col",
        default="text",
        help="Name of the column containing the policy document text"
    )
    parser.add_argument(
        "--label_col",
        default="label",
        help="Name of the column containing classification labels"
    )
    parser.add_argument(
        "--group_col",
        help="Optional column name for group-wise fairness analysis (e.g., 'institution_type')"
    )
    parser.add_argument(
        "--test_size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to include in the test split (0.0-1.0)"
    )
    parser.add_argument(
        "--random_state",
        type=int,
        default=42,
        help="Random seed for reproducibility of results"
    )
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Validate test_size parameter
    if not 0.0 < args.test_size < 1.0:
        raise ValueError("test_size must be between 0.0 and 1.0")

    df = pd.read_csv(args.data_path)

    # Usuń ewentualne zdublowane wiersze nagłówka
    if args.label_col in df[args.label_col].values:
        df = df[df[args.label_col] != args.label_col].reset_index(drop=True)
    X = df[args.text_col].astype(str)
    y = df[args.label_col].astype(str)

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
    except ValueError as ve:
        print("[WARN] Stratified split failed (", ve, ") – falling back to random split without stratify.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=True, random_state=42
        )

    baseline = build_baseline_model()
    baseline.fit(X_train, y_train)
    baseline_f1 = evaluate(baseline, X_test, y_test, "Baseline TF-IDF + LR")

    policy_model = PolicyClassifier()
    pc_f1 = evaluate_policy_classifier(policy_model, X_test, y_test)

    print("\nMacro-F1 Scores:\n  Baseline:", baseline_f1, "\n  PolicyClassifier:", pc_f1)

    if args.group_col and args.group_col in df.columns:
        groups = df[args.group_col]
        # Baseline fairness
        y_pred_base = baseline.predict(X)
        gf_base = group_fairness(y, y_pred_base, groups)
        diff_base, scores_base = gf_base if isinstance(gf_base, tuple) else (gf_base, {})
        # PolicyClassifier fairness
        y_pred_pc = [policy_model.classify_policy(t)["classification"] for t in X]
        gf_pc = group_fairness(y, y_pred_pc, groups)
        diff_pc, scores_pc = gf_pc if isinstance(gf_pc, tuple) else (gf_pc, {})
        print("\n=== Fairness metric (F1 max-min) ===")
        print("Baseline diff:", diff_base, "| per-group:", scores_base)
        print("PolicyClassifier diff:", diff_pc, "| per-group:", scores_pc)
