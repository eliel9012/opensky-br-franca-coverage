[![DOI](https://zenodo.org/badge/1239286292.svg)](https://doi.org/10.5281/zenodo.20601872)

# OpenSky BR Franca Coverage

This repository contains the final ADS-B-only local coverage figure and reproducibility materials for the abstract:

**Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations**

Author: Eliel Felipe Junior  
Sensor: `-1408044782`  
Location context: Franca, Sao Paulo State, Brazil

## Context

This repository accompanies an abstract being prepared for submission to the 14th OpenSky Symposium, hosted by CRIDA in Madrid (29–30 October 2026), as a community-contributor submission. The abstract submission deadline is 31 July 2026.

It provides the local ADS-B coverage figure, metrics, and reproducibility materials supporting that submission, so readers arriving from GitHub or search engines can understand the purpose of the repository. The current recommended figure uses a fixed 32-day Era A window from 2026-04-13 to 2026-05-14 23:59:59Z, before the antenna swap on 2026-05-16.

## Citation

```bibtex
@misc{felipe2026openskyfranca,
  author = {Eliel Felipe Junior},
  title = {Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations},
  year = {2026},
  version = {v4.0.0},
  doi = {10.5281/zenodo.20601872},
  url = {https://doi.org/10.5281/zenodo.20601872},
  note = {Companion materials to a community-contributor abstract submitted to the 14th OpenSky Symposium 2026}
}
```

## Scope

The figure is an operational indicator derived from local receiver logs. It is not a network-wide OpenSky coverage claim.

The current fixed-window figure:

- uses local `tar1090` / `readsb` `trace_full_*.json` files from an ultrafeeder stack;
- keeps ADS-B source types only: `adsb_icao` and `adsb_icao_nt`;
- excludes MLAT-derived positions;
- computes metrics over all valid ADS-B positions in the processed trace files;
- rounds receiver coordinates to two decimal places for privacy.

## Recommended Figure

Use `coverage_era_a_2026-04-13_to_2026-05-14.pdf` for LaTeX if the template accepts PDF figures. Use `coverage_era_a_2026-04-13_to_2026-05-14.png` otherwise.

The previous `coverage_map_v3_hexbin.pdf` figure is retained as historical material. The v3 figure used a window that ended in the middle of 2026-05-14. The current figure uses the complete fixed window through 2026-05-14 23:59:59Z, resulting in slightly larger and more precise counts.

## Main Metrics

- Observation window: 2026-04-13 to 2026-05-14, 32 calendar days inclusive
- Trace files processed: 20,923
- Valid ADS-B positions: 5,153,167
- Unique aircraft: 2,890
- Median range: 189.3 km
- P95 range: 299.7 km
- Max observed range: 510.3 km
- MLAT-derived positions excluded
- ADS-B source types retained: `adsb_icao` and `adsb_icao_nt`
- Processed trace file size on disk: approximately 133 MiB

## Files

- `coverage_era_a_2026-04-13_to_2026-05-14.pdf` / `.png`: current recommended abstract figure.
- `coverage_era_a_2026-04-13_to_2026-05-14.md`: fixed-window audit report and metrics.
- `figure_metrics_era_a.json`: machine-readable metrics and provenance for the current figure.
- `generate_era_a_fixed_window.py`: reproducible script for the fixed-window Era A figure.
- `coverage_map_v3_hexbin.pdf` / `.png`: previous v3 figure, retained for historical comparison.
- `figure_metrics_v3.json`: historical v3 metrics and provenance.
- `coverage_map_methods_v3.md`: historical v3 methods and limitations.
- `coverage_map_caption_v3.txt`: historical v3 proposed caption.
- `generate_coverage_figure_v3.py`: historical v3 reproducible script.
- `regulatory_checklist_br.md`: Brazilian regulatory touchpoints for volunteer ADS-B reception.

## Reproduce

The command below assumes the local receiver history is available at `/opt/adsb/ultrafeeder/globe_history`.

Current fixed-window Era A figure:

```bash
python3 generate_era_a_fixed_window.py
```

Historical v3 figure:

```bash
./generate_coverage_figure_v3.py \
  --input-dir /opt/adsb/ultrafeeder/globe_history \
  --output-dir . \
  --receiver-lat -20.51 \
  --receiver-lon -47.40 \
  --sensor-id=-1408044782 \
  --hexbin-gridsize 80 \
  --readsb-version 'readsb version: 3.16.14 wiedehopf git: b80c737 (committed: Mon May 4 20:10:25 2026 0000)' \
  --ultrafeeder-image 'ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:telegraf-build-925 sha256:b92424afd43db56d13296467c90782dc1b5bee187b59724f6db02ea09ff609f6'
```

## Privacy and Limitations

Receiver coordinates are rounded to two decimal places in public outputs. The resulting systematic distance error is approximately within +/-1 km and does not affect the kilometer-level metrics reported here.

The map shows observed local ADS-B position reports, not guaranteed coverage over every point in the region. Aircraft density is affected by traffic patterns, altitude, terrain, antenna installation, receiver configuration, and data-retention behavior.

## Regulatory Context

A separate document maps the regulatory touchpoints relevant to volunteer ADS-B reception in Brazil, including ANATEL, ANAC, DECEA, and the Brazilian General Data Protection Law. See `regulatory_checklist_br.md`.
