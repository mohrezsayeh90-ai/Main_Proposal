"""Section 3.3: signals, straight-tube coordinates, and symbolic window maps.

Run: MPLCONFIGDIR=/tmp/mpl-cache python figs/deeponet-magnetic-forward.py
Source: Master_Magnetic, revision a4fc9d7. No trajectories are simulated.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(7.6, 7.1))
    fig.text(0.025, 0.97, r"$(a)$", fontsize=13)
    signals = fig.add_axes([0.14, 0.74, 0.81, 0.21])
    s = np.linspace(0, 1, 17)
    left = 0.35 * np.sin(2*np.pi*s)
    right = 0.22 * np.cos(2*np.pi*s + np.pi/4)
    assert len(s) == 17 and np.max(abs(left)+abs(right)) < np.sqrt(0.5)
    signals.axhline(0, color="0.6", lw=0.7)
    signals.plot(s, left, "k-o", ms=3.8, lw=1.2, label=r"$a_L(\tau)$")
    signals.plot(s, right, "k--s", ms=3.8, lw=1.1, mfc="white", label=r"$a_R(\tau)$")
    signals.set(xlim=(0, 1), ylim=(-0.42, 0.42), xlabel=r"$\tau$",
                ylabel=r"$a_L,\ a_R$")
    signals.set_xticks([0, 1], [r"$\tau_j$", r"$\tau_{j+1}$"])
    signals.set_yticks([-0.35, 0, 0.35])
    signals.legend(loc="upper right", ncol=2, frameon=False, fontsize=10)
    signals.spines[["top", "right"]].set_visible(False)
    signals.text(0.5, 0.05, r"$17\ \mathrm{equidistant\ sensors}$",
                 transform=signals.transAxes, ha="center", fontsize=9)

    fig.text(0.025, 0.65, r"$(b)$", fontsize=13)
    tube = fig.add_axes([0.14, 0.38, 0.81, 0.24])
    tube.set(xlim=(-2.4, 2.1), ylim=(-2.3, 2.3),
             xlabel=r"$Z=z/D$", ylabel=r"$X=x/R$")
    # Longitudinal view of a circular tube. X and Z use different scales.
    for wall in (-1, 1):
        tube.plot([-2.35, 2.05], [wall, wall], "k-", lw=1.4)
    tube.add_patch(Rectangle((-2, -0.7), 3.7, 1.4, facecolor="0.95",
                             edgecolor="0.45", lw=1.0, ls="--", hatch="///"))
    tube.text(-0.15, 0.3, r"$|X|\leq0.7,\quad -2\leq Z\leq1.7$",
              ha="center", va="center", fontsize=10,
              bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})
    tube.annotate("", xy=(0.9, -0.35), xytext=(-0.9, -0.35),
                  arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.0})
    tube.text(0, -0.6, r"$\bar U^*(1-X^2)$", ha="center", va="center", fontsize=10,
              bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    # Source coordinates are xi=-1 and +1, far beyond X=+-1/epsilon.
    # These arrows indicate direction only; they do not place sources on walls.
    for side, xi, yy, end in (("R", "+1", 1.90, 1.1),
                              ("L", "-1", -1.90, -1.1)):
        tube.text(0, yy, rf"${side}:\ \xi={xi}\quad(\mathrm{{off\ scale}})$",
                  ha="center", va="center", fontsize=10)
        tube.add_patch(FancyArrowPatch((0, np.sign(yy)*1.55), (0, end), arrowstyle="->",
                                       mutation_scale=10, lw=1.0, linestyle=":"))
    tube.set_xticks([-2, 0, 1.7])
    tube.set_yticks([-1, -0.7, 0, 0.7, 1])
    tube.tick_params(labelsize=9, length=3)
    tube.spines[["top", "right"]].set_visible(False)

    fig.text(0.025, 0.29, r"$(c)$", fontsize=13)
    clock = fig.add_axes([0.08, 0.035, 0.89, 0.23])
    clock.set(xlim=(0, 10), ylim=(0, 3))
    clock.axis("off")
    for x0, x1, index, shade in ((0.8, 4.7, "j", "0.96"),
                                (4.7, 8.6, "j+1", "0.90")):
        clock.add_patch(Rectangle((x0, 1.85), x1-x0, 0.65,
                                  facecolor=shade, edgecolor="black", lw=0.7))
        clock.text((x0+x1)/2, 2.175,
                   r"$[\tau_j,\tau_{j+1}]$" if index=="j" else
                   r"$[\tau_{j+1},\tau_{j+2}]$", ha="center", va="center")
        clock.text((x0+x1)/2, 1.5, rf"$\mathbf{{a}}_{index},\ h_{index}$",
                   ha="center", va="center", fontsize=10)
    clock.annotate("", xy=(9.2, 1.85), xytext=(0.6, 1.85),
                   arrowprops={"arrowstyle": "->", "lw": 1.0})
    clock.text(9.3, 1.85, r"$\tau$", va="center")
    for x, text in ((0.8, r"$\mathbf{q}_j$"), (4.7, r"$\mathbf{q}_{j+1}$"),
                    (8.6, r"$\mathbf{q}_{j+2}$")):
        clock.text(x, 0.55, text, ha="center", va="center", fontsize=12,
                   bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "black"})
    for start, stop in ((1.3, 4.1), (5.3, 8.0)):
        clock.annotate("", xy=(stop, 0.55), xytext=(start, 0.55),
                       arrowprops={"arrowstyle": "->", "lw": 1.0})
        clock.text((start+stop)/2, 0.85, r"$\mathcal{G}_\theta$", ha="center", va="bottom")

    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Signed sources and windowed straight-tube magnetic operator",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
