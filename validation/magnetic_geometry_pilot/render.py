"""Render the thesis panels and verify the metrics against the archived arrays."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import numpy as np

CASES = (
    ("constant_left", "A  Constant left source"),
    ("source_switch", "B  Smooth source switch"),
    ("alternating", "C  Alternating sources"),
    ("short_pulse", "D  Short pulse"),
)
R_UM = 75.0
TIME_SCALE = 4 / 3
FIELD_SCALE = .05 * np.pi  # B_s in tesla from magnetic_operator.physics
PRED, REPLAY, TARGET = "#235990", "#ad452a", "#20252e"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / "figs" / "chapter4"


def style(ax, bins=3):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=.19, linewidth=.45)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(bins))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax.tick_params(length=2.4, pad=2.5)


def pair(fig, grid, i):
    cell = grid[i // 2, i % 2].subgridspec(2, 1, height_ratios=[1.42, 1], hspace=.12)
    top = fig.add_subplot(cell[0])
    bottom = fig.add_subplot(cell[1], sharex=top)
    style(top)
    style(bottom)
    top.tick_params(labelbottom=False)
    return top, bottom


def save(fig, directory, name):
    for extension in ("pdf", "png"):
        fig.savefig(directory / f"{name}.{extension}", dpi=320, facecolor="white")


def check(row, data):
    def error(values):
        residual = values - data["x_target"]
        return np.sqrt(np.mean(residual**2)), np.max(np.abs(residual))
    geom = data["replay"]
    path = data["predicted_path"]
    z = data["z"]
    np.testing.assert_allclose(data["x_nn"], np.interp(z, path[:, 1], path[:, 0]))
    np.testing.assert_allclose(data["x_replay"], np.interp(z, geom[:, 1], geom[:, 0]))
    for label, series in (("model", data["x_nn"]), ("replay", data["x_replay"]),
                          ("zero_field", np.full_like(z, data["x_target"][0]))):
        np.testing.assert_allclose(error(series), [row[label]["rmse_X"], row[label]["max_X"]])
    assert len(z) == 401 and geom[-1, 1] >= z[-1]
    assert np.all(np.diff(geom[:, 1]) > 0) and np.all(np.diff(path[:, 1]) > 0)
    assert np.max(np.abs(geom[:, 0])) <= .7
    assert np.min(geom[:, 1]) >= -2 and np.max(geom[:, 1]) <= 1.7
    assert np.max(np.abs(data["controls"]).sum(axis=1)) <= np.sqrt(.5)
    assert np.isclose(data["tau_hit"] * TIME_SCALE, row["time_s"])
    assert row["pilot_pass"] == (row["replay"]["max_X"] <= .01)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.titlesize": 8.5, "pdf.fonttype": 42})
    pf = plt.figure(figsize=(6.5, 5.35))
    cf = plt.figure(figsize=(6.5, 5.35))
    grids = [f.add_gridspec(2, 2, left=.114, right=.982, bottom=.088, top=.86,
                           wspace=.32, hspace=.42) for f in (pf, cf)]
    table = []

    for i, (name, title) in enumerate(CASES):
        row = json.loads((ROOT / "out" / f"{name}.json").read_text())
        with np.load(ROOT / "out" / f"{name}.npz", allow_pickle=False) as d:
            check(row, d)
            ax, res = pair(pf, grids[0], i)
            z = d["z"]
            x, y, q = [d[k] for k in ("x_target", "x_nn", "x_replay")]
            ax.set_title(title, loc="left", weight="bold", pad=4)
            ax.plot(z, x, color=TARGET, linewidth=2, label="Target")
            ax.plot(z, y, color=PRED, linestyle="--", linewidth=1.1)
            ax.plot(z, q, color=REPLAY, linestyle=":", linewidth=1.1)
            ax.set_ylabel(r"$X=x/R$")
            res.axhline(0, color="#777d85", linewidth=.7)
            res.plot(z, 1000 * (y - x), color=PRED, linestyle="--", linewidth=1.1)
            res.plot(z, 1000 * (q - x), color=REPLAY, linewidth=1)
            res.set_ylabel(r"$10^3\,\Delta X$")
            res.ticklabel_format(axis="y", style="plain", useOffset=False)
            res.set_xlabel(r"Axial coordinate $Z=z/D$")
            ax, bx = pair(cf, grids[1], i)
            ax.set_title(title, loc="left", weight="bold", pad=4)
            hit = float(d["tau_hit"])
            k = np.r_[d["knots"][d["knots"] < hit], hit]
            t = np.r_[d["tau"][d["tau"] < hit], hit]
            for j, color in enumerate((PRED, REPLAY)):
                ax.plot(k, np.interp(k, d["knots"], d["controls"][:, j]),
                        color=color, linewidth=1.3)
                bx.plot(t, np.interp(t, d["tau"], d["B_T"][:, j]) / FIELD_SCALE,
                        color=color, linewidth=1.3)
            ax.set_ylabel("Drive amplitude")
            bx.set_ylabel(r"Field $B/B_s$")
            bx.set_xlabel(r"Replay time $\tau=t/T_s$")
            table.append({"case": name, "span_um": R_UM*row["transverse_span_X"],
                          "zero_field_rmse_um": R_UM*row["zero_field"]["rmse_X"],
                          "model_rmse_um": R_UM*row["model"]["rmse_X"],
                          "replay_rmse_um": R_UM*row["replay"]["rmse_X"],
                          "replay_max_um": R_UM*row["replay"]["max_X"],
                          "arrival_s": row["time_s"], "iterations": row["iterations"],
                          "optimizer_converged": row["optimizer_converged"]})

    pf.legend(handles=[Line2D([], [], color=TARGET, label="DOP853 target"),
                       Line2D([], [], color=PRED, linestyle="--", label="Master10 prediction"),
                       Line2D([], [], color=REPLAY, label="Independent replay")],
              loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.52,.965))
    cf.legend(handles=[Line2D([], [], color=PRED, label=r"$a_L$ (upper), $B_x/B_s$ (lower)"),
                       Line2D([], [], color=REPLAY, label=r"$a_R$ (upper), $B_z/B_s$ (lower)")],
              loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(.54,.965))
    save(pf, args.output, "inverse-master10-geometry-replay")
    save(cf, args.output, "inverse-master10-geometry-field")
    with (ROOT / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=table[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)


if __name__ == "__main__":
    main()
