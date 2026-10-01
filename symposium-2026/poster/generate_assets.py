"""Poster-only layout of the existing azimuth summary. No metrics recomputed."""
from pathlib import Path
import json, sys
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from style import apply_style, ERA_A_COLOR, ERA_B_COLOR
j = json.loads((ROOT / "analysis/azimuth_range_by_bin.json").read_text())
apply_style()
plt.rcParams.update({"font.size":11,"axes.labelsize":11,"xtick.labelsize":10,"ytick.labelsize":10,"legend.fontsize":10})
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.7), sharex=True)
for ax in axes:
    ax.axvspan(*j["blind_sector_deg"], color="#6b6b6b", alpha=.20, lw=0)
    ax.axvspan(*j["peak_sector_deg"], color="#E69F00", alpha=.14, lw=0)
    ax.grid(axis="y", color="#dddddd", lw=.5)
    ax.set_axisbelow(True)
    ax.set_xlim(0,360)
    ax.set_xticks([0,90,180,270,360])
    ax.set_xlabel("Azimuth (deg)")
for era, color, label in [("a",ERA_A_COLOR,"Era A"),("b",ERA_B_COLOR,"Era B")]:
    axes[0].stairs(j[f"era_{era}_pct"], j["bins_deg"], baseline=None, color=color, label=label, lw=1.6)
    axes[1].stairs(j[f"era_{era}_p95_range_km"], j["bins_deg"], baseline=None, color=color, lw=1.6)
axes[0].set_ylabel("Share of positions (%)")
axes[0].set_ylim(0,13.5)
axes[0].legend(frameon=False, loc="upper left")
axes[1].set_ylabel("P95 range (km)")
axes[1].set_ylim(0,450)
axes[1].text(320,440,"Blind",ha="center",va="top",fontsize=10,color="#444444")
fig.tight_layout(pad=.6,w_pad=1.7)
fig.savefig(ROOT/"poster/figures/azimuth_range_ab.pdf",bbox_inches="tight")
