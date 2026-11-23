#!/usr/bin/env python3
"""Recheck legacy and revised numerical claims against pinned saved data only.

python figs/chapter4/validate_revision.py --flow FLOW --magnetic MAG
No training, inference, optimization or integration. Research sources stay clean.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np
from plot_revision import Evidence, THESIS, HERE
import plot_forward_results
import plot_inverse_results
import plot_particle_count


class Adapter(Evidence):
    json = Evidence.js

    def csv(self, source, relative):
        return np.genfromtxt(self.path(source, relative), delimiter=',', names=True,
                             dtype=None, encoding='utf8')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--flow', type=Path, required=True)
    p.add_argument('--magnetic', type=Path, required=True)
    args = p.parse_args()
    e = Adapter({'flow': args.flow, 'magnetic': args.magnetic, 'thesis': THESIS})
    _, _, forward = plot_forward_results.validate(e)
    _, _, _, inverse = plot_inverse_results.validate(e)
    archive = plot_particle_count.Archive(args.flow)
    _, _, count = plot_particle_count.verify(archive)
    manifest = json.loads((HERE/'revision-manifest.json').read_text())
    # The minimum spacing and inverse recovery values are independently read again.
    np.testing.assert_allclose(manifest['checks']['Duck 42_refined_min'], .0260481, atol=5e-8, rtol=0)
    np.testing.assert_allclose(manifest['checks']['Fish 100_refined_min'], .026197, atol=5e-7, rtol=0)
    np.testing.assert_allclose([manifest['checks']['A_single_X'], manifest['checks']['A_single_Z']],
                               [6.315e-5, 1.144e-5], rtol=.0005)
    np.testing.assert_allclose(manifest['checks']['timed_corners_beta4']['euclidean_rms_percent_H'],
                               [.0628, .0533], atol=.00005, rtol=0)
    report = dict(forward=forward, inverse=inverse, particle_count=count,
                  inputs_sha256=e.inputs, particle_count_inputs_sha256=archive.hashes)
    (HERE/'revision-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Passed: formal flow metrics, 12 magnetic cases, 12 geometry metric sets,')
    print('six durations, Master9, all 50 particle-count fits / 200 saved replays,')
    print('and revised spacing and single-source recovery claims.')


if __name__ == '__main__':
    main()
