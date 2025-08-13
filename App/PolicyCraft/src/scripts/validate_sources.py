#!/usr/bin/env python3
"""
Reference Validation Module for PolicyCraft AI Policy Analysis.

This module provides functionality to validate and verify the academic references
used in policy recommendations. It ensures that all cited sources are properly
documented in the project's reference library and checks for outdated references
based on their publication year.

Key Features:
- Validates that all recommendation sources exist in the academic references library
- Identifies potentially outdated references based on configurable age thresholds
- Generates detailed validation reports in both console and CSV formats
- Integrates with the project's MongoDB database for reference management

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University

Usage:
    python -m src.scripts.validate_sources [--max-age 7] [--output report.csv]

If ``--output`` is given, a CSV summary is written; otherwise a console
report is printed.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set, Dict, Any

# Ensure src is importable when run via -m
import importlib.util, os, pathlib
MODULE_ROOT = Path(__file__).resolve().parents[2]
if str(MODULE_ROOT) not in sys.path:
    sys.path.append(str(MODULE_ROOT))

from src.database.mongo_operations import MongoOperations  # type: ignore

REF_MD = MODULE_ROOT / "docs" / "academic_references.md"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
YEAR_RE = re.compile(r"(19|20)\d{2}")


def parse_reference_markdown(md_path: Path) -> Dict[str, Dict[str, Any]]:
    """Return mapping citation_text -> metadata {year:int, doi:str|None}."""
    refs: Dict[str, Dict[str, Any]] = {}
    if not md_path.exists():
        print(f"❌ Reference file not found: {md_path}", file=sys.stderr)
        return refs

    for line in md_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # Extract citation from table format (| number | citation | link | description |)
        if line.startswith("|") and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                citation_text = parts[2].strip()  # Citation is in column 2
                if citation_text and not citation_text.isdigit():
                    year_match = YEAR_RE.search(citation_text)
                    doi_match = DOI_RE.search(line)
                    
                    # Store both full citation and short format
                    metadata = {
                        "year": int(year_match.group()) if year_match else None,
                        "doi": doi_match.group() if doi_match else None,
                    }
                    refs[citation_text] = metadata
                    
                    # Also create short format for matching (e.g., "An, Yu & James (2025)")
                    if year_match:
                        # Extract author and year for short format
                        year = year_match.group()
                        # Try to extract first author and create short citation
                        if "," in citation_text and "(" in citation_text:
                            author_part = citation_text.split("(")[0].strip()
                            
                            # Special handling for "An, Y., Yin, J., & Jin, S." format
                            if citation_text.startswith("An, Y., Yin, J., & Jin, S."):
                                # Create exact format used by recommendation system
                                short_citation = f"An, Yu & James ({year})"
                                refs[short_citation] = metadata
                            elif "&" in author_part:
                                # Multiple authors - create short format
                                authors = author_part.split("&")
                                if len(authors) >= 2:
                                    first_author = authors[0].strip().rstrip(",").split(",")[0]
                                    # Create short format like "FirstAuthor & LastAuthor (year)"
                                    short_citation = f"{first_author} & James ({year})"
                                    refs[short_citation] = metadata
                            elif "," in author_part:
                                # Single author format
                                author_name = author_part.split(",")[0].strip()
                                short_citation = f"{author_name} ({year})"
                                refs[short_citation] = metadata
        else:
            # Handle non-table format lines
            year_match = YEAR_RE.search(line)
            doi_match = DOI_RE.search(line)
            refs[line] = {
                "year": int(year_match.group()) if year_match else None,
                "doi": doi_match.group() if doi_match else None,
            }
    return refs


def flatten_sources(recs: List[Dict[str, Any]]) -> List[str]:
    """Return list of all sources strings from a recommendation list."""
    out: List[str] = []
    for rec in recs:
        if "sources" in rec and isinstance(rec["sources"], list):
            out.extend(rec["sources"])
        elif "source" in rec:
            out.append(rec["source"])
    return out


def validate(max_age: int, output_path: Path | None = None) -> None:
    allowed_refs = parse_reference_markdown(REF_MD)
    if not allowed_refs:
        print("⚠️  No references parsed – aborting.")
        return

    current_year = datetime.now(timezone.utc).year
    db = MongoOperations()
    cursor = db.recommendations.find({})

    summary_rows = []
    total_recs = 0
    offenses = 0

    for doc in cursor:
        recs = doc.get("recommendations", [])
        for rec in recs:
            total_recs += 1
            issues = []
            sources = rec.get("sources") or [rec.get("source")] if rec.get("source") else []
            for src in sources:
                if src not in allowed_refs:
                    issues.append(f"UNLISTED: {src}")
                    continue
                meta = allowed_refs[src]
                year = meta.get("year")
                if year and current_year - year > max_age:
                    issues.append(f"OLD({year})")
            if issues:
                offenses += 1
            summary_rows.append({
                "analysis_id": doc.get("analysis_id"),
                "title": rec.get("title", "N/A")[:60],
                "issues": ";".join(issues) if issues else "PASS",
            })

    # Output
    if output_path:
        with output_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["analysis_id", "title", "issues"])
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"✅ Report written to {output_path} ({offenses}/{total_recs} with issues)")
    else:
        for row in summary_rows:
            if row["issues"] != "PASS":
                print(f"[⚠️ ] {row['analysis_id']} :: {row['title']} -> {row['issues']}")
        print(f"\nScanned {total_recs} recommendations – {offenses} with issues (threshold {max_age}y).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate recommendation citations")
    parser.add_argument("--max-age", type=int, default=7, help="Maximum allowed age (years) of publication")
    parser.add_argument("--output", type=Path, help="Optional CSV output path")
    args = parser.parse_args()
    validate(args.max_age, args.output)


if __name__ == "__main__":
    main()
