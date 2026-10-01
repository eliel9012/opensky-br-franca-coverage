FRANCA RAW READSB TRACES — APRIL–SEPTEMBER 2026
Author: Eliel Felipe Junior; ORCID 0000-0002-6333-1187
Local receiver: OpenSky sensor -1408044782, Franca, Brazil.

STATUS
Published dataset version 1.0.0, 1 October 2026:
https://doi.org/10.5281/zenodo.23090597
Dataset DOI covering all versions: 10.5281/zenodo.23090596.
Related code and aggregate results (v5.0.0):
https://doi.org/10.5281/zenodo.23089559
The dataset is publicly downloadable. All nine ZIP archives are unchanged
from the verified publication. This README and the manifest have been updated
to record publication and licensing.

LICENSES
Dataset and dataset documentation: Creative Commons Attribution 4.0
International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/.
Verification software (verify_archives.py): MIT; license text below.
The dataset license applies to rights held by the depositor and does not
replace third-party rights in included metadata.

CONTENTS
franca-readsb-era-a-raw.zip: 22,166 original traces, 147,088,252 payload bytes;
  directory dates 2026-04-13 through 2026-05-16 (34 dates).
Era B is distributed as eight independent ZIP parts (01-of-08 through 08-of-08),
  totaling 101,171 original traces and 994,674,644 payload bytes;
  directory dates 2026-05-16 through 2026-09-30 (138 dates).
  franca-readsb-era-b-raw-part-01-of-08.zip: 146.10 MB; 14,838 traces.
  franca-readsb-era-b-raw-part-02-of-08.zip: 144.81 MB; 14,243 traces.
  franca-readsb-era-b-raw-part-03-of-08.zip: 147.54 MB; 14,520 traces.
  franca-readsb-era-b-raw-part-04-of-08.zip: 146.54 MB; 14,024 traces.
  franca-readsb-era-b-raw-part-05-of-08.zip: 147.80 MB; 14,716 traces.
  franca-readsb-era-b-raw-part-06-of-08.zip: 142.91 MB; 14,083 traces.
  franca-readsb-era-b-raw-part-07-of-08.zip: 144.04 MB; 14,021 traces.
  franca-readsb-era-b-raw-part-08-of-08.zip: 7.62 MB; 726 traces.
dataset-manifest.json: archive hashes, sizes, windows and validation counts.
SHA256SUMS: SHA-256 of all nine ZIP archives.
verify_archives.py: standard-library Python verifier; no extraction required.

Original gzip bytes and relative directory layout are preserved. ZIP uses
STORE because the traces are already gzip compressed, despite .json names.
Each ZIP also contains data/manifests/era_a.sha256 or era_b_part_NN.sha256 with a
SHA-256 for every trace. No machine-specific paths, caches, credentials,
source-context notes, .DS_Store files or generated position arrays are included.
No observations or aircraft have been filtered out or anonymized. Raw files
contain all recorded source types, including MLAT, and aircraft metadata such
as ICAO address, registration and, where available, operator. The scientific
analysis applies the filters below; these archives are not an ADS-B-only or
anonymized export.

ANALYSIS WINDOWS (UTC, END EXCLUSIVE)
Era A: 2026-04-13T00:00:00Z <= t < 2026-05-15T00:00:00Z.
Era B: 2026-05-16T21:35:00Z <= t < 2026-10-01T00:00:00Z.
Paired B: same start, ending 2026-06-17T21:35:00Z.
The raw folders contain extra dates/observations intentionally. Do not merge
A and B folders blindly: 16 May overlaps, and the antenna boundary must be
applied per point using the absolute timestamp, not its directory date.
Keep only source types adsb_icao and adsb_icao_nt and valid latitude/longitude.
Expected valid positions: A 5,153,167; B 36,535,422.
Expected distinct aircraft in these windows: A 2,890; B 4,925.

FORMAT
Path: data/dados/era_{a,b}/YYYY/MM/DD/traces/HH/trace_full_ICAO.json
Decode with gzip.open(path, 'rt'), then json.load().
Top-level fields include icao, timestamp, trace, dbFlags, version, and optional
aircraft metadata. Each trace row includes:
  0 offset from base timestamp (seconds); 1 latitude (degrees);
  2 longitude (degrees); 3 altitude (feet, or 'ground');
  4 ground speed; 5 track; 6 flags; 7 vertical rate;
  8 optional details; 9 source type; later entries may also be present.
Absolute UTC epoch seconds = top-level timestamp + row[0].
The supplied analysis scripts define the exact parsing and selection rules.

VERIFY AND RESTORE
Run from the directory containing the ZIPs and this manifest:
  python3 verify_archives.py .
On macOS, the outer hashes can also be checked with:
  shasum -a 256 -c SHA256SUMS
From the cloned repository's symposium-2026 directory, replace /path/to/dataset:
  unzip -n /path/to/dataset/franca-readsb-era-a-raw.zip
  for archive in /path/to/dataset/franca-readsb-era-b-raw-part-*-of-08.zip; do
    unzip -n "$archive"
  done
Each part is a complete, independently readable ZIP. Extract all eight parts
into the same directory. Do not concatenate them; all eight are required.
The parts are separated at UTC directory-date boundaries, without splitting
an individual trace or changing the scientific analysis windows.
The -n flag preserves existing files. If data already exists there, verify it
against the extracted per-file manifests or use a fresh checkout to avoid
mixing old inputs with this dataset. For example, from symposium-2026:
  shasum -a 256 -c data/manifests/era_a.sha256
  for manifest in data/manifests/era_b_part_*.sha256; do
    shasum -a 256 -c "$manifest"
  done
Then, in an environment with the repository's requirements installed:
  python3 data/scripts/build_dataset.py
  python3 data/scripts/compute_metrics.py
  python3 scripts/compute_new_metrics.py
  python3 scripts/compute_new_metrics.py --poster
These analysis commands regenerate derived results. Raw inputs remain intact.
Do not commit raw traces, the archive ZIPs or generated arrays to Git.

VALIDATION AND PROVENANCE
Packaging decoded every gzip/JSON file and independently counted source types,
positions and aircraft using the existing analysis windows. Counts were
compared with the existing scan summary. All original bytes are preserved.
The archive verifier checks the SHA-256 of every ZIP and enclosed trace,
complete dataset counts and the absence of duplicate traces across parts.
Era B through 28 August has a prior source-backup checksum record. The following
33 days, 29 August through 30 September, lack original-receiver checksums.
The new export hashes verify these packages; they cannot establish missing
historical source integrity. These are local receiver observations, not an
OpenSky network database export.

CITATION
Felipe Junior, Eliel (2026). Franca Local Receiver Traces Supporting an
ADS-B Antenna Comparison, April-September 2026 (Version 1.0.0) [Data set].
Zenodo. https://doi.org/10.5281/zenodo.23090597
Cite the related code archive separately when reproducing the analysis:
https://doi.org/10.5281/zenodo.23089559
The manuscript and poster QR codes link to the version-specific dataset DOI.

SOFTWARE LICENSE (verify_archives.py)
MIT License

Copyright (c) 2026 Eliel Felipe Junior

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
