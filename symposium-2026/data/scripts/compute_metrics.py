#!/usr/bin/env python3
"""Consolidated metrics: Fase E (era B), Fase F (A vs B pareado), Fase G (novas métricas)."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"

SWAP_TS = datetime(2026, 5, 16, 21, 35, 0, tzinfo=UTC).timestamp()
PAIRED_END_EXCL = (datetime(2026, 5, 16, 21, 35, 0, tzinfo=UTC) + timedelta(days=32)).timestamp()
TROPO_DUCT_WINDOWS = [
    (datetime(2026, 6, 16, 18, 0, 0, tzinfo=UTC).timestamp(), datetime(2026, 6, 18, 13, 0, 0, tzinfo=UTC).timestamp()),
    (datetime(2026, 8, 15, 11, 30, 0, tzinfo=UTC).timestamp(), datetime(2026, 8, 15, 13, 0, 0, tzinfo=UTC).timestamp()),
    (datetime(2026, 8, 25, 9, 0, 0, tzinfo=UTC).timestamp(), datetime(2026, 8, 25, 12, 30, 0, tzinfo=UTC).timestamp()),
]


def load(label):
    d = np.load(OUT / f"positions_{label}.npz")
    icao_list = json.load(open(OUT / f"icao_{label}.json"))
    return d, icao_list


def basic_stats(abs_time, range_km, icao_id):
    n = abs_time.size
    out = {"n_positions": int(n)}
    if n == 0:
        return out
    out["n_unique_aircraft"] = int(len(set(icao_id.tolist())))
    out["median_range_km"] = round(float(np.median(range_km)), 1)
    out["p95_range_km"] = round(float(np.percentile(range_km, 95)), 1)
    out["max_range_km"] = round(float(range_km.max()), 1)
    return out


def daily_series(abs_time, icao_id):
    days = (abs_time // 86400).astype(np.int64)
    uniq_days = np.unique(days)
    series = []
    for dday in uniq_days:
        mask = days == dday
        dt = datetime.fromtimestamp(dday * 86400, UTC).date().isoformat()
        series.append({
            "date": dt,
            "positions": int(mask.sum()),
            "unique_aircraft": int(len(set(icao_id[mask].tolist()))),
        })
    return series


def main():
    d_a, icao_a = load("era_a")
    d_b, icao_b = load("era_b")

    # ---------- Fase E: era B full metrics ----------
    e_full = basic_stats(d_b["abs_time"], d_b["range_km"], d_b["icao_id"])
    e_full["n_trace_files"] = int(np.load(OUT / "scan_summary.json", allow_pickle=True)) if False else None
    scan = json.loads((OUT / "scan_summary.json").read_text())
    e_full["n_trace_files"] = scan["era_b"]["n_files_with_adsb_positions"]
    e_full["disk_size_bytes"] = scan["era_b"]["trace_files_total_size_bytes"]
    e_full["window"] = {
        "start_utc": "2026-05-16T21:35:00+00:00",
        "end_utc": "2026-09-30T23:59:59+00:00",
    }
    duct_mask = np.zeros(d_b["abs_time"].shape, dtype=bool)
    for s, e in TROPO_DUCT_WINDOWS:
        duct_mask |= (d_b["abs_time"] >= s) & (d_b["abs_time"] < e) & (d_b["range_km"] > 600)
    e_full["max_range_km_excluding_tropo_duct_events"] = round(float(d_b["range_km"][~duct_mask].max()), 1)
    e_full["n_positions_in_tropo_duct_events"] = int(duct_mask.sum())
    e_full["daily_series"] = daily_series(d_b["abs_time"], d_b["icao_id"])

    # ---------- Fase F: era A (32d) vs era B pareado (32d) vs era B full ----------
    mask_paired = d_b["abs_time"] < PAIRED_END_EXCL
    rb_p, ib_p, ab_p = d_b["range_km"][mask_paired], d_b["icao_id"][mask_paired], d_b["abs_time"][mask_paired]
    e_paired = basic_stats(ab_p, rb_p, ib_p)
    e_paired["window"] = {
        "start_utc": "2026-05-16T21:35:00+00:00",
        "end_utc_excl": datetime.fromtimestamp(PAIRED_END_EXCL, UTC).isoformat(timespec="seconds"),
        "calendar_days": 32,
    }

    a_full = basic_stats(d_a["abs_time"], d_a["range_km"], d_a["icao_id"])
    a_full["window"] = {"start_utc": "2026-04-13T00:00:00+00:00", "end_utc": "2026-05-14T23:59:59+00:00", "calendar_days": 32}

    def pct_delta(new, old):
        return round((new - old) / old * 100, 1) if old else None

    comparison_32d = {
        "era_a_32d": a_full,
        "era_b_32d_paired": e_paired,
        "delta_pct": {
            "n_positions": pct_delta(e_paired["n_positions"], a_full["n_positions"]),
            "n_unique_aircraft": pct_delta(e_paired["n_unique_aircraft"], a_full["n_unique_aircraft"]),
            "median_range_km": pct_delta(e_paired["median_range_km"], a_full["median_range_km"]),
            "p95_range_km": pct_delta(e_paired["p95_range_km"], a_full["p95_range_km"]),
            "max_range_km": pct_delta(e_paired["max_range_km"], a_full["max_range_km"]),
        },
    }

    # common fleet: ICAO strings appearing in both era A (32d) and era B paired (32d)
    set_a = set(icao_a[i] for i in np.unique(d_a["icao_id"]))
    set_b_paired = set(icao_b[i] for i in np.unique(ib_p))
    common = set_a & set_b_paired
    icao_a_rev = {v: i for i, v in enumerate(icao_a)}
    icao_b_rev = {v: i for i, v in enumerate(icao_b)}
    common_ids_a = {icao_a_rev[c] for c in common}
    common_ids_b = {icao_b_rev[c] for c in common}
    mask_common_a = np.isin(d_a["icao_id"], list(common_ids_a))
    mask_common_b = np.isin(ib_p, list(common_ids_b))
    avg_range_common_a = round(float(d_a["range_km"][mask_common_a].mean()), 1) if mask_common_a.any() else None
    avg_range_common_b = round(float(rb_p[mask_common_b].mean()), 1) if mask_common_b.any() else None

    common_fleet = {
        "n_common_icao24": len(common),
        "n_only_era_a": len(set_a - set_b_paired),
        "n_only_era_b_paired": len(set_b_paired - set_a),
        "avg_range_km_common_fleet_era_a": avg_range_common_a,
        "avg_range_km_common_fleet_era_b_paired": avg_range_common_b,
        "avg_range_delta_pct": pct_delta(avg_range_common_b, avg_range_common_a) if avg_range_common_a else None,
    }

    # ---------- Fase G.a: azimuthal distribution, 10-deg bins, normalized ----------
    bins_az = np.arange(0, 361, 10)
    hist_a_az, _ = np.histogram(d_a["bearing_deg"], bins=bins_az)
    hist_b_az, _ = np.histogram(d_b["bearing_deg"], bins=bins_az)
    azimuth = {
        "bins_deg": bins_az.tolist(),
        "era_a_counts": hist_a_az.tolist(),
        "era_b_counts": hist_b_az.tolist(),
        "era_a_pct": (hist_a_az / hist_a_az.sum() * 100).round(3).tolist(),
        "era_b_pct": (hist_b_az / hist_b_az.sum() * 100).round(3).tolist(),
    }

    # ---------- Fase G.b: altitude coverage, 5000ft bins 0-45000 ----------
    alt_bins = np.arange(0, 50001, 5000)
    alt_a = np.nan_to_num(d_a["alt_ft"], nan=-1)
    alt_b = np.nan_to_num(d_b["alt_ft"], nan=-1)
    valid_a = alt_a >= 0
    valid_b = alt_b >= 0
    hist_a_alt, _ = np.histogram(alt_a[valid_a], bins=alt_bins)
    hist_b_alt, _ = np.histogram(alt_b[valid_b], bins=alt_bins)
    bin_idx_a = np.clip(np.digitize(alt_a, alt_bins) - 1, 0, len(alt_bins) - 2)
    bin_idx_b = np.clip(np.digitize(alt_b, alt_bins) - 1, 0, len(alt_bins) - 2)
    alt_range_avg_a, alt_range_max_a, alt_range_avg_b, alt_range_max_b = [], [], [], []
    for bi in range(len(alt_bins) - 1):
        m_a = valid_a & (bin_idx_a == bi)
        m_b = valid_b & (bin_idx_b == bi)
        alt_range_avg_a.append(round(float(d_a["range_km"][m_a].mean()), 1) if m_a.any() else None)
        alt_range_max_a.append(round(float(d_a["range_km"][m_a].max()), 1) if m_a.any() else None)
        alt_range_avg_b.append(round(float(d_b["range_km"][m_b].mean()), 1) if m_b.any() else None)
        alt_range_max_b.append(round(float(d_b["range_km"][m_b].max()), 1) if m_b.any() else None)
    altitude = {
        "bins_ft": alt_bins.tolist(),
        "n_ground_era_a": int((d_a["alt_ft"] == 0).sum() - 0),
        "era_a_counts": hist_a_alt.tolist(),
        "era_b_counts": hist_b_alt.tolist(),
        "era_a_avg_range_km": alt_range_avg_a,
        "era_a_max_range_km": alt_range_max_a,
        "era_b_avg_range_km": alt_range_avg_b,
        "era_b_max_range_km": alt_range_max_b,
    }

    # ---------- Fase G.c: operational continuity (era B full window) ----------
    t = np.sort(d_b["abs_time"])
    diffs = np.diff(t)
    gap_threshold_s = 120.0  # below this: normal 15s reporting jitter / single-aircraft silence
    gap_idx = np.where(diffs > gap_threshold_s)[0]
    gaps = []
    win_start, win_end = scan["era_b"]["window_start_utc"] if False else None, None
    win_start_ts = SWAP_TS
    win_end_ts = datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC).timestamp()
    for i in gap_idx:
        g_start, g_end = float(t[i]), float(t[i + 1])
        dur_s = g_end - g_start
        bucket = "<15min" if dur_s < 900 else ("15-60min" if dur_s < 3600 else ">60min")
        g_start_utc = datetime.fromtimestamp(g_start, UTC)
        gaps.append({
            "start_utc": g_start_utc.isoformat(timespec="seconds"),
            "start_brt": (g_start_utc - timedelta(hours=3)).isoformat(timespec="seconds"),
            "end_utc": datetime.fromtimestamp(g_end, UTC).isoformat(timespec="seconds"),
            "duration_s": round(dur_s, 1),
            "bucket": bucket,
            "start_hour_utc": g_start_utc.hour,
        })
    total_downtime_s = sum(g["duration_s"] for g in gaps)
    window_span_s = win_end_ts - win_start_ts
    uptime_pct = round((1 - total_downtime_s / window_span_s) * 100, 4)
    bucket_counts = {"<15min": 0, "15-60min": 0, ">60min": 0}
    bucket_totaldur = {"<15min": 0.0, "15-60min": 0.0, ">60min": 0.0}
    hour_hist = np.zeros(24, dtype=int)
    for g in gaps:
        bucket_counts[g["bucket"]] += 1
        bucket_totaldur[g["bucket"]] += g["duration_s"]
        hour_hist[g["start_hour_utc"]] += 1
    continuity = {
        "gap_detection_threshold_s": gap_threshold_s,
        "method": "merged sorted timestamps of all valid ADS-B positions in era B window; any inter-arrival gap > threshold flagged as zero-coverage interval",
        "n_gaps": len(gaps),
        "bucket_counts": bucket_counts,
        "bucket_total_duration_s": {k: round(v, 1) for k, v in bucket_totaldur.items()},
        "total_downtime_s": round(total_downtime_s, 1),
        "total_downtime_h": round(total_downtime_s / 3600, 2),
        "window_span_s": window_span_s,
        "uptime_pct_position_level": uptime_pct,
        "gap_start_hour_utc_histogram": hour_hist.tolist(),
        "gaps": sorted(gaps, key=lambda g: -g["duration_s"])[:50],
        "n_gaps_truncated_in_output": max(0, len(gaps) - 50),
    }

    result = {
        "fase_e_era_b_full": e_full,
        "fase_f_comparison_32d": comparison_32d,
        "fase_f_era_b_full_separate": e_full,
        "fase_f_common_fleet": common_fleet,
        "fase_g_azimuth": azimuth,
        "fase_g_altitude": altitude,
        "fase_g_continuity": continuity,
        "tropo_duct_events_detected": [
            {"start_utc": datetime.fromtimestamp(s, UTC).isoformat(), "end_utc": datetime.fromtimestamp(e, UTC).isoformat()}
            for s, e in TROPO_DUCT_WINDOWS
        ],
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (ROOT / "relatorios").mkdir(exist_ok=True)
    (ROOT / "relatorios" / "figure_metrics_era_b.json").write_text(
        json.dumps(result, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    print("WROTE relatorios/figure_metrics_era_b.json")
    print(json.dumps({
        "e_full_n_positions": e_full["n_positions"],
        "e_full_n_unique_aircraft": e_full["n_unique_aircraft"],
        "e_full_max_range": e_full["max_range_km"],
        "e_full_max_range_no_duct": e_full["max_range_km_excluding_tropo_duct_events"],
        "comparison_32d_delta_pct": comparison_32d["delta_pct"],
        "common_fleet": common_fleet,
        "continuity_summary": {k: continuity[k] for k in ("n_gaps", "bucket_counts", "total_downtime_h", "uptime_pct_position_level")},
    }, indent=2))


if __name__ == "__main__":
    main()
