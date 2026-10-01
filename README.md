# OpenSky BR Franca Coverage

Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations.

[![Code DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23089559.svg)](https://doi.org/10.5281/zenodo.23089559)
[![Dataset DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23090597.svg)](https://doi.org/10.5281/zenodo.23090597)

Author: Eliel Felipe Junior, ORCID 0000-0002-6333-1187. Independent contributor, OpenSky Network community, Franca, Brazil.
14th OpenSky Symposium, Madrid, 29 to 30 October 2026.

## Paper, poster and reproducibility

- [Four-page JOAS poster short paper](symposium-2026/main.pdf), including references.
- [A0 poster PDF](symposium-2026/poster/poster.pdf).
- [Source, build and analysis instructions](symposium-2026/README.md).
- [Raw receiver traces, dataset v1.0.0](https://doi.org/10.5281/zenodo.23090597).
- [Archive verification and restoration](symposium-2026/data/archive/README.txt).
- [Analysis code and aggregate results, v5.0.0](https://doi.org/10.5281/zenodo.23089559).
- [Canonical metrics and provenance](symposium-2026/numbers.json).
- [Era B detailed metrics](symposium-2026/data/relatorios/figure_metrics_era_b.json).
- [Brazilian regulatory checklist](regulatory_checklist_br.md).

The current manuscript and updated poster cite both published deposits. Their latest text and QR updates are later Git changes, not files contained in the immutable v5.0.0 code archive. Neither DOI is a JOAS publication DOI for the paper.

## Scope

Local readsb receiver traces through 30 September 2026. The scientific analysis keeps direct ADS-B sources (adsb_icao and adsb_icao_nt) and excludes MLAT. Raw archives preserve all recorded source types and aircraft metadata. One receiver's observations do not measure network-wide OpenSky coverage.
The paper records the author-supplied antenna location and hardware; distance calculations retain the rounded analysis origin (-20.51, -47.40).

Raw traces are publicly archived on Zenodo and are not stored in Git. One Era A ZIP and eight independent Era B ZIP parts contain 123,337 traces and 1,141,762,896 original gzip bytes. Download all nine ZIPs, verify their hashes and restore them according to the dataset instructions. No binary concatenation is needed. Generated position arrays and aircraft-index caches are rebuilt locally.
The last 33 days of Era B lack original-receiver checksums; export checksums do not resolve that provenance limitation.

## Citation and licenses

For raw observations, cite dataset version 1.0.0: DOI [10.5281/zenodo.23090597](https://doi.org/10.5281/zenodo.23090597).
For the archived analysis code and aggregate results, cite v5.0.0: DOI [10.5281/zenodo.23089559](https://doi.org/10.5281/zenodo.23089559). CITATION.cff includes both references.
The paper and poster QR codes point to dataset version 1.0.0.
Dataset and dataset documentation: CC BY 4.0. Repository code and verification scripts: MIT. See the dataset README for the explicit scope and software license text.

## Historical Era A materials

Root-level coverage maps, reports and scripts are retained as historical material.
The fixed Era A window is 13 April through 14 May: 5,153,167 valid positions, 2,890 aircraft, median 189.3 km, P95 299.7 km, maximum 510.3 km.
The earlier v3 maps use a different end time and must not be mixed with the fixed-window comparison.
The preceding code release was [v4.0.1](https://doi.org/10.5281/zenodo.20601952); older releases remain citable historical records.
[Code archive, all versions](https://doi.org/10.5281/zenodo.20192179). [Dataset, all versions](https://doi.org/10.5281/zenodo.23090596).
