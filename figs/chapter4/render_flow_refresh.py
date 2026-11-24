#!/usr/bin/env python3
"""Validate staged results, then render the thesis panels with their original builders."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline

import plot_forward_results as forward_plot
import plot_inverse_results as inverse_plot
import plot_particle_count as count_plot
from refresh_flow_inputs import (
    ARCHIVE_REVISION, CASES, CHECKPOINT_PATH, CHECKPOINT_SHA, GEOMETRY, SOAP_REVISION,
    read_json, revision, sha,
)

BASELINE_SHA = "ccf6fa2b3e179a22c443384083e2dec338fc497f9562a567ed7e0955d3c67bf8"
THESIS_BASELINE = "993bb19cc445a6ad4c3961fdcacb73fef449b01c"
FIGURES = Path(__file__).parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_csv(path):
    return np.genfromtxt(path, delimiter=",", names=True)


def rel_l2(actual, reference):
    return float(np.linalg.norm(actual - reference) / np.linalg.norm(reference))


def rendering_style(group):
    plt.rcdefaults()
    tick_size = 8 if group == "count" else 7.5
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
                         "xtick.labelsize": tick_size, "ytick.labelsize": tick_size,
                         "axes.linewidth": .65, "pdf.fonttype": 42})
    if group != "count":
        plt.rcParams.update({"legend.fontsize": 8, "savefig.facecolor": "white"})


def figure_record(out, filename, renderer, experiment, references, labels, old_source):
    relative = f"figs/chapter4/{filename}"
    baseline = subprocess.check_output(
        ["git", "-C", str(FIGURES), "show", f"{THESIS_BASELINE}:{relative}"]
    )
    return dict(
        figure=relative, renderer=renderer,
        experiment=experiment, reference_sha256=references, latex_labels=labels,
        old_thesis_revision=THESIS_BASELINE, old_source_revision=old_source,
        old_checkpoint_sha256=BASELINE_SHA, old_pdf_sha256=hashlib.sha256(baseline).hexdigest(),
        new_source_revision=SOAP_REVISION, new_checkpoint_sha256=CHECKPOINT_SHA,
        new_pdf_sha256=sha(out / filename),
    )


def forward(staging, archive, out):
    base = staging / "forward/forward"
    report = read_json(base / "metrics.json")
    assert report["step"] == 314000 and report["checkpoint_sha256"] == CHECKPOINT_SHA
    by_name = {case["name"]: case for case in report["cases"]}
    baseline_dir = archive / forward_plot.FLOW_FOLDER / "validation_best_checkpoint"
    baseline_report = read_json(baseline_dir / "metrics.json")
    assert baseline_report["checkpoint_sha256"] == BASELINE_SHA
    comparison = out / "shared-scale"
    comparison.mkdir()
    figures = []
    for name in forward_plot.CASES:
        original = archive / "validation/references" / f"{name}.npz"
        with np.load(base / f"{name}.npz", allow_pickle=False) as raw:
            values = dict(raw)
        with np.load(original, allow_pickle=False) as data:
            np.testing.assert_array_equal(values["xy"], data["xy"])
            np.testing.assert_array_equal(values["reference"], data["reference"])
        x, y = (np.unique(values["xy"][:, i]) for i in range(2))
        assert (len(x), len(y), len(values["xy"])) == (73, 97, 7081)
        ix, iy = np.searchsorted(x, values["xy"][:, 0]), np.searchsorted(y, values["xy"][:, 1])
        assert len(np.unique(iy * len(x) + ix)) == 7081
        values.update(x=x, y=y, ix=ix, iy=iy)
        ref, pred = values["reference"], values["prediction"]
        computed = dict(velocity_relative_l2=rel_l2(pred[:, :2], ref[:, :2]),
                        v_relative_l2=rel_l2(pred[:, 1], ref[:, 1]),
                        v_rmse=float(np.sqrt(np.mean((pred[:, 1] - ref[:, 1])**2))),
                        pressure_relative_l2=rel_l2(pred[:, 2], ref[:, 2]))
        for key, value in computed.items():
            np.testing.assert_allclose(value, by_name[name][key], rtol=1e-10, atol=1e-14)
        np.testing.assert_allclose(values["inlet_requested"][[0, -1]], 0, atol=1e-14)
        np.testing.assert_allclose(np.trapezoid(values["inlet_requested"], values["inlet_y"]),
                                   1, atol=2e-6, rtol=0)
        report_case = by_name[name]
        report_case["reference_sha256"] = sha(original)
        report_case["arrays_sha256"] = sha(base / f"{name}.npz")
        if name in ("beta", "nine"):
            forward_plot.maps(values, out, name)
            with np.load(baseline_dir / f"{name}.npz", allow_pickle=False) as raw:
                baseline = dict(values)
                baseline.update(raw)
            for key in ("xy", "reference", "inlet_y", "inlet_requested"):
                np.testing.assert_array_equal(values[key], baseline[key])
            forward_plot.maps(baseline, comparison, f"{name}-94000", scale_with=values)
            forward_plot.maps(values, comparison, f"{name}-314000", scale_with=baseline)
            figures.append(figure_record(out, f"forward-flow-{name}.pdf", "plot_forward_results.maps",
                                         name, {name: sha(original)},
                                         [f"fig:results-forward-flow-{name}", "tab:results-forward-flow-errors"],
                                         forward_plot.FLOW_REV))
    write_json(out / "forward.json", dict(report, figures=figures))


def timed(staging, archive, out, soap):
    import jax
    import jax.numpy as jnp
    from flow_reconstruction.io import load_fit

    jax.config.update("jax_enable_x64", True)
    checkpoint = soap / CHECKPOINT_PATH
    assert sha(checkpoint) == CHECKPOINT_SHA
    base = staging / "timed"
    sources = read_json(archive / GEOMETRY / "comparison_sources.json")
    figures = []
    cases = {}
    for name in CASES:
        source = archive / sources[name]
        folder = base / name
        report = read_json(folder / "report.json")
        assert report["forward_checkpoint_sha256"] == CHECKPOINT_SHA
        assert report["forward_training_step"] == 314000 and report["forward_weights_unchanged"]
        assert report["config"] == read_json(source / "report.json")["config"]
        reference_meta = read_json(folder / "reference.json")
        with np.load(folder / "truth_comparison.npz", allow_pickle=False) as raw:
            arrays = dict(raw)
        reference = archive / reference_meta["path"]
        assert sha(reference) == reference_meta["sha256"]
        with np.load(reference, allow_pickle=False) as raw:
            for key in ("xy", "reference"):
                np.testing.assert_array_equal(arrays[key], raw[key])
        model, theta = load_fit(folder / "fitted_model.json", checkpoint, allow_unvalidated=True)
        shape, speed, reynolds = model.decode(jnp.asarray(theta))
        profile = {key: values[None] for key, values in model.builder.arrays(shape).items()}
        sample = np.linspace(0, len(arrays["xy"]) - 1, 129, dtype=int)
        own_units = np.asarray(model.functions["fields"](
            model.params, profile, reynolds[None], arrays["xy"][None, sample]
        ))[0]
        np.testing.assert_allclose(arrays["prediction"][sample],
                                   own_units * [speed, speed, speed**2], rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(arrays["inlet_prediction"],
                                   model.builder.inlet(shape).spline(arrays["inlet_y"]) * speed,
                                   rtol=1e-11, atol=1e-12)
        assert np.isfinite(arrays["prediction"]).all()
        observed_files = read_json(source / "problem.json")["tracks"]
        tracks = []
        for index, item in enumerate(observed_files, start=1):
            origin = source / item["csv"]
            observed = read_csv(folder / f"observed_track_{index}.csv")
            replay = read_csv(folder / f"track_{index}_forward.csv")
            np.testing.assert_array_equal(observed, read_csv(origin))
            np.testing.assert_array_equal(replay["t"], observed["t"][:len(replay)])
            np.testing.assert_array_equal(inverse_plot.xy(replay)[0], inverse_plot.xy(observed)[0])
            position_rmse = float(np.sqrt(np.mean((inverse_plot.xy(replay) -
                                                     inverse_plot.xy(observed)[:len(replay)])**2)))
            score = report["trajectories"][index - 1]
            np.testing.assert_allclose(position_rmse, score["position_rmse"], rtol=1e-10)
            assert score["completed"] and len(replay) == len(observed), (name, index, score)
            tracks.append(dict(obs=observed, replay=replay))
        prediction, reference_values = arrays["prediction"], arrays["reference"]
        selected = next(candidate for candidate in report["candidates"]
                        if candidate["start"] == report["selected_start"])
        cases[name] = dict(
            mean_speed=report["mean_speed"], reynolds=report["reynolds"],
            velocity_relative_l2=rel_l2(prediction[:, :2], reference_values[:, :2]),
            pressure_relative_l2=rel_l2(prediction[:, 2], reference_values[:, 2]),
            inlet_relative_l2=rel_l2(arrays["inlet_prediction"], arrays["inlet_truth"]),
            optimizer={key: selected[key]
                       for key in ("start", "iterations", "optimizer_success", "optimizer_message")},
            maximum_iterations=report["config"]["max_iterations"],
            inverse_config=report["config"], replays=report["trajectories"], reference=reference_meta,
        )
        if name == "corners_beta5":
            inverse_plot.timed_replay(dict(tracks=tracks, arrays=arrays), out)
            inverse_plot.fields(arrays, out)
            with np.load(reference, allow_pickle=False) as original:
                baseline = dict(original)
            comparison = out / "shared-scale"
            for label, data, other in (("94000", baseline, arrays), ("314000", arrays, baseline)):
                folder = comparison / label
                folder.mkdir(parents=True)
                inverse_plot.fields(data, folder, scale_with=other)
            for suffix, function in (("replay", "timed_replay"), ("fields", "fields")):
                figures.append(figure_record(
                    out, f"inverse-timed-{suffix}.pdf", f"plot_inverse_results.{function}", name,
                    {reference_meta["path"]: reference_meta["sha256"],
                     **reference_meta["observations_sha256"]},
                    [f"fig:results-inverse-timed-{suffix}", "tab:results-inverse-timed"],
                    inverse_plot.FLOW_REV,
                ))
    write_json(out / "timed.json", dict(cases=cases, figures=figures))


def csv_record(columns):
    return np.rec.fromarrays(list(columns.values()), names=list(columns))


def baseline_geometry_limits(archive):
    comparisons = archive / GEOMETRY / "comparisons"
    peak, upper = 0, {}
    margin = plt.rcParams["axes.ymargin"]
    for name in CASES:
        inlet = read_csv(comparisons / name / "inlet_comparison.csv")
        peak = max(peak, inlet["timed_u"].max(), inlet["no_time_u"].max())
        distance = [read_csv(comparisons / name / f"geometric_error_{i}.csv") for i in (1, 2)]
        values = 1e4 * np.concatenate([data[field] for data in distance
                                      for field in ("timed_distance_H", "no_time_distance_H")])
        upper[name] = float(values.max() + margin * np.ptp(values))
    return dict(inlet_upper=float(1.05 * peak), distance_upper=upper)


def geometry(staging, archive, out, soap):
    from flow_reconstruction.io import load_fit, read_problem
    from flow_reconstruction.particles import Track
    from flow_reconstruction_no_time.geometry import curve_metrics, point_polyline_distance, resample_curve
    checkpoint = soap / CHECKPOINT_PATH
    assert sha(checkpoint) == CHECKPOINT_SHA
    sources = read_json(archive / GEOMETRY / "comparison_sources.json")
    data_dir = out / "comparison_data"
    data_dir.mkdir()
    plot_data, evidence, durations, inputs = {}, {}, [], {}
    for name in CASES:
        geometry_input = archive / GEOMETRY / "experiments" / name
        geometry_folder = staging / "geometry" / name
        timed_folder = staging / "timed" / name
        old_problem = archive / sources[name] / "problem.json"
        tracks, _, _ = read_problem(old_problem)
        report = read_json(geometry_folder / "report.json")
        old_report = read_json(geometry_input / "result/report.json")
        assert report["checkpoint_sha256"] == CHECKPOINT_SHA and report["forward_weights_unchanged"]
        assert not report["measured_timestamps_used"] and not report["timed_fit_initialization_used"]
        assert report["config"] == old_report["config"] and report["flow_config"] == old_report["flow_config"]
        inputs[name] = read_json(geometry_folder / "input_sha256.json")
        inputs[name].update(read_json(timed_folder / "reference.json")["observations_sha256"])
        model, theta = load_fit(timed_folder / "fitted_model.json", checkpoint, allow_unvalidated=True)
        timed_report = read_json(timed_folder / "report.json")
        arrays = {}
        panel_tracks, paths = [], []
        for index, track in enumerate(tracks, start=1):
            raw = inverse_plot.xy(read_csv(geometry_input / "input" / f"curve_{index}.csv"))
            np.testing.assert_allclose(raw, resample_curve(track.position, 257)[0], atol=1e-14)
            observed = csv_record(dict(x=track.position[:, 0], y=track.position[:, 1]))
            t = np.linspace(track.time[0], track.time[-1], 1001)
            interpolated = np.column_stack([np.interp(t, track.time, q) for q in track.position.T])
            dense_track = Track(track.name, t, interpolated, track.initial_velocity, track.stokes_time)
            replay = model.simulate(theta, dense_track)
            actual = csv_record(dict(x=replay["position"][:, 0], y=replay["position"][:, 1]))
            untimed = read_csv(geometry_folder / f"track_{index}_forward.csv")
            clock = read_csv(geometry_folder / f"track_{index}_latent_clock.csv")["inferred_t"]
            completed = report["paths"][index - 1]["completed"]
            assert replay["completed"] and completed, (name, index)
            assert len(actual) == len(untimed) == 1001
            assert np.all(np.diff(clock) > 0)
            for output in (actual, untimed):
                np.testing.assert_array_equal(inverse_plot.xy(output)[0], track.position[0])
            scores = {method: curve_metrics(track.position, inverse_plot.xy(output), count=1001)
                      for method, output in (("timed", actual), ("without_time", untimed))}
            q, arc = resample_curve(track.position, 1001)
            error = csv_record(dict(
                normalized_arclength=arc / arc[-1],
                timed_distance_H=point_polyline_distance(q, resample_curve(inverse_plot.xy(actual), 1001)[0]),
                no_time_distance_H=point_polyline_distance(q, resample_curve(inverse_plot.xy(untimed), 1001)[0]),
            ))
            t_obs = float(track.time[-1] - track.time[0])
            t_geo = float(clock[-1] - clock[0])
            np.testing.assert_allclose([replay["time"][-1] - replay["time"][0],
                                        untimed["inferred_t"][-1] - untimed["inferred_t"][0],
                                        report["inferred_durations"][index - 1]],
                                       [t_obs, t_geo, t_geo], atol=1e-12)
            durations.append((t_obs, t_geo, 100 * (t_geo - t_obs) / t_obs))
            paths.append(dict(particle=index, timed_completed=replay["completed"],
                              without_time_completed=completed, **scores))
            panel_tracks.append(dict(obs=observed, timed=actual, no_time=untimed, error=error))
            arrays.update({f"obs_{index}": observed, f"timed_{index}": actual,
                           f"geometry_{index}": untimed, f"clock_{index}": clock, f"error_{index}": error})
        y = np.linspace(0, 1, 4097)
        profiles = []
        for folder in (timed_folder, geometry_folder):
            inlet = read_csv(folder / "inlet_reference_units.csv")
            profiles.append(CubicSpline(inlet["y"], inlet["u"])(y))
        u1, u2 = profiles
        normalized1, normalized2 = u1 / timed_report["mean_speed"], u2 / report["mean_speed"]
        inlet = csv_record(dict(y=y, timed_u=u1, no_time_u=u2,
                                timed_normalized=normalized1, no_time_normalized=normalized2))
        evidence[name] = dict(paths=paths, inlet_difference=rel_l2(u2, u1),
                              shape_difference=rel_l2(normalized2, normalized1),
                              optimizer=report["candidates"], maximum_iterations=report["config"]["max_iterations"],
                              selected_start=report["selected_start"], geometry_config=report["config"],
                              flow_config=report["flow_config"])
        plot_data[name] = dict(tracks=panel_tracks, inlet=inlet)
        np.savez_compressed(data_dir / f"{name}.npz", **arrays, inlet=inlet)

    duration = np.rec.fromrecords(durations, names="timed_duration,no_time_inferred_duration,relative_difference_percent")
    np.save(data_dir / "durations.npy", duration, allow_pickle=False)
    baseline_limits = baseline_geometry_limits(archive)
    limits = inverse_plot.geometry(plot_data, {"geometric": evidence}, out, baseline_limits=baseline_limits)
    inverse_plot.durations(duration, out)
    figures = [
        figure_record(out, f"inverse-geometry-{suffix}.pdf", f"plot_inverse_results.{function}", list(CASES), inputs,
                      [f"fig:results-inverse-{label}", "tab:results-inverse-geometry"], inverse_plot.FLOW_REV)
        for suffix, function, label in (("comparison", "geometry", "geometry"), ("duration", "durations", "duration"))
    ]
    write_json(out / "geometry.json", dict(cases=evidence, baseline_axis_limits=baseline_limits, axis_limits=limits,
               durations=[dict(case=name, particle=i+1,
               observed=row[0], inferred=row[1], difference_percent=row[2])
               for name, pair in zip(CASES, np.asarray(durations).reshape(3, 2, 3), strict=True)
               for i, row in enumerate(pair)], figures=figures))


def count(staging, archive, out):
    baseline = archive / "results/particle_count"
    old_summary = read_json(baseline / "summary.json")
    design = read_json(baseline / "design.json")
    order = old_summary["profile_order"]
    counts = design["particle_counts"]
    assert counts == [2, 3, 4, 5, 6] and len(set(order)) == 10
    assert design["reference_mean_speed"] == 1 and design["reference_reynolds"] == 30
    config = read_json(baseline / "fits" / order[0] / "N2/report.json")["config"]
    matrix = np.empty((10, 5))
    inlets, old_inlets, runs = {}, {}, {}
    refs, input_digests, archives = {}, {}, {}
    replay_count = 0
    paths = sorted((staging / "count").glob("*/fits"))
    assert sum(len(list(path.glob("*/N*/report.json"))) for path in paths) == 50
    for row, name in enumerate(order):
        runs[name] = {}
        reference = baseline / "reference" / name / "reference.npz"
        refs[name] = sha(reference)
        tracks = baseline / "observations" / name
        input_digests[name] = {f"track_{i}.csv": sha(tracks / f"track_{i}.csv") for i in range(1, 7)}
        parent, = [path / name for path in paths if (path / name).is_dir()]
        for column, n in enumerate(counts):
            folder = parent / f"N{n}"
            old_folder = baseline / "fits" / name / f"N{n}"
            original = read_csv(old_folder / "inlet.csv")
            data = read_csv(folder / "inlet.csv")
            np.testing.assert_array_equal(data["y"], original["y"])
            np.testing.assert_allclose(data["truth"], original["truth"], atol=1e-12, rtol=1e-12)
            np.testing.assert_allclose(data["y"], np.linspace(0, 1, 4097), atol=1e-14)
            assert np.isfinite(data["estimated"]).all()
            report = read_json(folder / "report.json")
            assert report["checkpoint_sha256"] == CHECKPOINT_SHA and report["checkpoint_unchanged"]
            assert (report["profile"], report["N"]) == (name, n)
            assert report["config"] == read_json(old_folder / "report.json")["config"] == config
            assert len(report["candidates"]) == 2 and report["config"]["max_iterations"] == 200
            assert report["config"]["profile_points"] == 65
            chosen = report["candidates"][report["selected_start"]]
            assert chosen["valid_inlet"]
            assert chosen["objective"] == min(c["objective"] for c in report["candidates"] if c["valid_inlet"])
            error = rel_l2(data["estimated"], data["truth"])
            np.testing.assert_allclose(error, report["inlet_relative_l2"], rtol=1e-12)
            matrix[row, column] = 100 * error
            inlets[name, n], old_inlets[name, n] = data, original
            archives[f"{name}_N{n}"] = data
            assert len(report["trajectories"]) == n
            for i, score in enumerate(report["trajectories"], start=1):
                observed = read_csv(tracks / f"track_{i}.csv")
                replay = read_csv(folder / f"replay_{i}.csv")
                np.testing.assert_array_equal(replay["t"], observed["t"][:len(replay)])
                np.testing.assert_array_equal(inverse_plot.xy(replay)[0], inverse_plot.xy(observed)[0])
                rms = np.sqrt(np.mean((inverse_plot.xy(replay) - inverse_plot.xy(observed)[:len(replay)])**2))
                np.testing.assert_allclose(rms, score["position_rmse_observed"], rtol=1e-11)
                assert score["completed"] == (len(replay) == len(observed))
                replay_count += int(score["completed"])
            runs[name][n] = dict(selected_start=report["selected_start"], optimizer=[
                {key: candidate[key] for key in ("start", "objective", "iterations", "optimizer_success", "reason")}
                for candidate in report["candidates"]], replay=report["trajectories"])
    summary = dict(profile_order=order, N=counts, inlet_errors_percent=matrix.tolist(),
                   median_error_percent_by_N=np.median(matrix, axis=0).tolist(),
                   improving_steps=int((np.diff(matrix, axis=1) < 0).sum()),
                   strictly_monotonic_profiles=[name for name, row in zip(order, matrix, strict=True)
                                                if np.all(np.diff(row) < 0)],
                   N6_better_than_N2=int((matrix[:, -1] < matrix[:, 0]).sum()),
                   replays_completed=replay_count, runs=runs,
                   selected_optimizer_converged=sum(int(run["optimizer"][run["selected_start"]]["optimizer_success"])
                                                    for profile in runs.values() for run in profile.values()),
                   observation_sha256=input_digests, reference_sha256=refs,
                   design_sha256=sha(baseline / "design.json"), inverse_config=config)
    axes_profiles = ("beta5", "lobes4_r30", "flat30", "nine30")
    upper = 1.04 * max(float(old_inlets[name, n][key].max()) for name in axes_profiles
                       for n in counts for key in ("truth", "estimated"))
    count_plot.errors_plot(summary, out)
    count_plot.profiles_plot(inlets, out, minimum_upper_limit=upper)
    color_max = max(matrix.max(), np.asarray(old_summary["inlet_errors_percent"]).max())
    shared_upper = max(upper, 1.04 * max(float(inlets[name, n][key].max())
                                         for name in axes_profiles for n in counts
                                         for key in ("truth", "estimated")))
    for label, record, profiles in (("94000", old_summary, old_inlets), ("314000", summary, inlets)):
        folder = out / "shared-scale" / label
        folder.mkdir(parents=True)
        count_plot.errors_plot(record, folder, minimum_color_max=color_max)
        count_plot.profiles_plot(profiles, folder, minimum_upper_limit=shared_upper)
    np.savez_compressed(out / "inlets.npz", **archives)
    for suffix in ("errors", "profiles"):
        filename = f"inverse-particle-count-{suffix}.pdf"
        summary.setdefault("figures", []).append(figure_record(
            out, filename, f"plot_particle_count.{suffix}_plot", "10 profiles × N=2–6",
            refs, [f"fig:inverse-count-{suffix}"], ARCHIVE_REVISION,
        ))
    summary["cached_objective_parity"] = [check for path in paths
                                         for check in read_json(path.parent / "objective_parity.json")]
    write_json(out / "count.json", summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--soap", type=Path, required=True)
    parser.add_argument("group", choices=("forward", "timed", "geometry", "count"))
    args = parser.parse_args()
    assert revision(args.archive) == ARCHIVE_REVISION
    assert revision(args.soap) == SOAP_REVISION
    soap = args.soap.resolve()
    if any(args.output.resolve().is_relative_to(source) for source in (soap, args.archive.resolve())):
        parser.error("--output must be outside the read-only research checkouts")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(soap))
    args.output.mkdir(parents=True, exist_ok=False)
    rendering_style(args.group)
    if args.group == "timed":
        timed(args.staging, args.archive, args.output, soap)
    elif args.group == "geometry":
        geometry(args.staging, args.archive, args.output, soap)
    elif args.group == "forward":
        forward(args.staging, args.archive, args.output)
    else:
        count(args.staging, args.archive, args.output)


if __name__ == "__main__":
    main()
