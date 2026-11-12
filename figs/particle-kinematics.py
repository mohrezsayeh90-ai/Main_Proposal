"""Build the vector schematic: MPLCONFIGDIR=/tmp/mpl-cache python figs/particle-kinematics.py."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, PathPatch
from matplotlib.path import Path as PlotPath


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 12,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(5.0, 2.65))
    # All coordinates are illustrative; there are no physical scales or ticks.
    ax.plot([0.2, 8.8], [0.3, 0.3], color="black", lw=1.4)
    ax.plot([0.2, 8.8], [4.3, 4.3], color="black", lw=1.4)
    start, particle = (0.9, 0.8), (4.0, 2.3)
    # The incoming and outgoing Bezier segments share tangent (1, 0.55).
    vertices = [start, (2.0, 0.85), (3.0, 1.75), particle,
                (5.0, 2.85), (6.5, 3.1), (8.2, 3.15)]
    codes = [PlotPath.MOVETO] + [PlotPath.CURVE4] * 6
    ax.add_patch(PathPatch(PlotPath(vertices, codes), fill=False,
                           color="0.4", lw=1.2, ls=":"))
    ax.plot(*start, marker="o", ms=4, color="black")
    ax.text(0.65, 1.18, r"$\mathbf{r}_{p,0}$")
    ax.add_patch(Circle(particle, 0.13, facecolor="white",
                        edgecolor="black", lw=1.3, zorder=4))
    ax.text(3.25, 1.40, r"$\mathbf{r}_p(t)$")
    # Filled solid arrow: particle velocity, exactly tangent at the particle.
    ax.add_patch(FancyArrowPatch(particle, (5.9, 3.345),
                                arrowstyle="-|>", mutation_scale=15,
                                lw=1.5, color="black", shrinkA=0, shrinkB=0,
                                zorder=5))
    ax.text(5.25, 3.52, r"$\mathbf{v}_p(t)$")
    # Open dashed arrow: local downstream fluid velocity, same origin.
    ax.add_patch(FancyArrowPatch(particle, (6.6, 2.3),
                                arrowstyle="->", mutation_scale=15,
                                lw=1.4, linestyle="--", color="black",
                                shrinkA=0, shrinkB=0, zorder=5))
    ax.text(5.75, 1.72, r"$\mathbf{U}(\mathbf{r}_p)$")
    ax.set(xlim=(0, 9), ylim=(0, 4.6), aspect="equal")
    ax.axis("off")
    fig.tight_layout(pad=0.3)
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Schematic particle kinematics",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
