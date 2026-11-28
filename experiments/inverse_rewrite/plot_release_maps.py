"""Draw the observed training paths used in thesis figures 4-41 to 4-49."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np

from deliver import COLORS, LABELS, PRIMARY
from run import COUNTS, NAMES, OUT

STAGES = COUNTS['random']
DESIGNS = ('random', 'hybrid')
COLORS_BY_POOL = {'random': COLORS['random'], 'near': COLORS['hybrid']}
ZOOM = (-.018, .50)


def training_paths(profile_dir, design):
    """Match archived observations to the actual fitting order in the replay record."""
    observations = profile_dir / 'observations'
    pool = {}
    for kind in COLORS_BY_POOL:
        folder = observations / kind
        launches = json.loads((folder / 'launches.json').read_text())['launches']
        for i, launch in enumerate(launches, 1):
            path = np.loadtxt(folder / f'track_{i}.csv', delimiter=',', skiprows=1)
            np.testing.assert_array_equal(path[0, 1:], launch['position'])
            key = tuple(path[0, 1:])
            if key in pool:
                raise ValueError(f'Duplicate release position in {profile_dir}: {key}')
            pool[key] = kind, path

    fitted = profile_dir / design
    summary = json.loads((fitted / 'summary.json').read_text())
    assert tuple(stage['N'] for stage in summary['stages']) == STAGES
    indices = [row['index'] for row in summary['final_replay'] if row['subset'] == 'train']
    assert indices == list(range(1, STAGES[-1] + 1))
    tracks = []
    used = set()
    for i in indices:
        replay = np.loadtxt(fitted / f'replay_{i:02d}.csv', delimiter=',', skiprows=1)
        key = tuple(replay[0, 3:])
        assert key not in used
        used.add(key)
        kind, path = pool[key]
        np.testing.assert_array_equal(replay[:, (0, 3, 4)], path)
        tracks.append((kind, path[:, 1:]))
    near = sum(kind == 'near' for kind, _ in tracks)
    assert near == (31 if design == 'hybrid' else 0)
    return tracks


def draw(ax, tracks, xlim, zoom=False):
    for kind, color in COLORS_BY_POOL.items():
        segments = [xy for group, xy in tracks if group == kind]
        if not segments:
            continue
        ax.add_collection(LineCollection(segments, colors=color, linewidths=.65,
                                         alpha=.53, capstyle='round', zorder=2))
        start = np.array([xy[0] for xy in segments])
        ax.scatter(*start.T, s=12 if zoom else 8, color=color,
                   edgecolors='white', linewidths=.25, zorder=3)
    ax.set(xlim=xlim, ylim=(0, 1), yticks=(0, .5, 1))
    ax.set_xticks((0, .1, .2, .3, .4, .5) if zoom else np.arange(6))
    if zoom:
        ax.axvline(0, color='.3', lw=.7)
    ax.tick_params(length=2.5, labelsize=7)
    ax.grid(color='#e5e7ec', linewidth=.55, zorder=0)


def release_map(profile, label, figure_number):
    source = OUT / f'seed_{PRIMARY}' / profile
    random, mixed = (training_paths(source, design) for design in DESIGNS)
    for (_, random_path), (_, mixed_path) in zip(random[:2], mixed[:2], strict=True):
        np.testing.assert_array_equal(random_path, mixed_path)

    fig, axes = plt.subplots(len(STAGES) + 1, 2, figsize=(8.3, 11.5),
                             gridspec_kw={'height_ratios': [1] * len(STAGES) + [1.24]})
    fig.subplots_adjust(left=.12, right=.97, bottom=.075, top=.891, wspace=.17, hspace=.54)
    fig.text(.12, .974, f'Figure 4–{figure_number}  |  {label}',
             fontsize=17, fontweight='semibold', va='top')
    fig.text(.12, .941, 'Release locations and synthetic observations used in the fit · Run 1',
             fontsize=9, color='#475569', va='top')
    axes[0, 0].set_title('Random releases', loc='left', fontsize=11, fontweight='semibold')
    axes[0, 1].set_title('Mixed releases', loc='left', fontsize=11, fontweight='semibold')
    for row, count in enumerate(STAGES):
        for ax, tracks in zip(axes[row], (random, mixed), strict=True):
            draw(ax, tracks[:count], (0, 5))
        axes[row, 0].set_ylabel(f'{count} particles\ny/H', fontsize=8, labelpad=7)

    for ax, tracks in zip(axes[-1], (random, mixed), strict=True):
        draw(ax, tracks, ZOOM, zoom=True)
        ax.set_title('Inlet detail · 48 particles', loc='left', fontsize=8, pad=4)
        ax.set_xlabel('x/H', fontsize=9, labelpad=2)
    axes[-1, 0].set_ylabel('y/H', fontsize=8, labelpad=7)
    for ax in axes[:-1, :].flat:
        ax.set_xlabel('x/H', fontsize=7, labelpad=1)
    fig.legend(handles=[
        Line2D([], [], color=COLORS_BY_POOL['random'], lw=1.25, label='Random release path'),
        Line2D([], [], color=COLORS_BY_POOL['near'], lw=1.25, label='Near-inlet release path'),
        Line2D([], [], marker='o', ls='none', color='.3', ms=4, label='Release position'),
    ], loc='lower center', bbox_to_anchor=(.54, .021), ncol=3, frameon=False, fontsize=9)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT / 'figures' / 'release-path-maps.pdf')
    args = parser.parse_args()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42})
    with PdfPages(args.output, metadata={'Title': 'Release and path maps for figures 4–41 to 4–49'}) as pdf:
        for number, (profile, label) in enumerate(zip(NAMES, LABELS, strict=True), 41):
            fig = release_map(profile, label, number)
            pdf.savefig(fig)
            plt.close(fig)
    print(f'Wrote {len(NAMES)} maps after matching archived paths to all fitting stages.')


if __name__ == '__main__':
    main()
