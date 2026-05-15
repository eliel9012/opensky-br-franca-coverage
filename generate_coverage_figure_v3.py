#!/usr/bin/env python3
"""Generate the v3 ADS-B-only local coverage figure from tar1090/readsb traces.

The script is read-only for input data. It writes only into the selected output
directory.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import random
import shlex
import socket
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DEFAULT_INPUT = "/opt/adsb/ultrafeeder/globe_history"
DEFAULT_OUTPUT = "/home/pi/opensky_coverage_figure_v3"
ADSB_SOURCE_TYPES = {"adsb_icao", "adsb_icao_nt"}
RNG_SEED = 20260514

AIRPORTS = [
    ("FRC", -20.592, -47.383),
    ("RAO", -21.136, -47.776),
    ("VCP", -23.007, -47.134),
    ("GRU", -23.435, -46.473),
    ("CGH", -23.627, -46.656),
    ("CNF", -19.624, -43.971),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ADS-B-only local coverage figures from tar1090/readsb trace_full files."
    )
    parser.add_argument("--input-dir", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    parser.add_argument("--receiver-lat", type=float, default=None)
    parser.add_argument("--receiver-lon", type=float, default=None)
    parser.add_argument("--sample-step", type=int, default=1, help="Process every Nth trace file.")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum number of trace files to process.")
    parser.add_argument("--hexbin-gridsize", type=int, default=80)
    parser.add_argument("--sensor-id", default="-1408044782")
    parser.add_argument("--author", default="Eliel Felipe Junior")
    parser.add_argument("--readsb-version", default="not verified")
    parser.add_argument("--ultrafeeder-image", default="not verified")
    parser.add_argument("--previous-metrics", default="/home/pi/opensky_coverage_figure_v2/figure_metrics_v2.json")
    return parser.parse_args()


def is_gzip(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


def load_json(path: Path) -> Any:
    if path.suffix == ".gz" or is_gzip(path):
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            return json.load(f)
    with path.open("rt", encoding="utf-8", errors="ignore") as f:
        return json.load(f)


def iso_from_ts(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def date_label(value: str | None) -> str:
    dt = parse_iso(value)
    return dt.date().isoformat() if dt else "unknown"


def human_date(value: str | None) -> str:
    dt = parse_iso(value)
    return dt.strftime("%-d %b %Y") if dt else "unknown"


def period_days(start: str | None, end: str | None) -> int | None:
    a = parse_iso(start)
    b = parse_iso(end)
    if not a or not b:
        return None
    return max(1, round((b - a).total_seconds() / 86400))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


def destination_point(lat: float, lon: float, distance_km: float, bearing_deg: float) -> tuple[float, float]:
    radius_km = 6371.0088
    bearing = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    delta = distance_km / radius_km
    phi2 = math.asin(math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(bearing))
    lambda2 = lambda1 + math.atan2(
        math.sin(bearing) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), math.degrees(lambda2)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = (len(ordered) - 1) * pct / 100
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[int(idx)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def collect_trace_files(input_dir: Path, sample_step: int, max_files: int | None) -> tuple[list[Path], list[Path]]:
    all_files = sorted(input_dir.rglob("trace_full_*.json"))
    sampled = all_files[:: max(sample_step, 1)]
    if max_files is not None:
        sampled = sampled[:max_files]
    return all_files, sampled


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_points(
    files: list[Path],
    receiver_lat: float | None,
    receiver_lon: float | None,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    lats: list[float] = []
    lons: list[float] = []
    times: list[float] = []
    ranges: list[float] = []
    unique_aircraft: set[str] = set()
    source_types_all: Counter[str] = Counter()
    source_types_kept: Counter[str] = Counter()
    files_with_positions = 0
    files_failed = 0
    invalid_rows = 0
    total_rows = 0
    rows_without_source = 0

    for path in files:
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
            source = row[9] if isinstance(row[9], str) else None
            if source:
                source_types_all[source] += 1
            else:
                rows_without_source += 1
            if source not in ADSB_SOURCE_TYPES:
                continue
            lat = row[1]
            lon = row[2]
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
            source_types_kept[source] += 1
            if isinstance(row[0], (int, float)) and isinstance(base_ts, (int, float)):
                times.append(float(base_ts) + float(row[0]))
            if receiver_lat is not None and receiver_lon is not None:
                ranges.append(haversine_km(receiver_lat, receiver_lon, float(lat), float(lon)))
        if len(lats) > before:
            files_with_positions += 1

    lat_arr = np.asarray(lats, dtype=float)
    lon_arr = np.asarray(lons, dtype=float)
    metrics: dict[str, Any] = {
        "source_filter": sorted(ADSB_SOURCE_TYPES),
        "n_files_processed": len(files),
        "n_files_with_adsb_positions": files_with_positions,
        "n_files_failed": files_failed,
        "n_trace_rows_seen": total_rows,
        "n_positions_all_sources_seen": total_rows - invalid_rows,
        "n_positions_adsb_valid": int(lat_arr.size),
        "n_positions_filtered_out_non_adsb": int(max(0, total_rows - invalid_rows - lat_arr.size)),
        "n_rows_invalid_or_skipped": invalid_rows,
        "n_rows_without_source": rows_without_source,
        "n_unique_aircraft_adsb": len(unique_aircraft),
        "period_start": iso_from_ts(min(times)) if times else None,
        "period_end": iso_from_ts(max(times)) if times else None,
        "source_type_counts_all_rows": dict(source_types_all.most_common()),
        "source_type_counts_kept": dict(source_types_kept.most_common()),
    }
    if ranges:
        metrics.update(
            {
                "max_range_km": round(max(ranges), 1),
                "p95_range_km": round(percentile(ranges, 95) or 0, 1),
                "median_range_km": round(median(ranges), 1),
            }
        )
    else:
        metrics.update({"max_range_km": None, "p95_range_km": None, "median_range_km": None})
    return metrics, lat_arr, lon_arr


def apply_axes_style(ax: plt.Axes, receiver_lat: float | None, receiver_lon: float | None) -> None:
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, color="#dddddd", linewidth=0.45, alpha=0.75)
    ax.set_facecolor("#fbfbf7")
    if receiver_lat is not None and receiver_lon is not None:
        for dist in (100, 250, 500):
            ring = [destination_point(receiver_lat, receiver_lon, dist, b) for b in range(0, 361, 3)]
            ax.plot(
                [p[1] for p in ring],
                [p[0] for p in ring],
                color="#262626",
                linewidth=0.9,
                alpha=0.58,
                zorder=5,
            )
        ax.scatter(
            [receiver_lon],
            [receiver_lat],
            s=70,
            marker="*",
            color="#8f1d18",
            edgecolor="white",
            linewidth=0.8,
            zorder=6,
        )


def add_airports(ax: plt.Axes) -> None:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    offsets = {
        "FRC": (0.06, -0.16),
        "RAO": (0.06, -0.12),
        "VCP": (0.07, 0.08),
        "GRU": (0.07, -0.11),
        "CGH": (-0.42, -0.08),
        "CNF": (0.07, 0.08),
    }
    for code, lat, lon in AIRPORTS:
        if xmin <= lon <= xmax and ymin <= lat <= ymax:
            ax.scatter([lon], [lat], marker="+", s=28, color="#202020", linewidth=0.7, zorder=7)
            dx, dy = offsets.get(code, (0.05, 0.05))
            ax.text(lon + dx, lat + dy, code, fontsize=6.8, color="#202020", zorder=7)


def format_metrics_box(metrics: dict[str, Any]) -> str:
    days = period_days(metrics.get("period_start"), metrics.get("period_end"))
    day_text = f" ({days} days)" if days else ""
    return (
        f"Period: {date_label(metrics.get('period_start'))} to {date_label(metrics.get('period_end'))}{day_text}\n"
        f"Valid ADS-B positions: {metrics['n_positions_adsb_valid']:,} from {metrics['n_files_processed']:,} trace files\n"
        f"Unique aircraft (ICAO24): {metrics['n_unique_aircraft_adsb']:,}\n"
        f"Range: median {metrics['median_range_km']:.1f} km · p95 {metrics['p95_range_km']:.1f} km · max ~{metrics['max_range_km']:.0f} km\n"
        "Source: ADS-B only; local receiver logs, not network-wide coverage"
    )


def title_text(metrics: dict[str, Any], sensor_id: str) -> str:
    start = parse_iso(metrics.get("period_start"))
    end = parse_iso(metrics.get("period_end"))
    if start and end:
        period = f"{start.strftime('%-d %b')} - {end.strftime('%-d %b %Y')}"
    else:
        period = "period unknown"
    return f"Local ADS-B coverage, sensor {sensor_id}\nFranca/BR ({period})"


def set_extent(ax: plt.Axes, lats: np.ndarray, lons: np.ndarray, receiver_lat: float | None, receiver_lon: float | None) -> None:
    lat_values = lats
    lon_values = lons
    if receiver_lat is not None and receiver_lon is not None:
        lat_values = np.append(lat_values, receiver_lat)
        lon_values = np.append(lon_values, receiver_lon)
    ymin, ymax = float(np.min(lat_values)), float(np.max(lat_values))
    xmin, xmax = float(np.min(lon_values)), float(np.max(lon_values))
    lat_pad = max(0.25, (ymax - ymin) * 0.05)
    lon_pad = max(0.25, (xmax - xmin) * 0.05)
    ax.set_ylim(ymin - lat_pad, ymax + lat_pad)
    ax.set_xlim(xmin - lon_pad, xmax + lon_pad)
    ax.set_aspect("equal", adjustable="box")


def estimated_hex_cell_label(ax: plt.Axes, gridsize: int) -> str:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    mid_lat = (ymin + ymax) / 2
    lon_km = 111.32 * math.cos(math.radians(mid_lat))
    lat_km = 111.32
    width_km = abs(xmax - xmin) * lon_km / max(gridsize, 1)
    height_km = abs(ymax - ymin) * lat_km / max(gridsize, 1)
    approx_km = int(round((width_km + height_km) / 2 / 5) * 5)
    if 5 <= approx_km <= 30:
        return f"ADS-B position reports per ~{approx_km} km hex cell (log scale)"
    return "ADS-B position reports per hexagonal cell (log scale)"


def save_hexbin(
    out_png: Path,
    out_pdf: Path,
    lats: np.ndarray,
    lons: np.ndarray,
    metrics: dict[str, Any],
    receiver_lat: float | None,
    receiver_lon: float | None,
    sensor_id: str,
    gridsize: int,
) -> None:
    fig, ax = plt.subplots(figsize=(7.1, 7.2), dpi=220)
    set_extent(ax, lats, lons, receiver_lat, receiver_lon)
    hb = ax.hexbin(
        lons,
        lats,
        gridsize=gridsize,
        mincnt=1,
        bins="log",
        cmap="cividis",
        linewidths=0,
        alpha=0.95,
        zorder=2,
    )
    apply_axes_style(ax, receiver_lat, receiver_lon)
    add_airports(ax)
    ax.set_title(title_text(metrics, sensor_id), fontsize=9.6, pad=10)
    cbar = fig.colorbar(hb, ax=ax, shrink=0.78, pad=0.015)
    cbar_label = estimated_hex_cell_label(ax, gridsize)
    cbar.set_label(cbar_label, fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    metrics["hexbin_colorbar_label"] = cbar_label
    ax.text(
        0.012,
        0.012,
        format_metrics_box(metrics),
        transform=ax.transAxes,
        fontsize=7.4,
        va="bottom",
        ha="left",
        bbox={"boxstyle": "round,pad=0.32", "facecolor": "white", "edgecolor": "#bbbbbb", "alpha": 0.94},
        zorder=8,
    )
    fig.tight_layout(rect=(0.0, 0.0, 0.96, 1.0))
    fig.savefig(out_png, dpi=260)
    fig.savefig(out_pdf)
    plt.close(fig)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_previous_metrics(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_caption(path: Path, metrics: dict[str, Any]) -> None:
    days = period_days(metrics.get("period_start"), metrics.get("period_end"))
    caption = (
        f"Figure 1. Local ADS-B coverage of sensor -1408044782 in Franca, Sao Paulo State, Brazil, "
        f"covering a {days}-day observation window from {human_date(metrics.get('period_start'))} to "
        f"{human_date(metrics.get('period_end'))}. The figure uses logarithmic hexagonal binning of "
        f"{metrics['n_positions_adsb_valid']:,} valid ADS-B position reports from "
        f"{metrics['n_unique_aircraft_adsb']:,} unique aircraft, derived from "
        f"{metrics['n_files_processed']:,} local trace_full files from the tar1090/readsb ultrafeeder stack. "
        "MLAT-derived positions were excluded. "
        f"Observed reception range was {metrics['median_range_km']:.0f} km median, "
        f"{metrics['p95_range_km']:.0f} km p95, and {metrics['max_range_km']:.0f} km maximum. "
        "Receiver coordinates are rounded to two decimal places for privacy. This is an operational indicator "
        "from local receiver logs, not a network-wide OpenSky coverage claim.\n"
    )
    path.write_text(caption, encoding="utf-8")


def write_methods(path: Path, metrics: dict[str, Any], args: argparse.Namespace, command: str, script_hash: str) -> None:
    previous = metrics.get("previous_version_comparison", {})
    text = f"""# Coverage Figure v3 Methods

