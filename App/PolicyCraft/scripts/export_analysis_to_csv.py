#!/usr/bin/env python3
"""
Data Export Utility for PolicyCraft AI Policy Analysis Platform.

This script exports analysed policy documents to CSV format for model evaluation and
further analysis. It extracts cleaned text, classification labels, and institutional
metadata from the database and formats them into a structured CSV file.

Key Features:
- Exports cleaned policy text and classification results
- Includes institutional metadata for analysis
- Supports filtering by document type and source
- Generates formatted CSV output for use in data analysis tools

Usage:
    python scripts/export_analysis_to_csv.py --output data/policy_dataset.csv
    python scripts/export_analysis_to_csv.py --include_clean --output full_dataset.csv

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""
import argparse
import os
import pandas as pd
from src.database.mongo_operations import MongoOperations


def export_to_csv(output_path: str):
    db = MongoOperations()
    rows = []
    for analysis in db.get_user_analyses(-1):
        cleaned = analysis.get("text_data", {}).get("cleaned_text", "")
        label = analysis.get("classification", {}).get("prediction", "")
        metadata = analysis.get("metadata", {}) or {}
        institution = metadata.get("institution_type", "unknown")
        if cleaned and label:
            rows.append({
                "text": cleaned,
                "label": label,
                "institution_type": institution
            })

    if not rows:
        print("[WARN] No analyses found in storage. Nothing exported.")
        return

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Exported {len(df)} rows to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export analysed policies to CSV")
    parser.add_argument("--include_clean", action="store_true", help="Also analyse files in data/policies/clean_dataset")
    parser.add_argument("--output", default="data/policy_dataset.csv", help="Output CSV path")
    args = parser.parse_args()

    export_to_csv(args.output)

    if args.include_clean:
        from src.nlp.text_processor import TextProcessor
        from src.nlp.policy_classifier import PolicyClassifier
        import glob

        clean_dir = "data/policies/clean_dataset"
        files = glob.glob(f"{clean_dir}/*.*")
        if not files:
            print(f"[WARN] No files found in {clean_dir}")
            exit()

        tp = TextProcessor()
        clf = PolicyClassifier()
        extra_rows = []
        for fp in files:
            text = tp.extract_text_from_file(fp)
            if not text:
                continue
            prediction = clf.classify_policy(text)["classification"]
            uni_name = os.path.basename(fp).split("-ai-policy")[0].replace("_", " ").strip()
            extra_rows.append({
                "text": text[:10000],  # limit size
                "label": prediction,
                "institution_type": uni_name
            })
        if extra_rows:
            df_extra = pd.DataFrame(extra_rows)
            df_extra.to_csv(args.output, mode="a", header=False, index=False)
            print(f"Appended {len(df_extra)} rows from clean_dataset to {args.output}")
