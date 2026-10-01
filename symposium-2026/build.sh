#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ./texenv.sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex > paper-build-1.log
biber main > paper-biber.log
pdflatex -interaction=nonstopmode -halt-on-error main.tex > paper-build-2.log
pdflatex -interaction=nonstopmode -halt-on-error main.tex > paper-build-3.log
pdfinfo main.pdf
