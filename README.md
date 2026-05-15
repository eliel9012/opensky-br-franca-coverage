[![DOI](https://zenodo.org/badge/1239286292.svg)](https://doi.org/10.5281/zenodo.20192180)

# OpenSky BR Franca Coverage

This repository contains the final ADS-B-only local coverage figure and reproducibility materials for the abstract:

**Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations**

Author: Eliel Felipe Junior  
Sensor: `-1408044782`  
Location context: Franca, Sao Paulo State, Brazil

## Context

This repository accompanies an abstract submitted to the OpenSky Symposium 2026.

It provides the local ADS-B coverage figure, metrics, and reproducibility materials supporting that submission, so readers arriving from GitHub or search engines can understand the purpose of the repository.

## Citation

```bibtex
@misc{felipe2026openskyfranca,
  author = {Eliel Felipe Junior},
  title = {Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations},
  year = {2026},
  version = {v3.0.1},
  doi = {10.5281/zenodo.20192180},
  url = {https://doi.org/10.5281/zenodo.20192180},
  note = {Companion materials to a community-contributor abstract submitted to the 14th OpenSky Symposium 2026}
}
```

## Scope

The figure is an operational indicator derived from local receiver logs. It is not a network-wide OpenSky coverage claim.

The v3 figure:

- uses local `tar1090` / `readsb` `trace_full_*.json` files from an ultrafeeder stack;
- keeps ADS-B source types only: `adsb_icao` and `adsb_icao_nt`;
- excludes MLAT-derived positions;
- computes metrics over all valid ADS-B positions in the processed trace files;
- rounds receiver coordinates to two decimal places for privacy.

## Recommended Figure

Use `coverage_map_v3_hexbin.pdf` for LaTeX if the template accepts PDF figures. Use `coverage_map_v3_hexbin.png` otherwise.

## Main Metrics

- Observation window: 2026-04-13 to 2026-05-14, approximately 31 days
- Trace files processed: 20,486
- Valid ADS-B positions: 5,034,865
- Unique aircraft: 2,870
- Median range: 189.4 km
- P95 range: 300.1 km
- Max observed range: 510.3 km
- MLAT-derived positions excluded: 470,426

## Files

- `coverage_map_v3_hexbin.pdf` / `.png`: recommended abstract figure.
- `figure_metrics_v3.json`: metrics and provenance.
- `coverage_map_methods_v3.md`: methods and limitations.
- `coverage_map_caption_v3.txt`: proposed caption.
- `generate_coverage_figure_v3.py`: reproducible script.
- `regulatory_checklist_br.md`: Brazilian regulatory touchpoints for volunteer ADS-B reception.

## Reproduce

The command below assumes the local receiver history is available at `/opt/adsb/ultrafeeder/globe_history`.

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
