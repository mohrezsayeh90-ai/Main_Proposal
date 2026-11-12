"""Implemented Master9 scalar tracking loop and independent inertial replay.

Run: MPLCONFIGDIR=/tmp/mpl-cache python figs/inverse-magnetic-master9.py
Source: Master_Magnetic, revision a4fc9d7, master9/control.py and physics.py.
This chart contains no Master10 experiment or numerical tracking results.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.set(xlim=(-0.5, 10.3), ylim=(-1.0, 6.9))
    ax.axis("off")

    def box(x, y, w, h, text, shade="white", size=10):
        ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
                                    boxstyle="round,pad=0.08,rounding_size=0.07",
                                    facecolor=shade, edgecolor="black", lw=0.9))
        ax.text(x, y, text, ha="center", va="center", fontsize=size, linespacing=1.5)

    def arrow(points, dashed=False):
        for a, b in zip(points[:-2], points[1:-1]):
            ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=0.9,
                    ls="--" if dashed else "-")
        ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="->",
                                     mutation_scale=10, lw=0.9,
                                     linestyle="--" if dashed else "-"))

    box(1.0, 6.1, 2.2, 0.8, r"$X_{\mathrm{tar}}(Z)$")
    box(1.0, 4.35, 2.2, 1.0, r"$(\mathbf{q}_k,\mathbf{V}_k)$")
    box(4.3, 4.35, 2.3, 1.35, r"$\mathcal{T}_9$" + "\n" + r"$h_9=0.025$")
    box(8.2, 4.35, 3.3, 1.35, r"$e_k(c)$" + "\n" +
        r"$X_{k+1}(c)-X_{\mathrm{tar}}(Z_{k+1}(c))$", size=9)
    box(8.2, 2.05, 3.3, 1.7,
        r"$e_k(-0.5)e_k(0.5)\leq0:\ \mathrm{root}$" + "\n" +
        r"$\mathrm{else}:\ \arg\min_{c\in\{-0.5,0,0.5\}}|e_k(c)|$", size=9)
    box(4.3, 2.05, 2.3, 1.2, r"$c_k\in[-0.5,0.5]$" + "\n" + r"$c=c_k$", shade="0.95")
    box(4.3, -0.15, 3.0, 1.0, r"$\mathcal{T}_9(\mathbf{q}_k,\mathbf{V}_k,c_k)$" + "\n" +
        r"$(\mathbf{q}_{k+1},\mathbf{V}_{k+1})$", shade="0.95")
    box(8.2, -0.15, 3.3, 1.0, "Independent Radau\n" +
        r"$(\mathbf{q}_{k+1}^{\mathrm{R}},\mathbf{V}_{k+1}^{\mathrm{R}})$", shade="0.95")
    arrow([(2.18, 4.35), (3.07, 4.35)])
    arrow([(5.53, 4.35), (6.47, 4.35)])
    arrow([(2.18, 6.1), (8.2, 6.1), (8.2, 5.10)])
    arrow([(8.2, 3.60), (8.2, 2.98)])
    arrow([(6.47, 2.05), (5.53, 2.05)])
    arrow([(4.3, 2.73), (4.3, 3.60)])
    arrow([(4.3, 1.37), (4.3, 0.43)])
    arrow([(2.72, -0.15), (-0.32, -0.15), (-0.32, 3.2), (1.0, 3.2), (1.0, 3.77)])
    ax.text(0.7, 0.15, r"$k\leftarrow k+1$", fontsize=10)
    arrow([(5.53, 1.77), (6.1, 1.77), (6.1, 0.85), (8.2, 0.85), (8.2, 0.43)], dashed=True)
    ax.text(7.15, 0.72, r"$\{c_k\}_{k\geq0}$", ha="center", va="top", fontsize=10)
    fig.tight_layout(pad=0.2)
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Implemented Master9 tracking and independent Radau replay",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
