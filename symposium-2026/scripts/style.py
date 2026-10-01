"""Shared matplotlib style for paper and poster figures.

Design rule: every figure is drawn at FIG_W inches wide (paper subfigure width)
with fonts >= 8 pt, so it stays legible in the paper and, scaled about 3x,
at A0 on the poster.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
NPZ_DIR = ROOT / "data" / "scripts" / "out"
FIG_DIR.mkdir(exist_ok=True)

# Receiver position, rounded for privacy. Never use unrounded coordinates.
RECV_LAT, RECV_LON = -20.51, -47.40
R_EARTH_KM = 6371.0088
ADSB_SOURCES = ("adsb_icao", "adsb_icao_nt")

FIG_W = 3.4  # inches, one paper subfigure column

# Okabe-Ito (colour-blind safe)
OI = {
    "black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73",
    "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7",
}
ERA_A_COLOR = OI["vermillion"]
ERA_B_COLOR = OI["blue"]
ACCENT = OI["orange"]
GREY = "#6b6b6b"


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.4,
        "pdf.fonttype": 42,   # embed TrueType, no Type 3
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })


def save(fig, name: str, **kw) -> Path:
    path = FIG_DIR / name
    fig.savefig(path, **kw)
    plt.close(fig)
    return path
