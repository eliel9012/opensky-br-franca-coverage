"""DEC by Brazilian region (Idec 2022, ANEEL data) -> figures/dec_by_region.pdf

Inputs live in analysis/external_inputs.json. INPUTS below is the same data
and is used to (re)create the JSON only if it is missing.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

from style import FIG_W, OI, ROOT, GREY, apply_style, save

NODE_REGION = "Southeast"  # Franca/SP

INPUTS = {
    "dec_fec_by_region_idec2022": {
        "source": "Idec 2022, based on ANEEL data; approximate regional values "
                  "(DEC in h per consumer unit per year, FEC in interruptions per consumer unit per year)",
        "regions": {
            "North": {"dec": 24, "fec": 12},
            "Center-West": {"dec": 15, "fec": 7},
            "Northeast": {"dec": 13, "fec": 5},
            "South": {"dec": 10, "fec": 6},
            "Southeast": {"dec": 7, "fec": 4},
        },
    },
    "national_aneel_2025": {"dec": 9.30, "fec": 4.66, "source": "ANEEL national indicators, 2025"},
}

JSON_PATH = ROOT / "analysis" / "external_inputs.json"


def load_inputs() -> dict:
    if not JSON_PATH.exists():
        JSON_PATH.parent.mkdir(exist_ok=True)
        JSON_PATH.write_text(json.dumps(INPUTS, indent=2) + "\n")
    return json.loads(JSON_PATH.read_text())


def main() -> None:
    inp = load_inputs()
    regions = inp["dec_fec_by_region_idec2022"]["regions"]
    nat = inp["national_aneel_2025"]

    names = sorted(regions, key=lambda r: regions[r]["dec"], reverse=True)
    dec = [regions[r]["dec"] for r in names]
    fec = [regions[r]["fec"] for r in names]
    colors = [OI["vermillion"] if r == NODE_REGION else OI["sky"] for r in names]

    apply_style()
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    y = list(range(len(names)))
    ax.barh(y, dec, color=colors, height=0.66)
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlim(0, 36)
    ax.set_xlabel("DEC (h per consumer unit)")
    ax.tick_params(axis="y", length=0)

    for yi, d, f, r in zip(y, dec, fec, names):
        label = f"{d:g} h, FEC {f:g}"
        kw = {}
        if r == NODE_REGION:
            label += "\nnode region"
            kw = dict(bbox=dict(fc="white", ec="none", pad=1.0), color=OI["vermillion"],
                      fontweight="bold", zorder=3)
        ax.text(d + 0.5, yi, label, va="center", ha="left", fontsize=8, linespacing=1.15, **kw)

    ax.axvline(nat["dec"], color=GREY, ls="--", lw=1.1, zorder=0)
    ax.text(nat["dec"] + 0.5, -0.62, f"Brazil 2025: {nat['dec']:.2f} h", ha="left",
            va="bottom", fontsize=8, color=GREY)
    ax.set_ylim(len(names) - 0.4, -0.95)

    fig.tight_layout(pad=0.4)
    save(fig, "dec_by_region.pdf")


if __name__ == "__main__":
    main()
