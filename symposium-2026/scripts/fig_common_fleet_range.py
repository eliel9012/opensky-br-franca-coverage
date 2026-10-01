"""Per-aircraft change in mean range, common fleet -> figures/common_fleet_range.pdf

Common fleet: ICAO24 seen in Era A (32 d) and Era B paired window
([2026-05-16T21:35Z, +32 d)). Per aircraft mean range in A and in B; histogram of
delta = meanB - meanA. Military/state aircraft (dbFlags & 1 in the raw trace_full
json) are dropped. The exclusion set is cached only in the session scratchpad,
never in the project. No identifiers are plotted.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from style import FIG_W, NPZ_DIR, OI, ROOT, GREY, apply_style, save

SCRATCH = Path("/private/tmp/claude-501/-Users-eliel/e2d6e951-eb59-46ff-a034-78ea2ed0cdf6/scratchpad")
CACHE = SCRATCH / "military_exclusion_common_fleet.json"
SWAP = datetime(2026, 5, 16, 21, 35, tzinfo=UTC)
PAIRED_END = (SWAP + timedelta(days=32)).timestamp()


def common_fleet_means():
    da = np.load(NPZ_DIR / "positions_era_a.npz")
    db = np.load(NPZ_DIR / "positions_era_b.npz")
    ia = json.load(open(NPZ_DIR / "icao_era_a.json"))
    ib = json.load(open(NPZ_DIR / "icao_era_b.json"))
    m = db["abs_time"] < PAIRED_END
    rb, idb = db["range_km"][m], db["icao_id"][m]
    ra, ida = da["range_km"], da["icao_id"]

    def per_icao(r, ids, names):
        n = len(names)
        s = np.bincount(ids, weights=r, minlength=n)
        c = np.bincount(ids, minlength=n)
        return s, c

    sa, ca = per_icao(ra, ida, ia)
    sb, cb = per_icao(rb, idb, ib)
    pos_a = {ia[i]: i for i in np.nonzero(ca)[0]}
    pos_b = {ib[i]: i for i in np.nonzero(cb)[0]}
    common = sorted(set(pos_a) & set(pos_b))
    mean_a = np.array([sa[pos_a[c]] / ca[pos_a[c]] for c in common])
    mean_b = np.array([sb[pos_b[c]] / cb[pos_b[c]] for c in common])
    # position-weighted fleet means (same definition as the frozen 188.5 / 217.9)
    ma = np.isin(ida, [pos_a[c] for c in common])
    mb = np.isin(idb, [pos_b[c] for c in common])
    pooled = (float(ra[ma].mean()), float(rb[mb].mean()))
    return common, mean_a, mean_b, pooled


def military_set(common):
    """ICAO24 with dbFlags bit 0 set in any raw trace_full file of either era."""
    if CACHE.exists():
        c = json.loads(CACHE.read_text())
        if c.get("n_common") == len(common):
            return set(c["military"])
    want = set(common)
    mil = set()
    for era in ("era_a", "era_b"):
        base = ROOT / "data" / "dados" / era
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.startswith("trace_full_"):
                    continue
                icao = fn[len("trace_full_"):].rsplit(".", 1)[0]
                if icao not in want or icao in mil:
                    continue
                try:
                    with gzip.open(os.path.join(dirpath, fn), "rt") as fh:
                        flags = json.load(fh).get("dbFlags", 0)
                except (OSError, ValueError):
                    continue
                if isinstance(flags, int) and flags & 1:
                    mil.add(icao)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"n_common": len(common), "military": sorted(mil)}))
    return mil


def main() -> None:
    common, ma, mb, pooled = common_fleet_means()
    n_common = len(common)
    ok = n_common == 2234 and round(pooled[0], 1) == 188.5 and round(pooled[1], 1) == 217.9
    print(f"common={n_common} pooled mean A={pooled[0]:.2f} B={pooled[1]:.2f} "
          f"check(2234,188.5,217.9)={'PASS' if ok else 'FAIL'}")
    mil = military_set(common)
    keep = np.array([c not in mil for c in common])
    delta = (mb - ma)[keep]
    n_excl, n_plot = int((~keep).sum()), int(keep.sum())
    med = float(np.median(delta))
    print(f"excluded military/state={n_excl} plotted={n_plot} median delta={med:.1f} km "
          f"mean delta={delta.mean():.1f} share>0={(delta > 0).mean():.3f}")

    apply_style()
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    edges = np.arange(np.floor(delta.min() / 10) * 10, np.ceil(delta.max() / 10) * 10 + 1, 10)
    ax.hist(delta, bins=edges, color=OI["blue"], edgecolor="white", linewidth=0.3)
    xlo, xhi = -150, 300
    nout = int(((delta < xlo) | (delta > xhi)).sum())
    ax.axvline(0, color="black", lw=1.0)
    ax.axvline(med, color=OI["vermillion"], lw=1.4, ls="--")
    ymax = ax.get_ylim()[1]
    ax.set_ylim(0, ymax * 1.18)
    ax.text(-3, ymax * 1.12, "0", ha="right", va="top", fontsize=8, color="black")
    ax.text(med + 4, ymax * 1.12, f"median {med:+.0f} km", ha="left", va="top",
            fontsize=8, color=OI["vermillion"])
    ax.set_xlabel("change in mean range per aircraft (km)")
    ax.set_ylabel("aircraft")
    ax.set_xlim(xlo, xhi)
    fig.tight_layout(pad=0.4)
    save(fig, "common_fleet_range.pdf")
    print(f"delta min {delta.min():.0f} max {delta.max():.0f}; outside shown x range: {nout}")


if __name__ == "__main__":
    main()
