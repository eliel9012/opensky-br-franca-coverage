"""Share of positions and p95 range by azimuth, Era A vs Era B -> figures/azimuth_range_ab.pdf

Same 10 degree binning as the original azimuth figure (np.arange(0, 361, 10) on
bearing_deg). Top panel: share of the era's positions per bin (%). Bottom panel:
p95 range per bin (km). Also writes analysis/azimuth_range_by_bin.json.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

from style import ERA_A_COLOR, ERA_B_COLOR, FIG_W, GREY, NPZ_DIR, ROOT, apply_style, save

BINS = np.arange(0, 361, 10)
BLIND = (290, 350)
PEAK = (140, 200)


def per_bin(d):
    b = d["bearing_deg"]
    r = d["range_km"]
    idx = np.clip(np.digitize(b, BINS) - 1, 0, len(BINS) - 2)
    counts = np.bincount(idx, minlength=len(BINS) - 1)
    p95 = np.array([np.percentile(r[idx == i], 95) if counts[i] else np.nan
                    for i in range(len(BINS) - 1)])
    median = np.array([np.median(r[idx == i]) if counts[i] else np.nan
                       for i in range(len(BINS) - 1)])
    return counts, counts / counts.sum() * 100, p95, median


def main() -> None:
    res = {}
    for era in ("a", "b"):
        d = np.load(NPZ_DIR / f"positions_era_{era}.npz")
        res[era] = per_bin(d)
        # cross-check against the frozen histogram
        h, _ = np.histogram(d["bearing_deg"], bins=BINS)
        assert (h == res[era][0]).all()

    out = {
        "bins_deg": BINS.tolist(),
        "binning": "10 degree bins, bearing_deg from receiver (rounded), np.arange(0,361,10)",
        "blind_sector_deg": list(BLIND),
        "peak_sector_deg": list(PEAK),
    }
    for era in ("a", "b"):
        c, pct, p95, med = res[era]
        out[f"era_{era}_counts"] = c.tolist()
        out[f"era_{era}_pct"] = np.round(pct, 3).tolist()
        out[f"era_{era}_p95_range_km"] = np.round(p95, 1).tolist()
        out[f"era_{era}_median_range_km"] = np.round(med, 1).tolist()
    (ROOT / "analysis" / "azimuth_range_by_bin.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")

    apply_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIG_W, 4.0), sharex=True,
                                   gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.10})
    x = BINS
    for ax in (ax1, ax2):
        ax.axvspan(*BLIND, color=GREY, alpha=0.22, lw=0, zorder=0)
        ax.axvspan(*PEAK, color="#E69F00", alpha=0.14, lw=0, zorder=0)
        ax.grid(True, axis="y", color="#dddddd", linewidth=0.5)
        ax.set_axisbelow(True)

    for era, color, label in (("a", ERA_A_COLOR, "Era A (32 d)"), ("b", ERA_B_COLOR, "Era B (137 d)")):
        _, pct, p95, _ = res[era]
        ax1.stairs(pct, x, baseline=None, color=color, lw=1.4, label=label)
        ax2.stairs(p95, x, baseline=None, color=color, lw=1.4)

    ax1.set_ylabel("share of positions (%)")
    ax1.set_ylim(0, 13.5)
    ax1.legend(loc="upper left", frameon=False, handlelength=1.6, borderaxespad=0.2)
    ax1.text(np.mean(BLIND), 13.0, "blind sector", ha="center", va="top", fontsize=8, color="#333333")
    ax1.text(np.mean(PEAK), 13.0, "peak", ha="center", va="top", fontsize=8, color="#7a5200")

    ax2.set_ylabel("p95 range (km)")
    ax2.set_ylim(0, max(res["a"][2].max(), res["b"][2].max()) * 1.08)
    ax2.set_xlabel("azimuth from receiver (deg)")
    ax2.set_xlim(0, 360)
    ax2.set_xticks(range(0, 361, 90))
    ax1.tick_params(labelbottom=False)

    fig.subplots_adjust(left=0.17, right=0.97, top=0.985, bottom=0.115)
    p = save(fig, "azimuth_range_ab.pdf")
    print(p)
    for era in ("a", "b"):
        c, pct, p95, med = res[era]
        bl = slice(29, 35)
        pk = slice(14, 20)
        print(era, "blind share %.2f%%" % pct[bl].sum(), "peak share %.2f%%" % pct[pk].sum(),
              "p95 blind range", np.nanmin(p95[bl]), np.nanmax(p95[bl]), "p95 peak", np.nanmin(p95[pk]), np.nanmax(p95[pk]),
              "min counts blind", c[bl].min())


if __name__ == "__main__":
    main()