## Execution
- Execution time: {datetime.now(UTC).isoformat(timespec="seconds")}
- Host: {socket.gethostname()}
- Platform: {platform.platform()}
- Python: {sys.version.split()[0]}
- matplotlib: {matplotlib.__version__}
- numpy: {np.__version__}
- Script SHA256: `{script_hash}`
- Command: `{command}`

## Input Data
- Input directory: `{args.input_dir}`
- File pattern: `trace_full_*.json`
- Note: files have `.json` extension but are gzip-compressed tar1090/readsb traces.
- Trace files available: {metrics['n_files_total']:,}
- Trace files processed: {metrics['n_files_processed']:,}
- Trace files with ADS-B positions: {metrics['n_files_with_adsb_positions']:,}
- Processing sample step: {args.sample_step}
- Maximum files option: {args.max_files}
- Total trace rows inspected: {metrics['n_trace_rows_seen']:,}

## ADS-B Filter
- Kept source types: {', '.join(metrics['source_filter'])}
- Source field equivalence: the tar1090 trace row uses `row[9]` as the source type. Rows with `row[9] == "adsb_icao"` or `row[9] == "adsb_icao_nt"` were treated as ADS-B positions.
- Source counts before filtering: `{json.dumps(metrics['source_type_counts_all_rows'], sort_keys=True)}`
- Source counts kept: `{json.dumps(metrics['source_type_counts_kept'], sort_keys=True)}`
- Valid ADS-B positions after filtering: {metrics['n_positions_adsb_valid']:,}
- Non-ADS-B positions filtered out: {metrics['n_positions_filtered_out_non_adsb']:,}
- Unique aircraft after filtering: {metrics['n_unique_aircraft_adsb']:,}

