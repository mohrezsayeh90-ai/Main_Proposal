"""Residual-trained time/space-marching neural benchmark of Mao et al. Fig. 9(a-2)."""
import argparse
import json
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_bvp, solve_ivp
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.special import roots_legendre

OMEGA = 2.
REYNOLDS = 10.
EPSILON = .2
RELAXATION = 2 * EPSILON**2 / 3  # Eq. 5.4 converted from l to h=l/2 scales.
LIFT_FACTOR = EPSILON**3 / (6 * np.pi * np.sqrt(REYNOLDS))
WAVINESS = (0., .05, .1)
LENGTH = 2000.
PERIOD = 2 * np.pi / OMEGA


def path_points(drawing):
    return np.array([(point.x, point.y) for item in drawing["items"]
                     for point in (item[1], item[-1])])


def sampled_stroke(drawing):
    segments = []
    for item in drawing["items"]:
        control = np.array([(point.x, point.y) for point in item[1:]])
        count = max(2, int(np.ceil(np.ptp(control[:, 0]) / .012)) + 1)
        t = np.linspace(0, 1, count)[:, None]
        if item[0] == "l":
            segments.append((1-t)*control[0] + t*control[1])
        elif item[0] == "c":
            segments.append((1-t)**3*control[0] + 3*t*(1-t)**2*control[1]
                            + 3*t*t*(1-t)*control[2] + t**3*control[3])
        else:
            raise ValueError(f"Unexpected path primitive {item[0]}")
    return np.concatenate(segments)


def read_vectors(pdf_path):
    """Read the vector paths of the official Cambridge 42-page PDF."""
    with fitz.open(pdf_path) as pdf:
        force = pdf[16].get_drawings()
        paths = pdf[21].get_drawings()
        assert "Figure 6. Normalized" in pdf[16].get_text()
        assert "Figure 9. (a) Simulated trajectories" in pdf[21].get_text()
    left, _, right, _ = force[25]["rect"]
    zero = force[46]["rect"].y0
    height = force[45]["rect"].height
    points = path_points(force[47])
    z = (points[:, 0] - left) / (right - left)
    z, indices = np.unique(z, return_index=True)
    force_values = (zero - points[indices, 1]) * 40 / height
    force_values[0] = 0.
    interpolator = PchipInterpolator(z, force_values, extrapolate=False)

    left, bottom, right, _ = paths[70]["rect"]
    height = paths[82]["rect"].height
    def to_data(points):
        return np.column_stack(((points[:, 0] - left) * LENGTH / (right - left),
                                (bottom - points[:, 1]) * .8 / height))

    straight = to_data(path_points(paths[105]))
    x, indices = np.unique(straight[:, 0], return_index=True)
    straight = np.column_stack((x, straight[indices, 1]))
    bands = {}
    for amplitude, (downstream, upstream) in {0.05: (103, 104), 0.1: (101, 102)}.items():
        points = to_data(np.concatenate([sampled_stroke(paths[j]) for j in (downstream, upstream)]))
        # The PDF splits the expanded stroke into two closed filled paths.
        # Their join contains artificial cap segments, not a complete trajectory.
        join = to_data(np.array([[paths[downstream]["rect"].x0, bottom],
                                 [paths[upstream]["rect"].x1, bottom]]))[:, 0]
        bands[amplitude] = (points, join)
    return interpolator, np.column_stack((z, force_values)), straight, bands, .25 * .8 / height


