# Coverage Figure v3 Methods

## Execution
- Execution time: 2026-05-14T22:45:17+00:00
- Host: Pi5
- Platform: Linux-6.12.75+rpt-rpi-2712-aarch64-with-glibc2.41
- Python: 3.13.5
- matplotlib: 3.10.1+dfsg1
- numpy: 2.2.4
- Script SHA256: `155eb9e246cf873419283587806aae05ccb83bad5f2c1f4055029fefea6dfdfe`
- Command: `/home/pi/opensky_coverage_figure_v3/generate_coverage_figure_v3.py --input-dir /opt/adsb/ultrafeeder/globe_history --output-dir /home/pi/opensky_coverage_figure_v3 --receiver-lat -20.51 --receiver-lon -47.40 --sensor-id=-1408044782 --hexbin-gridsize 80 --readsb-version 'readsb version: 3.16.14 wiedehopf git: b80c737 (committed: Mon May 4 20:10:25 2026 0000)' --ultrafeeder-image 'ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:telegraf-build-925 sha256:b92424afd43db56d13296467c90782dc1b5bee187b59724f6db02ea09ff609f6'`

## Input Data
- Input directory: `/opt/adsb/ultrafeeder/globe_history`
- File pattern: `trace_full_*.json`
- Note: files have `.json` extension but are gzip-compressed tar1090/readsb traces.
- Trace files available: 20,486
- Trace files processed: 20,486
- Trace files with ADS-B positions: 18,882
- Processing sample step: 1
- Maximum files option: None
- Total trace rows inspected: 5,505,291

## ADS-B Filter
- Kept source types: adsb_icao, adsb_icao_nt
- Source field equivalence: the tar1090 trace row uses `row[9]` as the source type. Rows with `row[9] == "adsb_icao"` or `row[9] == "adsb_icao_nt"` were treated as ADS-B positions.
- Source counts before filtering: `{"adsb_icao": 5034854, "adsb_icao_nt": 11, "mlat": 470426}`
- Source counts kept: `{"adsb_icao": 5034854, "adsb_icao_nt": 11}`
- Valid ADS-B positions after filtering: 5,034,865
- Non-ADS-B positions filtered out: 470,426
- Unique aircraft after filtering: 2,870

## Observation Window
- Coverage figure period: 2026-04-13T10:45:15+00:00 to 2026-05-14T14:23:56+00:00
- Observation-window duration: approximately 31 days.
- Historical local stack inventory: earlier inventory found a broader local history of about 139 calendar days in the stack. This v3 figure uses only the `trace_full` coverage files available for the map window and does not claim 139 days of plotted coverage.

## Distance Metrics
- Receiver coordinates used for distance and plotting: rounded to two decimal places, `-20.51`, `-47.4`.
- Privacy note: Distance metrics were computed using receiver coordinates rounded to two decimal places for privacy; the resulting systematic error is within approximately +/-1 km and does not affect km-level metrics reported here.
- Median range: 189.4 km
- P95 range: 300.1 km
- Maximum observed range: 510.3 km

## Figure Rendering
- Recommended abstract figure: `coverage_map_v3_hexbin.pdf` or `coverage_map_v3_hexbin.png`.
- Hexbin rendering: logarithmic hexagonal binning, gridsize 80, metrics computed over all valid ADS-B positions.
- Colorbar label: ADS-B position reports per ~10 km hex cell (log scale).
- Range rings: 100, 250, and 500 km are plotted above the hexbin layer with neutral translucent lines.
- Airport reference markers: FRC, RAO, VCP, GRU, CGH, and CNF are plotted only if they fall within the map extent.
- No basemap or public receiver-precision coordinate is included. The receiver is shown only by a star marker; the previous explicit receiver text label was removed for legibility.

## Stack Version Evidence
- readsb version: readsb version: 3.16.14 wiedehopf git: b80c737 (committed: Mon May 4 20:10:25 2026 0000)
- ultrafeeder image: ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:telegraf-build-925 sha256:b92424afd43db56d13296467c90782dc1b5bee187b59724f6db02ea09ff609f6
- tar1090 CLI version: not verified; `tar1090 --version` was not available in the ultrafeeder container PATH during inspection.

## v2 to v3 Difference
- v2 valid ADS-B positions: 5025795
- v2 unique aircraft: 2867
- v2 range metrics: median 189.4 km, p95 300.1 km, max 510.3 km.
- v3 valid ADS-B positions: 5,034,865
- Main visual changes: v3 keeps ADS-B-only filtering, uses the hexbin version only, draws range rings above the hexbin layer, removes the red receiver text label, and uses a clearer colorbar label.

## Limitations
- This is an operational indicator based on local receiver logs, not a final OpenSky network-wide coverage analysis.
- The map shows received positions, not guaranteed coverage over every point in the region.
- Aircraft density is affected by traffic patterns, altitude, terrain, antenna installation, receiver configuration, and data-retention behavior.
- The figure should not be used to claim comprehensive coverage of southeastern Brazil.

## Recommendation for the abstract
- Use in abstract: yes, use the v3 hexbin version.
- Reason: the v3 figure is ADS-B-only, traceable to local logs, legible at abstract size, and includes the most defensible metrics for a short field-report abstract.
- Suggested caption: see `coverage_map_caption_v3.txt`.