## Observation Window
- Coverage figure period: {metrics['period_start']} to {metrics['period_end']}
- Observation-window duration: approximately {period_days(metrics.get('period_start'), metrics.get('period_end'))} days.
- Historical local stack inventory: earlier inventory found a broader local history of about 139 calendar days in the stack. This v3 figure uses only the `trace_full` coverage files available for the map window and does not claim 139 days of plotted coverage.

## Distance Metrics
- Receiver coordinates used for distance and plotting: rounded to two decimal places, `{metrics['receiver_lat_used_for_distance']}`, `{metrics['receiver_lon_used_for_distance']}`.
- Privacy note: Distance metrics were computed using receiver coordinates rounded to two decimal places for privacy; the resulting systematic error is within approximately +/-1 km and does not affect km-level metrics reported here.
- Median range: {metrics['median_range_km']} km
- P95 range: {metrics['p95_range_km']} km
- Maximum observed range: {metrics['max_range_km']} km

## Figure Rendering
- Recommended abstract figure: `coverage_map_v3_hexbin.pdf` or `coverage_map_v3_hexbin.png`.
- Hexbin rendering: logarithmic hexagonal binning, gridsize {args.hexbin_gridsize}, metrics computed over all valid ADS-B positions.
- Colorbar label: {metrics.get('hexbin_colorbar_label', 'not recorded')}.
- Range rings: 100, 250, and 500 km are plotted above the hexbin layer with neutral translucent lines.
- Airport reference markers: FRC, RAO, VCP, GRU, CGH, and CNF are plotted only if they fall within the map extent.
- No basemap or public receiver-precision coordinate is included. The receiver is shown only by a star marker; the previous explicit receiver text label was removed for legibility.

