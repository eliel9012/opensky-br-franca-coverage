#!/usr/bin/env python3
"""Era A fixed-window ADS-B coverage figure + report.

Fixed window: 2026-04-13T00:00:00Z .. 2026-05-14T23:59:59Z (inclusive).
Read-only over input trace_full files. Per-point absolute-timestamp filter so
NO data after 2026-05-14T23:59:59Z is included. Methodology matches the existing
v3 figure (ADS-B only, MLAT excluded, haversine R=6371.0088, gridsize 80, log).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import platform
import socket
import sys
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INPUT_DIR = Path("/opt/adsb/ultrafeeder/globe_history")
OUT_DIR = Path("/home/pi/coverage_era_a_rebuild")
ADSB_SOURCE_TYPES = {"adsb_icao", "adsb_icao_nt"}

# --- Fixed window (UTC) ---
WIN_START = datetime(2026, 4, 13, 0, 0, 0, tzinfo=UTC)
WIN_END_INCL = datetime(2026, 5, 14, 23, 59, 59, tzinfo=UTC)
WIN_END_EXCL = datetime(2026, 5, 15, 0, 0, 0, tzinfo=UTC)  # half-open upper bound
TS_START = WIN_START.timestamp()
TS_END_EXCL = WIN_END_EXCL.timestamp()

RECV_LAT = -20.51
RECV_LON = -47.40
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
    "FRC": (0.06, -0.16),
    "RAO": (0.06, -0.12),
    "VCP": (0.07, 0.08),
    "GRU": (0.07, -0.11),
    "CGH": (-0.42, -0.08),
    "CNF": (0.07, 0.08),
}
COLORBAR_LABEL = "ADS-B position reports per ~10 km hex cell (log scale)"


def is_gzip(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


def load_json(path: Path):
    if path.suffix == ".gz" or is_gzip(path):
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            return json.load(f)
    with path.open("rt", encoding="utf-8", errors="ignore") as f:
        return json.load(f)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def destination_point(lat, lon, dist_km, bearing_deg):
    r = 6371.0088
    b = math.radians(bearing_deg)
    p1 = math.radians(lat)
    l1 = math.radians(lon)
    d = dist_km / r
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1),
                         math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def percentile(values, pct):
    if not values:
        return None
    o = sorted(values)
    if len(o) == 1:
        return o[0]
    idx = (len(o) - 1) * pct / 100
    lo, hi = math.floor(idx), math.ceil(idx)
    if lo == hi:
        return o[int(idx)]
    return o[lo] + (o[hi] - o[lo]) * (idx - lo)


def window_dirs():
    """Date dirs YYYY/MM/DD from Apr 13 to May 14 inclusive."""
    dirs = []
    d = date(2026, 4, 13)
    last = date(2026, 5, 14)
    while d <= last:
        p = INPUT_DIR / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}" / "traces"
        if p.is_dir():
            dirs.append(p)
        d += timedelta(days=1)
    return dirs


def collect_files():
    files = []
    for tdir in window_dirs():
        files.extend(sorted(tdir.rglob("trace_full_*.json")))
    return files


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files = collect_files()
    if not files:
        raise SystemExit("No trace_full files found in window dirs")

    lats, lons, ranges, times = [], [], [], []
    unique_aircraft = set()
    src_all = Counter()
    src_kept = Counter()
    files_processed = 0
    files_with_pos = 0
    files_failed = 0
    total_rows = 0
    invalid_rows = 0
    rows_no_source = 0
    rows_outside_window = 0

    for path in files:
        files_processed += 1
        try:
            data = load_json(path)
        except Exception:
            files_failed += 1
            continue
        if not isinstance(data, dict):
            files_failed += 1
            continue
        icao = data.get("icao")
        base_ts = data.get("timestamp")
        trace = data.get("trace")
        if not isinstance(trace, list):
            files_failed += 1
            continue
        before = len(lats)
        for row in trace:
            total_rows += 1
            if not isinstance(row, list) or len(row) < 10:
                invalid_rows += 1
                continue
            # absolute timestamp of this point
            if not (isinstance(row[0], (int, float)) and isinstance(base_ts, (int, float))):
                invalid_rows += 1
                continue
            ts = float(base_ts) + float(row[0])
            # HARD fixed-window filter (half-open): start <= ts < end_excl
            if ts < TS_START or ts >= TS_END_EXCL:
                rows_outside_window += 1
                continue
            source = row[9] if isinstance(row[9], str) else None
            if source:
                src_all[source] += 1
            else:
                rows_no_source += 1
            if source not in ADSB_SOURCE_TYPES:
                continue
            lat, lon = row[1], row[2]
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                invalid_rows += 1
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                invalid_rows += 1
                continue
            if isinstance(icao, str) and icao:
                unique_aircraft.add(icao)
            lats.append(float(lat))
            lons.append(float(lon))
            times.append(ts)
            ranges.append(haversine_km(RECV_LAT, RECV_LON, float(lat), float(lon)))
            src_kept[source] += 1
        if len(lats) > before:
            files_with_pos += 1

    lat_arr = np.asarray(lats, dtype=float)
    lon_arr = np.asarray(lons, dtype=float)
    n_pos = int(lat_arr.size)
    if n_pos == 0:
        raise SystemExit("No valid ADS-B positions in window")

    med = round(median(ranges), 1)
    p95 = round(percentile(ranges, 95), 1)
    rmax = round(max(ranges), 1)

    obs_start = min(times)
    obs_end = max(times)
    cal_days = (date(2026, 5, 14) - date(2026, 4, 13)).days + 1  # inclusive = 32

    # --- gap detection: hourly buckets with zero kept positions ---
    hour_buckets = set(int(t // 3600) for t in times)
    first_hour = int(TS_START // 3600)
    last_hour = int((TS_END_EXCL - 1) // 3600)
    missing_hours = [h for h in range(first_hour, last_hour + 1) if h not in hour_buckets]
    # group consecutive missing hours into intervals
    gaps = []
    if missing_hours:
        run_start = prev = missing_hours[0]
        for h in missing_hours[1:]:
            if h == prev + 1:
                prev = h
            else:
                gaps.append((run_start, prev))
                run_start = prev = h
        gaps.append((run_start, prev))
    gap_records = []
    for gs, ge in gaps:
        start_dt = datetime.fromtimestamp(gs * 3600, UTC)
        end_dt = datetime.fromtimestamp((ge + 1) * 3600, UTC)
        dur_h = (ge - gs) + 1
        gap_records.append({
            "start_utc": start_dt.isoformat(timespec="seconds"),
            "end_utc": end_dt.isoformat(timespec="seconds"),
            "duration_hours": dur_h,
        })

    size_bytes = sum(p.stat().st_size for p in files)

    metrics = {
        "window_start_utc": WIN_START.isoformat(timespec="seconds"),
        "window_end_utc": WIN_END_INCL.isoformat(timespec="seconds"),
        "window_filter": "half-open [start, end_excl) with end_excl=2026-05-15T00:00:00Z",
        "calendar_days_inclusive": cal_days,
        "observed_first_point_utc": datetime.fromtimestamp(obs_start, UTC).isoformat(timespec="seconds"),
        "observed_last_point_utc": datetime.fromtimestamp(obs_end, UTC).isoformat(timespec="seconds"),
        "n_files_processed": files_processed,
        "n_files_with_adsb_positions": files_with_pos,
        "n_files_failed": files_failed,
        "n_trace_rows_seen": total_rows,
        "n_rows_outside_window": rows_outside_window,
        "n_rows_invalid_or_skipped": invalid_rows,
        "n_rows_without_source": rows_no_source,
        "n_positions_adsb_valid": n_pos,
        "n_unique_aircraft_adsb": len(unique_aircraft),
        "source_type_counts_all_rows": dict(src_all.most_common()),
        "source_type_counts_kept": dict(src_kept.most_common()),
        "median_range_km": med,
        "p95_range_km": p95,
        "max_range_km": rmax,
        "trace_files_total_size_bytes": size_bytes,
        "receiver_lat": RECV_LAT,
        "receiver_lon": RECV_LON,
        "gridsize": GRIDSIZE,
        "gaps_zero_position_hours": gap_records,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
    }
    (OUT_DIR / "figure_metrics_era_a.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ---------------- figure ----------------
    fig, ax = plt.subplots(figsize=(7.1, 7.2), dpi=220)
    fig.patch.set_facecolor("white")

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
                   cmap="cividis", linewidths=0, alpha=0.95, zorder=2)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, color="#dddddd", linewidth=0.45, alpha=0.75)
    ax.set_facecolor("#fbfbf7")

    # range rings (match existing v3 figure: 100, 250, 500 km)
    for dist in (100, 250, 500):
        ring = [destination_point(RECV_LAT, RECV_LON, dist, b) for b in range(0, 361, 3)]
        ax.plot([p[1] for p in ring], [p[0] for p in ring],
                color="#262626", linewidth=0.9, alpha=0.58, zorder=5)

    # RX red star
    ax.scatter([RECV_LON], [RECV_LAT], s=70, marker="*", color="#8f1d18",
               edgecolor="white", linewidth=0.8, zorder=6)

    # airports
    cx0, cx1 = ax.get_xlim()
    cy0, cy1 = ax.get_ylim()
    for code, lat, lon in AIRPORTS:
        if cx0 <= lon <= cx1 and cy0 <= lat <= cy1:
            ax.scatter([lon], [lat], marker="+", s=28, color="#202020", linewidth=0.7, zorder=7)
            dx, dy = AIRPORT_OFFSETS.get(code, (0.05, 0.05))
            ax.text(lon + dx, lat + dy, code, fontsize=6.8, color="#202020", zorder=7)

    ax.set_title(f"Local ADS-B coverage, sensor {SENSOR_ID}\nFranca/BR (13 Apr - 14 May 2026)",
                 fontsize=9.6, pad=10)

    cbar = fig.colorbar(hb, ax=ax, shrink=0.78, pad=0.015)
    cbar.set_label(COLORBAR_LABEL, fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    box = (
        f"Period: 2026-04-13 to 2026-05-14 ({cal_days} days)\n"
        f"Valid ADS-B positions: {n_pos:,} from {files_processed:,} trace files\n"
        f"Unique aircraft (ICAO24): {len(unique_aircraft):,}\n"
        f"Range: median {med:.1f} km · p95 {p95:.1f} km · max ~{rmax:.0f} km\n"
        "Source: ADS-B only; local receiver logs, not network-wide coverage"
    )
    ax.text(0.012, 0.012, box, transform=ax.transAxes, fontsize=7.4,
            va="bottom", ha="left",
            bbox={"boxstyle": "round,pad=0.32", "facecolor": "white",
                  "edgecolor": "#bbbbbb", "alpha": 0.94}, zorder=8)

    fig.tight_layout(rect=(0.0, 0.0, 0.96, 1.0))
    fig.savefig(OUT_DIR / "coverage_era_a_2026-04-13_to_2026-05-14.png",
                dpi=260, facecolor="white")
    fig.savefig(OUT_DIR / "coverage_era_a_2026-04-13_to_2026-05-14.pdf",
                facecolor="white")
    plt.close(fig)

    print(json.dumps({k: metrics[k] for k in (
        "window_start_utc", "window_end_utc", "calendar_days_inclusive",
        "observed_first_point_utc", "observed_last_point_utc",
        "n_files_processed", "n_files_with_adsb_positions",
        "n_positions_adsb_valid", "n_unique_aircraft_adsb",
        "median_range_km", "p95_range_km", "max_range_km",
        "n_rows_outside_window", "trace_files_total_size_bytes",
    )}, indent=2))
    print("GAPS (zero-position hours):", len(gap_records))
    for g in gap_records:
        print("  ", g["start_utc"], "->", g["end_utc"], f"({g['duration_hours']}h)")


if __name__ == "__main__":
    main()
