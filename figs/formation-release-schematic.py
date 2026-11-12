"""Draw the section 3.2 method schematic, without simulating trajectories.

Run from the repository root:
    MPLCONFIGDIR=/tmp/mpl-cache python figs/formation-release-schematic.py
Geometry and C centers match Master3, commit c17460d. Timeline positions are
illustrative layout coordinates, not a computed or numerical release schedule.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 12,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    length, height = 2.2, 0.30
    station_x = length * np.array([0.25, 0.50, 0.75])
    theta = np.linspace(np.pi / 4, 7 * np.pi / 4, 6)
    targets = np.column_stack((0.86 * length + 0.075 * np.cos(theta),
                               0.50 * height + 0.095 * np.sin(theta)))

    fig = plt.figure(figsize=(7.6, 5.3))
    fig.text(0.025, 0.96, r"$(a)$", fontsize=13)
    channel = fig.add_axes([0.12, 0.785, 0.83, 0.17])
    for y in (0, height):
        channel.plot([0, length], [y, y], color="black", lw=1.35)
        # Mark wall ports, not the slightly offset particle release centers.
        channel.plot(station_x, np.full(3, y), "ks", ms=5.5, clip_on=False)
    channel.plot(targets[:, 0], targets[:, 1], "o", ms=4.8,
                 markerfacecolor="white", markeredgecolor="black", mew=1.0)
    channel.set(xlim=(0, length), ylim=(0, height), aspect="equal",
                xlabel=r"$x^*$", ylabel=r"$y^*$")
    channel.set_xticks([0, *station_x, length],
                      [r"$0$", r"$0.55$", r"$1.10$", r"$1.65$", r"$2.2$"])
    channel.set_yticks([0, height], [r"$0$", r"$0.30$"])
    channel.tick_params(length=3, labelsize=11, pad=4)
    # Neither inlet nor outlet has a vertical wall; spines are not boundaries.
    for spine in channel.spines.values():
        spine.set_visible(False)

    handles = [Line2D([], [], marker="s", linestyle="none", color="black",
                      markersize=6, label=r"$\mathrm{wall\ ports}$"),
               Line2D([], [], marker="o", linestyle="none", color="black",
                      markerfacecolor="white", markersize=6,
                      label=r"$\mathrm{C\ target\ centers}$")]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.12, 0.59),
               frameon=False, handletextpad=0.7, labelspacing=0.9)

    zoom = fig.add_axes([0.69, 0.47, 0.26, 0.23])
    zoom.plot(targets[:, 0], targets[:, 1], "o", ms=6.0,
              markerfacecolor="white", markeredgecolor="black", mew=1.1)
    zoom.set(xlim=(1.80, 1.99), ylim=(0.04, 0.26), aspect="equal",
             xlabel=r"$x^*$", ylabel=r"$y^*$")
    zoom.set_title(r"$\mathrm{C\ (zoom)}$", fontsize=11, pad=7)
    zoom.set_xticks([1.82, 1.97], [r"$1.82$", r"$1.97$"])
    zoom.set_yticks([0.06, 0.15, 0.24], [r"$0.06$", r"$0.15$", r"$0.24$"])
    zoom.tick_params(labelsize=9, length=2)
    zoom.xaxis.labelpad = 2
    zoom.yaxis.labelpad = 1
    for spine in zoom.spines.values():
        spine.set_color("0.55")
        spine.set_linewidth(0.6)
    channel.add_patch(Rectangle((1.80, 0.04), 0.19, 0.22,
                                fill=False, ls=":", lw=0.8, ec="0.5"))

    fig.text(0.025, 0.385, r"$(b)$", fontsize=13)
    clock = fig.add_axes([0.12, 0.085, 0.83, 0.28])
    clock.set(xlim=(0, 1), ylim=(-0.4, 2.0))
    clock.axis("off")
    # Symbolic positions only: both flights end at the same target time.
    rel_i, rel_j, final = 0.13, 0.43, 0.87
    clock.add_patch(Rectangle((rel_j, 0.18), final - rel_j, 1.55,
                              facecolor="0.96", edgecolor="0.8", lw=0,
                              hatch="///", zorder=0))
    clock.annotate("", xy=(0.99, 0), xytext=(0.03, 0),
                   arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "black"})
    clock.text(1.00, -0.04, r"$t^*$", ha="left", va="top")
    for start, y, index, style in ((rel_i, 1.45, "i", "-"),
                                    (rel_j, 0.9, "j", "--")):
        clock.plot([start, start], [0, y], ":", color="0.45", lw=0.8)
        clock.plot([start, final], [y, y], linestyle=style, color="black", lw=1.4)
        clock.plot([start, final], [y, y], "|", color="black", ms=8)
        clock.text((start + final) / 2, y + 0.12,
                   rf"$a_{index}^*$", ha="center", va="bottom")
        clock.plot([start, start], [-0.04, 0.04], color="black", lw=0.9)
        clock.text(start, -0.14, rf"$t_{{\mathrm{{rel}},{index}}}^*$",
                   ha="center", va="top")
    clock.plot([final, final], [-0.04, 1.8], "--", color="black", lw=0.9)
    clock.text(final, -0.14, r"$T^*$", ha="center", va="top")
    clock.annotate("", xy=(final, 0.32), xytext=(rel_j, 0.32),
                   arrowprops={"arrowstyle": "|-|", "lw": 0.9, "color": "black"})
    clock.text((rel_j + final) / 2, 0.39,
               r"$[\max(t_{\mathrm{rel},i}^*,t_{\mathrm{rel},j}^*),\,T^*]$",
               ha="center", va="bottom", fontsize=10)

    # Equal spatial data scaling is essential in the main panel and its zoom.
    fig.canvas.draw()
    for ax in (channel, zoom):
        origin, dx, dy = ax.transData.transform([[0, 0], [1, 0], [0, 1]])
        assert np.isclose(np.linalg.norm(dx - origin), np.linalg.norm(dy - origin))
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Nondimensional release geometry and shared clock",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
