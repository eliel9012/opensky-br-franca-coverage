#!/usr/bin/env python3
"""Recolor only the FRC receiver marker in the poster's vector PDF copy.

No data or raster layer is changed. The shared paper figure remains intact.
Input: ../figures/coverage_era_b_hexbin.pdf
Output: figures/coverage_era_b_hexbin.pdf
Dependency: pypdf
"""
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, FloatObject

HERE = Path(__file__).resolve().parent
source = HERE.parent / 'figures/coverage_era_b_hexbin.pdf'
target = HERE / 'figures/coverage_era_b_hexbin.pdf'
reader = PdfReader(source)
writer = PdfWriter()
writer.add_page(reader.pages[0])
page = writer.pages[0]
stream = ContentStream(page.get_contents(), writer)
old = (143/255, 29/255, 24/255)  # Original receiver red, #8F1D18.
new = (86/255, 180/255, 233/255)  # Okabe-Ito sky blue, #56B4E9.
count = 0
for operands, operator in stream.operations:
    if operator == b'rg' and len(operands) == 3 and all(abs(float(x)-y)<1e-8 for x,y in zip(operands,old)):
        operands[:] = [FloatObject(x) for x in new]
        count += 1
if count != 2:
    raise RuntimeError(f'Expected two marker fill settings, found {count}; inspect source before recoloring')
page.replace_contents(stream)
target.parent.mkdir(exist_ok=True)
with target.open('wb') as f:
    writer.write(f)
print(f'{target}: receiver marker sky blue; white outline unchanged')
