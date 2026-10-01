# OpenSky BR Franca Coverage

Operating a Volunteer OpenSky Node in Brazil: Field Notes on Coverage, Uptime, and Local Regulations.
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23089559.svg)](https://doi.org/10.5281/zenodo.23089559)

**September 2026 materials:** [symposium-2026](symposium-2026/README.md).
This update adds the commercial-antenna observations from 16 May through 30 September, the paired comparison, reliability/propagation summaries, analysis scripts and an editable A0 poster.

- [A0 poster PDF](symposium-2026/poster/poster.pdf)
- [Canonical metrics and provenance](symposium-2026/numbers.json)
- [Era B detailed metrics](symposium-2026/data/relatorios/figure_metrics_era_b.json)
- [Build and reproducibility instructions](symposium-2026/README.md)
- [Release notes](RELEASE_NOTES.md)
- [Brazilian regulatory checklist](regulatory_checklist_br.md)
- [Zenodo, all versions](https://doi.org/10.5281/zenodo.20192179)

Author: Eliel Felipe Junior, ORCID 0000-0002-6333-1187. Independent contributor, OpenSky Network community, Franca, Brazil.
14th OpenSky Symposium, Madrid, 29 to 30 October 2026.

## Scope

Local readsb traces, direct ADS-B only (adsb_icao and adsb_icao_nt), MLAT excluded, receiver coordinates rounded for privacy.
One receiver's observations do not measure network-wide OpenSky coverage.
Raw traces and aircraft-index caches are not stored in Git. Two lossless raw-data ZIPs have been prepared locally for a separate Zenodo dataset deposit (123,337 traces; 1,141,762,896 original gzip bytes). See [dataset structure, checksums and restoration instructions](symposium-2026/data/archive/README.txt). The dataset is not yet published and has no assigned DOI; the existing code/aggregate DOI does not contain these ZIPs. Recomputing from raw observations currently requires access to those input archives.
The updated short paper will follow the data release and will cite its specific Zenodo DOI.

## Citation

Use CITATION.cff for author/title/version metadata. For reproducibility, cite the specific DOI assigned by Zenodo to this release after archival, not an older May version.
The all-versions DOI is used for discoverability and the printed QR, not as a replacement for a pinned version citation.

## Historical Era A materials

Existing root-level coverage maps, reports and scripts are retained as historical material.
The fixed Era A window is 13 April through 14 May: 5,153,167 valid positions, 2,890 aircraft, median 189.3 km, P95 299.7 km, maximum 510.3 km.
The earlier v3 maps use a different end time and must not be mixed with the fixed-window comparison.
The preceding release was [v4.0.1](https://doi.org/10.5281/zenodo.20601952); older releases remain citable historical records.