## Stack Version Evidence
- readsb version: {args.readsb_version}
- ultrafeeder image: {args.ultrafeeder_image}
- tar1090 CLI version: not verified; `tar1090 --version` was not available in the ultrafeeder container PATH during inspection.

## v2 to v3 Difference
- v2 valid ADS-B positions: {previous.get('v2_positions_adsb_valid', 'not available')}
- v2 unique aircraft: {previous.get('v2_unique_aircraft_adsb', 'not available')}
- v2 range metrics: median {previous.get('v2_median_range_km', 'not available')} km, p95 {previous.get('v2_p95_range_km', 'not available')} km, max {previous.get('v2_max_range_km', 'not available')} km.
- v3 valid ADS-B positions: {metrics['n_positions_adsb_valid']:,}
- Main visual changes: v3 keeps ADS-B-only filtering, uses the hexbin version only, draws range rings above the hexbin layer, removes the red receiver text label, and uses a clearer colorbar label.

## Limitations
- This is an operational indicator based on local receiver logs, not a final OpenSky network-wide coverage analysis.
- The map shows received positions, not guaranteed coverage over every point in the region.
- Aircraft density is affected by traffic patterns, altitude, terrain, antenna installation, receiver configuration, and data-retention behavior.
- The figure should not be used to claim comprehensive coverage of southeastern Brazil.

