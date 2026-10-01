#!/usr/bin/env python3
"""Generate numbers.tex from numbers.json (single source of data values).

Usage:
  python3 scripts/gen_numbers_tex.py            # numbers.json -> numbers.tex
  python3 scripts/gen_numbers_tex.py --build    # rebuild numbers.json first, then numbers.tex

--build composes numbers.json from (1) the frozen values typed below, (2) the
external inputs in analysis/external_inputs.json, (3) the computed values in
analysis/new_metrics.json (run scripts/compute_new_metrics.py first).

numbers.json layout: {"macros": {"<camelCaseName>": {"value": "...", "source": "...", "frozen": bool}}, ...}
Macro names are letters only (LaTeX). Values are plain text, thousands separators
written as "2,890". Percent signs are not stored in values; write \\% in the paper.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUMBERS_JSON = ROOT / "numbers.json"
NUMBERS_TEX = ROOT / "numbers.tex"
NEW_METRICS = ROOT / "analysis" / "new_metrics.json"
EXTERNAL = ROOT / "analysis" / "external_inputs.json"

NAME_RE = re.compile(r"^[A-Za-z]+$")
LATEX_ESC = {
    "\\": r"\textbackslash{}",
    "%": r"\%",
    "#": r"\#",
    "&": r"\&",
    "_": r"\_",
    "$": r"\$",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def esc(s: str) -> str:
    return "".join(LATEX_ESC.get(c, c) for c in s)


def fmt_int(n) -> str:
    return f"{int(n):,}"


def fmt1(x) -> str:
    return f"{float(x):.1f}"


# ==== ====
# Build numbers.json
# ==== ====
def build_macros() -> dict:
    m: dict[str, dict] = {}

    def add(name, value, source, frozen=False):
        assert NAME_RE.match(name), name
        assert name not in m, f"duplicate macro {name}"
        m[name] = {"value": str(value), "source": source, "frozen": bool(frozen)}

    nm = json.loads(NEW_METRICS.read_text(encoding="utf-8"))
    ext = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    FZ = "frozen headline, analysis/RULES.md rule 1 (reproduced from npz in analysis/new_metrics.json step1)"
    BR = "computed, analysis/new_metrics.json"

    # ==== swap and era windows (frozen) ====
    add("swapDate", "2026-05-16", FZ, True)
    add("swapTimeUtc", "21:35", FZ, True)
    add("swapTimeBrt", "18:35", "swap 21:35 UTC minus 3 h", True)
    add("eraAStart", "2026-04-13", FZ, True)
    add("eraAEnd", "2026-05-14", FZ, True)
    add("eraBStart", "2026-05-16", "first calendar date of Era B (partial day, swap 21:35 UTC); paper draft had a TODO for 2026-05-17", True)
    add("eraBEnd", "2026-09-30", FZ, True)
    add("eraBPairedEnd", "2026-06-17", "swap + 32 d = 2026-06-17T21:35Z (exclusive)", True)
    add("eraBLiveStart", "2026-08-29", "last 33 days processed from live receiver history (paper limitations)", True)
    add("eraBLiveDays", "33", "2026-08-29 to 2026-09-30 inclusive, data/contexto_analise_adsb.md section 4", True)
    add("eraADays", "32", FZ, True)
    add("eraBPairedDays", "32", FZ, True)
    add("eraBFullDays", "137", FZ, True)
    h = nm["h_era_b_duration"]
    add("eraBHours", fmt1(h["hours"]), "computed: 2026-05-16T21:35Z to 2026-10-01T00:00Z, new_metrics h_era_b_duration", True)
    add("eraBCalendarDates", h["calendar_dates_inclusive_16_05_to_30_09"], "calendar dates 16/05 to 30/09 inclusive (16/05 partial), new_metrics h_era_b_duration")
    add("eraBFirstPointUtc", h["first_observed_point_utc"][11:16], "first observed Era B point, new_metrics h_era_b_duration")

    # ==== era table (frozen) ====
    add("eraAPositions", "5,153,167", FZ, True)
    add("eraBPairedPositions", "8,123,970", FZ, True)
    add("eraBFullPositions", "36,535,422", FZ, True)
    add("eraAAircraft", "2,890", FZ, True)
    add("eraBPairedAircraft", "3,159", FZ, True)
    add("eraBFullAircraft", "4,925", FZ, True)
    add("eraAMedian", "189.3", FZ, True)
    add("eraBPairedMedian", "224.0", FZ, True)
    add("eraBFullMedian", "222.0", FZ, True)
    add("eraAPNinetyFive", "299.7", FZ, True)
    add("eraBFullPNinetyFive", "350.1", FZ, True)
    add("eraBFullPNinetyFiveRounded", "350", "paper text rounding of 350.1", True)
    add("eraAMax", "510.3", FZ, True)
    add("eraBFullMax", "786.3", FZ, True)
    add("eraBFullMaxNoDucting", "599.9", FZ, True)
    ap = nm["a_paired"]
    add("eraBPairedPNinetyFive", fmt1(ap["p95_km"]), "computed, new_metrics a_paired (matches the earlier report, 350.6)")
    add("eraBPairedMax", fmt1(ap["max_km"]), "computed, new_metrics a_paired (includes the 17 June ducting event)")

    # ==== gains ====
    g = nm["g_gains"]
    add("posGain", fmt1(g["positions_gain_pct_exact"]), "computed exact 57.6500 percent rounded to 1 dp (paper draft had 57.6; earlier report 57.7), new_metrics g_gains")
    add("posGainExact", f"{g['positions_gain_pct_exact']:.2f}", "computed exact, new_metrics g_gains")
    add("aircraftGain", fmt1(g["aircraft_gain_pct_exact"]), "computed exact 9.308 percent rounded to 1 dp, new_metrics g_gains")

    # ==== common fleet ====
    add("commonFleetN", "2,234", FZ, True)
    add("commonFleetMeanA", "188.5", FZ, True)
    add("commonFleetMeanB", "217.9", FZ, True)
    add("commonFleetGain", "15.6", FZ, True)
    f = nm["f_common_fleet_deltas"]
    NEW = "NEW (not frozen): common fleet without military/state aircraft, new_metrics f_common_fleet_deltas"
    add("commonFleetMilExcluded", fmt_int(f["n_excluded_military_state"]), NEW)
    add("commonFleetPlotted", fmt_int(f["n_plotted"]), NEW)
    add("commonFleetDeltaMedian", fmt1(f["delta_median_km"]), NEW)
    add("commonFleetDeltaMean", fmt1(f["delta_mean_km"]), NEW)
    add("commonFleetDeltaPositivePct", fmt1(f["share_delta_positive_pct"]), NEW)
    add("commonFleetPlottedMeanA", fmt1(f["mean_range_a_km_plotted"]), NEW)
    add("commonFleetPlottedMeanB", fmt1(f["mean_range_b_km_plotted"]), NEW)
    add("commonFleetDeltaPFive", fmt1(f["delta_p5_km"]), NEW)
    add("commonFleetDeltaPNinetyFive", fmt1(f["delta_p95_km"]), NEW)
    # poster revision: unified definitions (new_metrics j_common_fleet_unified)
    jf = nm["j_common_fleet_unified"]["filtered_no_military"]
    ja = nm["j_common_fleet_unified"]["frozen_all_2234"]
    assert (ja["pooled_mean_a_km"], ja["pooled_mean_b_km"], ja["pooled_gain_pct"]) == (188.5, 217.9, 15.6)
    assert jf["n_aircraft"] == f["n_plotted"]
    assert (jf["per_aircraft_mean_a_km"], jf["per_aircraft_mean_b_km"]) == (f["mean_range_a_km_plotted"], f["mean_range_b_km_plotted"])
    PR = "NEW (poster revision, not frozen), new_metrics j_common_fleet_unified"
    add("commonFleetMeanDefinition", "mean of all position ranges", "definition behind the frozen commonFleetMeanA/B and commonFleetPlottedPooledMeanA/B (pooled over every valid position of the aircraft set, Era A vs Era B paired)")
    add("commonFleetPlottedMeanDefinition", "mean of per-aircraft mean ranges", "definition behind commonFleetPlottedMeanA/B and the delta histogram (each aircraft weighted once)")
    add("commonFleetPlottedPooledMeanA", fmt1(jf["pooled_mean_a_km"]), PR + " filtered_no_military pooled mean, Era A (same definition as frozen 188.5)")
    add("commonFleetPlottedPooledMeanB", fmt1(jf["pooled_mean_b_km"]), PR + " filtered_no_military pooled mean, Era B paired (same definition as frozen 217.9)")
    add("commonFleetPlottedPooledGain", fmt1(jf["pooled_gain_pct"]), PR + " percent change of the pooled means, military/state excluded")
    add("commonFleetPlottedGain", fmt1(jf["per_aircraft_gain_pct"]), PR + " percent change of commonFleetPlottedMeanA/B (per-aircraft means), military/state excluded")

    # ==== continuity (frozen claims and data) ====
    c = nm["c_gaps"]
    add("uptimePct", "99.33", FZ, True)
    add("gapCount", "40", FZ, True)
    add("gapThresholdS", "120", "gap threshold in seconds on merged sorted timestamps, compute_metrics.py", True)
    add("gapNightFrozen", "38", "frozen user claim: 38 of 40 gaps between 05 and 07 UTC (DOES NOT match data)", True)
    add("gapNightData", c["start_in_05_07_utc"], "data: gaps whose start hour is in [05,07) UTC, new_metrics c_gaps")
    add("gapNightOverlapData", c["overlap_05_07_utc"], "data: gaps overlapping [05:00,07:00) UTC at all, new_metrics c_gaps")
    add("gapOutageCount", "2", "frozen: 2 real outages", True)
    add("gapOverSixtyCount", c["bucket_counts"][">60min"], "data: gaps longer than 60 min, new_metrics c_gaps")
    add("gapShortCount", c["bucket_counts"]["<15min"], "data: gaps shorter than 15 min, new_metrics c_gaps")
    add("gapMidCount", c["bucket_counts"]["15-60min"], "data: gaps 15 to 60 min, new_metrics c_gaps")
    add("gapDowntimeHours", f"{c['total_downtime_h']:.2f}", "data: total downtime in hours, new_metrics c_gaps", True)
    add("gapWindowHours", fmt1(c["window_span_h"]), "data: Era B span in hours, new_metrics c_gaps", True)
    # poster revision: receiver uptime (2 confirmed outages) vs reception continuity (all gaps)
    us = nm["i_uptime_split"]
    assert us["reception_continuity_pct"] == 99.33 and us["n_reception_gaps_other"] == c["n_gaps"] - 2
    assert us["n_other_start_05_07_utc"] == c["start_in_05_07_utc"]
    PU = "NEW (poster revision), new_metrics i_uptime_split; fallback method: no readsb stats in data/, Pi unreachable; receiver uptime = 1 - confirmed outage duration / Era B window"
    add("receiverUptimePct", f"{us['receiver_uptime_pct']:.2f}", PU)
    add("receiverDowntimeHours", f"{us['receiver_downtime_h']:.2f}", PU + "; outages 2026-07-06 19:08:50 to 07-07 00:21:09 UTC and 2026-08-02 02:47:52 to 12:35:07 UTC, durations from the gap list in seconds")
    add("receptionUptimePct", f"{us['reception_continuity_pct']:.2f}", "reception continuity: all 40 gaps above 120 s counted as downtime; equals frozen uptimePct, new_metrics i_uptime_split")
    add("receptionGapOtherCount", us["n_reception_gaps_other"], "reception gaps other than the two outages, new_metrics i_uptime_split")
    add("receptionGapOtherHours", f"{us['reception_gap_other_h']:.2f}", "total duration of reception gaps not attributed to the two outages, new_metrics i_uptime_split")
    add("receptionGapOffNightCount", us["n_other_not_05_07_utc"], "reception gaps other than the outages that start outside 05 to 07 UTC (includes the 30 August 64 min gap), new_metrics i_uptime_split")
    hh = nm["e_gap_start_hour_hist_utc"]
    add("gapHourFiveCount", hh[5], "data: gaps starting 05 UTC, new_metrics e_gap_start_hour_hist_utc")
    add("gapHourSixCount", hh[6], "data: gaps starting 06 UTC, new_metrics e_gap_start_hour_hist_utc")
    add("gapNightStartUtc", "05:00", "night window start used in the claim", True)
    add("gapNightEndUtc", "07:00", "night window end used in the claim", True)
    add("gapNightStartBrt", "02:00", "05:00 UTC minus 3 h", True)
    add("gapNightEndBrt", "04:00", "07:00 UTC minus 3 h", True)
    add("gapOverstateFactor", "20", "frozen draft: 40 gaps over 2 outages", True)
    o = {x["start_utc"][:10]: x for x in c["gaps_over_60min"]}
    add("outageJulDate", "6 July", "outage start 2026-07-06T19:08:50Z", True)
    add("outageJulHours", "5", "5 h 12 min", True)
    add("outageJulMinutes", "12", "5 h 12 min", True)
    add("outageAugDate", "2 August", "outage start 2026-08-02T02:47:52Z", True)
    add("outageAugHours", "9", "9 h 47 min", True)
    add("outageAugMinutes", "47", "9 h 47 min", True)
    add("gapBucketShortMin", "15", "bucket boundary in minutes: gaps shorter than 15 min, new_metrics c_gaps bucket_counts")
    add("gapBucketLongMin", "60", "bucket boundary in minutes: gaps longer than 60 min, new_metrics c_gaps bucket_counts")
    out_min = 5 * 60 + 12 + 9 * 60 + 47
    out_h = out_min / 60.0
    add("outageTotalHours", f"{out_h:.0f}", "5 h 12 min + 9 h 47 min = 14 h 59 min = 14.98 h, rounded to hours (frozen outages)")
    add("outageTotalHoursExact", f"{out_h:.2f}", "5 h 12 min + 9 h 47 min in hours (frozen outages)")
    add("outageAnnualHours", f"{out_h / (h['hours'] / 24.0) * 365:.0f}", "arithmetic check: outage hours per Era B day times 365, NOT used as an annual estimate: the observation period is not a representative year")
    third = o["2026-08-30"]
    add("gapThirdDate", "30 August", "third gap over 60 min, start 2026-08-30T15:39:21Z, new_metrics c_gaps")
    add("gapThirdMinutes", f"{third['duration_min']:.0f}", "duration in min rounded, new_metrics c_gaps")

    # ==== ducting ====
    d = nm["d_daily_max"]
    add("ductThresholdKm", "600", FZ, True)
    add("ductEventCount", "3", FZ, True)
    add("ductEventOneDates", "16 to 18 June", FZ, True)
    add("ductEventOnePoints", "1,060", "more than 1,060 points, " + FZ, True)
    add("ductEventTwoDate", "15 August", FZ, True)
    add("ductEventThreeDate", "25 August", FZ, True)
    add("ductPositionsTotal", fmt_int(d["n_positions_over_600km_in_ducting_windows"]), "positions over 600 km inside the three windows, new_metrics d_daily_max")
    kd = nm["k_duct_criterion"]
    assert kd["threshold_km"] == 600 and kd["n_positions_over_600km_total"] == d["n_positions_over_600km_in_ducting_windows"]
    KD = "NEW (poster revision), new_metrics k_duct_criterion"
    add("ductClusterGapHours", kd["cluster_gap_h"], KD + "; positions over ductThresholdKm clustered, a gap above this many hours starts a new cluster; windows in TROPO_DUCT_WINDOWS delimit the clusters")
    add("ductClusterStrictCount", kd["n_strict_clusters_gap_over_6h"], KD + "; strict gap-over-6-h clusters (the 2-point tail on 18 June 7.8 h after the main cluster is merged into event one by its window)")
    add("ductEventOneWindowPoints", fmt_int(kd["positions_per_window"]["1"]), KD + "; positions over 600 km inside the event-one window (1,060 main cluster plus 2)")
    import datetime as _dt
    mx = max(d["days_over_600km"], key=lambda r: r["max_km"])
    _d = _dt.date.fromisoformat(mx["date"])
    add("eraBMaxDate", f"{_d.day} {_d.strftime('%B')}", "UTC day of the Era B maximum range (786.3 km), new_metrics d_daily_max days_over_600km")
    add("dailyMaxEvents", d["n_days_over_600km"], "POSTER: UTC days with daily max over 600 km, new_metrics d_daily_max")
    add("dailyMaxNonDuctDayMax", fmt1(d["max_over_non_ducting_days_km"]), "POSTER: largest daily max on days outside ducting windows, new_metrics d_daily_max")
    add("dailyMaxDays", d["n_days"], "UTC calendar days with Era B data, new_metrics d_daily_max")

    # ==== azimuth ====
    az = json.loads((ROOT / "analysis" / "azimuth_range_by_bin.json").read_text(encoding="utf-8"))
    lo, hi = az["blind_sector_deg"]
    i0, i1 = az["bins_deg"].index(lo), az["bins_deg"].index(hi)
    for era, key in (("A", "era_a_counts"), ("B", "era_b_counts")):
        cnt = az[key]
        add(f"blindSectorShareEra{era}", fmt1(100.0 * sum(cnt[i0:i1]) / sum(cnt)), "computed: share of positions in the 290 to 350 deg sector, analysis/azimuth_range_by_bin.json era counts, 10 degree bins")
    add("azimuthBinDeg", "10", "azimuth bin width in degrees, analysis/azimuth_range_by_bin.json binning")
    add("blindSectorStart", "290", FZ, True)
    add("blindSectorEnd", "350", FZ, True)
    add("peakSectorStart", "140", FZ, True)
    add("peakSectorEnd", "200", FZ, True)

    # ==== method ====
    add("recvLat", "-20.51", "receiver latitude rounded, RULES.md rule 2", True)
    add("recvLon", "-47.40", "receiver longitude rounded, RULES.md rule 2", True)
    add("earthRadiusKm", "6371.0088", "haversine radius, RULES.md rule 2", True)
    add("hexbinRingOneKm", "100", "range rings drawn in figures/coverage_era_b_hexbin.pdf, scripts/fig_coverage_hexbin.py")
    add("hexbinRingTwoKm", "250", "range rings drawn in figures/coverage_era_b_hexbin.pdf, scripts/fig_coverage_hexbin.py")
    add("hexbinRingThreeKm", "500", "range rings drawn in figures/coverage_era_b_hexbin.pdf, scripts/fig_coverage_hexbin.py")
    add("recvRoundingErrorKm", "1", "paper text: about 1 km", False)
    add("antennaAltitude", "1,030", "antenna altitude above mean sea level confirmed by author, 2026-10-01")
    add("francaUrbanElevation", "1,040", "Prefeitura Municipal de Franca, Plano de Contingencia de Defesa Civil: Estiagem, edition 2026/2027, section B.3, p. 7; approximate city elevation, distinct from the antenna altitude")
    add("antennaHeightAgl", "4", "antenna height above ground confirmed by author, 2026-10-01")
    add("sdrModel", "AirNav ADS-B 1090 MHz FlightStick", "SDR model confirmed by author, 2026-10-01")
    add("sensorSerial", "-1408044782", "OSN serial, data/contexto_analise_adsb.md", True)
    add("readsbVersion", "3.16.14", "version string in trace files, data/scripts raw trace_full header")
    add("osnRefRangeLow", "400", "OSN reference range, paper text (olive2023report)", False)
    add("osnRefRangeHigh", "500", "OSN reference range, paper text (olive2023report)", False)

    # ==== Brazilian ICAO block ====
    b = nm["b_brazil_block"]
    add("brBlockStart", "E40000", "Brazilian ICAO 24-bit block start, paper text", True)
    add("brBlockEnd", "E7FFFF", "Brazilian ICAO 24-bit block end, paper text", True)
    add("brAircraftCount", fmt_int(b["era_b_aircraft_in_block"]), BR + " b_brazil_block")
    add("brAircraftShare", fmt1(b["era_b_aircraft_share_pct"]), BR + " b_brazil_block (of 4,925 Era B aircraft)")
    add("brPositionCount", fmt_int(b["era_b_positions_in_block"]), BR + " b_brazil_block")
    add("brPositionShare", fmt1(b["era_b_positions_share_pct"]), BR + " b_brazil_block (of 36,535,422 Era B positions)")

    # ==== survey ====
    SV = "OSN 2024/2025 user survey as cited in main.tex (inauen2026citizen, osn2025surveyrepo)"
    add("surveyBrazil", "6", SV)
    add("surveyCountryIdentified", "561", SV)
    add("surveyLatam", "11", SV)
    add("surveyNonOwnerReasons", "375", SV)
    add("surveyPowerReasons", "34", SV)
    add("surveyPowerShare", "9.1", SV)
    add("surveyCostReasons", "58", SV + "; non-owner reasons citing cost (task text, frozen external context)", True)
    add("surveyCostShare", "15.5", SV + "; 58 of 375 non-owner reasons (task text, frozen external context)", True)
    add("surveyMalePct", "94", SV)
    add("surveyUniversityPct", "76", SV)

    # ==== power (ANEEL, Idec) ====
    na = ext["national_aneel_2025"]
    add("aneelDec", f"{na['dec']:.2f}", "analysis/external_inputs.json national_aneel_2025")
    add("aneelFec", f"{na['fec']:.2f}", "analysis/external_inputs.json national_aneel_2025")
    add("aneelYear", "2025", "analysis/external_inputs.json national_aneel_2025")
    add("idecYear", "2022", "analysis/external_inputs.json dec_fec_by_region_idec2022")
    for region, key in (("North", "North"), ("CenterWest", "Center-West"), ("Northeast", "Northeast"), ("South", "South"), ("Southeast", "Southeast")):
        r = ext["dec_fec_by_region_idec2022"]["regions"][key]
        add(f"idec{region}Dec", r["dec"], "analysis/external_inputs.json dec_fec_by_region_idec2022 (approximate)")
        add(f"idec{region}Fec", r["fec"], "analysis/external_inputs.json dec_fec_by_region_idec2022 (approximate)")

    # ==== import cost ====
    ik = ext["import_kit"]
    IK = "analysis/external_inputs.json import_kit"
    add("importExemptUsd", "50", "paper text, mf2026portaria")
    add("importMaxUsd", "3,000", "paper text, mf2026portaria")
    add("importDutyPct", "60", "paper text, mf2026portaria")
    add("importDeductionUsd", "30", "paper text, mf2026portaria")
    add("icmsLowPct", "17", "paper text, state ICMS range low")
    add("icmsHighPct", "20", "paper text, state ICMS range high")
    add("importKitUsd", ik["price_usd"], IK)
    add("importDutyUsd", ik["duty_usd"], IK)
    add("importTotalUsd", ik["total_usd"], IK)
    add("importIcmsPct", ik["icms_rate_pct"], IK)
    add("importMarkupPct", ik["markup_pct"], IK)
    # scenario arithmetic computed here, inputs only from external_inputs.json
    rate = ik["icms_rate_pct"] / 100.0
    duty1 = max(ik["price_usd"] * 0.60 - 30.0, 0.0)
    tot1 = (ik["price_usd"] + duty1) / (1 - rate)
    assert round(duty1) == ik["duty_usd"] and abs(tot1 - ik["total_usd"]) <= 1 and round((tot1 / ik["price_usd"] - 1) * 100) == ik["markup_pct"]
    add("importIcmsUsd", f"{tot1 - ik['price_usd'] - duty1:.0f}", "scenario 1 (Remessa Conforme) arithmetic from " + IK + ": total minus price minus duty")
    add("importTotalUsdExact", f"{tot1:.2f}", "scenario 1 arithmetic: (price + duty) / (1 - ICMS rate) from " + IK)
    alt = ext["import_kit_outside_remessa"]
    AK = "scenario supplied by author; arithmetic from analysis/external_inputs.json import_kit_outside_remessa"
    p2 = alt["price_usd"]
    duty2 = p2 * alt["duty_rate_pct"] / 100.0 - alt["deduction_usd"]
    rate2 = alt["icms_rate_pct"] / 100.0
    tot2 = (p2 + duty2) / (1 - rate2)
    icms2 = tot2 - p2 - duty2
    mk2 = (tot2 / p2 - 1) * 100
    assert duty2 == 90 and abs(tot2 - 289.157) < 0.01 and round(icms2) == 49 and round(mk2) == 93
    assert abs(p2 + duty2 + icms2 - tot2) < 1e-9
    add("importAltDutyPct", alt["duty_rate_pct"], AK)
    add("importAltDeductionUsd", alt["deduction_usd"], AK)
    add("importAltDutyUsd", f"{duty2:.0f}", AK)
    add("importAltIcmsUsd", f"{icms2:.0f}", AK)
    add("importAltTotalUsd", f"{tot2:.0f}", AK)
    add("importAltTotalUsdExact", f"{tot2:.2f}", AK)
    add("importAltMarkupPct", f"{mk2:.0f}", AK)
    return m


def build_json() -> None:
    macros = build_macros()
    doc = {
        "macros": macros,
        "notes": "Generated by scripts/gen_numbers_tex.py --build from typed frozen values, analysis/external_inputs.json and analysis/new_metrics.json. Edit the builder, not this file. Author-supplied site coordinates and antenna altitude updated on 2026-10-01. Author confirmed antenna height 4 m above ground on 2026-10-01. Reported interruption causes were occasional power loss, k3s conflicts after updates and USB SDR-stick overheating beyond its operating limit. This is operator testimony; no event-by-event attribution or cause-specific downtime was supplied. Coverage calculations retain the archived rounded receiver coordinates.",
    }
    NUMBERS_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


# ==== ====
# numbers.json -> numbers.tex
# ==== ====
def build_tex() -> None:
    doc = json.loads(NUMBERS_JSON.read_text(encoding="utf-8"))
    macros = doc["macros"]
    lines = [
        "% numbers.tex: GENERATED by scripts/gen_numbers_tex.py from numbers.json. DO NOT EDIT.",
        "% Every data value in the paper and poster is read from these macros.",
    ]
    for name in sorted(macros):
        if not NAME_RE.match(name):
            raise SystemExit(f"invalid macro name: {name}")
        val = macros[name]["value"]
        if not isinstance(val, str):
            raise SystemExit(f"value of {name} must be a string")
        lines.append(f"\\newcommand{{\\{name}}}{{{esc(val)}}}")
    text = "\n".join(lines) + "\n"
    if chr(0x2014) in text or "-" * 3 in text:
        raise SystemExit("forbidden em dash or triple hyphen in output")
    depth = 0
    for ch in text.replace("\\{", "").replace("\\}", ""):
        depth += ch == "{"
        depth -= ch == "}"
        if depth < 0:
            raise SystemExit("unbalanced braces")
    if depth != 0:
        raise SystemExit("unbalanced braces")
    NUMBERS_TEX.write_text(text, encoding="ascii")
    # JOAS submission requires a single main.tex; preserve the canonical generator.
    main = ROOT / "main.tex"
    if main.exists():
        source = main.read_text()
        begin = "% BEGIN GENERATED NUMBERS"
        end = "% END GENERATED NUMBERS"
        if begin in source:
            assert source.count(begin) == source.count(end) == 1
            head, remainder = source.split(begin, 1)
            _, tail = remainder.split(end, 1)
            main.write_text(head + begin + "\n" + text + end + tail)
    print(f"WROTE {NUMBERS_TEX} ({len(macros)} macros)")


if __name__ == "__main__":
    if "--build" in sys.argv:
        build_json()
    build_tex()
