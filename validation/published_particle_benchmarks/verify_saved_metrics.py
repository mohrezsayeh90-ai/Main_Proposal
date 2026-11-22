"""Check the supplied archived CSVs against their recorded JSON metrics (no training)."""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parent / 'original'
mag = json.loads((ROOT/'data/magnetic/validation.json').read_text())
for i, row in enumerate(mag['results']):
    a = np.genfromtxt(ROOT/f'data/magnetic/comparison_{i:02d}.csv', delimiter=',', names=True)
    err = abs(a['X_PINN'] - a['X_analytic'])
    assert np.allclose(err, a['abs_error_Rv'], rtol=1e-10, atol=1e-14)
    assert np.isclose(err.max(), row['max_error_Rv'], rtol=1e-9)
    assert np.isclose(np.sqrt(np.mean(err**2)), row['rms_error_Rv'], rtol=1e-9)
assert all(r['pinn_captured'] == r['reference_captured'] for r in mag['results'])
wavy = json.loads((ROOT/'data/wavy/metrics.json').read_text())
for case in wavy['cases']:
    amp = case['waviness']
    if amp == 0:
        a = np.genfromtxt(ROOT/'data/wavy/trajectory_0.csv', delimiter=',', names=True)
        use = (a['X'] >= 10) & (a['X'] <= 1990)
        err = a['Z_neural'][use] - a['Z_published'][use]
        keys = ('figure_rmse', 'figure_max_abs_error')
    else:
        a = np.genfromtxt(ROOT/f'data/wavy/envelope_{amp}.csv', delimiter=',', names=True)
        use = a['used_for_error'] > 0
        err = np.r_[a['neural_low'][use]-a['published_low'][use],
                    a['neural_high'][use]-a['published_high'][use]]
        keys = ('figure_envelope_rmse', 'figure_envelope_max_abs_error')
    assert np.isclose(np.sqrt(np.mean(err**2)), case[keys[0]], rtol=1e-9)
    assert np.isclose(abs(err).max(), case[keys[1]], rtol=1e-9)
print('PASS: 10 magnetic cases, matching events, and all 3 wavy comparisons.')
