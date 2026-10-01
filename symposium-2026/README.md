# OpenSky Symposium 2026: local observations through 30 September

This bundle adds Era B and the antenna comparison to the historical Era A materials.
It contains aggregated results, the analysis source code, vector figure PDFs and the A0 poster.
The short paper is deliberately not included: the author will update it after this data release receives its version DOI.

## Windows and results

| Metric | Era A | Era B paired | Era B full |
| :-- | --: | --: | --: |
| Days | 32 | 32 | 137 |
| ADS-B positions | 5,153,167 | 8,123,970 | 36,535,422 |
| Aircraft | 2,890 | 3,159 | 4,925 |
| Median range (km) | 189.3 | 224.0 | 222.0 |
| P95 range (km) | 299.7 | 350.6 | 350.1 |

Era A: 2026-04-13 to 2026-05-14. Antenna replacement: 2026-05-16 at 21:35 UTC.
Era B: from that instant through 2026-09-30; 137 elapsed days span 138 calendar dates.
The 32-day paired B window ends at 2026-06-17T21:35Z (exclusive).
Only adsb_icao and adsb_icao_nt are retained. MLAT is excluded. Receiver coordinates are rounded to (-20.51, -47.40).

Common fleet: 2,234 aircraft in A and paired B, pooled position-range means 188.5 to 217.9 km (+15.6%).
Receiver uptime: 99.54%, inferred from the two confirmed receiver outages; reception continuity: 99.33%.
40 gaps exceed 120 s; 19 start between 05:00 and 07:00 UTC. No receiver statistics distinguish the night gaps from an empty observable sky.
Three ducting event windows: 16 to 18 June, 15 August, 25 August; maximum 786.3 km, or 599.9 km outside those windows.
This is one local receiver, not a network-wide OpenSky coverage claim.

## Canonical inputs and aggregate outputs

- `numbers.json`: canonical values, source annotations and frozen flags.
- `numbers.tex`: generated macros shared with the local manuscript and poster.
- `analysis/new_metrics.json`: existing consistency checks, daily maxima, gaps, common-fleet definitions and duration audit.
- `analysis/azimuth_range_by_bin.json`: share of positions and P95 range by azimuth.
- `analysis/external_inputs.json`: regional power and illustrative import inputs.
- `data/relatorios/figure_metrics_era_b.json`: existing Era B report metrics and daily series.
- `figures/`: the existing scientific figures; filtered common-fleet histogram is supporting material, not the +15.6% headline definition.
- `poster/`: selected navy-sidebar design in editable LaTeX and compiled A0 PDF.

No measurements or scientific results were recalculated for this release export.

## Build the poster

Requirements: a TeX installation with tikzposter, qrcode, Helvetica, anyfontsize, booktabs and ragged2e; Poppler (`pdfinfo`, `pdftotext`); Python 3.
The supplied figure PDFs allow compilation without the raw observations.

```sh
cd symposium-2026
bash poster/build.sh
```

The build checks canonical-number usage, compiles twice, rejects layout/font warnings and verifies one A0 portrait page.
It never rebuilds the short paper. All fonts are embedded in the supplied poster.
The blue FRC star is a poster-only vector recoloring; the shared source figure is unchanged.
To regenerate that copy, install pypdf and run `python3 poster/recolor_receiver.py`.
`poster/generate_assets.py` produces the optional side-by-side azimuth layout from existing aggregate data; the selected sidebar poster uses the original stacked plot.

## Reproduce the scientific analysis

This public package contains aggregates and scripts, not the raw trace records or aircraft-index caches.
Recomputing from observations requires the author's raw inputs under `data/dados/era_a` and `data/dados/era_b`.
With those inputs available, the existing pipeline is:

```sh
python3 data/scripts/build_dataset.py
python3 data/scripts/compute_metrics.py
python3 scripts/compute_new_metrics.py
python3 scripts/compute_new_metrics.py --poster
```

These commands regenerate metrics and require the full datasets; they were NOT run as part of the visual redesign.
`python3 scripts/gen_numbers_tex.py` regenerates only numbers.tex from the canonical numbers.json.
The optional `--build` mode also reconstructs numbers.json; use it only for an intentional audited scientific update.
Figure-specific scripts under `scripts/` use the resulting arrays; the color and density rules are recorded in `scripts/style.py`.

## Known distinctions and provenance limits

- Common-fleet pooled means differ from the average of per-aircraft means; the filtered histogram has 2,176 aircraft.
- Three event windows contain four strict clusters separated by more than six hours. June's two-point tail belongs to the same declared event window.
- The 599.9 km maximum excludes event windows; excluding entire event days instead gives 581.4 km.
- The old 38-night-gaps claim is retained as a historical audit field; the current start-hour count is 19.
- Receiver uptime uses outage durations; outage causes have not been established.
- The last 33 days of Era B came from live receiver history without a source checksum. This release's checksums verify exported files, not that missing source provenance.

## Archive and QR

The poster QR uses the all-versions DOI https://doi.org/10.5281/zenodo.20192179.
Before the new release is archived, that link still leads to v4.0.1, with data only through May.
After archiving, verify the latest record contains this September bundle. The short paper must cite that new version DOI explicitly for reproducibility.
The banner's full-paper label is intended for the completed symposium package; this data-first release does not yet contain the revised paper.
Do not treat the DOI as updated merely because the QR scans or a Git push succeeded.

## References and licensing

The repository's existing regulatory checklist and license remain applicable.
Regional/context inputs follow the source annotations in `numbers.json`: Idec (2023), ANEEL (2026), ANATEL 715/2019, LGPD (2018), DECEA (2022/2024), and Portaria MF 1.342/2026.
This export preserves the submitted research inputs; it is not an external legal or fiscal re-audit.
