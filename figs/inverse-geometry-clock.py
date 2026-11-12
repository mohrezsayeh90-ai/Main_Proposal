"""Equal arc-length sampling and an illustrative positive hidden clock.

Run: MPLCONFIGDIR=/tmp/mpl-cache python figs/inverse-geometry-clock.py
Source: inverse_fromtrajectory_to_FlowReconstruction, revision d5e9b5a.
Clock plotting coordinates are symbolic; no measured or recovered times are used.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    vertices = np.array([[0.3, 0.2], [1.1, 0.4], [1.9, 0.65], [3.1, 0.7], [4.6, 0.48]])
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(vertices, axis=0), axis=1))]
    uniform = np.linspace(0, arc[-1], 12)
    points = np.column_stack([np.interp(uniform, arc, vertices[:, j]) for j in (0, 1)])
    fig = plt.figure(figsize=(7.8, 3.1))
    geometry = fig.add_axes([0.07, 0.23, 0.41, 0.62])
    for y in (0, 1):
        geometry.plot([0, 5], [y, y], "k-", lw=1.2)
    geometry.plot(*vertices.T, color="black", lw=1.0)
    geometry.plot(*points.T, "o", mfc="white", mec="black", ms=4.5)
    geometry.set(xlim=(0, 5), ylim=(0, 1), aspect="equal",
                  xlabel=r"$x^*$", ylabel=r"$y^*$")
    geometry.set_xticks([0, 1, 2, 3, 4, 5]); geometry.set_yticks([0, 1])
    geometry.tick_params(length=3, labelsize=10)
    geometry.set_title("(a) Ordered geometry (schematic)", fontsize=10.5, pad=18)
    for spine in geometry.spines.values():
        spine.set_visible(False)
    geometry.annotate("", xy=vertices[-1]-[0.10, -0.03], xytext=vertices[-1]-[0.7, -0.13],
                       arrowprops={"arrowstyle": "->", "lw": 1.1})
    geometry.text(2.5, 0.1, r"$\Delta s^*=\mathrm{constant}$", ha="center", fontsize=10)

    clock = fig.add_axes([0.66, 0.23, 0.29, 0.62])
    s = np.linspace(0, 1, 201)
    t = s + 0.6*s*s
    assert np.all(np.diff(t) > 0) and t[0] == 0
    clock.plot(s, t, "k-", lw=1.3)
    clock.plot(s[:55], s[:55], "k--", lw=0.9)
    clock.plot([1], [t[-1]], "ko", ms=4)
    clock.set(xlim=(0, 1.05), ylim=(0, 1.85), xlabel=r"$s^*$", ylabel=r"$t_i^*$")
    clock.set_xticks([0, 1], [r"$0$", r"$L_i^*$"])
    clock.set_yticks([0, t[-1]], [r"$0$", r"$t_i^*(L_i^*)$"])
    clock.set_title("(b) Hidden clock (schematic)", fontsize=10.5, pad=18)
    clock.spines[["top", "right"]].set_visible(False)
    clock.annotate(r"$\left.\frac{\mathrm{d}t_i^*}{\mathrm{d}s^*}\right|_0=\frac{1}{\|\mathbf{v}_{p,i,0}^*\|}$",
                    xy=(0.20, 0.20), xytext=(0.12, 1.1), fontsize=10,
                    arrowprops={"arrowstyle": "->", "lw": 0.8})
    clock.tick_params(length=3)
    fig.canvas.draw()
    origin, dx, dy = geometry.transData.transform([[0, 0], [1, 0], [0, 1]])
    assert np.isclose(np.linalg.norm(dx-origin), np.linalg.norm(dy-origin))
    assert np.allclose(np.diff(uniform), uniform[1])
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Ordered arc-length samples and symbolic monotone clock",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
