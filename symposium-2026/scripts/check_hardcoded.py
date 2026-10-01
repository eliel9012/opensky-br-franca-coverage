#!/usr/bin/env python3
"""Fail if a data value from numbers.json appears hard-coded in a .tex file other than numbers.tex.

Short or ambiguous values (single digits, bare years, plain words) are skipped
because they would match ordinary prose; every value with a decimal point, a
thousands separator or at least four digits (other than a year) is checked.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
macros = json.loads((ROOT / "numbers.json").read_text())["macros"]
tex_files = [p for p in [ROOT / "main.tex", ROOT / "poster" / "poster.tex"] if p.exists()]

def strip_comments(text):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", l) for l in text.splitlines())

def checkable(v):
    if not re.search(r"\d", v):
        return False
    if re.fullmatch(r"(19|20)\d\d", v):
        return False
    if re.fullmatch(r"\d{4}-\d\d-\d\d", v):
        return False
    return bool(re.search(r"\d[.,]\d", v)) or len(re.sub(r"\D", "", v)) >= 4

bad = 0
for name, m in sorted(macros.items()):
    v = str(m["value"]).strip()
    if not checkable(v):
        continue
    pat = re.compile(r"(?<![\d.,])" + re.escape(v) + r"(?![\d])")
    for f in tex_files:
        text = strip_comments(f.read_text())
        for ln, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                print(f"HARDCODED {v!r} (\\{name}) in {f.relative_to(ROOT)}:{ln}")
                bad += 1
print(f"hardcoded-value check: {bad} problem(s)")
sys.exit(1 if bad else 0)
