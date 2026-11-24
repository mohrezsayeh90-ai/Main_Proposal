#!/usr/bin/env python3
"""Run the original inlet experiments with the pinned SOAP checkpoint in a staging tree."""
import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

SOAP_REVISION = "f6b8690059716e809c2dac27c8715e65fcb1d267"
ARCHIVE_REVISION = "92897a6962e537a4bea88042609be102095db037"
CHECKPOINT_SHA = "e46687f8d50818329072eca1af7c70136fb9e3d314207f89e9427ccc140dfbf9"
CHECKPOINT_PATH = Path("reports/experiments/soap_cosine_200k/final_checkpoint.npz")
CACHE_REVISION = "a9984f07e91680eb22e2a236e74116190d0cb210"
GEOMETRY = Path("flow_reconstruction_no_time")
CASES = ("corners_beta4", "corners_beta5", "oblique_beta5")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def revision(root):
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def forward(soap, archive, checkpoint, output):
    import jax
    from flow_operator.checkpoint import load
    from flow_operator.evaluate import evaluate_fields
    from flow_operator.validation import read_cases

    references = archive / "validation/references"
    for name in ("beta", "flat", "asymmetric", "nine"):
        assert sha(references / f"{name}.npz") == sha(soap / "validation/references" / f"{name}.npz")
    jax.config.update("jax_enable_x64", True)
    params, config, metadata, _ = load(checkpoint)
    assert metadata["step"] == 314000
    params = jax.tree_util.tree_map(lambda value: value.astype(np.float64), params)
    published = read_json(checkpoint.with_name("final_metrics.json"))
    report = evaluate_fields(params, config, read_cases(references), published["thresholds"], output)
    assert report["gates"] == published["gates"]
    for case, expected in zip(report["cases"], published["cases"], strict=True):
        assert case["name"] == expected["name"]
        for key, value in case.items():
            if isinstance(value, (int, float)):
                np.testing.assert_allclose(value, expected[key], rtol=1e-7, atol=1e-12)
    report.update(step=metadata["step"], checkpoint_sha256=sha(checkpoint), source_revision=SOAP_REVISION)
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")


def timed(archive, checkpoint, name, output):
    from flow_reconstruction.inverse import FlowReconstructor
    from flow_reconstruction.io import read_problem, save_fit

    source = archive / read_json(archive / GEOMETRY / "comparison_sources.json")[name]
    tracks, config, _ = read_problem(source / "problem.json")
    archived_report = read_json(source / "report.json")
    assert json.loads(json.dumps(asdict(config))) == archived_report["config"]
    model = FlowReconstructor(checkpoint, config, allow_unvalidated=True)
    result = model.fit(tracks)
    save_fit(model, result, output)

    if name == "corners_beta4":
        from flow_operator.profiles import Inlet

        reference_path = source.parent.parent / "beta4_re30.npz"
        with np.load(reference_path, allow_pickle=False) as data:
            points, reference = data["xy"], data["reference"]
            inlet_y = np.linspace(0, 1, 1025)
            inlet_truth = Inlet.from_samples(data["inlet_y"], data["inlet_values"]).spline(inlet_y)
    else:
        reference_path = source / "truth_comparison.npz"
        with np.load(reference_path, allow_pickle=False) as data:
            points, reference = data["xy"], data["reference"]
            inlet_y, inlet_truth = data["inlet_y"], data["inlet_truth"]

    prediction = model.fields(result["theta"], points)
    inlet_prediction = result["inlet"].spline(inlet_y) * result["report"]["mean_speed"]
    np.savez_compressed(output / "truth_comparison.npz", xy=points, reference=reference,
                        prediction=prediction, inlet_y=inlet_y, inlet_truth=inlet_truth,
                        inlet_prediction=inlet_prediction)
    (output / "reference.json").write_text(json.dumps({
        "path": str(reference_path.relative_to(archive)),
        "sha256": sha(reference_path),
        "problem_sha256": sha(source / "problem.json"),
        "observations_sha256": {item["csv"]: sha(source / item["csv"])
                                for item in read_json(source / "problem.json")["tracks"]},
    }, indent=2) + "\n")


def geometric(archive, checkpoint, name, output):
    from flow_reconstruction.inverse import InverseConfig
    from flow_reconstruction_no_time.inverse import GeometryConfig, GeometryReconstructor
    from flow_reconstruction_no_time.run_cases import read_geometry

    source = archive / GEOMETRY / "experiments" / name
    curves, spec = read_geometry(source / "input/problem.json")
    old = read_json(source / "result/report.json")
    config = GeometryConfig(**old["config"])
    flow_config = InverseConfig(**old["flow_config"])
    assert flow_config.reference_reynolds == spec["reference_reynolds"]

    class GeometryFit(GeometryReconstructor):
        def prepare(self, inputs):
            super().prepare(inputs)
            evaluate = self.value_gradient
            last_theta, last_result = None, None

            def objective(theta):
                # The archived callback asks for the same accepted objective again.
                nonlocal last_theta, last_result
                if last_theta is None or not np.array_equal(theta, last_theta):
                    last_theta, last_result = np.asarray(theta).copy(), evaluate(theta)
                return last_result

            self.value_gradient = objective
            return self

    GeometryFit(checkpoint, config, flow_config).fit(curves, output)
    (output / "input_sha256.json").write_text(json.dumps({
        str(path.relative_to(archive)): sha(path) for path in sorted((source / "input").iterdir())
    }, indent=2) + "\n")



