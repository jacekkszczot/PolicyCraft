"""Utility functions for validating recommendation citations."""
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
    return re.sub(r"\s+", " ", text.strip().lower())


def validate_recommendation_sources(recommendations: List[Dict[str, Any]], max_age: int = 7) -> List[Dict[str, Any]]:
    """Return list of issues per recommendation.

    Each issue dict: {idx, title, issues: [str]}
    Empty issues list == pass.
    """
    allowed_refs = _load_reference_index()
    current_year = datetime.utcnow().year

    # Build normalized lookup for quick matching
    norm_allowed = {_norm(k): k for k in allowed_refs}

    results: List[Dict[str, Any]] = []
    for idx, rec in enumerate(recommendations):
        title = rec.get("title", f"rec_{idx}")
        srcs = rec.get("sources") or ([rec.get("source")] if rec.get("source") else [])
        issues: List[str] = []

        for src in srcs:
            norm_src = _norm(src)
            orig_key = norm_allowed.get(norm_src)
            if orig_key is None:
                issues.append(f"UNLISTED: {src}")
                continue
            meta = allowed_refs[orig_key]
            yr = meta.get("year")
            if yr and current_year - yr > max_age:
                issues.append(f"OLD({yr})")

        results.append({"idx": idx, "title": title, "issues": issues})

    return results
