"""
LiteratureRepository: unified, incremental index for literature sources.

- Provides a stable interface for analysis modules (confidence, stakeholder, risk/benefit)
- Automatically updates when a new literature document is integrated
- Reads from unified knowledge base path `docs/knowledge_base/`

British English spelling is used across messages and comments.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

try:
    # Reuse existing manager to read KB consistently
    from src.literature.knowledge_manager import KnowledgeBaseManager
except Exception:  # pragma: no cover
    KnowledgeBaseManager = None  # type: ignore


@dataclass
class SourceRecord:
    document_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    url: Optional[str]
    quality: Optional[float]  # 0–100
    topics: List[str]
    filename: Optional[str]


class LiteratureRepository:
    _instance: Optional["LiteratureRepository"] = None
    _lock = threading.Lock()

    def __init__(self, kb_path: str = "docs/knowledge_base") -> None:
        self.kb_path = kb_path
        self._kb = KnowledgeBaseManager(kb_path) if KnowledgeBaseManager else None
        self._index: Dict[str, SourceRecord] = {}
        self._last_refresh_ts: float = 0.0
        self._refresh_interval_s: int = 10  # debounce frequent updates
        self._build_index_full()

    @classmethod
    def get(cls) -> "LiteratureRepository":
        with cls._lock:
            if cls._instance is None:
                cls._instance = LiteratureRepository()
            return cls._instance

    # --------------------------- Public API ---------------------------
    def on_document_integrated(self, processing_results: Dict[str, Any]) -> None:
        """Incrementally add/update a single document after successful integration.
        processing_results should contain: document_id, filename, metadata, quality_score, insights.
        """
        try:
            doc_id = processing_results.get("document_id") or _stem(processing_results.get("filename"))
            if not doc_id:
                return
            rec = self._record_from_processing(processing_results)
            if rec:
                self._index[rec.document_id] = rec
                self._last_refresh_ts = time.time()
        except Exception:
            # Best-effort; do not interrupt the upload pipeline
            pass

    def refresh_indices_if_needed(self) -> None:
        """Debounced full refresh useful after batch/auto-scan operations."""
        now = time.time()
        if now - self._last_refresh_ts < self._refresh_interval_s:
            return
        self._build_index_full()

    def find_sources(self, query: Optional[str] = None, topics: Optional[List[str]] = None) -> List[SourceRecord]:
        """Very lightweight lookup by substring and/or topic tag."""
        q = (query or "").lower().strip()
        topics = topics or []
        out: List[SourceRecord] = []
        for rec in self._index.values():
            if q and q not in (rec.title or "").lower():
                # try authors
                if not any(q in (a or "").lower() for a in rec.authors):
                    continue
            if topics and not any(t.lower() in [x.lower() for x in rec.topics] for t in topics):
                continue
            out.append(rec)
        return out

    def get_metadata(self, document_id: str) -> Optional[SourceRecord]:
        return self._index.get(document_id)

    def stats(self) -> Dict[str, Any]:
        return {
            "count": len(self._index),
            "last_refresh": self._last_refresh_ts,
            "kb_path": self.kb_path,
        }

    # ------------------------ Internal helpers -----------------------
    def _build_index_full(self) -> None:
        try:
            if not self._kb:
                return
            docs = self._kb.get_all_documents()
            new_index: Dict[str, SourceRecord] = {}
            for d in docs:
                rec = self._record_from_kb(d)
                if rec:
                    new_index[rec.document_id] = rec
            self._index = new_index
            self._last_refresh_ts = time.time()
        except Exception:
            # Keep previous index on failure
            pass

    def _record_from_kb(self, d: Dict[str, Any]) -> Optional[SourceRecord]:
        try:
            meta = d.get("metadata", {})
            title = meta.get("title") or d.get("title") or _friendly_title(d.get("filename"))
            authors = meta.get("authors") or meta.get("author") or []
            if isinstance(authors, str):
                authors = [authors]
            year = None
            pub_date = meta.get("publication_date") or meta.get("publication_year")
            if isinstance(pub_date, str) and pub_date[:4].isdigit():
                year = int(pub_date[:4])
            elif isinstance(pub_date, int):
                year = pub_date
            url = meta.get("doi") or meta.get("url") or meta.get("source_url")
            quality = _to_pct(d.get("quality_score"))
            topics = meta.get("topics") or meta.get("tags") or []
            if isinstance(topics, str):
                topics = [topics]
            return SourceRecord(
                document_id=d.get("document_id") or _stem(d.get("filename")),
                title=title,
                authors=authors,
                year=year,
                url=url,
                quality=quality,
                topics=topics,
                filename=d.get("filename"),
            )
        except Exception:
            return None

    def _record_from_processing(self, pr: Dict[str, Any]) -> Optional[SourceRecord]:
        try:
            meta = pr.get("metadata", {})
            title = meta.get("title") or _friendly_title(pr.get("filename"))
            authors = meta.get("authors") or meta.get("author") or []
            if isinstance(authors, str):
                authors = [authors]
            year = None
            pub_date = meta.get("publication_date") or meta.get("publication_year")
            if isinstance(pub_date, str) and pub_date[:4].isdigit():
                year = int(pub_date[:4])
            elif isinstance(pub_date, int):
                year = pub_date
            url = meta.get("doi") or meta.get("url") or meta.get("source_url")
            quality = _to_pct(pr.get("quality_assessment", {}).get("total_score") or pr.get("quality_score"))
            topics = meta.get("topics") or meta.get("tags") or []
            if isinstance(topics, str):
                topics = [topics]
            return SourceRecord(
                document_id=pr.get("document_id") or _stem(pr.get("filename")),
                title=title,
                authors=authors,
                year=year,
                url=url,
                quality=quality,
                topics=topics,
                filename=pr.get("filename"),
            )
        except Exception:
            return None


def _to_pct(val: Any) -> Optional[float]:
    try:
        f = float(val)
        if f <= 1.0:
            f *= 100.0
        f = max(0.0, min(100.0, f))
        return round(f, 1)
    except Exception:
        return None


def _stem(filename: Optional[str]) -> str:
    if not filename:
        return ""
    base = os.path.basename(filename)
    if "." in base:
        base = base.rsplit(".", 1)[0]
    return base


def _friendly_title(filename: Optional[str]) -> str:
    stem = _stem(filename)
    if not stem:
        return "Untitled"
    # Drop leading IDs like abcdef12_, keep readable part
    parts = stem.split("_", 1)
    if len(parts) == 2:
        stem = parts[1]
    return stem.replace("_", " ").replace("-", " ").title()