def particle_count(archive, checkpoint, cache_source, names, output):
    import jax
    import jax.numpy as jnp
    from experiments.particle_count import fit_campaign as campaign
    from flow_operator.model import context
    from flow_operator.profiles import Inlet
    from flow_reconstruction.particles import integral_observations, simulate

    assert revision(cache_source) == CACHE_REVISION
    sys.path.insert(0, str(cache_source / "experiments/soap_particle_count"))
    from cached_operator import CachedObjective

    baseline = archive / "results/particle_count"
    (output / "observations").symlink_to(baseline / "observations", target_is_directory=True)
    archived_config = json.loads(json.dumps(asdict(campaign.CONFIG)))
    assert (campaign.CONFIG.starts, campaign.CONFIG.max_iterations) == (2, 200)

    def profile(name):
        with np.load(baseline / "reference" / name / "reference.npz", allow_pickle=False) as data:
            return Inlet.from_samples(data["inlet_y"], data["inlet_values"])

    campaign.OUT = output
    campaign.CP = checkpoint
    campaign.SHA = CHECKPOINT_SHA
    campaign.profile = profile
    fitter = campaign.CampaignFitter()
    model = fitter.m
    uncached_loss, uncached_data = fitter.loss, fitter.data
    cached = CachedObjective(fitter, campaign.CONFIG)
    fitter.loss = cached.loss
    fitter.data = lambda tracks: cached.data(tracks, integral_observations)

    def replay(theta, track):
        z, speed, reynolds = model.decode(jnp.asarray(theta))
        inlet = model.builder.arrays(z)
        branch = context(model.params, inlet, reynolds, model.operator.config)
        return simulate(lambda xy: np.asarray(cached.point(jnp.asarray(xy), branch, inlet, reynolds, speed)),
                        track.time, track.position[0], track.initial_velocity, track.stokes_time,
                        model.operator.config.length)

    model.simulate = replay
    checks = []
    checked_counts = set()
    for name in names:
        for count in range(2, 7):
            original = baseline / "fits" / name / f"N{count}"
            assert read_json(original / "report.json")["config"] == archived_config
            tracks = campaign.load_tracks(name, count)
            old_truth = np.genfromtxt(original / "inlet.csv", names=True, delimiter=",")
            np.testing.assert_allclose(profile(name).spline(old_truth["y"]), old_truth["truth"],
                                       rtol=1e-12, atol=1e-12)
            if count not in checked_counts:
                raw = uncached_data(tracks)
                factored = fitter.data(tracks)
                for theta in (np.zeros(len(model.bounds)),
                              np.random.default_rng(29).normal(0, .02, len(model.bounds))):
                    value, gradient = uncached_loss(theta, raw, float(count))
                    actual, actual_gradient = cached.loss(theta, factored, float(count))
                    np.testing.assert_allclose(value, actual, rtol=1e-9, atol=1e-10)
                    np.testing.assert_allclose(gradient, actual_gradient, rtol=1e-7, atol=1e-8)
                    checks.append(dict(profile=name, particles=count, jax=jax.__version__,
                                       loss_difference=float(abs(value - actual)),
                                       max_gradient_difference=float(np.max(abs(gradient - actual_gradient)))))
                (output / "objective_parity.json").write_text(json.dumps(checks, indent=2) + "\n")
                checked_counts.add(count)
            fitter.fit(name, tracks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soap", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("experiment", choices=("forward", "timed", "geometry", "count"))
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--cache-source", type=Path)
    parser.add_argument("--profiles", nargs="+")
    args = parser.parse_args()
    if args.experiment == "count" and not (args.cache_source and args.profiles):
        parser.error("count requires --cache-source and --profiles")
    if args.experiment in ("timed", "geometry") and args.case is None:
        parser.error("--case is required for inverse experiments")
    soap, archive, output = (p.resolve() for p in (args.soap, args.archive, args.output))
    sources = [soap, archive]
    if args.cache_source is not None:
        sources.append(args.cache_source.resolve())
    if any(output.is_relative_to(source) for source in sources):
        parser.error("--output must be outside the read-only research checkouts")
    assert revision(soap) == SOAP_REVISION
    assert revision(archive) == ARCHIVE_REVISION
    checkpoint = soap / CHECKPOINT_PATH
    assert sha(checkpoint) == CHECKPOINT_SHA
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(soap))
    output.mkdir(parents=True, exist_ok=False)
    if args.experiment == "forward":
        forward(soap, archive, checkpoint, output)
    elif args.experiment == "timed":
        timed(archive, checkpoint, args.case, output)
    elif args.experiment == "geometry":
        geometric(archive, checkpoint, args.case, output)
    else:
        particle_count(archive, checkpoint, args.cache_source.resolve(), args.profiles, output)


if __name__ == "__main__":
    main()