def solve_carrier():
    """Solve the real/imaginary split of Eq. 2.5 for the normal Fourier mode."""
    w = OMEGA
    viscosity = 2 / REYNOLDS

    def equation(z, state):
        f = state[:4] + 1j * state[4:]
        d4 = 2 * w*w * f[2] - w**4 * f[0]
        d4 += 1j*w/viscosity * ((1-z*z)*(f[2]-w*w*f[0]) + 2*f[0])
        d = np.vstack((f[1:], d4))
        return np.vstack((d.real, d.imag))

    def wall(a, b):
        return [a[0], b[0], a[1], b[1], a[4], b[4], a[5]-2*w, b[5]-2*w]

    grid = np.linspace(-1, 1, 101)
    coarse = solve_bvp(equation, wall, grid, np.zeros((8, grid.size)), tol=1e-7)
    fine = solve_bvp(equation, wall, grid, coarse.sol(grid), tol=2e-10, max_nodes=10000)
    if not (coarse.success and fine.success):
        raise RuntimeError(fine.message)
    z = np.linspace(-1, 1, 4001)
    grid_error = float(np.max(np.abs(coarse.sol(z) - fine.sol(z))))
    return Carrier(fine.sol), grid_error, float(fine.rms_residuals.max())


class Carrier:
    def __init__(self, solution):
        z = np.linspace(-1, 1, 1201)
        rows = solution(z)
        f = rows[:4] + 1j * rows[4:]
        self.modes = CubicSpline(z, np.column_stack((f[1]/(-1j*OMEGA), f[0],
                                                     f[2]/(-1j*OMEGA), f[1])))

    def values(self, x, z, amplitude):
        wave = amplitude * np.exp(1j * OMEGA * x)
        a, b, da, db = np.moveaxis(self.modes(z), -1, 0)
        return (1-z*z + (wave*a).real, (wave*b).real,
                (1j*OMEGA*wave*a).real, -2*z+(wave*da).real,
                (1j*OMEGA*wave*b).real, (wave*db).real)


def physical_terms(carrier, lift, x, state, amplitude):
    z, sx, sz = np.moveaxis(state, -1, 0)
    u, w, ux, uz, wx, wz = carrier.values(x, z, amplitude)
    axial = u + sx
    forcing_x = -ux*sx - uz*sz
    forcing_z = LIFT_FACTOR * lift(z) / RELAXATION - wx*sx - wz*sz
    return axial, np.stack((w+sz, forcing_x, forcing_z), axis=-1)


def rhs(carrier, lift, x, state, amplitude):
    axial, driving = physical_terms(carrier, lift, x, state, amplitude)
    result = driving.copy()
    result[..., 1:] -= state[..., 1:] / RELAXATION
    return result / np.asarray(axial)[..., None]


class NeuralWindow:
    """Single hidden tanh layer; fit readout weights on physics residual only."""
    def __init__(self, order):
        nodes, _ = roots_legendre(order)
        self.nodes = (nodes + 1)/2
        rng = np.random.default_rng(548)
        self.weight = rng.uniform(1.8, 5.5, size=4*order)
        self.bias = -self.weight * rng.uniform(-.45, 1.45, size=4*order)
        _, singular, right = np.linalg.svd(self.derivative(self.nodes), full_matrices=False)
        self.transform = right.T / singular
        self.trial = self.values(self.nodes) @ self.transform
        self.gradient = self.derivative(self.nodes) @ self.transform

    def values(self, x):
        return np.tanh(x[:, None]*self.weight + self.bias) - np.tanh(self.bias)

    def derivative(self, x):
        return (1 - np.tanh(x[:, None]*self.weight + self.bias)**2)*self.weight

    def solve(self, carrier, lift, amplitude, order_label, window_count):
        edges = np.linspace(0., LENGTH, window_count+1)
        h = edges[1]
        output = np.linspace(0., LENGTH, 80001)
        z_profile = np.empty_like(output)
        state0 = np.array([.1, 0., 0.])
        checkpoints = []
        check_nodes = np.linspace(.013, .987, 19)
        activation_end = self.values(np.array([1.])) @ self.transform
        check_value = self.values(check_nodes) @ self.transform
        check_gradient = self.derivative(check_nodes) @ self.transform / h
        grad = self.gradient / h
        damping = self.trial / RELAXATION
        for i, start in enumerate(edges[:-1]):
            collocation = start + h*self.nodes
            state = np.broadcast_to(state0, (len(self.nodes), 3)).copy()
            for iteration in range(40):
                axial, driving = physical_terms(carrier, lift, collocation, state, amplitude)
                coef_z = np.linalg.solve(grad, driving[:, 0]/axial)
                coef_s = np.linalg.solve(axial[:, None]*grad + damping,
                                        driving[:, 1:] - state0[1:]/RELAXATION)
                weights = np.column_stack((coef_z, coef_s))
                update = state0 + self.trial @ weights
                if np.max(np.abs(update-state)) < 2e-12:
                    break
                state = update
            else:
                raise RuntimeError(f"Residual iteration stalled near X={start:g}")
            check_state = state0 + check_value @ weights
            residual = check_gradient @ weights - rhs(carrier, lift, start+h*check_nodes, check_state, amplitude)
            checkpoints.append(np.max(np.abs(residual), axis=0))
            mask = (output >= start) & (output < edges[i+1] if i+1 < window_count else output <= LENGTH)
            z_profile[mask] = state0[0] + (self.values((output[mask]-start)/h) @ self.transform) @ weights[:, 0]
            state0 = state0 + (activation_end @ weights)[0]
        print("PINN", order_label, amplitude, "max unused point residual",
              np.max(checkpoints, axis=0), flush=True)
        return output, z_profile, np.max(checkpoints, axis=0)


