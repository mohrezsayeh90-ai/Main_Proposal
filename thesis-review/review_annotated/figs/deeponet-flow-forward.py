"""Section 3.3: schematic of the flow operator, not a computed flow result.

Run: MPLCONFIGDIR=/tmp/mpl-cache python figs/deeponet-flow-forward.py
Source: inverse_fromtrajectory_to_FlowReconstruction, revision d5e9b5a.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def main():
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11,
                         "mathtext.fontset": "dejavuserif", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(7.3, 6.2))
    fig.text(0.02, 0.97, r"$(a)$", fontsize=13)
    channel = fig.add_axes([0.10, 0.78, 0.85, 0.19])
    channel.plot([0, 5], [0, 0], "k-", lw=1.4)
    channel.plot([0, 5], [1, 1], "k-", lw=1.4)
    y = np.linspace(0, 1, 201)
    inlet = 30 * y**2 * (1 - y)**2
    # Arrow lengths depict an illustrative profile, not particle trajectories.
    channel.plot(0.35 * inlet, y, "k:", lw=0.9)
    for yy in np.linspace(0.125, 0.875, 7):
        channel.add_patch(FancyArrowPatch((0, yy), (0.35 * 30 * yy**2 * (1-yy)**2, yy),
                                          arrowstyle="->", mutation_scale=8, lw=0.8))
    channel.text(1.1, 0.48, r"$f^*(y^*)=30(y^*)^2(1-y^*)^2$", va="center")
    channel.text(3.6, 0.92, r"$\mathbf{U}^*=\mathbf{0}$", va="top", fontsize=10)
    channel.set(xlim=(0, 5), ylim=(0, 1), aspect="equal",
                xlabel=r"$x^*$", ylabel=r"$y^*$")
    channel.set_xticks([0, 1, 2, 3, 4, 5])
    channel.set_yticks([0, 1])
    channel.tick_params(length=3, pad=3)
    for spine in channel.spines.values():
        spine.set_visible(False)

    fig.text(0.02, 0.66, r"$(b)$", fontsize=13)
    ax = fig.add_axes([0.025, 0.025, 0.95, 0.61])
    ax.set(xlim=(-0.2, 12), ylim=(-0.2, 8))
    ax.axis("off")

    def box(x, y, w, h, text, shade="white", size=10):
        ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
                                    boxstyle="round,pad=0.08,rounding_size=0.07",
                                    facecolor=shade, edgecolor="black", lw=0.9))
        ax.text(x, y, text, ha="center", va="center", fontsize=size, linespacing=1.5)

    def arrow(points, dashed=False):
        for p, q in zip(points[:-2], points[1:-1]):
            ax.plot([p[0], q[0]], [p[1], q[1]], color="black", lw=0.9,
                    ls="--" if dashed else "-")
        ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="->",
                                     mutation_scale=10, lw=0.9,
                                     linestyle="--" if dashed else "-"))

    box(1.1, 6.7, 2.0, 1.0, "Cubic spline\n" + r"$f^*$")
    box(4.15, 6.7, 2.8, 1.4,
        "257 uniform samples\n" + r"$\Delta f^*=f^*-f_{\mathrm{P}}^*$" + "\n" +
        r"$\mathrm{Re},\ \kappa$", size=10)
    box(7.35, 6.7, 2.0, 1.0, "Branches\n" + r"$b_\psi,\ b_p$")
    box(10.4, 6.7, 2.4, 1.0, r"$(x^*,y^*)$" + "\nTrunks " + r"$t_\psi,\ t_p$")
    box(1.1, 4.4, 2.0, 1.1, "Full integral\n" + r"$I=\int_0^{y^*}f^*(\xi)\,\mathrm{d}\xi$", size=10)
    box(4.15, 4.4, 2.8, 1.1, "Boundary lift\n" + r"$\psi_{\mathrm{lift}}^*,\ p_{\mathrm{O}}^*$", shade="0.95")
    box(8.8, 4.4, 3.0, 1.1, "Learned corrections\n" + r"$N_\psi,\ N_p$", shade="0.95")
    box(5.5, 2.4, 3.1, 1.15,
        "Lift + corrections\n" + r"$(\psi^*,p^*)$", size=10)
    box(10.1, 2.4, 2.7, 1.15, "Carrier field\n" + r"$(u^*,v^*,p^*)$", shade="0.93")
    box(10.1, 0.45, 2.7, 1.0, "Stokes ODE\n" + r"$t_{\mathrm{s}}^*,\ A,\ \mathrm{St}$", shade="0.93")
    box(5.5, 0.45, 3.1, 1.0, "Particle path\n" + r"$\mathbf{r}_p^*(t_{\mathrm{s}}^*)$")

    arrow([(2.18, 6.7), (2.67, 6.7)])
    arrow([(5.63, 6.7), (6.27, 6.7)])
    arrow([(1.1, 6.12), (1.1, 5.03)], dashed=True)
    arrow([(2.18, 4.4), (2.67, 4.4)], dashed=True)
    arrow([(7.35, 6.12), (7.35, 5.5), (8.15, 5.5), (8.15, 5.03)])
    arrow([(10.4, 6.12), (10.4, 5.5), (9.5, 5.5), (9.5, 5.03)])
    arrow([(4.15, 3.77), (4.15, 3.25), (4.7, 3.25), (4.7, 3.05)], dashed=True)
    arrow([(8.8, 3.77), (8.8, 3.25), (6.3, 3.25), (6.3, 3.05)])
    arrow([(7.13, 2.4), (8.67, 2.4)])
    ax.text(7.86, 2.68, "derivatives",
            ha="center", fontsize=10)
    arrow([(10.1, 1.75), (10.1, 1.03)])
    arrow([(8.67, 0.45), (7.13, 0.45)])

    fig.canvas.draw()
    origin, dx, dy = channel.transData.transform([[0, 0], [1, 0], [0, 1]])
    assert np.isclose(np.linalg.norm(dx-origin), np.linalg.norm(dy-origin))
    fig.savefig(Path(__file__).with_suffix(".pdf"), bbox_inches="tight",
                metadata={"Title": "Forward flow DeepONet and separate Stokes solver",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
