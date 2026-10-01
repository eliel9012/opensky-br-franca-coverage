#!/usr/bin/env python3
"""
Build consolidated ADS-B position datasets for era A and era B.

Reads trace_full_*.json.gz files from dados/era_a and dados/era_b (copied
read-only from the Pi's globe_history / backup_era_b), extracts valid ADS-B
positions (source_type in {adsb_icao, adsb_icao_nt}; MLAT excluded), and
writes compact .npz arrays for downstream metric/figure scripts.

Era boundary: 2026-05-16T21:35:00Z (antenna swap). Day 2026-05-16 is split
position-by-position by absolute timestamp, never treated as a whole-day
block, per known pitfall #3.

Windows:
  - Era A (fixed, matches referencia/era_a_rebuild): [2026-04-13T00:00:00Z, 2026-05-15T00:00:00Z)
  - Era B (full):   [2026-05-16T21:35:00Z, 2026-10-01T00:00:00Z)   -> through 2026-09-30T23:59:59Z
  - Era B (paired): [2026-05-16T21:35:00Z, 2026-06-17T21:35:00Z)   -> first 32 days of era B

Output: scripts/out/positions_era_a.npz, scripts/out/positions_era_b.npz,
        scripts/out/icao_era_a.json, scripts/out/icao_era_b.json,
        scripts/out/scan_summary.json
"""
from __future__ import annotations

import gzip
import json
import math
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

ADSB_SOURCE_TYPES = {"adsb_icao", "adsb_icao_nt"}
RECV_LAT = -20.51
RECV_LON = -47.40
R_EARTH = 6371.0088

SWAP_TS = datetime(2026, 5, 16, 21, 35, 0, tzinfo=UTC).timestamp()

ERA_A_START = datetime(2026, 4, 13, 0, 0, 0, tzinfo=UTC).timestamp()
ERA_A_END_EXCL = datetime(2026, 5, 15, 0, 0, 0, tzinfo=UTC).timestamp()

ERA_B_START = SWAP_TS
ERA_B_END_EXCL = datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC).timestamp()


def load_json(path: Path):
    with path.open("rb") as f:
        magic = f.read(2)
    if magic == b"\x1f\x8b":
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            return json.load(f)
    with path.open("rt", encoding="utf-8", errors="ignore") as f:
        return json.load(f)


