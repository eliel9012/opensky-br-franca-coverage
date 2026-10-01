FRANCA RAW READSB TRACES — APRIL–SEPTEMBER 2026
Author: Eliel Felipe Junior; ORCID 0000-0002-6333-1187
Local receiver: OpenSky sensor -1408044782, Franca, Brazil.

STATUS
Prepared locally for a separate dataset deposit. Not uploaded or published.
No dataset DOI has been assigned. The existing code/aggregate archive
10.5281/zenodo.23089559 does not contain these new raw-data ZIPs.
No new dataset license has been assigned by this packaging operation; select
the intended data license in the Zenodo deposit before publication.

CONTENTS
franca-readsb-era-a-raw.zip: 22,166 original traces, 147,088,252 payload bytes;
  directory dates 2026-04-13 through 2026-05-16 (34 dates).
franca-readsb-era-b-raw.zip: 101,171 original traces, 994,674,644 payload bytes;
  directory dates 2026-05-16 through 2026-09-30 (138 dates).
dataset-manifest.json: archive hashes, sizes, windows and validation counts.
SHA256SUMS: SHA-256 of the two ZIP archives.
verify_archives.py: standard-library Python verifier; no extraction required.

Original gzip bytes and relative directory layout are preserved. ZIP uses
STORE because the traces are already gzip compressed, despite .json names.
Each ZIP also contains data/manifests/era_a.sha256 or era_b.sha256 with a
SHA-256 for every trace. No machine-specific paths, caches, credentials,
source-context notes, .DS_Store files or generated position arrays are included.
No observations or aircraft have been filtered out or anonymized. Raw files
contain all recorded source types, including MLAT, and aircraft metadata such
as ICAO address, registration and, where available, operator. The scientific
analysis applies the filters below; these archives are not an ADS-B-only or
anonymized export. Dataset publication has not been performed.

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
  unzip -n /path/to/dataset/franca-readsb-era-b-raw.zip
The -n flag preserves existing files. If data already exists there, verify it
against the extracted per-file manifests or use a fresh checkout to avoid
mixing old inputs with this dataset. For example, from symposium-2026:
  shasum -a 256 -c data/manifests/era_a.sha256
  shasum -a 256 -c data/manifests/era_b.sha256
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
The archive verifier checks the SHA-256 of both ZIPs and every enclosed trace.
Era B through 28 August has a prior source-backup checksum record. The following
33 days, 29 August through 30 September, lack original-receiver checksums.
The new export hashes verify these packages; they cannot establish missing
historical source integrity. These are local receiver observations, not an
OpenSky network database export.

PUBLICATION ORDER
1. Deposit these six files in a Zenodo dataset record; choose the data license
   and public access, then publish manually. Relate it to the code DOI above.
2. Record the real dataset DOI in dataset-manifest.json and repository docs.
3. Update the paper's Open Data statement, dataset citation and poster/QR.
4. Rebuild the submission PDFs/ZIP. Only then describe the traces as public.
GitHub-to-Zenodo integration will not upload these external ZIPs for you.
