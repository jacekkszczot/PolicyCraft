#!/usr/bin/env python3
"""Convert American→British spelling in visible text within HTML/Jinja templates.

Only text nodes rendered to the user are altered; tag attributes, Jinja blocks
and variable placeholders remain untouched. The script operates idempotently
and preserves a *.bak* back-up of each modified template.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List
import sys

SPELLING_MAP: Dict[str, str] = {
    "color": "colour",
    "colors": "colours",
    "analyze": "analyse",
    "analyzed": "analysed",
    "analyzes": "analyses",
    "analyzing": "analysing",
    "organize": "organise",
    "organizes": "organises",
    "organizing": "organising",
    "organised": "organised",  # ensure already UK remains
    "organization": "organisation",
    "organizations": "organisations",
    "center": "centre",
    "centers": "centres",
    "license": "licence",
    "licenses": "licences",
    "utilize": "utilise",
    "utilizes": "utilises",
    "utilizing": "utilising",
}

WORD_RE = re.compile(r"\\b(" + "|".join(map(re.escape, SPELLING_MAP.keys())) + r")\\b", re.IGNORECASE)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
JINJA_SPLIT_RE = re.compile(r"(\{[{%].*?[}%]\})")


def convert_spelling(text: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        w = match.group(0)
        repl = SPELLING_MAP.get(w.lower(), w)
        if w.isupper():
            return repl.upper()
        if w[0].isupper():
            return repl.capitalize()
        return repl
    return WORD_RE.sub(_repl, text)


def process_line(line: str) -> str:
    """Process a single template line, converting visible text only."""
    parts = TAG_SPLIT_RE.split(line)
    new_parts: List[str] = []
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            # HTML tag, leave untouched
            new_parts.append(part)
        else:
            # Potentially visible text, but exclude Jinja blocks
            segments = JINJA_SPLIT_RE.split(part)
            for seg in segments:
                if JINJA_SPLIT_RE.match(seg):
                    new_parts.append(seg)
                else:
                    new_parts.append(convert_spelling(seg))
    return ''.join(new_parts)


def process_file(path: Path) -> bool:
    with path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = [process_line(ln) for ln in lines]
    if new_lines == lines:
        return False  # No change

    backup = path.with_suffix(path.suffix + '.bak2')
    shutil.copy2(path, backup)
    path.write_text(''.join(new_lines), encoding='utf-8')
    print(f"Updated visible text in {path.relative_to(PROJECT_ROOT)} (backup → {backup.name})")
    return True


def main(root: Path):
    modified = 0
    for file in root.rglob('*.html'):
        if process_file(file):
            modified += 1
    print(f"Completed conversion – {modified} template(s) modified.")


if __name__ == '__main__':
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if len(sys.argv) > 1:
        PROJECT_ROOT = Path(sys.argv[1]).resolve()
    main(PROJECT_ROOT / 'src' / 'web' / 'templates')
