"""Era B daily maximum range per UTC day -> figures/daily_max_range.pdf

Stem plot of the per-day maximum range (ADS-B positions, receiver rounded),
600 km reference line and the three tropospheric ducting events marked.
The first day (2026-05-16) is partial: antenna swap at 21:35 UTC.
"""
from __future__ import annotations

from datetime import UTC, datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from style import FIG_W, NPZ_DIR, OI, GREY, apply_style, save

# (label, first day, last day) of the three ducting events (UTC)
EVENTS = [("1", "2026-06-16", "2026-06-18"), ("2", "2026-08-15", "2026-08-15"),
          ("3", "2026-08-25", "2026-08-25")]


def main() -> None:
    d = np.load(NPZ_DIR / "positions_era_b.npz")
    day = (d["abs_time"] // 86400).astype(np.int64)
    r = d["range_km"]
    order = np.argsort(day, kind="stable")
    day_s, r_s = day[order], r[order]
    uniq, start = np.unique(day_s, return_index=True)
    dmax = np.maximum.reduceat(r_s, start)
    dates = [datetime.fromtimestamp(int(u) * 86400, UTC).date() for u in uniq]
    iso = [x.isoformat() for x in dates]
    print(f"days={len(dates)} first={iso[0]} last={iso[-1]} first-day max={dmax[0]:.1f}")
    ev_days = {x for _, a, b in EVENTS for x in iso if a <= x <= b}
    for lab, a, b in EVENTS:
        sel = [dmax[i] for i, x in enumerate(iso) if a <= x <= b]
        print(f"event {lab} {a}..{b}: max {max(sel):.1f} km")
    print(f"max excluding event days: {max(v for v, x in zip(dmax, iso) if x not in ev_days):.1f}; "
          f"days >600: {[x for v, x in zip(dmax, iso) if v > 600]}")

    apply_style()
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    x = mdates.date2num(dates)
    is_ev = np.array([i in ev_days for i in iso])
    ax.plot(x, dmax, "-", lw=0.7, color=OI["blue"])
    ax.plot(x[~is_ev], dmax[~is_ev], "o", ms=2.0, color=OI["blue"])
    ax.plot(x[is_ev], dmax[is_ev], "o", ms=4.0, color=OI["vermillion"])
    ax.plot(x[0], dmax[0], "o", ms=3.6, mfc="white", mec=OI["blue"], mew=0.9)
    ax.annotate("partial day", (x[0], dmax[0]), xytext=(x[0] + 6, 425), fontsize=8,
                color=GREY, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6),
                va="center")
    ax.axhline(600, color="black", lw=0.9, ls="--")
    ax.text(x[-1] + 1, 600, "600 km", ha="right", va="bottom", fontsize=8)
    for lab, a, b in EVENTS:
        sel = [i for i, xx in enumerate(iso) if a <= xx <= b]
        i = max(sel, key=lambda k: dmax[k])
        ax.annotate(lab, (x[i], dmax[i]), xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color=OI["vermillion"],
                    fontweight="bold")
    ax.set_ylim(400, 830)
    ax.set_xlim(x[0] - 3, x[-1] + 3)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_ylabel("daily maximum range (km)")
    ax.set_xlabel("2026 (UTC day)")
    fig.tight_layout(pad=0.4)
    save(fig, "daily_max_range.pdf")


if __name__ == "__main__":
    main()
