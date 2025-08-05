"""
Validation Utilities for PolicyCraft AI Policy Analysis.

This module provides validation functions for ensuring data integrity and consistency
across the PolicyCraft platform. It includes utilities for validating recommendation
citations, academic references, and other data structures used throughout the application.

Key Features:
- Validation of academic references against a centralised reference library
- Citation normalisation and matching for robust reference checking
- Detection of potentially outdated or missing references
- Support for batch validation of multiple recommendations

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parents[2]
REF_MD = ROOT_DIR / "docs" / "academic_references.md"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
YEAR_RE = re.compile(r"(19|20)\d{2}")


def _load_reference_index() -> Dict[str, Dict[str, Any]]:
    """Return mapping citation string -> metadata (year, doi). Cached in module attr."""
    # Always reload to reflect recent edits - size is small so overhead negligible
    refs: Dict[str, Dict[str, Any]] = {}
    if not REF_MD.exists():
        return refs
    for line in REF_MD.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        year_match = YEAR_RE.search(line)
        doi_match = DOI_RE.search(line)
        refs[line] = {
            "year": int(year_match.group()) if year_match else None,
            "doi": doi_match.group() if doi_match else None,
        }
    return refs


def _norm(text: str) -> str:
    """Normalize citation string for loose comparison."""
    # Remove common citation patterns that might cause mismatches
    text = re.sub(r'[\[\]"\']', '', text)  # Remove brackets and quotes
    text = re.sub(r'\([^)]*\)', '', text)   # Remove anything in parentheses
    text = re.sub(r'\b(et al\.?|and (others|colleagues))\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text.strip().lower())
    return text


def _extract_authors_year(citation: str) -> tuple[str, str]:
    """Extract author(s) and year from citation string."""
    # Match patterns like "Chen et al. (2024)" or "(Chen et al., 2024)"
    import re
    match = re.search(r'([A-Z][a-z]+(?:\s+et\s+al\.)?(?:\s+[A-Z][a-z]+)*)[\s,]*\(?(\d{4})\)?', citation)
    if match:
        authors = match.group(1).strip()
        year = match.group(2)
        return authors, year
    return None, None

def _find_best_match(citation: str, allowed_refs: Dict[str, Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
    """Find the best matching reference for a given citation.
    
    Args:
        citation: The citation text to match
        allowed_refs: Dictionary of allowed references with metadata
        
    Returns:
        Tuple of (matched_reference_text, reference_metadata) or (None, None) if no match
    """
    if not citation or not allowed_refs:
        return None, None
        
    norm_citation = _norm(citation)
    
    # Try exact match first
    for ref_text, ref_data in allowed_refs.items():
        if _norm(ref_text) == norm_citation:
            return ref_text, ref_data
    
    # Try to extract author(s) and year
    authors, year = _extract_authors_year(citation)
    
    # If we have author and year, try to find a matching reference
    if authors and year:
        for ref_text, ref_data in allowed_refs.items():
            # Check if both author and year are in the reference
            if (authors.lower() in ref_text.lower() and 
                f'({year})' in ref_text or f', {year}' in ref_text):
                return ref_text, ref_data
    
    # Try partial match as fallback
    for ref_text, ref_data in allowed_refs.items():
        norm_ref = _norm(ref_text)
        # Check if citation is a substring of reference or vice versa
        if (norm_citation in norm_ref or 
            norm_ref in norm_citation or 
            any(word in norm_ref for word in norm_citation.split() if len(word) > 3)):
            return ref_text, ref_data
    
    # Try to match by first few words of the title if available
    title_words = [w for w in norm_citation.split() if len(w) > 3]
    if len(title_words) > 2:
        for ref_text, ref_data in allowed_refs.items():
            norm_ref = _norm(ref_text)
            if all(word in norm_ref for word in title_words[:3]):
                return ref_text, ref_data
    
    return None, None

def validate_recommendation_sources(recommendations: List[Dict[str, Any]], max_age: int = 7) -> List[Dict[str, Any]]:
    """Return list of issues per recommendation.

    Each issue dict: {idx, title, issues: [str], sources: [str]}
    Empty issues list == pass.
    """
    allowed_refs = _load_reference_index()
    current_year = datetime.utcnow().year
    results: List[Dict[str, Any]] = []

    for idx, rec in enumerate(recommendations):
        title = rec.get("title", f"rec_{idx}")
        srcs = rec.get("sources") or ([rec.get("source")] if rec.get("source") else [])
        issues: List[str] = []
        validated_sources = []

        for src in srcs:
            if not src:
                continue
                
            # Find the best matching reference
            ref_text, ref_data = _find_best_match(src, allowed_refs)
            
            if ref_text is None:
                issues.append(f"UNLISTED: {src}")
                validated_sources.append({"original": src, "validated": None, "valid": False})
                continue
                
            # Check publication year if available
            yr = ref_data.get("year")
            if yr and current_year - yr > max_age:
                issues.append(f"OUTDATED: {ref_text} (from {yr})")
                
            validated_sources.append({
                "original": src,
                "validated": ref_text,
                "valid": True,
                "year": yr
            })

        results.append({
            "idx": idx,
            "title": title,
            "issues": issues,
            "sources": validated_sources
        })

    return results
