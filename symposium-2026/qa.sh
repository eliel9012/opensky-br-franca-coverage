#!/usr/bin/env bash
# Submission checks for the 2026 OpenSky poster short paper.
set -euo pipefail
cd "$(dirname "$0")"
source ./texenv.sh
"${PYTHON:-python3}" scripts/check_hardcoded.py
bash build.sh > paper-qa-build.log
bash poster/build.sh
"${PYTHON:-python3}" - <<'PY'
from pathlib import Path
import re, subprocess
p=Path('.')
tex=(p/'main.tex').read_text()
body=tex.split(r'\begin{document}',1)[1]
assert 'manuscript=poster' in tex and 'layout=preprint' in tex
assert r'\conference{The 14th OpenSky Symposium}' in tex
assert not re.search(r'\\(?:input|include)\s*\{',tex), 'External TeX input in submission'
assert 'TODO' not in tex
assert not re.search(r'\\(?:geometry|newgeometry|enlargethispage|tiny)\b',body)
assert '\u2014' not in tex and '-'*3 not in tex
for name in ['main.pdf','poster/poster.pdf']:
    info=subprocess.check_output(['pdfinfo',name],text=True)
    pages=int(re.search(r'Pages:\s+(\d+)',info)[1])
    if name=='main.pdf':
        assert pages<=4, 'Paper exceeds four pages including references'
    else:
        assert pages==1
        w,h=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups())
        assert abs(w*25.4/72-841)<.01 and abs(h*25.4/72-1189)<.01
    text=subprocess.check_output(['pdftotext',name,'-'],text=True)
    assert 'TODO' not in text
    rows=subprocess.check_output(['pdffonts',name],text=True).splitlines()[2:]
    assert all(row.split()[-5]=='yes' for row in rows if row.strip()), 'Unembedded font'
    assert all('Type 3' not in row for row in rows)
    print(f'PASS: {name}, {pages} pages, fonts embedded, no TODOs')
for name in ['main.log','poster/poster.log']:
    log=Path(name).read_text()
    assert not re.search(r'^!|Undefined control sequence|undefined references|Citation .* undefined',log,re.M)
    widths=[float(v) for v in re.findall(r'Overfull \\[hv]box \(([\d.]+)pt',log)]
    assert max(widths,default=0)<=5, f'Overfull box above 5 pt: {name}'
assert not re.search(r'ERROR|WARN',Path('paper-biber.log').read_text())
print('PASS: JOAS poster category, single main.tex, four-page limit, A0 poster, no compile errors')
print('NOTE: exact site coordinates are included at the author\'s explicit request; analysis origin stays rounded.')
assert '10.5281/zenodo.23090597' in tex and 'felipe2026traces' in tex
assert 'available on request' not in tex
assert 'zenodo.23090597' in Path('poster/poster.tex').read_text()
print('PASS: public dataset DOI in paper and poster; code DOI retained separately.')
PY
