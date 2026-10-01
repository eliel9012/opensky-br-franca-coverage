#!/usr/bin/env bash
# Build only the A0 poster; never rebuild or edit the short paper.
set -euo pipefail
cd "$(dirname "$0")"
source ../texenv.sh
"${PYTHON:-python3}" ../scripts/check_hardcoded.py
for pass in 1 2; do
  pdflatex -interaction=nonstopmode -halt-on-error poster.tex > "build-pass${pass}.log"
done
if grep -Eq 'Overfull|Underfull|LaTeX Warning|LaTeX Font Warning|^!' poster.log; then
  grep -nE 'Overfull|Underfull|LaTeX Warning|LaTeX Font Warning|^!' poster.log
  exit 1
fi
pdfinfo poster.pdf | grep -E 'Pages:|Page size:|Page rot:'
"${PYTHON:-python3}" - <<'PY'
import re, subprocess
info = subprocess.check_output(['pdfinfo', 'poster.pdf'], text=True)
assert re.search(r'Pages:\s+1\b', info), 'Poster must have one page'
w,h=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups())
assert abs(w*25.4/72-841)<.01 and abs(h*25.4/72-1189)<.01, 'Poster must be A0 portrait'
text=subprocess.check_output(['pdftotext','poster.pdf','-'],text=True)
assert 'TODO' not in text and 'TODO' not in open('poster.tex').read()
print('PASS: A0 portrait, one page, no pending markers or LaTeX warnings')
PY
cp poster.pdf ../poster.pdf
