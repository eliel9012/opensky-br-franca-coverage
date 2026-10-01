#!/usr/bin/env python3
"""Fase H figures, same visual style as referencia/era_a_rebuild/generate_era_a_fixed_window.py."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DATA = Path(__file__).resolve().parent / "out"
OUT_FIG = ROOT / "relatorios"
OUT_FIG.mkdir(exist_ok=True)

RECV_LAT, RECV_LON = -20.51, -47.40
SENSOR_ID = "-1408044782"
GRIDSIZE = 80
AIRPORTS = [
    ("FRC", -20.592, -47.383),
    ("RAO", -21.136, -47.774),
    ("VCP", -23.007, -47.134),
    ("GRU", -23.432, -46.470),
    ("CGH", -23.626, -46.656),
    ("CNF", -19.624, -43.972),
]
AIRPORT_OFFSETS = {
    "FRC": (0.06, -0.16), "RAO": (0.06, -0.12), "VCP": (0.07, 0.08),
    "GRU": (0.07, -0.11), "CGH": (-0.42, -0.08), "CNF": (0.07, 0.08),
}
COLORBAR_LABEL = "ADS-B position reports per ~10 km hex cell (log scale)"


def destination_point(lat, lon, dist_km, bearing_deg, r=6371.0088):
    b = math.radians(bearing_deg)
    p1, l1 = math.radians(lat), math.radians(lon)
    d = dist_km / r
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def draw_coverage(ax, lat_arr, lon_arr, vmin=None, vmax=None):
    lat_vals = np.append(lat_arr, RECV_LAT)
    lon_vals = np.append(lon_arr, RECV_LON)
    ymin, ymax = float(lat_vals.min()), float(lat_vals.max())
    xmin, xmax = float(lon_vals.min()), float(lon_vals.max())
    lat_pad = max(0.25, (ymax - ymin) * 0.05)
    lon_pad = max(0.25, (xmax - xmin) * 0.05)
    ax.set_ylim(ymin - lat_pad, ymax + lat_pad)
    ax.set_xlim(xmin - lon_pad, xmax + lon_pad)
    ax.set_aspect("equal", adjustable="box")
    hb = ax.hexbin(lon_arr, lat_arr, gridsize=GRIDSIZE, mincnt=1, bins="log",
                   cmap="cividis", linewidths=0, alpha=0.95, zorder=2,
                   vmin=vmin, vmax=vmax)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, color="#dddddd", linewidth=0.45, alpha=0.75)
    ax.set_facecolor("#fbfbf7")
    for dist in (100, 250, 500):
        ring = [destination_point(RECV_LAT, RECV_LON, dist, b) for b in range(0, 361, 3)]
        ax.plot([p[1] for p in ring], [p[0] for p in ring], color="#262626", linewidth=0.9, alpha=0.58, zorder=5)
    ax.scatter([RECV_LON], [RECV_LAT], s=70, marker="*", color="#8f1d18", edgecolor="white", linewidth=0.8, zorder=6)
    cx0, cx1 = ax.get_xlim(); cy0, cy1 = ax.get_ylim()
    for code, lat, lon in AIRPORTS:
        if cx0 <= lon <= cx1 and cy0 <= lat <= cy1:
            ax.scatter([lon], [lat], marker="+", s=28, color="#202020", linewidth=0.7, zorder=7)
            dx, dy = AIRPORT_OFFSETS.get(code, (0.05, 0.05))
            ax.text(lon + dx, lat + dy, code, fontsize=6.8, color="#202020", zorder=7)
    return hb


def fig1_hexbin_era_b(d_b, metrics):
    fig, ax = plt.subplots(figsize=(7.1, 7.2), dpi=220)
    fig.patch.set_facecolor("white")
    hb = draw_coverage(ax, d_b["lat"], d_b["lon"])
    ax.set_title(f"Local ADS-B coverage, sensor {SENSOR_ID}\nFranca/BR, era B (16 May - 30 Sep 2026)", fontsize=9.6, pad=10)
    cbar = fig.colorbar(hb, ax=ax, shrink=0.78, pad=0.015)
    cbar.set_label(COLORBAR_LABEL, fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    e = metrics["fase_e_era_b_full"]
    box = (
        f"Period: 2026-05-16 21:35Z to 2026-09-30 (137 days)\n"
        f"Valid ADS-B positions: {e['n_positions']:,} from {e['n_trace_files']:,} trace files\n"
        f"Unique aircraft (ICAO24): {e['n_unique_aircraft']:,}\n"
        f"Range: median {e['median_range_km']:.1f} km · p95 {e['p95_range_km']:.1f} km · max ~{e['max_range_km_excluding_tropo_duct_events']:.0f} km (excl. tropo-duct)\n"
        "Source: ADS-B only; local receiver logs, not network-wide coverage"
    )
    ax.text(0.012, 0.012, box, transform=ax.transAxes, fontsize=7.4, va="bottom", ha="left",
            bbox={"boxstyle": "round,pad=0.32", "facecolor": "white", "edgecolor": "#bbbbbb", "alpha": 0.94}, zorder=8)
    fig.tight_layout(rect=(0.0, 0.0, 0.96, 1.0))
    fig.savefig(OUT_FIG / "coverage_era_b_2026-05-16_to_2026-09-30.png", dpi=260, facecolor="white")
    fig.savefig(OUT_FIG / "coverage_era_b_2026-05-16_to_2026-09-30.pdf", facecolor="white")
    plt.close(fig)


def fig2_comparison(d_a, d_b):
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.0), dpi=220)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(top=0.86, bottom=0.11, left=0.055, right=0.90, wspace=0.18)
    lat_all = np.concatenate([d_a["lat"], d_b["lat"]])
    lon_all = np.concatenate([d_a["lon"], d_b["lon"]])
    lat_all_ext = np.append(lat_all, RECV_LAT)
    lon_all_ext = np.append(lon_all, RECV_LON)
    ymin, ymax = float(lat_all_ext.min()), float(lat_all_ext.max())
    xmin, xmax = float(lon_all_ext.min()), float(lon_all_ext.max())
    lat_pad = max(0.25, (ymax - ymin) * 0.05)
    lon_pad = max(0.25, (xmax - xmin) * 0.05)
    xlim = (xmin - lon_pad, xmax + lon_pad)
    ylim = (ymin - lat_pad, ymax + lat_pad)

    counts_a, _, _ = np.histogram2d(d_a["lon"], d_a["lat"], bins=100)
    counts_b, _, _ = np.histogram2d(d_b["lon"], d_b["lat"], bins=100)
    vmax = max(counts_a.max(), counts_b.max())

    for ax, d, title in ((axes[0], d_a, "Era A (13 Apr - 14 May 2026, 32 d)"), (axes[1], d_b, "Era B (16 May - 30 Sep 2026, 137 d)")):
        hb = ax.hexbin(d["lon"], d["lat"], gridsize=GRIDSIZE, mincnt=1, bins="log",
                       cmap="cividis", linewidths=0, alpha=0.95, zorder=2, vmax=vmax)
        ax.set_xlim(xlim); ax.set_ylim(ylim)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.grid(True, color="#dddddd", linewidth=0.45, alpha=0.75)
        ax.set_facecolor("#fbfbf7")
        for dist in (100, 250, 500):
            ring = [destination_point(RECV_LAT, RECV_LON, dist, b) for b in range(0, 361, 3)]
            ax.plot([p[1] for p in ring], [p[0] for p in ring], color="#262626", linewidth=0.9, alpha=0.58, zorder=5)
        ax.scatter([RECV_LON], [RECV_LAT], s=70, marker="*", color="#8f1d18", edgecolor="white", linewidth=0.8, zorder=6)
        cx0, cx1 = ax.get_xlim(); cy0, cy1 = ax.get_ylim()
        for code, lat, lon in AIRPORTS:
            if cx0 <= lon <= cx1 and cy0 <= lat <= cy1:
                ax.scatter([lon], [lat], marker="+", s=28, color="#202020", linewidth=0.7, zorder=7)
                dx, dy = AIRPORT_OFFSETS.get(code, (0.05, 0.05))
                ax.text(lon + dx, lat + dy, code, fontsize=6.8, color="#202020", zorder=7)
        ax.set_title(title, fontsize=9.6, pad=8)

    cbar = fig.colorbar(hb, ax=axes, shrink=0.78, pad=0.015)
    cbar.set_label(COLORBAR_LABEL, fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    fig.suptitle(f"ADS-B coverage comparison, sensor {SENSOR_ID}, Franca/BR — antenna swap 2026-05-16", fontsize=10.5, y=0.97)
    fig.savefig(OUT_FIG / "coverage_comparison_era_a_vs_era_b.png", dpi=260, facecolor="white")
    fig.savefig(OUT_FIG / "coverage_comparison_era_a_vs_era_b.pdf", facecolor="white")
    plt.close(fig)


def fig3_azimuth(metrics):
    az = metrics["fase_g_azimuth"]
    bins = np.array(az["bins_deg"][:-1])
    theta = np.radians(bins + 5)
    pct_a = np.array(az["era_a_pct"])
    pct_b = np.array(az["era_b_pct"])
    fig = plt.figure(figsize=(7.0, 7.0), dpi=220)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    width = np.radians(9)
    ax.bar(theta, pct_a, width=width, bottom=0, color="#8f1d18", alpha=0.55, label="Era A (32 d)", edgecolor="none")
    ax.bar(theta, pct_b, width=width, bottom=0, color="#1d5c8f", alpha=0.45, label="Era B (137 d)", edgecolor="none")
    ax.set_title("Azimuthal distribution of ADS-B positions (normalized, % of era total)", fontsize=9.6, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "azimuth_distribution_era_a_vs_era_b.png", dpi=260, facecolor="white")
    fig.savefig(OUT_FIG / "azimuth_distribution_era_a_vs_era_b.pdf", facecolor="white")
    plt.close(fig)


def fig4_altitude(metrics):
    alt = metrics["fase_g_altitude"]
    bins = np.array(alt["bins_ft"][:-1])
    counts_a = np.array(alt["era_a_counts"], dtype=float)
    counts_b = np.array(alt["era_b_counts"], dtype=float)
    pct_a = counts_a / counts_a.sum() * 100
    pct_b = counts_b / counts_b.sum() * 100
    fig, ax = plt.subplots(figsize=(9.0, 5.4), dpi=220)
    fig.patch.set_facecolor("white")
    x = np.arange(len(bins))
    w = 0.38
    ax.bar(x - w / 2, pct_a, width=w, color="#8f1d18", alpha=0.75, label="Era A (32 d)")
    ax.bar(x + w / 2, pct_b, width=w, color="#1d5c8f", alpha=0.75, label="Era B (137 d)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b // 1000}-{(b + 5000) // 1000}k" for b in bins], rotation=45, ha="right", fontsize=7.5)
    ax.set_xlabel("Altitude band (ft)")
    ax.set_ylabel("% of era's valid ADS-B positions")
    ax.set_title("ADS-B position coverage by altitude band, era A vs era B (normalized)", fontsize=9.8)
    ax.grid(True, axis="y", color="#dddddd", linewidth=0.5, alpha=0.8)
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "altitude_coverage_era_a_vs_era_b.png", dpi=260, facecolor="white")
    fig.savefig(OUT_FIG / "altitude_coverage_era_a_vs_era_b.pdf", facecolor="white")
    plt.close(fig)


def main():
    d_a = np.load(OUT_DATA / "positions_era_a.npz")
    d_b = np.load(OUT_DATA / "positions_era_b.npz")
    metrics = json.loads((ROOT / "relatorios" / "figure_metrics_era_b.json").read_text())
    fig1_hexbin_era_b(d_b, metrics)
    print("fig1 done")
    fig2_comparison(d_a, d_b)
    print("fig2 done")
    fig3_azimuth(metrics)
    print("fig3 done")
    fig4_altitude(metrics)
    print("fig4 done")


if __name__ == "__main__":
    main()
