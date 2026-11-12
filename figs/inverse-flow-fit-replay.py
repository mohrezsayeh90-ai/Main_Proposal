"""Observed-curve quadrature versus independent replay: schematic only.

Run: MPLCONFIGDIR=/tmp/mpl-cache python figs/inverse-flow-fit-replay.py
Source: inverse_fromtrajectory_to_FlowReconstruction, revision d5e9b5a.
The curves below illustrate evaluation locations; no model or ODE is evaluated.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    observed = np.array([[0.25, 0.22], [0.9, 0.34], [1.7, 0.56],
                         [2.55, 0.73], [3.4, 0.64], [4.65, 0.47]])
    # Three Gauss nodes strictly inside each observed segment.
    nodes = (np.polynomial.legendre.leggauss(3)[0] + 1) / 2
    quadrature = (observed[:-1, None] * (1-nodes)[None, :, None]
                  + observed[1:, None] * nodes[None, :, None]).reshape(-1, 2)
    x = np.linspace(observed[0, 0], observed[-1, 0], 321)
    phase = np.maximum(x - observed[1, 0], 0) / (observed[-1, 0]-observed[1, 0])
    replay = np.column_stack((x, np.interp(x, *observed.T) + 0.085*np.sin(np.pi*phase)**2))
    # The replay shares the first segment, hence the same initial tangent.
    fig = plt.figure(figsize=(7.8, 2.9))
    axes = [fig.add_axes([0.07, 0.35, 0.40, 0.48]),
            fig.add_axes([0.57, 0.35, 0.40, 0.48])]
    titles = ["(a) Integral fit (schematic)", "(b) ODE replay (schematic)"]
    for ax, title in zip(axes, titles):
        for y in (0, 1):
            ax.plot([0, 5], [y, y], "k-", lw=1.2)
        ax.set(xlim=(0, 5), ylim=(0, 1), aspect="equal",
                xlabel=r"$x^*$", ylabel=r"$y^*$")
        ax.set_xticks([0, 1, 2, 3, 4, 5])
        ax.set_yticks([0, 1])
        ax.tick_params(length=3, labelsize=10)
        ax.set_title(title, fontsize=10.5, pad=18)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fit, independent = axes
    fit.plot(*observed.T, color="0.4", lw=0.9)
    fit.plot(*observed.T, "o", mfc="white", mec="black", ms=5, zorder=4)
    fit.plot(*quadrature.T, "k.", ms=3.3, zorder=5)
    for point in quadrature[[7, 11]]:
        fit.annotate("", xy=point+[0.44, 0], xytext=point,
                     arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.0})
    fit.text(2.5, 0.11, r"$A\mathbf{U}_\theta^*(\mathbf{r}_{\mathrm{obs}}^*)$",
              ha="center", fontsize=10)
    independent.plot(*observed.T, "--", color="0.72", lw=0.9)
    independent.plot(*observed.T, "o", mfc="white", mec="0.65", ms=4)
    independent.plot(*replay.T, color="black", lw=1.1)
    samples = replay[np.linspace(0, len(replay)-1, 12, dtype=int)]
    independent.plot(*samples.T, "ks", ms=3.3, zorder=4)
    for ax in axes:
        delta = np.array([0.62, 0.62*(observed[1, 1]-observed[0, 1])/(observed[1, 0]-observed[0, 0])])
        ax.annotate("", xy=observed[0]+delta, xytext=observed[0],
                    arrowprops={"arrowstyle": "-|>", "lw": 1.0, "color": "black"})
    independent.text(2.7, 0.11, r"$A\mathbf{U}_\theta^*(\mathbf{r}_{\mathrm{replay}}^*)$",
                     ha="center", fontsize=10)
    fig.text(0.52, 0.91, r"$\mathbf{r}_{p,0}^*,\ \mathbf{v}_{p,0}^*\quad\mathrm{shared}$",
              ha="center", fontsize=11)
    handles = [Line2D([], [], marker="o", mfc="white", mec="black", ls="none",
                      label="Observed positions"),
               Line2D([], [], marker=".", color="black", ls="none", label="Quadrature nodes"),
               Line2D([], [], marker="s", color="black", ls="none", ms=4, label="Replay positions")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.52, 0.04),
                ncol=3, frameon=False, fontsize=10, columnspacing=1.5, handletextpad=0.4)
    fig.canvas.draw()
    for ax in axes:
        origin, dx, dy = ax.transData.transform([[0, 0], [1, 0], [0, 1]])
        assert np.isclose(np.linalg.norm(dx-origin), np.linalg.norm(dy-origin))
    assert np.all((replay[:, 1] > 0) & (replay[:, 1] < 1))
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Observed-curve fit and independent replay, schematic",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
