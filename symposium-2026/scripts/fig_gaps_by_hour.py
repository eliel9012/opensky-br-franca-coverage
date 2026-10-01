"""Era B coverage gaps by UTC start hour -> figures/gaps_by_hour.pdf

Gaps: inter-arrival > 120 s in the merged sorted timestamps of all valid ADS-B
positions of Era B (same method as data/scripts/compute_metrics.py). The two
receiver outages (2026-07-06 19:09 to 07-07 00:21 UTC and 2026-08-02 02:48 to
12:35 UTC) are coloured separately; all other gaps use the base colour.
"""
from __future__ import annotations

from datetime import UTC, datetime

import matplotlib.pyplot as plt
import numpy as np

from style import FIG_W, NPZ_DIR, OI, apply_style, save

OUTAGE_STARTS = [datetime(2026, 7, 6, 19, 9, tzinfo=UTC), datetime(2026, 8, 2, 2, 48, tzinfo=UTC)]
TOL_S = 180  # report start = first minute after the last position before the gap


def main() -> None:
    d = np.load(NPZ_DIR / "positions_era_b.npz")
    t = np.sort(d["abs_time"])
    diffs = np.diff(t)
    idx = np.where(diffs > 120.0)[0]
    starts = [datetime.fromtimestamp(float(t[i]), UTC) for i in idx]
    durs = diffs[idx]
    n = len(starts)
    is_out = np.array([any(abs((s - o).total_seconds()) <= TOL_S for o in OUTAGE_STARTS) for s in starts])
    hours = np.array([s.hour for s in starts])
    hist_all = np.bincount(hours, minlength=24)
    hist_out = np.bincount(hours[is_out], minlength=24)
    hist_oth = hist_all - hist_out
    in_win = int(((hours >= 5) & (hours < 7)).sum())
    print(f"gaps={n} outages_matched={int(is_out.sum())} starts in [05,07) UTC={in_win}")
    print("hour histogram:", hist_all.tolist())
    for s, du, o in zip(starts, durs, is_out):
        if du > 3600:
            print(f"  >60min: {s.isoformat(timespec='minutes')} dur={du/60:.0f} min outage={bool(o)}")

    apply_style()
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    h = np.arange(24)
    ax.axvspan(4.5, 6.5, color=OI["sky"], alpha=0.25, lw=0, zorder=0)
    ax.bar(h, hist_oth, width=0.8, color=OI["blue"], label="other gaps", zorder=2)
    ax.bar(h, hist_out, width=0.8, bottom=hist_oth, color=OI["vermillion"],
           label="receiver outages", zorder=2)
    ymax = hist_all.max()
    ax.set_ylim(0, ymax + 2)
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))
    ax.text(7.2, ymax + 1.8, "05 to 07 UTC\n(02 to 04 local)", ha="left", va="top",
            fontsize=8)
    ax.set_xlim(-0.7, 23.7)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlabel("gap start hour (UTC)")
    ax.set_ylabel("gaps (count)")
    ax.legend(loc="upper right", frameon=False, handlelength=1.0)
    fig.tight_layout(pad=0.4)
    save(fig, "gaps_by_hour.pdf")


if __name__ == "__main__":
    main()
