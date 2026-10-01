# OpenSky Symposium 2026: local observations through 30 September

This bundle adds Era B and the antenna comparison to the historical Era A materials.
It contains the four-page JOAS poster short paper, aggregated results, analysis source code, vector figure PDFs and the A0 poster. The raw observations are published separately as dataset v1.0.0, DOI 10.5281/zenodo.23090597; code and aggregate results are archived as v5.0.0, DOI 10.5281/zenodo.23089559. The updated manuscript and poster are subsequent Git changes, not additions to the older code archive.

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

## Build the short paper and validate the submission

Run `bash build.sh` in this directory (TeX Live with pdflatex and biber).
Run `bash qa.sh` to build/check both the four-page paper and the A0 poster.
The JOAS class uses `manuscript=poster`, `layout=preprint` and `The 14th OpenSky Symposium`.
All numeric macros are embedded in main.tex for submission; numbers.tex remains the poster input.
The paper retains the template's magenta headings and links, with black body text.

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

The raw traces are publicly downloadable from https://doi.org/10.5281/zenodo.23090597.
See [data/archive/README.txt](data/archive/README.txt) for archive hashes, exact date windows and restoration commands. [data/archive/dataset-manifest.json](data/archive/dataset-manifest.json) records the published DOI and archive inventory. Restore the Era A archive and all eight Era B ZIP parts into this directory to populate `data/dados/era_a` and `data/dados/era_b`. Generated arrays and aircraft-index caches remain outside Git.
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
- Receiver uptime uses outage durations. The operator reports occasional power loss, post-update k3s conflicts and USB SDR-stick overheating, without event-by-event attribution.
- The last 33 days of Era B came from live receiver history without a source checksum. This release's checksums verify exported files, not that missing source provenance.

## Archive and QR

Both QR codes point to the public raw dataset version 1.0.0: https://doi.org/10.5281/zenodo.23090597.
The short paper separately cites analysis code and aggregate results version v5.0.0: https://doi.org/10.5281/zenodo.23089559.
Neither DOI identifies the JOAS publication of the paper. Latest manuscript/poster edits are later Git changes and do not alter either immutable archive's contents.

## References and licensing

The repository's existing regulatory checklist remains available. Code and verification scripts use MIT; the dataset and its documentation use CC BY 4.0. The dataset README defines the scopes explicitly.
Regional/context inputs follow the source annotations in `numbers.json`: Idec (2023), ANEEL (2026), ANATEL 715/2019, LGPD (2018), DECEA (2022/2024), and Portaria MF 1.342/2026.
This export preserves the submitted research inputs; it is not an external legal or fiscal re-audit.