## Recommendation for the abstract
- Use in abstract: yes, use the v3 hexbin version.
- Reason: the v3 figure is ADS-B-only, traceable to local logs, legible at abstract size, and includes the most defensible metrics for a short field-report abstract.
- Suggested caption: see `coverage_map_caption_v3.txt`.
"""
    path.write_text(text, encoding="utf-8")


def write_readme(path: Path, metrics: dict[str, Any], command: str) -> None:
    text = f"""# OpenSky Coverage Figure v3

This directory contains the final ADS-B-only local coverage hexbin figure for the OpenSky Symposium abstract.

## Recommended File

Use `coverage_map_v3_hexbin.pdf` for LaTeX if accepted by the template. Use `coverage_map_v3_hexbin.png` otherwise.

## Reproduce

```bash
{command}
```

## Main Metrics

- Observation window: {date_label(metrics.get('period_start'))} to {date_label(metrics.get('period_end'))}, approximately {period_days(metrics.get('period_start'), metrics.get('period_end'))} days
- Trace files processed: {metrics['n_files_processed']:,}
- Valid ADS-B positions: {metrics['n_positions_adsb_valid']:,}
- Unique aircraft: {metrics['n_unique_aircraft_adsb']:,}
- Median range: {metrics['median_range_km']} km
- P95 range: {metrics['p95_range_km']} km
- Max observed range: {metrics['max_range_km']} km
- MLAT-derived positions excluded: {metrics['n_positions_filtered_out_non_adsb']:,}

## Files

- `coverage_map_v3_hexbin.pdf` / `.png`: recommended abstract figure.
- `figure_metrics_v3.json`: metrics and provenance.
- `coverage_map_methods_v3.md`: methods and limitations.
- `coverage_map_caption_v3.txt`: proposed caption.
- `generate_coverage_figure_v3.py`: reproducible script.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files, selected_files = collect_trace_files(input_dir, args.sample_step, args.max_files)
    if not selected_files:
        raise SystemExit(f"No trace_full_*.json files found under {input_dir}")

    receiver_lat = round(args.receiver_lat, 2) if args.receiver_lat is not None else None
    receiver_lon = round(args.receiver_lon, 2) if args.receiver_lon is not None else None
    metrics, lats, lons = extract_points(selected_files, receiver_lat, receiver_lon)
    if lats.size == 0:
        raise SystemExit("No valid ADS-B positions found after filtering.")

    save_hexbin(
        output_dir / "coverage_map_v3_hexbin.png",
        output_dir / "coverage_map_v3_hexbin.pdf",
        lats,
        lons,
        metrics,
        receiver_lat,
        receiver_lon,
        args.sensor_id,
        args.hexbin_gridsize,
    )

    script_path = Path(__file__).resolve()
    script_hash = sha256_file(script_path)
    command = " ".join(shlex.quote(arg) for arg in sys.argv)
    previous = load_previous_metrics(Path(args.previous_metrics))
    comparison = None
    if previous:
        comparison = {
            "v2_positions_adsb_valid": previous.get("n_positions_adsb_valid"),
            "v2_unique_aircraft_adsb": previous.get("n_unique_aircraft_adsb"),
            "v2_median_range_km": previous.get("median_range_km"),
            "v2_p95_range_km": previous.get("p95_range_km"),
            "v2_max_range_km": previous.get("max_range_km"),
            "v2_files_processed": previous.get("n_files_processed"),
            "v2_period_end": previous.get("period_end"),
        }
    metrics.update(
        {
            "author": args.author,
            "sensor_id": args.sensor_id,
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "n_files_total": len(all_files),
            "trace_files_total_size_bytes": sum(p.stat().st_size for p in selected_files),
            "sample_step": args.sample_step,
            "max_files": args.max_files,
            "hexbin_gridsize": args.hexbin_gridsize,
            "receiver_lat_used_for_distance": receiver_lat,
            "receiver_lon_used_for_distance": receiver_lon,
            "receiver_location_precision": "rounded/approximate",
            "python_version": sys.version.split()[0],
            "matplotlib_version": matplotlib.__version__,
            "numpy_version": np.__version__,
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "script_sha256": script_hash,
            "reproduce_command": command,
            "readsb_version": args.readsb_version,
            "ultrafeeder_image": args.ultrafeeder_image,
            "tar1090_cli_version": "not verified; tar1090 --version not available in container PATH",
            "previous_version_comparison": comparison,
        }
    )

    write_json(output_dir / "figure_metrics_v3.json", metrics)
    write_caption(output_dir / "coverage_map_caption_v3.txt", metrics)
    write_methods(output_dir / "coverage_map_methods_v3.md", metrics, args, command, script_hash)
    write_readme(output_dir / "README_figure_v3.md", metrics, command)


if __name__ == "__main__":
    main()
