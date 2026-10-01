"""Illustrative import cost waterfalls, two scenarios -> figures/import_cost.pdf

Inputs from analysis/external_inputs.json: import_kit (Remessa Conforme, duty 60%
minus a deduction, ICMS grossed up) and import_kit_outside_remessa (author-supplied
scenario: duty 60% with no deduction). All derived values are computed here.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

from style import FIG_W, OI, ROOT, GREY, apply_style, save


def scenario(price, duty_rate, deduction, icms_rate):
    duty = max(price * duty_rate - deduction, 0.0)
    total = (price + duty) / (1 - icms_rate)  # ICMS grossed up
    icms = total - price - duty
    assert abs(price + duty + icms - total) < 1e-9
    return duty, icms, total, (total / price - 1) * 100


def draw(ax, price, duty, icms, total, markup, name, ymax):
    labels = ["Sticker\nprice", "Federal\nduty", "ICMS", "Total\nlanded"]
    bottoms = [0, price, price + duty, 0]
    heights = [price, duty, icms, total]
    colors = [OI["sky"], OI["orange"], OI["vermillion"], OI["blue"]]
    x = range(4)
    ax.bar(x, heights, bottom=bottoms, color=colors, width=0.66)
    for i, t in enumerate([price, price + duty, total][:3]):
        ax.plot([i + 0.33, i + 1 - 0.33], [t, t], color=GREY, lw=0.8)
    texts = [f"{price:.0f}", f"+{duty:.0f}", f"+{icms:.0f}", f"{total:.0f}"]
    for i, (b, h, t) in enumerate(zip(bottoms, heights, texts)):
        ax.text(i, b + h + ymax * 0.02, t, ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, ymax)
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("US$")
    ax.text(0.02, 1.0, name, transform=ax.transAxes, ha="left", va="top", fontsize=8, fontweight="bold")
    ax.text(0.02, 0.86, f"+{markup:.0f}% vs sticker price", transform=ax.transAxes, ha="left",
            va="top", fontsize=8)


def main() -> None:
    ext = json.loads((ROOT / "analysis" / "external_inputs.json").read_text())
    k1, k2 = ext["import_kit"], ext["import_kit_outside_remessa"]
    d1, i1, t1, m1 = scenario(k1["price_usd"], 0.60, 30.0, k1["icms_rate_pct"] / 100)
    d2, i2, t2, m2 = scenario(k2["price_usd"], k2["duty_rate_pct"] / 100, k2["deduction_usd"], k2["icms_rate_pct"] / 100)
    assert round(d1) == k1["duty_usd"] and abs(t1 - k1["total_usd"]) <= 1 and round(m1) == k1["markup_pct"] == 69
    assert round(d2) == 90 and round(i2) == 49 and round(t2) == 289 and round(m2) == 93

    apply_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIG_W, 4.1), sharex=True)
    ymax = 360
    draw(ax1, k1["price_usd"], d1, i1, t1, m1, "Remessa Conforme", ymax)
    draw(ax2, k2["price_usd"], d2, i2, t2, m2, "outside Remessa Conforme", ymax)
    ax1.tick_params(axis="x", labelbottom=False)
    for ax in (ax1, ax2):
        ax.text(0.99, 1.0, "illustrative", transform=ax.transAxes, ha="right", va="top",
                fontsize=8, fontstyle="italic", color=GREY)
    fig.tight_layout(pad=0.4, h_pad=0.6)
    save(fig, "import_cost.pdf")


if __name__ == "__main__":
    main()
