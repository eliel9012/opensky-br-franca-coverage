#!/usr/bin/env python3
"""Verify archive SHA-256 and every original trace, without extracting files."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=Path('.'))
    args = parser.parse_args()
    manifest = json.loads((args.directory / 'dataset-manifest.json').read_text())
    for item in manifest['archives']:
        path = args.directory / item['filename']
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
                h.update(chunk)
        if path.stat().st_size != item['archive_bytes'] or h.hexdigest() != item['sha256']:
            raise SystemExit(f'Archive checksum mismatch: {path.name}')
        with zipfile.ZipFile(path) as archive:
            records = {}
            for line in archive.read(item['internal_checksums']).decode().splitlines():
                expected, name = line.split('  ', 1)
                pure = PurePosixPath(name)
                if pure.is_absolute() or '..' in pure.parts or name in records:
                    raise SystemExit('Unsafe or duplicate member name')
                records[name] = expected
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != set(records) | {item['internal_checksums']}:
                raise SystemExit('Unexpected or duplicate ZIP members')
            total_bytes = 0
            for name, expected in records.items():
                data = archive.read(name)
                total_bytes += len(data)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise SystemExit(f'Trace checksum mismatch: {name}')
            if len(records) != item['trace_files'] or total_bytes != item['trace_bytes']:
                raise SystemExit('Trace count or byte count mismatch')
        print(f'PASS {path.name}: archive SHA-256, {len(records):,} trace checksums and ZIP CRCs')


if __name__ == '__main__':
    main()