def process_dir(base_dir: Path, ts_start: float, ts_end_excl: float, label: str):
    files = sorted(base_dir.rglob("trace_full_*.json"))
    abs_time, lat, lon, alt_ft, is_ground, icao_ids = [], [], [], [], [], []
    icao_list = []
    icao_to_id = {}
    src_all = Counter()
    src_kept = Counter()
    n_files = len(files)
    n_files_with_pos = 0
    n_files_failed = 0
    total_rows = 0
    rows_outside_window = 0
    rows_invalid = 0
    rows_no_source = 0
    size_bytes = 0

    for path in files:
        size_bytes += path.stat().st_size
        try:
            data = load_json(path)
        except Exception as e:
            n_files_failed += 1
            print(f"  WARN: failed to parse {path}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, dict):
            n_files_failed += 1
            continue
        icao = data.get("icao")
        base_ts = data.get("timestamp")
        trace = data.get("trace")
        if not isinstance(trace, list) or not isinstance(base_ts, (int, float)):
            n_files_failed += 1
            continue
        icao_id = icao_to_id.get(icao)
        if icao_id is None:
            icao_id = len(icao_list)
            icao_to_id[icao] = icao_id
            icao_list.append(icao)
        before = len(abs_time)
        for row in trace:
            total_rows += 1
            if not isinstance(row, list) or len(row) < 10:
                rows_invalid += 1
                continue
            if not isinstance(row[0], (int, float)):
                rows_invalid += 1
                continue
            ts = float(base_ts) + float(row[0])
            if ts < ts_start or ts >= ts_end_excl:
                rows_outside_window += 1
                continue
            source = row[9] if isinstance(row[9], str) else None
            if source:
                src_all[source] += 1
            else:
                rows_no_source += 1
            if source not in ADSB_SOURCE_TYPES:
                continue
            la, lo = row[1], row[2]
            if not isinstance(la, (int, float)) or not isinstance(lo, (int, float)):
                rows_invalid += 1
                continue
            if not (-90 <= la <= 90 and -180 <= lo <= 180):
                rows_invalid += 1
                continue
            alt_raw = row[3]
            if alt_raw == "ground":
                alt_val, ground = 0.0, True
            elif isinstance(alt_raw, (int, float)):
                alt_val, ground = float(alt_raw), False
            else:
                alt_val, ground = float("nan"), False
            abs_time.append(ts)
            lat.append(float(la))
            lon.append(float(lo))
            alt_ft.append(alt_val)
            is_ground.append(ground)
            icao_ids.append(icao_id)
            src_kept[source] += 1
        if len(abs_time) > before:
            n_files_with_pos += 1

    abs_time = np.asarray(abs_time, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    alt_ft = np.asarray(alt_ft, dtype=np.float64)
    is_ground = np.asarray(is_ground, dtype=bool)
    icao_ids = np.asarray(icao_ids, dtype=np.int32)

    # vectorized haversine range + bearing from receiver
    p1 = math.radians(RECV_LAT)
    l1 = math.radians(RECV_LON)
    p2 = np.radians(lat)
    l2 = np.radians(lon)
    dp = p2 - p1
    dl = l2 - l1
    a = np.sin(dp / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    range_km = 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    x = np.sin(dl) * np.cos(p2)
    y = math.cos(p1) * np.sin(p2) - math.sin(p1) * np.cos(p2) * np.cos(dl)
    bearing = (np.degrees(np.arctan2(x, y))) % 360.0

    np.savez_compressed(
        OUT / f"positions_{label}.npz",
        abs_time=abs_time, lat=lat, lon=lon, alt_ft=alt_ft,
        is_ground=is_ground, icao_id=icao_ids, range_km=range_km, bearing_deg=bearing,
    )
    (OUT / f"icao_{label}.json").write_text(json.dumps(icao_list), encoding="utf-8")

    summary = {
        "label": label,
        "window_start_utc": datetime.fromtimestamp(ts_start, UTC).isoformat(timespec="seconds"),
        "window_end_excl_utc": datetime.fromtimestamp(ts_end_excl, UTC).isoformat(timespec="seconds"),
        "n_files": n_files,
        "n_files_with_adsb_positions": n_files_with_pos,
        "n_files_failed": n_files_failed,
        "n_trace_rows_seen": total_rows,
        "n_rows_outside_window": rows_outside_window,
        "n_rows_invalid_or_skipped": rows_invalid,
        "n_rows_without_source": rows_no_source,
        "n_positions_adsb_valid": int(abs_time.size),
        "n_unique_aircraft_adsb": int(len(set(icao_ids.tolist()))) if abs_time.size else 0,
        "source_type_counts_all_rows": dict(src_all.most_common()),
        "source_type_counts_kept": dict(src_kept.most_common()),
        "trace_files_total_size_bytes": size_bytes,
    }
    if abs_time.size:
        summary["median_range_km"] = round(float(np.median(range_km)), 1)
        summary["p95_range_km"] = round(float(np.percentile(range_km, 95)), 1)
        summary["max_range_km"] = round(float(range_km.max()), 1)
        summary["observed_first_point_utc"] = datetime.fromtimestamp(float(abs_time.min()), UTC).isoformat(timespec="seconds")
        summary["observed_last_point_utc"] = datetime.fromtimestamp(float(abs_time.max()), UTC).isoformat(timespec="seconds")
    return summary


def main():
    print("Processing era A ...", file=sys.stderr)
    sum_a = process_dir(ROOT / "dados" / "era_a", ERA_A_START, ERA_A_END_EXCL, "era_a")
    print("Processing era B ...", file=sys.stderr)
    sum_b = process_dir(ROOT / "dados" / "era_b", ERA_B_START, ERA_B_END_EXCL, "era_b")
    out = {"era_a": sum_a, "era_b": sum_b}
    (OUT / "scan_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
