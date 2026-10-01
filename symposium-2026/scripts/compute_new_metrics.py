#!/usr/bin/env python3
"""New metrics for the short paper and poster (fixed methodology).

Step 1: reproduces the frozen headline numbers from the cached position arrays.
Step 2: computes the new metrics (paired p95/max, Brazilian ICAO block share,
gap analysis, daily maxima, gap hour histogram, common-fleet deltas, gains,
era B day count, 17/05 audit check).

Inputs : data/scripts/out/positions_era_{a,b}.npz, icao_era_{a,b}.json,
         raw trace_full files under data/dados/era_{a,b} (header only, for dbFlags).
Outputs: analysis/new_metrics.json, analysis/common_fleet_deltas.npz

Privacy: no ICAO24 address and no military list is written anywhere. Only the
count of excluded military/state aircraft is stored.
Methodology: only adsb_icao and adsb_icao_nt (MLAT excluded), receiver rounded
-20.51/-47.40, haversine R = 6371.0088 km (all already applied in the arrays).
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "scripts" / "out"
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(DATA / "scripts"))
from compute_metrics import PAIRED_END_EXCL, SWAP_TS, TROPO_DUCT_WINDOWS  # noqa: E402

END_B = datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC).timestamp()
GAP_THRESHOLD_S = 120.0
BR_LO, BR_HI = 0xE40000, 0xE7FFFF


def iso(ts):
    return datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds")


def stats(t, r, i):
    return {
        "n_positions": int(t.size),
        "n_aircraft": int(np.unique(i).size),
        "median_km": round(float(np.median(r)), 1),
        "p95_km": round(float(np.percentile(r, 95)), 1),
        "max_km": round(float(r.max()), 1),
    }


def find_gaps(t_sorted):
    diffs = np.diff(t_sorted)
    idx = np.where(diffs > GAP_THRESHOLD_S)[0]
    return [(float(t_sorted[i]), float(t_sorted[i + 1])) for i in idx]


def overlaps_0507(s, e):
    d0 = int(s // 86400) - 1
    d1 = int(e // 86400) + 1
    for d in range(d0, d1 + 1):
        ws, we = d * 86400 + 5 * 3600, d * 86400 + 7 * 3600
        if s < we and e > ws:
            return True
    return False


DBFLAGS_RE = re.compile(rb'"dbFlags"\s*:\s*(\d+)')


def trace_dbflags(path: Path):
    """dbFlags from a trace_full file (gzip or plain). Header read first, full parse as fallback."""
    with path.open("rb") as f:
        magic = f.read(2)
    try:
        if magic == b"\x1f\x8b":
            with gzip.open(path, "rb") as f:
                head = f.read(2048)
        else:
            head = path.read_bytes()[:2048]
        m = DBFLAGS_RE.search(head)
        if m:
            return int(m.group(1))
        if magic == b"\x1f\x8b":
            with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
                d = json.load(f)
        else:
            d = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return int(d.get("dbFlags", 0) or 0)
    except Exception:
        return None


def main():
    da = np.load(OUT / "positions_era_a.npz")
    db = np.load(OUT / "positions_era_b.npz")
    icao_a = json.load(open(OUT / "icao_era_a.json"))
    icao_b = json.load(open(OUT / "icao_era_b.json"))
    ta, ra, ia = da["abs_time"], da["range_km"], da["icao_id"]
    tb, rb, ib = db["abs_time"], db["range_km"], db["icao_id"]
    res = {"generated_utc": datetime.now(UTC).isoformat(timespec="seconds")}

    # ==== STEP 1: frozen consistency ====
    duct_mask = np.zeros(tb.shape, dtype=bool)
    for s, e in TROPO_DUCT_WINDOWS:
        duct_mask |= (tb >= s) & (tb < e) & (rb > 600)
    a_full = stats(ta, ra, ia)
    b_full = stats(tb, rb, ib)
    b_full["max_excl_ducting_km"] = round(float(rb[~duct_mask].max()), 1)
    b_full["n_duct_positions"] = int(duct_mask.sum())
    mp = tb < PAIRED_END_EXCL
    b_pair = stats(tb[mp], rb[mp], ib[mp])

    # common fleet (string match across eras, A vs paired B)
    set_a = {icao_a[i] for i in np.unique(ia)}
    set_bp = {icao_b[i] for i in np.unique(ib[mp])}
    common = sorted(set_a & set_bp)
    rev_a = {v: i for i, v in enumerate(icao_a)}
    rev_b = {v: i for i, v in enumerate(icao_b)}
    ids_a = np.array([rev_a[c] for c in common])
    ids_b = np.array([rev_b[c] for c in common])
    ma = np.isin(ia, ids_a)
    mb = np.isin(ib[mp], ids_b)
    mean_a_fleet = float(ra[ma].mean())
    mean_b_fleet = float(rb[mp][mb].mean())

    ts_sorted = np.sort(tb)
    gaps = find_gaps(ts_sorted)
    total_down = sum(e - s for s, e in gaps)
    span = END_B - SWAP_TS
    uptime = (1 - total_down / span) * 100

    checks = {
        "era_a_positions": (a_full["n_positions"], 5153167),
        "era_a_aircraft": (a_full["n_aircraft"], 2890),
        "era_a_median": (a_full["median_km"], 189.3),
        "era_a_p95": (a_full["p95_km"], 299.7),
        "era_a_max": (a_full["max_km"], 510.3),
        "era_b_full_positions": (b_full["n_positions"], 36535422),
        "era_b_full_aircraft": (b_full["n_aircraft"], 4925),
        "era_b_full_median": (b_full["median_km"], 222.0),
        "era_b_full_p95": (b_full["p95_km"], 350.1),
        "era_b_full_max_raw": (b_full["max_km"], 786.3),
        "era_b_full_max_excl_ducting": (b_full["max_excl_ducting_km"], 599.9),
        "era_b_paired_positions": (b_pair["n_positions"], 8123970),
        "era_b_paired_aircraft": (b_pair["n_aircraft"], 3159),
        "era_b_paired_median": (b_pair["median_km"], 224.0),
        "era_b_paired_p95_report": (b_pair["p95_km"], 350.6),
        "era_b_paired_max_report": (b_pair["max_km"], 786.3),
        "common_fleet_n": (len(common), 2234),
        "common_fleet_mean_a": (round(mean_a_fleet, 1), 188.5),
        "common_fleet_mean_b": (round(mean_b_fleet, 1), 217.9),
        "common_fleet_pct": (round((mean_b_fleet - mean_a_fleet) / mean_a_fleet * 100, 1), 15.6),
        "uptime_pct": (round(uptime, 2), 99.33),
        "n_gaps_120s": (len(gaps), 40),
    }
    step1 = {k: {"computed": v[0], "frozen": v[1], "pass": bool(v[0] == v[1])} for k, v in checks.items()}
    res["step1_frozen_check"] = step1
    res["step1_all_pass"] = all(v["pass"] for v in step1.values())
    if not res["step1_all_pass"]:
        print("FROZEN CHECK FAILED:", [k for k, v in step1.items() if not v["pass"]])
        (ANALYSIS / "new_metrics.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
        sys.exit(1)

    # ==== (a) paired p95 and max ====
    res["a_paired"] = {
        "p95_km": b_pair["p95_km"],
        "max_km": b_pair["max_km"],
        "note": "paired window max includes the 2026-06-17 ducting event",
        "report_values": {"p95_km": 350.6, "max_km": 786.3},
        "confirmed": b_pair["p95_km"] == 350.6 and b_pair["max_km"] == 786.3,
    }

    # ==== (b) Brazilian ICAO block ====
    n_ids = len(icao_b)
    is_br = np.zeros(n_ids, dtype=bool)
    is_hex = np.zeros(n_ids, dtype=bool)
    for k, s in enumerate(icao_b):
        s2 = s.strip().lower()
        if len(s2) == 6 and all(c in "0123456789abcdef" for c in s2):
            is_hex[k] = True
            is_br[k] = BR_LO <= int(s2, 16) <= BR_HI
    ids_with_pos = np.unique(ib)
    n_aircraft = int(ids_with_pos.size)
    br_aircraft = int(is_br[ids_with_pos].sum())
    nonhex_aircraft = int((~is_hex[ids_with_pos]).sum())
    pos_br = int(is_br[ib].sum())
    res["b_brazil_block"] = {
        "icao_string_format": "lowercase 6-hex strings; some entries carry a leading tilde (non-ICAO addresses), treated as outside the block",
        "block": "E40000 to E7FFFF (24-bit, inclusive)",
        "era_b_aircraft_total": n_aircraft,
        "era_b_aircraft_in_block": br_aircraft,
        "era_b_aircraft_nonhex_tilde": nonhex_aircraft,
        "era_b_aircraft_share_pct": round(br_aircraft / n_aircraft * 100, 1),
        "era_b_positions_total": int(ib.size),
        "era_b_positions_in_block": pos_br,
        "era_b_positions_share_pct": round(pos_br / ib.size * 100, 1),
    }

    # ==== (c) gap analysis ====
    gap_rows = []
    hour_hist = np.zeros(24, dtype=int)
    for s, e in gaps:
        sd = datetime.fromtimestamp(s, UTC)
        dur = e - s
        bucket = "<15min" if dur < 900 else ("15-60min" if dur < 3600 else ">60min")
        hour_hist[sd.hour] += 1
        gap_rows.append({
            "start_utc": iso(s),
            "end_utc": iso(e),
            "duration_min": round(dur / 60, 1),
            "duration_s": round(dur, 1),
            "bucket": bucket,
            "start_hour_utc": sd.hour,
            "start_hour_brt": (sd - timedelta(hours=3)).hour,
            "overlaps_05_07_utc": overlaps_0507(s, e),
        })
    start_in = sum(1 for g in gap_rows if 5 <= g["start_hour_utc"] < 7)
    overl = sum(1 for g in gap_rows if g["overlaps_05_07_utc"])
    bc = {"<15min": 0, "15-60min": 0, ">60min": 0}
    for g in gap_rows:
        bc[g["bucket"]] += 1
    over60 = [g for g in gap_rows if g["bucket"] == ">60min"]
    res["c_gaps"] = {
        "threshold_s": GAP_THRESHOLD_S,
        "method": "merged sorted timestamps of all valid ADS-B positions in the Era B window; inter-arrival gap > threshold",
        "n_gaps": len(gap_rows),
        "start_in_05_07_utc": start_in,
        "overlap_05_07_utc": overl,
        "frozen_claim_in_05_07_utc": 38,
        "divergence": {
            "frozen_claim": 38,
            "data_start_in_05_07_utc": start_in,
            "data_overlap_05_07_utc": overl,
            "difference_vs_start": 38 - start_in,
            "difference_vs_overlap": 38 - overl,
            "text": "Frozen claim says 38 of 40 gaps lie between 05 and 07 UTC; the data show the counts above. Not reconciled; frozen figure kept as a separate field.",
        },
        "bucket_counts": bc,
        "gaps_over_60min": over60,
        "total_downtime_s": round(total_down, 1),
        "total_downtime_h": round(total_down / 3600, 2),
        "window_span_h": round(span / 3600, 2),
        "uptime_pct": round(uptime, 2),
        "uptime_pct_4dp": round(uptime, 4),
        "gaps": gap_rows,
    }
    # (e) hour histogram
    res["e_gap_start_hour_hist_utc"] = hour_hist.tolist()
    brt = np.zeros(24, dtype=int)
    for g in gap_rows:
        brt[g["start_hour_brt"]] += 1
    res["e_gap_start_hour_hist_brt"] = brt.tolist()

    # ==== (d) daily max range ====
    days = (tb // 86400).astype(np.int64)
    ud = np.unique(days)
    daily = []
    for d in ud:
        m = days == d
        ds, de = d * 86400.0, d * 86400.0 + 86400.0
        flag = any(s < de and e > ds for s, e in TROPO_DUCT_WINDOWS)
        mx = float(rb[m].max())
        mx_nd = float(rb[m & ~duct_mask].max())
        daily.append({
            "date": datetime.fromtimestamp(ds, UTC).date().isoformat(),
            "max_km": round(mx, 1),
            "max_excl_ducting_km": round(mx_nd, 1),
            "ducting_window_day": bool(flag),
        })
    over600 = [x for x in daily if x["max_km"] > 600]
    res["d_daily_max"] = {
        "rule": "all positions per UTC day; ducting flag = day intersects a TROPO_DUCT_WINDOW from compute_metrics.py",
        "ducting_windows_utc": [{"start": iso(s), "end": iso(e)} for s, e in TROPO_DUCT_WINDOWS],
        "n_days": len(daily),
        "n_positions_over_600km_in_ducting_windows": b_full["n_duct_positions"],
        "days_over_600km": over600,
        "n_days_over_600km": len(over600),
        "max_over_non_ducting_days_km": round(max(x["max_km"] for x in daily if not x["ducting_window_day"]), 1),
        "max_excl_ducting_positions_km": b_full["max_excl_ducting_km"],
        "series": daily,
    }

    # ==== (f) common fleet deltas, military excluded ====
    mil = set()
    n_unreadable = 0
    wanted = set(common)
    for era in ("era_a", "era_b"):
        for p in (DATA / "dados" / era).rglob("trace_full_*.json"):
            code = p.name[len("trace_full_"):-len(".json")]
            if code not in wanted:
                continue
            fl = trace_dbflags(p)
            if fl is None:
                n_unreadable += 1
            elif fl & 1:
                mil.add(code)
    keep_codes = [c for c in common if c not in mil]
    k_a = np.array([rev_a[c] for c in keep_codes])
    k_b = np.array([rev_b[c] for c in keep_codes])
    cnt_a = np.bincount(ia, minlength=len(icao_a))
    sum_a = np.bincount(ia, weights=ra, minlength=len(icao_a))
    ib_p, rb_p = ib[mp], rb[mp]
    cnt_b = np.bincount(ib_p, minlength=len(icao_b))
    sum_b = np.bincount(ib_p, weights=rb_p, minlength=len(icao_b))
    mean_a = sum_a[k_a] / cnt_a[k_a]
    mean_b = sum_b[k_b] / cnt_b[k_b]
    delta = mean_b - mean_a
    order = np.argsort(delta)
    np.savez_compressed(
        ANALYSIS / "common_fleet_deltas.npz",
        delta_km=delta[order],
        mean_range_a_km=mean_a[order],
        mean_range_b_km=mean_b[order],
        n_pos_a=cnt_a[k_a][order],
        n_pos_b=cnt_b[k_b][order],
    )
    res["f_common_fleet_deltas"] = {
        "label": "NEW numbers (not frozen); common fleet with military/state aircraft excluded",
        "n_common_all": len(common),
        "n_excluded_military_state": len(mil),
        "n_files_unreadable_for_dbflags": n_unreadable,
        "n_plotted": int(delta.size),
        "delta_median_km": round(float(np.median(delta)), 1),
        "delta_mean_km": round(float(delta.mean()), 1),
        "share_delta_positive_pct": round(float((delta > 0).mean() * 100), 1),
        "mean_range_a_km_plotted": round(float(mean_a.mean()), 1),
        "mean_range_b_km_plotted": round(float(mean_b.mean()), 1),
        "delta_p5_km": round(float(np.percentile(delta, 5)), 1),
        "delta_p95_km": round(float(np.percentile(delta, 95)), 1),
        "npz": "analysis/common_fleet_deltas.npz (arrays only, sorted by delta, no ICAO addresses)",
    }

    # ==== (g) gains ====
    pos_gain = (b_pair["n_positions"] - a_full["n_positions"]) / a_full["n_positions"] * 100
    ac_gain = (b_pair["n_aircraft"] - a_full["n_aircraft"]) / a_full["n_aircraft"] * 100
    res["g_gains"] = {
        "positions_gain_pct_exact": round(pos_gain, 6),
        "positions_gain_pct_1dp": round(pos_gain, 1),
        "aircraft_gain_pct_exact": round(ac_gain, 6),
        "aircraft_gain_pct_1dp": round(ac_gain, 1),
        "report_positions_gain_pct": 57.7,
        "note": "report rounded positions gain differently; exact value above, paper uses 1 dp of exact",
    }

    # ==== (h) era B day count and 17/05 check ====
    dur_s = END_B - SWAP_TS
    first_obs = float(tb.min())
    first_day = datetime(2026, 5, 16, tzinfo=UTC).date()
    last_day = datetime(2026, 9, 30, tzinfo=UTC).date()
    res["h_era_b_duration"] = {
        "swap_utc": iso(SWAP_TS),
        "end_excl_utc": iso(END_B),
        "hours": round(dur_s / 3600, 2),
        "days_float": round(dur_s / 86400, 3),
        "full_24h_days_from_midnight_17_05": 137,
        "calendar_dates_inclusive_16_05_to_30_09": (last_day - first_day).days + 1,
        "first_observed_point_utc": iso(first_obs),
        "swap_to_first_point_min": round((first_obs - SWAP_TS) / 60, 1),
        "explanation": "137 full UTC days 17/05 to 30/09 plus 2 h 25 min of 16/05 after the swap = 3290.4 h (137.1 d); 16/05 is a partial day so 16/05 to 30/09 spans 138 calendar dates",
    }

    d17 = int(datetime(2026, 5, 17, tzinfo=UTC).timestamp())
    m17 = (tb >= d17) & (tb < d17 + 86400)
    n17 = int(m17.sum())
    brt_start = d17 + 3 * 3600
    n17_brt = int(((tb >= brt_start) & (tb < brt_start + 86400)).sum())
    # dedup hypotheses
    key = np.round(tb[m17], 0).astype(np.int64) * 100000 + ib[m17].astype(np.int64)
    n17_dedup_1s = int(np.unique(key).size)
    n17_dedup_exact = int(np.unique(tb[m17] * 100000 + ib[m17]).size)
    n17_nonground = int((m17 & ~db["is_ground"]).sum())
    n17_alt_valid = int((m17 & ~np.isnan(db["alt_ft"])).sum())
    # raw directory scan for 2026/05/17 (all rows, by source type)
    raw_rows = {"files": 0, "rows_all": 0, "rows_adsb": 0, "rows_mlat": 0, "rows_other": 0, "rows_adsb_with_latlon": 0}
    base17 = DATA / "dados" / "era_b" / "2026" / "05" / "17"
    for p in base17.rglob("trace_full_*.json"):
        raw_rows["files"] += 1
        try:
            with gzip.open(p, "rt", encoding="utf-8", errors="ignore") as f:
                dd = json.load(f)
        except Exception:
            continue
        for row in dd.get("trace", []):
            raw_rows["rows_all"] += 1
            if not isinstance(row, list) or len(row) < 10:
                continue
            src = row[9]
            if src in ("adsb_icao", "adsb_icao_nt"):
                raw_rows["rows_adsb"] += 1
                if isinstance(row[1], (int, float)) and isinstance(row[2], (int, float)):
                    raw_rows["rows_adsb_with_latlon"] += 1
            elif src == "mlat":
                raw_rows["rows_mlat"] += 1
            else:
                raw_rows["rows_other"] += 1
    # audit-window comparison: audit era B 22 d = UTC days 05-17 to 06-07 (06-07 partial at audit time)
    w0 = d17
    w1 = int(datetime(2026, 6, 8, tzinfo=UTC).timestamp())
    n_22d = int(((tb >= w0) & (tb < w1)).sum())
    w1b = int(datetime(2026, 6, 7, tzinfo=UTC).timestamp())
    n_21d = int(((tb >= w0) & (tb < w1b)).sum())
    res["h_17_05_check"] = {
        "current_pipeline_utc_day_positions": n17,
        "audit_value": 209431,
        "ratio_audit_over_current": round(209431 / n17, 4),
        "hypotheses_counts_from_npz": {
            "utc_day_2026_05_17": n17,
            "brt_day_2026_05_17 (03:00Z to 03:00Z next day)": n17_brt,
            "dedup_icao_and_time_1s": n17_dedup_1s,
            "dedup_exact_icao_time": n17_dedup_exact,
            "excluding_ground_alt": n17_nonground,
            "alt_not_nan": n17_alt_valid,
            "excluding_adsb_icao_nt": n17,
            "note_adsb_icao_nt": "Era B contains zero adsb_icao_nt rows, so excluding it changes nothing",
        },
        "raw_dir_2026_05_17": raw_rows,
        "era_b_positions_utc_05_17_to_06_07_incl": n_22d,
        "era_b_positions_utc_05_17_to_06_06_incl": n_21d,
        "audit_era_b_22d_positions": 5301055,
        "audit_era_b_full_positions_to_06_07": 5330054,
        "audit_swap_downtime": "audit reports no data between 20:41Z and 21:51Z on 05-16 and first Era B point 21:51Z (current first observed point is in h_era_b_duration)",
    }

    (ANALYSIS / "new_metrics.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print("WROTE analysis/new_metrics.json; step1_all_pass =", res["step1_all_pass"])
    print(json.dumps({k: res[k] for k in ("a_paired", "b_brazil_block", "g_gains", "h_era_b_duration", "h_17_05_check")}, indent=1))
    c = dict(res["c_gaps"])
    c.pop("gaps")
    print(json.dumps(c, indent=1))
    print(json.dumps(res["f_common_fleet_deltas"], indent=1))
    print(json.dumps({k: v for k, v in res["d_daily_max"].items() if k != "series"}, indent=1))
    print("hour hist utc", res["e_gap_start_hour_hist_utc"])


SCRATCH_MIL = Path("/private/tmp/claude-501/-Users-eliel/e2d6e951-eb59-46ff-a034-78ea2ed0cdf6/scratchpad/military_exclusion_common_fleet.json")
OUTAGE_DATES = ("2026-07-06", "2026-08-02")  # the two confirmed receiver outages (gap list entries over 60 min)


def poster_revision():
    """Poster revision additions (does not change any frozen result).

    Reads analysis/new_metrics.json, adds keys i_uptime_split, j_common_fleet_unified,
    k_duct_criterion, and writes it back. Run: python3 scripts/compute_new_metrics.py --poster
    The military/state exclusion set stays in the scratchpad cache (never in the project).
    """
    path = ANALYSIS / "new_metrics.json"
    res = json.loads(path.read_text(encoding="utf-8"))
    da = np.load(OUT / "positions_era_a.npz")
    db = np.load(OUT / "positions_era_b.npz")
    icao_a = json.load(open(OUT / "icao_era_a.json"))
    icao_b = json.load(open(OUT / "icao_era_b.json"))
    ta, ra, ia = da["abs_time"], da["range_km"], da["icao_id"]
    tb, rb, ib = db["abs_time"], db["range_km"], db["icao_id"]
    mp = tb < PAIRED_END_EXCL

    # ==== i) uptime split: receiver outages vs reception gaps ====
    c = res["c_gaps"]
    gaps = c["gaps"]
    window_h = c["window_span_h"]
    outs = [g for g in gaps if g["start_utc"][:10] in OUTAGE_DATES and g["duration_min"] > 60]
    assert len(outs) == 2, outs
    assert [round(g["duration_min"], 1) for g in outs] == [312.3, 587.3]
    out_h = sum(g["duration_s"] for g in outs) / 3600.0
    all_h = sum(g["duration_s"] for g in gaps) / 3600.0
    others = [g for g in gaps if g not in outs]
    oth_h = sum(g["duration_s"] for g in others) / 3600.0
    night_others = [g for g in others if 5 <= g["start_hour_utc"] < 7]
    night_all = [g for g in gaps if 5 <= g["start_hour_utc"] < 7]
    assert len(night_others) == len(night_all) == c["start_in_05_07_utc"] == 19
    assert len(others) == 38 and abs(out_h + oth_h - all_h) < 1e-9
    res["i_uptime_split"] = {
        "label": "NEW (poster revision). No readsb stats/logs exist in data/ and the Pi was unreachable; fallback method from the gap list.",
        "window_h": window_h,
        "outages": [{"start_utc": g["start_utc"], "end_utc": g["end_utc"], "duration_min": g["duration_min"]} for g in outs],
        "receiver_downtime_h": round(out_h, 2),
        "receiver_uptime_pct": round((1 - out_h / window_h) * 100, 2),
        "receiver_uptime_pct_4dp": round((1 - out_h / window_h) * 100, 4),
        "reception_downtime_h": round(all_h, 2),
        "reception_continuity_pct": round((1 - all_h / window_h) * 100, 2),
        "n_reception_gaps_total": len(gaps),
        "n_reception_gaps_other": len(others),
        "reception_gap_other_h": round(oth_h, 2),
        "n_other_start_05_07_utc": len(night_others),
        "n_other_not_05_07_utc": len(others) - len(night_others),
        "third_long_gap": [{"start_utc": g["start_utc"], "duration_min": g["duration_min"]} for g in others if g["duration_min"] > 60],
    }

    # ==== j) common fleet unified definition ====
    set_a = {icao_a[i] for i in np.unique(ia)}
    set_bp = {icao_b[i] for i in np.unique(ib[mp])}
    common = sorted(set_a & set_bp)
    rev_a = {v: i for i, v in enumerate(icao_a)}
    rev_b = {v: i for i, v in enumerate(icao_b)}
    if SCRATCH_MIL.exists():
        mil = set(json.loads(SCRATCH_MIL.read_text())["military"])
        mil_src = "scratchpad cache"
    else:
        mil, wanted = set(), set(common)
        for era in ("era_a", "era_b"):
            for p in (DATA / "dados" / era).rglob("trace_full_*.json"):
                code = p.name[len("trace_full_"):-len(".json")]
                if code in wanted:
                    fl = trace_dbflags(p)
                    if fl is not None and fl & 1:
                        mil.add(code)
        SCRATCH_MIL.write_text(json.dumps({"n_common": len(common), "military": sorted(mil)}))
        mil_src = "recomputed from dbFlags bit 0, cached in scratchpad"
    assert set(common) >= mil and len(mil) == res["f_common_fleet_deltas"]["n_excluded_military_state"]
    cnt_a = np.bincount(ia, minlength=len(icao_a))
    sum_a = np.bincount(ia, weights=ra, minlength=len(icao_a))
    cnt_b = np.bincount(ib[mp], minlength=len(icao_b))
    sum_b = np.bincount(ib[mp], weights=rb[mp], minlength=len(icao_b))

    def block(codes):
        k_a = np.array([rev_a[x] for x in codes])
        k_b = np.array([rev_b[x] for x in codes])
        pooled_a = sum_a[k_a].sum() / cnt_a[k_a].sum()
        pooled_b = sum_b[k_b].sum() / cnt_b[k_b].sum()
        pa, pb = sum_a[k_a] / cnt_a[k_a], sum_b[k_b] / cnt_b[k_b]
        return {
            "n_aircraft": len(codes),
            "n_positions_a": int(cnt_a[k_a].sum()),
            "n_positions_b": int(cnt_b[k_b].sum()),
            "pooled_mean_a_km": round(float(pooled_a), 1),
            "pooled_mean_b_km": round(float(pooled_b), 1),
            "pooled_gain_pct": round(float((pooled_b - pooled_a) / pooled_a * 100), 1),
            "per_aircraft_mean_a_km": round(float(pa.mean()), 1),
            "per_aircraft_mean_b_km": round(float(pb.mean()), 1),
            "per_aircraft_gain_pct": round(float((pb.mean() - pa.mean()) / pa.mean() * 100), 1),
            "delta_median_km": round(float(np.median(pb - pa)), 1),
            "delta_mean_km": round(float((pb - pa).mean()), 1),
        }

    all_blk = block(common)
    keep = [x for x in common if x not in mil]
    fil_blk = block(keep)
    assert (all_blk["pooled_mean_a_km"], all_blk["pooled_mean_b_km"], all_blk["pooled_gain_pct"]) == (188.5, 217.9, 15.6)
    f = res["f_common_fleet_deltas"]
    assert fil_blk["n_aircraft"] == f["n_plotted"]
    assert (fil_blk["per_aircraft_mean_a_km"], fil_blk["per_aircraft_mean_b_km"]) == (f["mean_range_a_km_plotted"], f["mean_range_b_km_plotted"])
    assert fil_blk["delta_median_km"] == f["delta_median_km"]
    res["j_common_fleet_unified"] = {
        "label": "NEW (poster revision). Definitions: pooled = mean over all valid positions of the aircraft set (frozen 188.5 to 217.9 definition); per_aircraft = mean of per-aircraft mean ranges (histogram definition).",
        "military_source": mil_src,
        "frozen_all_2234": all_blk,
        "filtered_no_military": fil_blk,
    }

    # ==== k) ducting criterion: positions over 600 km clustered by gaps over 6 h ====
    over = rb > 600.0
    t_o, r_o = tb[over], rb[over]
    order = np.argsort(t_o)
    t_o, r_o = t_o[order], r_o[order]
    brk = np.where(np.diff(t_o) > 6 * 3600.0)[0]
    starts = np.concatenate([[0], brk + 1])
    ends = np.concatenate([brk + 1, [t_o.size]])
    clusters = []
    for s0, e0 in zip(starts, ends):
        clusters.append({
            "first_utc": iso(t_o[s0]),
            "last_utc": iso(t_o[e0 - 1]),
            "n_positions_over_600km": int(e0 - s0),
            "max_km": round(float(r_o[s0:e0].max()), 1),
        })
    # each cluster must lie inside one hand-set window; a window may hold more than one cluster
    win_of = []
    for cl in clusters:
        f0 = datetime.fromisoformat(cl["first_utc"]).timestamp()
        l0 = datetime.fromisoformat(cl["last_utc"]).timestamp()
        w = [k for k, (ws, we) in enumerate(TROPO_DUCT_WINDOWS) if ws <= f0 and l0 <= we]
        assert len(w) == 1, cl
        win_of.append(w[0])
        cl["window_index"] = w[0] + 1
    assert sorted(set(win_of)) == [0, 1, 2]
    n_win = {k + 1: sum(c["n_positions_over_600km"] for c in clusters if c["window_index"] == k + 1) for k in range(3)}
    gap_h_main_to_tail = (datetime.fromisoformat(clusters[1]["first_utc"]) - datetime.fromisoformat(clusters[0]["last_utc"])).total_seconds() / 3600.0
    assert sum(n_win.values()) == int(over.sum()) == res["d_daily_max"]["n_positions_over_600km_in_ducting_windows"]
    res["k_duct_criterion"] = {
        "label": "NEW (poster revision). Criterion documented in data/relatorios/coverage_era_b_*.md and data/contexto_analise_adsb.md; TROPO_DUCT_WINDOWS in data/scripts/compute_metrics.py are the hand-rounded windows delimiting each cluster.",
        "threshold_km": 600,
        "cluster_gap_h": 6,
        "n_positions_over_600km_total": int(over.sum()),
        "n_strict_clusters_gap_over_6h": len(clusters),
        "n_events_after_window_merge": 3,
        "positions_per_window": n_win,
        "gap_between_main_cluster_and_two_point_tail_h": round(gap_h_main_to_tail, 1),
        "note": "A strict gap-over-6-h clustering gives 4 clusters: the first event splits into a 1,060-point main cluster and a 2-point tail 7.8 h later (18 June 12:56 to 12:57 UTC), both inside the hand-set window of event one. The window merges them, hence 3 events.",
        "clusters": clusters,
        "n_days_with_daily_max_over_600km": res["d_daily_max"]["n_days_over_600km"],
    }
    path.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("i_uptime_split", "j_common_fleet_unified", "k_duct_criterion")}, indent=1))


if __name__ == "__main__":
    if "--poster" in sys.argv:
        poster_revision()
    else:
        main()