def scipy_reference(carrier, lift, amplitude, x):
    def equation(t, q):
        return rhs(carrier, lift, t, q, amplitude)
    sol = solve_ivp(equation, (0., LENGTH), (.1, 0., 0.),
                    t_eval=x, method="LSODA", rtol=2e-9, atol=2e-11, max_step=.25)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y[0]


def envelopes(x, y, centers, correction=0.):
    lower = []
    upper = []
    for center in centers:
        span = y[(x >= center-PERIOD/2) & (x < center+PERIOD/2)]
        lower.append(np.min(span) + correction if span.size else np.nan)
        upper.append(np.max(span) - correction if span.size else np.nan)
    lo, hi = np.array(lower), np.array(upper)
    return np.minimum(lo, hi), np.maximum(lo, hi)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reuse-trajectories", action="store_true",
                        help="Redraw using trajectories and solver diagnostics from this output directory.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output
    lift, lift_data, straight, bands, stroke = read_vectors(args.pdf)
    carrier, bvp_change, bvp_residual = solve_carrier()
    neural = NeuralWindow(20)
    fine = NeuralWindow(22)
    centers = (np.arange(2, int(LENGTH/PERIOD)-1)+.5)*PERIOD
    cached = {}
    if args.reuse_trajectories:
        report = json.loads((out/"metrics.json").read_text())
        cached = {case["waviness"]: case for case in report["cases"]}
    cases = []
    fig, panels = plt.subplots(1, 3, figsize=(13.3, 4.0), sharex=True, sharey=True,
                               layout="constrained")
    np.savetxt(out/"fig6_lift.csv", lift_data, delimiter=",", comments="",
               header="Z,normalized_zeroth_order_lift")
    for panel, amp in zip(panels, WAVINESS):
        if args.reuse_trajectories:
            x, neural_z, ode_z = np.loadtxt(out/f"trajectory_{amp:g}.csv", delimiter=",",
                                           skiprows=1, usecols=(0, 1, 2), unpack=True)
            pinned = cached[amp]
        else:
            x, neural_z, residual = fine.solve(carrier, lift, amp, "fine", 1600)
            _, coarse_z, _ = neural.solve(carrier, lift, amp, "coarse", 1000)
            ode_z = scipy_reference(carrier, lift, amp, x)
            pinned = {"waviness": amp, "max_residual": residual.tolist(),
                      "max_pinn_vs_ode": float(np.max(np.abs(neural_z-ode_z))),
                      "max_neural_refinement_change": float(np.max(np.abs(neural_z-coarse_z)))}
        if amp == 0:
            published_z = np.interp(x, straight[:, 0], straight[:, 1], left=np.nan, right=np.nan)
            mask = (x >= 10) & (x <= 1990)
            error = neural_z[mask]-published_z[mask]
            pinned.update(figure_rmse=float(np.sqrt(np.mean(error**2))),
                          figure_max_abs_error=float(np.max(np.abs(error))),
                          published_plateau=float(np.nanmean(published_z[x > 1900])),
                          neural_plateau=float(np.mean(neural_z[x > 1900])))
            panel.plot(x, published_z, "--", color=".22", lw=1.6, label="Mao et al., Fig. 9(a-2)")
            panel.plot(x, neural_z, color="#007b71", lw=1.2, label="Neural solution")
            data = np.column_stack((x, neural_z, ode_z, published_z))
            header = "X,Z_neural,Z_ode,Z_published"
        else:
            published, join = bands[amp]
            low_ref, high_ref = envelopes(*published.T, centers, stroke)
            low, high = envelopes(x, neural_z, centers)
            away_from_join = (centers+PERIOD/2 < min(join)) | (centers-PERIOD/2 > max(join))
            valid = np.isfinite(low_ref) & np.isfinite(high_ref) & away_from_join
            if valid.sum() < .95*len(valid):
                raise RuntimeError("Incomplete published vector envelope")
            for boundary in (low_ref, high_ref):
                boundary[~valid] = np.interp(centers[~valid], centers[valid], boundary[valid])
            mask = (centers >= 20) & (centers <= 1980) & valid
            error = np.concatenate((low[mask]-low_ref[mask], high[mask]-high_ref[mask]))
            tail = (centers > 1800) & (centers < 1950)
            pinned.update(figure_envelope_rmse=float(np.sqrt(np.mean(error**2))),
                          figure_envelope_max_abs_error=float(np.max(np.abs(error))),
                          figure_envelope_period_count=int(mask.sum()),
                          interpolated_pdf_join_centers=centers[~valid].tolist(),
                          published_plateau=[float(np.median(low_ref[tail])),float(np.median(high_ref[tail]))],
                          neural_plateau=[float(np.median(low[tail])),float(np.median(high[tail]))])
            panel.fill_between(centers, low_ref, high_ref, color=".75", label="Published envelope")
            panel.plot(centers, low, color="#007b71", lw=1.2, label="Neural envelope")
            panel.plot(centers, high, color="#007b71", lw=1.2)
            np.savetxt(out/f"envelope_{amp:g}.csv",
                       np.column_stack((centers, low_ref, high_ref, low, high, mask.astype(int))), delimiter=",",
                       comments="", header="X,published_low,published_high,neural_low,neural_high,used_for_error")
            data = np.column_stack((x, neural_z, ode_z))
            header = "X,Z_neural,Z_ode"
        if not args.reuse_trajectories:
            np.savetxt(out/f"trajectory_{amp:g}.csv", data, delimiter=",", comments="", header=header)
        panel.set(title=rf"$\epsilon_w={amp:g}$", xlabel=r"$X_p$", xlim=(0, 2000), ylim=(.075,.71))
        panel.grid(alpha=.22)
        panel.legend(loc="lower right", frameon=False, fontsize=8)
        cases.append(pinned)
        print(json.dumps(pinned), flush=True)
    panels[0].set_ylabel(r"$Z_p$")
    fig.suptitle("Particle focusing in a wavy channel", fontsize=15)
    fig.savefig(out/"wavy_fig9_comparison.png", dpi=240)
    fig.savefig(out/"wavy_fig9_comparison.pdf")
    metrics = {"reference": "Mao, Bischofberger & Hosoi, doi:10.1017/jfm.2023.558",
               "lift_input": "Fig. 6 Rc=10 vector curve, PCHIP; Fig. 9 excluded from fit",
               "comparison": "Fig. 9(a-2) vector paths; one-period envelopes",
               "carrier_bvp_max_mesh_change": bvp_change, "carrier_bvp_max_residual": bvp_residual,
               "cases": cases}
    (out/"metrics.json").write_text(json.dumps(metrics, indent=2)+"\n")


if __name__ == "__main__":
    main()
