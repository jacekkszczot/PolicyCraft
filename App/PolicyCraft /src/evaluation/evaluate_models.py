#!/usr/bin/env python3
"""Evaluate PolicyCraft classifiers.

Usage:
    python -m src.evaluation.evaluate_models --data_path data/policy_dataset.csv [--text_col text] [--label_col label] [--group_col institution_type]

The script trains two classifiers:
1. Baseline: TF-IDF + LogisticRegression
2. PolicyCraft spaCy/Rule-based hybrid (imported from src.nlp.policy_classifier)

It outputs precision, recall, F1-score and confusion matrix for each classifier.
If --group_col is provided, the script additionally computes per-group F1 and a simple fairness metric
(difference between max and min group F1).
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
    """Return TF-IDF + LogisticRegression pipeline."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_df=0.9, ngram_range=(1,2))),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    return pipeline


def evaluate(clf, X_test, y_test, name: str):
    """Print classification metrics for a model."""
    print("\n===", name, "===")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
    return f1_score(y_test, y_pred, average="macro")


def evaluate_policy_classifier(model: PolicyClassifier, X, y):
    y_pred = [model.classify_policy(text)["classification"] for text in X]
    print(classification_report(y, y_pred, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y, y_pred))
    return f1_score(y, y_pred, average="macro")


def group_fairness(y_true, y_pred, groups):
    """Compute simple fairness metric: difference between max and min group F1."""
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
    parser = argparse.ArgumentParser(description="Evaluate PolicyCraft classifiers.")
    parser.add_argument("--data_path", required=True, help="CSV with text and label columns")
    parser.add_argument("--text_col", default="text", help="Name of text column")
    parser.add_argument("--label_col", default="label", help="Name of label column")
    parser.add_argument("--group_col", default=None, help="Optional column for fairness analysis")
    args = parser.parse_args()

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
