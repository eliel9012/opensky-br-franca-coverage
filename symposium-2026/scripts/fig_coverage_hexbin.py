"""Era B coverage hexbin -> figures/coverage_era_b_hexbin.pdf

Raw Era B positions (ducting points included in the data). Axis limits cover the
500 km ring plus a margin; points beyond that frame (ducting outliers up to
786 km and a few far-south reports) are outside the view and not drawn.
Receiver rounded; airports and label offsets reused from data/scripts/make_figures.py.
"""
from __future__ import annotations

import math

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from style import FIG_W, NPZ_DIR, RECV_LAT, RECV_LON, apply_style, save

GRIDSIZE = 80
AIRPORTS = [
    ("FRC", -20.592, -47.383),
    ("RAO", -21.136, -47.774),
    ("VCP", -23.007, -47.134),
    ("GRU", -23.432, -46.470),
    ("CGH", -23.626, -46.656),
    ("CNF", -19.624, -43.972),
]
# offsets from make_figures.py, adjusted here for the narrow 3.4 in frame
AIRPORT_OFFSETS = {
    "FRC": (0.14, 0.12), "RAO": (0.10, -0.12), "VCP": (0.10, 0.08),
    "GRU": (0.14, 0.04), "CGH": (-0.62, -0.34), "CNF": (0.10, 0.08),
}
RING_LABEL_BEARING = 315  # inside the blind sector, where cells are sparse
MARGIN_DEG = 0.35


def destination_point(lat, lon, dist_km, bearing_deg, r=6371.0088):
    b = math.radians(bearing_deg)
    p1, l1 = math.radians(lat), math.radians(lon)
    d = dist_km / r
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1),
                         math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def main() -> None:
    d = np.load(NPZ_DIR / "positions_era_b.npz")
    lon, lat = d["lon"], d["lat"]

    # frame: 500 km ring bounding box plus margin
    ring500 = [destination_point(RECV_LAT, RECV_LON, 500, b) for b in range(0, 360, 2)]
    la = [p[0] for p in ring500]
    lo = [p[1] for p in ring500]
    xlim = (min(lo) - MARGIN_DEG, max(lo) + MARGIN_DEG)
    ylim = (min(la) - MARGIN_DEG, max(la) + MARGIN_DEG)

    apply_style()
    fig, ax = plt.subplots(figsize=(FIG_W, 2.75))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect(1 / math.cos(math.radians(RECV_LAT)), adjustable="box")
    ax.set_facecolor("#fbfbf7")
    ax.grid(True, color="#dddddd", linewidth=0.4, alpha=0.75, zorder=0)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)

    hb = ax.hexbin(lon, lat, gridsize=GRIDSIZE, mincnt=1, bins="log", cmap="cividis",
                   linewidths=0, zorder=2, extent=(*xlim, *ylim), rasterized=True)

    halo = [pe.withStroke(linewidth=1.8, foreground="white", alpha=0.85)]
    for dist in (100, 250, 500):
        ring = [destination_point(RECV_LAT, RECV_LON, dist, b) for b in range(0, 361, 3)]
        ax.plot([p[1] for p in ring], [p[0] for p in ring], color="#262626",
                linewidth=0.8, alpha=0.65, zorder=5)
        la_, lo_ = destination_point(RECV_LAT, RECV_LON, dist, RING_LABEL_BEARING)
        ax.text(lo_, la_, str(dist), fontsize=8, color="#202020", ha="center", va="center",
                zorder=7, path_effects=halo)

    ax.scatter([RECV_LON], [RECV_LAT], s=80, marker="*", color="#8f1d18",
               edgecolor="white", linewidth=0.8, zorder=8)
    for code, alat, alon in AIRPORTS:
        if xlim[0] <= alon <= xlim[1] and ylim[0] <= alat <= ylim[1]:
            ax.scatter([alon], [alat], marker="+", s=22, color="#202020",
                       linewidth=1.0, zorder=7, path_effects=halo)
            dx, dy = AIRPORT_OFFSETS[code]
            ax.text(alon + dx, alat + dy, code, fontsize=8, color="#202020", zorder=9,
                    path_effects=halo)

    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.xaxis.set_major_locator(plt.MultipleLocator(2))
    ax.yaxis.set_major_locator(plt.MultipleLocator(2))

    fig.subplots_adjust(left=0.14, right=0.80, top=0.985, bottom=0.158)
    ax.apply_aspect()
    pos = ax.get_position()
    cax = fig.add_axes([pos.x1 + 0.025, pos.y0, 0.03, pos.height])
    cbar = fig.colorbar(hb, cax=cax)
    cbar.set_label("positions per cell (log)", fontsize=8)
    cbar.ax.tick_params(labelsize=8, length=2)
    cbar.outline.set_linewidth(0.5)

    out = save(fig, "coverage_era_b_hexbin.pdf", dpi=600)
    print(out, f"{out.stat().st_size / 1e6:.2f} MB", "xlim", xlim, "ylim", ylim)


if __name__ == "__main__":
    main()
