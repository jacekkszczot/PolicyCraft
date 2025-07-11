# !/usr/bin/env python3
"""PolicyCraft – Bulk comment refactoring utility.

This helper traverses the repository, updating comments and doc-strings to
British English whilst preserving executable code verbatim.  A lightweight
American→British spelling map is employed; the utility may be executed
multiple times safely, thanks to automatic *.bak* back-ups.

Usage
-----
    python tools/refactor_comments.py [ROOT_DIR]

If *ROOT_DIR* is omitted, the script assumes the directory containing this
file and ascends one level to the project root.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tokenize
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# American → British spelling substitutions (extend where necessary)
# ---------------------------------------------------------------------------
SPELLING_MAP: Dict[str, str] = {
    "color": "colour",
    "colors": "colours",
    "initialize": "initialise",
    "initialized": "initialised",
    "initializes": "initialises",
    "initializing": "initialising",
    "analyze": "analyse",
    "analyzed": "analysed",
    "analyzer": "analyser",
    "analyzing": "analysing",
    "organize": "organise",
    "organized": "organised",
    "organizing": "organising",
    "organizes": "organises",
    "center": "centre",
    "centered": "centred",
    "centering": "centring",
    "license": "licence",
    "licenses": "licences",
    "modeling": "modelling",
    "utilize": "utilise",
    "utilized": "utilised",
    "utilizes": "utilises",
    "utilizing": "utilising",
}

WORD_RE = re.compile(r"\\b(" + "|".join(map(re.escape, SPELLING_MAP.keys())) + r")\\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def convert_spelling(text: str) -> str:
    """Convert American English words in *text* to British English, case-preserving."""

    def _repl(match: re.Match[str]) -> str:
        word = match.group(0)
        lower_word = word.lower()
        replacement = SPELLING_MAP.get(lower_word, word)
        # Preserve original capitalisation style
        if word.isupper():
            return replacement.upper()
        if word[0].isupper():
            return replacement.capitalize()
        return replacement

    return WORD_RE.sub(_repl, text)


# ---------------------------------------------------------------------------
# Python processing via *tokenize*
# ---------------------------------------------------------------------------

def refactor_python(path: Path) -> bool:
    """Rewrite comments and doc-strings in *path*. Returns *True* if modified."""
    modified = False
    with path.open("r", encoding="utf-8") as f:
        src = f.read()
    tokens: List[tokenize.TokenInfo] = []
    changed_any = False
    try:
        for tok in tokenize.generate_tokens(iter(src.splitlines(True)).__next__):
            if tok.type == tokenize.COMMENT:
                new = "# " + convert_spelling(tok.string.lstrip("# "))
                if new != tok.string:
                    tok = tok._replace(string=new)
                    changed_any = True
            elif tok.type == tokenize.STRING and is_probable_docstring(tok, tokens):
                # Strip triple quotes and convert internal text
                quote = tok.string[:3]
                inner = tok.string[3:-3]
                new_inner = convert_spelling(inner)
                if new_inner != inner:
                    tok = tok._replace(string=f"{quote}{new_inner}{quote}")
                    changed_any = True
            tokens.append(tok)
    except tokenize.TokenError:
        # Fall back to line-wise replacement (safer than failing)
        new_src = convert_spelling(src)
        if new_src != src:
            backup_and_write(path, new_src)
            return True
        return False

    if changed_any:
        new_src = tokenize.untokenize(tokens)
        backup_and_write(path, new_src)
        modified = True
    return modified


def is_probable_docstring(tok: tokenize.TokenInfo, prev_tokens: List[tokenize.TokenInfo]) -> bool:
    """Heuristic: string token is a doc-string if it is the first in module or
    immediately follows *def*/*class* with INDENT."""
    if not prev_tokens:  # module docstring
        return True
    # Look at previous non-NL/COMMENT tokens
    for prev in reversed(prev_tokens):
        if prev.type in {tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT}:
            continue
        return prev.string in {"def", "class"}
    return False

# ---------------------------------------------------------------------------
# Simple pattern-based replacement for HTML / CSS
# ---------------------------------------------------------------------------

def process_block_comments(content: str, start: str, end: str) -> Tuple[str, bool]:
    """Replace spelling within comment blocks delimited by *start*/*end*."""
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)

    def _repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        new_inner = convert_spelling(inner)
        return f"{start}{new_inner}{end}"

    new_content, n = pattern.subn(_repl, content)
    return new_content, n > 0


def refactor_text_file(path: Path, filetype: str) -> bool:
    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    modified = False
    if filetype == "html":
        content, modified = process_block_comments(content, "<!--", "-->")
    elif filetype == "css":
        content, modified = process_block_comments(content, "/*", "*/")
    else:
        return False

    if modified:
        backup_and_write(path, content)
    return modified

# ---------------------------------------------------------------------------
# File IO helpers
# ---------------------------------------------------------------------------

def backup_and_write(path: Path, new_content: str) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    path.write_text(new_content, encoding="utf-8")
    print(f"Updated {path.relative_to(PROJECT_ROOT)} (backup → {backup_path.name})")

# ---------------------------------------------------------------------------
# Main traversal
# ---------------------------------------------------------------------------

def walk_repository(root: Path) -> None:
    modified_files = 0
    for file in root.rglob("*"):
        if not file.is_file():
            continue
        if file.match("*.py"):
            if refactor_python(file):
                modified_files += 1
        elif file.match("*.html") or file.match("*.jinja"):
            if refactor_text_file(file, "html"):
                modified_files += 1
        elif file.match("*.css"):
            if refactor_text_file(file, "css"):
                modified_files += 1
    print(f"\nRefactor complete – {modified_files} file(s) modified.")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    PROJECT_ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    print(f"Scanning repository root: {PROJECT_ROOT}\n")
    walk_repository(PROJECT_ROOT)
