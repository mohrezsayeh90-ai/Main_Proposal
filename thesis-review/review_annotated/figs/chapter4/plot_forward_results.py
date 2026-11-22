#!/usr/bin/env python3
"""Replot section 4.2 from pinned, read-only research checkouts; no inference.

python figs/chapter4/plot_forward_results.py --flow /path/to/flow --magnetic /path/to/magnetic
Requires Python 3.12, NumPy and Matplotlib. See forward-results-provenance.md.
"""
import argparse
import hashlib
import json
from pathlib import Path
import string
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
import numpy as np

FLOW_REV = 'd5e9b5a1a08107cbfbce34fdd66932f2f99588df'
MAG_REV = 'a4fc9d722487a5af09b9a05c745f5184d1c87b22'
FLOW_HASH = 'ccf6fa2b3e179a22c443384083e2dec338fc497f9562a567ed7e0955d3c67bf8'
MAG_HASH = '080b7e5dd76c98a75fca7f92cc4ec314907a7f7340c809b739b1e2eabc0e3133'
FLOW_FOLDER = Path('reports/experiments/pressure_long/output')
MAG_FOLDER = Path('results/trained_presentation')
CASES = ['beta', 'flat', 'asymmetric', 'nine']
SELECTED = ['03_gaussian_pulse', '05_source_switch', '06_two_source_chirp', '07_offset_alternating']
R, D, TIME_FACTOR = 75e-6, .04, .75
WIDTH = 6.27  # A4 minus the template's two one-inch margins.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Evidence:
    def __init__(self, flow, magnetic):
        self.roots = {'flow': flow, 'magnetic': magnetic}
        self.files = {}
        for name, revision in [('flow', FLOW_REV), ('magnetic', MAG_REV)]:
            actual = subprocess.check_output(['git', '-C', str(self.roots[name]),
                                             'rev-parse', 'HEAD'], text=True).strip()
            if actual != revision:
                raise ValueError(f'{name}: expected {revision}, got {actual}')

    def path(self, source, relative):
        path = self.roots[source] / relative
        self.files[f'{source}/{relative}'] = sha(path)
        return path

    def json(self, source, relative):
        return json.loads(self.path(source, relative).read_text())


def validate(e):
    report = e.json('flow', FLOW_FOLDER / 'selected_checkpoint.validation.json')
    maps = e.json('flow', FLOW_FOLDER / 'validation_best_checkpoint/metrics.json')
    for j in [report, maps]:
        assert j['step'] == 94000 and j['checkpoint_sha256'] == FLOW_HASH
    assert sha(e.path('flow', FLOW_FOLDER / 'selected_checkpoint.npz')) == FLOW_HASH
    assert sha(e.path('magnetic', 'results/operator/checkpoint.pt')) == MAG_HASH
    by_name = {c['name']: c for c in report['cases']}
    flow, flow_checks = {}, {}
    for name in CASES:
        a = dict(np.load(e.path('flow', FLOW_FOLDER / f'validation_best_checkpoint/{name}.npz')))
        reference = dict(np.load(e.path('flow', f'validation/references/{name}.npz')))
        np.testing.assert_array_equal(a['xy'], reference['xy'])
        np.testing.assert_array_equal(a['reference'], reference['reference'])
        assert a['xy'].shape == (7081, 2)
        x, y = (np.unique(a['xy'][:, i]) for i in range(2))
        assert (len(x), len(y)) == (73, 97)
        # Rebuild from coordinates, checking every tensor-product cell once.
        ix, iy = np.searchsorted(x, a['xy'][:, 0]), np.searchsorted(y, a['xy'][:, 1])
        assert len(np.unique(iy * len(x) + ix)) == len(a['xy'])
        a.update(x=x, y=y, ix=ix, iy=iy)
        delta = a['prediction'] - a['reference']
        computed = {
            'velocity_relative_l2': np.linalg.norm(delta[:, :2]) / np.linalg.norm(a['reference'][:, :2]),
            'v_relative_l2': np.linalg.norm(delta[:, 1]) / np.linalg.norm(a['reference'][:, 1]),
            'v_rmse': np.sqrt(np.mean(delta[:, 1]**2)),
            'pressure_relative_l2': np.linalg.norm(delta[:, 2]) / np.linalg.norm(a['reference'][:, 2]),
        }
        for key, value in computed.items():
            np.testing.assert_allclose(value, by_name[name][key], rtol=1e-10, atol=1e-14)
        np.testing.assert_allclose(a['inlet_requested'][[0, -1]], 0, atol=1e-14)
        flux = np.trapezoid(a['inlet_requested'], a['inlet_y'])
        assert abs(flux - 1) < 2e-6
        mesh = json.loads(str(reference['metadata']))['mesh_change']
        assert mesh['velocity_relative_l2'] < .0001 and mesh['pressure_relative_l2'] < .002
        flow_checks[name] = dict(computed, reynolds=by_name[name]['reynolds'],
                                 momentum_rms=by_name[name]['momentum_rms'],
                                 inlet_flux=float(flux), mesh_change=mesh,
                                 inlet_max_error=float(np.max(np.abs(a['inlet_applied']-a['inlet_requested']))))
        flow[name] = a
    assert sum(not passed for passed in report['gates'].values()) == 3
    last = e.json('flow', FLOW_FOLDER / 'validation_checkpoint/metrics.json')
    assert last['step'] == 100000 and sum(not v for v in last['gates'].values()) == 3
    exploratory = e.json('flow', 'results/diverse_profiles_2026_11_07/metrics.json')['selected_forward_cases']
    assert len(exploratory) == 7 and all(c['checkpoint_sha256'] == FLOW_HASH for c in exploratory)
    mag_report = e.json('magnetic', MAG_FOLDER / 'validation.json')
    assert mag_report['checkpoint_sha256'] == MAG_HASH and mag_report['all_passed']
    magnetic, mag_checks = {}, {}
    for case in mag_report['cases']:
        name = case['case']
        a = np.genfromtxt(e.path('magnetic', MAG_FOLDER / f'{name}.csv'), delimiter=',', names=True)
        assert len(a) == 801 and np.all(np.diff(a['time_s']) > 0)
        tau = TIME_FACTOR * a['time_s']
        xn, zn = a['x_network_m']/R, a['z_network_m']/D
        xr, zr = a['x_numerical_m']/R, a['z_numerical_m']/D
        ex, ez = np.abs(xn-xr), np.abs(zn-zr)
        np.testing.assert_allclose([xn[0], zn[0]], np.array(case['initial_m'])/[R,D], atol=1e-14)
        np.testing.assert_allclose([xr[0], zr[0]], [xn[0], zn[0]], atol=1e-14)
        np.testing.assert_allclose(tau[-1], case['duration_s']*TIME_FACTOR)
        np.testing.assert_allclose([ex.max(), ez.max()],
            [case['max_x_error_um']*1e-6/R, case['max_z_error_um']*1e-6/D], rtol=1e-9)
        assert ex.max() < .01 and ez.max() < 3.75e-4 and case['passed']
        assert max(case['reference_step_refinement_change_um']) < .001
        assert case['no_field_analytic_error_m'] < 1e-11
        assert np.max(np.abs(a['a_left'])+np.abs(a['a_right'])) <= np.sqrt(.5)+1e-14
        assert max(np.abs(xn).max(), np.abs(xr).max()) <= .7
        magnetic[name] = dict(raw=a, tau=tau, xn=xn, zn=zn, xr=xr, zr=zr, ex=ex, ez=ez)
        mag_checks[name] = dict(X0=float(xn[0]), Z0=float(zn[0]), tau_f=float(tau[-1]),
                                max_X_error=float(ex.max()), max_Z_error=float(ez.max()), samples=len(a))
    assert len(magnetic) == 12
    assert max(mag_checks, key=lambda k:mag_checks[k]['max_X_error']) == '04_sinusoidal'
    assert max(mag_checks, key=lambda k:mag_checks[k]['max_Z_error']) == '07_offset_alternating'
    return flow, magnetic, dict(flow=flow_checks, magnetic=mag_checks,
        flow_gates=report['gates'], exploratory_selected=[{k:c[k] for k in
        ['name','reynolds','velocity_relative_l2','pressure_relative_l2']} for c in exploratory])


def save(fig, out, name):
    fig.savefig(out / (name+'.pdf'), dpi=500, metadata={
        'Title': name, 'Creator': 'Matplotlib; archived data only', 'CreationDate': None, 'ModDate': None})
    plt.close(fig)


def inlets(flow, out):
    fig, axes = plt.subplots(1, 4, figsize=(WIDTH, 2.25), sharex=True, sharey=True)
    titles = ['Beta(5,5)', 'Near-flat', 'Asymmetric', 'Nine oscillations']
    xmax = max(a['inlet_requested'].max() for a in flow.values()) * 1.07
    for i, (name, ax, title) in enumerate(zip(CASES, axes, titles)):
        a = flow[name]
        ax.plot(a['inlet_requested'], a['inlet_y'], color='#24588b', lw=1.2)
        ax.set(xlim=(0, xmax), ylim=(0, 1), xlabel=r'$f^*(y^*)$')
        ax.set_title(f'({string.ascii_lowercase[i]}) {title}\nRe = {[30,70,100,55][i]}', fontsize=8)
        ax.set_xticks([0,1,2]); ax.set_yticks([0,.5,1]); ax.grid(alpha=.2, lw=.4)
    axes[0].set_ylabel(r'$y^*$')
    fig.subplots_adjust(left=.085, right=.99, bottom=.23, top=.78, wspace=.19)
    save(fig, out, 'forward-flow-inlets')


def maps(a, out, name):
    fig = plt.figure(figsize=(WIDTH, 3.25))
    gs = fig.add_gridspec(3, 6, width_ratios=[1,1,.055,.27,1,.055],
                          left=.075, right=.915, bottom=.13, top=.90, wspace=.20, hspace=.9)
    x, y = a['x'], a['y']
    # Mid-cell edges remain strictly inside the sampled rectangle.
    xe = np.r_[x[0], (x[1:]+x[:-1])/2, x[-1]]
    ye = np.r_[y[0], (y[1:]+y[:-1])/2, y[-1]]
    for row, symbol in enumerate([r'$u^*$',r'$v^*$',r'$p^*$']):
        values = []
        for key in ['reference', 'prediction']:
            z = np.empty((len(y),len(x)))
            z[a['iy'],a['ix']] = a[key][:,row]
            values.append(z)
        values.append(values[1]-values[0])
        low, high = min(z.min() for z in values[:2]), max(z.max() for z in values[:2])
        norm = Normalize(low,high)
        cmap = 'viridis'
        if row == 1:
            high = max(abs(low),abs(high)); norm = Normalize(-high,high); cmap='RdBu_r'
        diffmax = np.max(np.abs(values[2]))
        axes = [fig.add_subplot(gs[row,col]) for col in [0,1,4]]
        for col, (ax,z) in enumerate(zip(axes, values)):
            mesh = ax.pcolormesh(xe, ye, z, cmap=cmap if col<2 else 'RdBu_r',
                norm=norm if col<2 else Normalize(-diffmax,diffmax), shading='flat', rasterized=True)
            ax.set(xlim=(0,5), ylim=(0,1), aspect='equal', xticks=[0,2.5,5], yticks=[0,1])
            ax.tick_params(labelsize=8, pad=1.5, length=2)
            ticks = ax.get_xticklabels()
            ticks[0].set_horizontalalignment('left')
            ticks[-1].set_horizontalalignment('right')
            ax.text(.02, 1.13, f'({string.ascii_lowercase[row*3+col]})', transform=ax.transAxes, fontsize=7)
            if col == 0:
                ax.set_ylabel(symbol+'\n'+r'$y^*$', fontsize=8, labelpad=3)
            else:
                ax.tick_params(labelleft=False)
            if row == 0:
                ax.set_title(['FEM','DeepONet','DeepONet − FEM'][col], fontsize=8, pad=19)
            if row == 2:
                ax.set_xlabel(r'$x^*$', labelpad=1)
            if col in [1,2]:
                cax = fig.add_subplot(gs[row,2 if col==1 else 5])
                # Colorbar height follows the actual 5:1 field panel.
                pos=ax.get_position(); cp=cax.get_position()
                cax.set_position([cp.x0,pos.y0,cp.width,pos.height])
                cb=fig.colorbar(mesh,cax=cax,ticks=np.linspace(norm.vmin,norm.vmax,3) if col==1
                               else [-diffmax,0,diffmax])
                cb.solids.set_rasterized(False)
                cb.ax.tick_params(labelsize=7.5, pad=1, length=2)
                cb.ax.yaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    save(fig,out,'forward-flow-'+name)


def paths(magnetic, out):
    fig, axes = plt.subplots(4,3,figsize=(WIDTH,6.65))
    labels=['03 Gaussian pulse','05 Source switch','06 Two-source chirp','07 Off-axis alternating']
    for row, (name,label) in enumerate(zip(SELECTED,labels)):
        a=magnetic[name]; t=a['tau']; raw=a['raw']
        left, spatial, temporal = axes[row]
        left.plot(t,raw['a_left'],color='#24588b',lw=1.15)
        left.plot(t,raw['a_right'],color='#bc4a24',lw=1.15,ls='--')
        for bound in [-np.sqrt(.5),np.sqrt(.5)]:
            left.axhline(bound,color='.65',lw=.45,ls=':')
        left.set(ylim=(-.76,.76),yticks=[-.7,0,.7],ylabel=r'$a_L,\ a_R$')
        for ax, xnet, xref in [(spatial,a['zn'],a['zr']), (temporal,t,t)]:
            ax.plot(xnet,a['xn'],color='#9b3069',lw=1.25)
            ax.plot(xref,a['xr'],color='.12',lw=.85,ls='--', marker='o',markevery=80,
                    mfc='none',mec='.12',ms=3,mew=.65)
            ax.set_ylabel(r'$X=x/R$')
            ax.yaxis.set_major_locator(MaxNLocator(3))
        spatial.set_xlabel(r'$Z=z/D$')
        spatial.margins(x=.06,y=.12)
        for ax in [left,temporal]:
            ax.set(xlim=(0,t[-1]),xlabel=r'$\tau$')
        for col,ax in enumerate(axes[row]):
            ax.set_title(f'({string.ascii_lowercase[3*row+col]})'+(' '+label if col==0 else ''),
                         loc='left',fontsize=7.5,pad=5)
            ax.grid(alpha=.17,lw=.4); ax.tick_params(pad=2,length=2.5)
        if row==3:
            spatial.set_title(r'(k) $X_0=-0.30,\ Z_0=-1$',loc='left',fontsize=7,pad=5)
    handles=[Line2D([],[],color='#24588b',lw=1.2,label=r'$a_L$'),
             Line2D([],[],color='#bc4a24',lw=1.2,ls='--',label=r'$a_R$'),
             Line2D([],[],color='#9b3069',lw=1.3,label='Master10'),
             Line2D([],[],color='.12',ls='--',marker='o',mfc='none',ms=3,label='DOP853')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.51,.033),ncol=4,frameon=False,
               handlelength=2,columnspacing=1.3)
    fig.text(.5,.012,'Trajectory zooms: independent X and Z axis scales',ha='center',fontsize=7.5)
    fig.subplots_adjust(left=.1,right=.985,top=.97,bottom=.13,hspace=.85,wspace=.57)
    save(fig,out,'forward-magnetic-paths')


def errors(magnetic,out):
    fig,axes=plt.subplots(1,2,figsize=(WIDTH,2.15))
    for name,color,style in zip(SELECTED,['#24588b','#bc4a24','#34804b','#9b3069'],['-','--','-.',':']):
        a=magnetic[name]
        for ax,key in zip(axes,['ex','ez']):
            ax.plot(a['tau'],1e5*a[key],color=color,ls=style,lw=1.15,label='Case '+name[:2])
    for i,ax in enumerate(axes):
        ax.set(xlim=(0,2.4),ylim=(0,None),xlabel=r'$\tau$')
        ax.set_ylabel([r'$10^5 |X_{\rm net}-X_{\rm ODE}|$',r'$10^5 |Z_{\rm net}-Z_{\rm ODE}|$'][i])
        ax.set_title(f'({string.ascii_lowercase[i]})',loc='left',fontsize=8)
        ax.grid(alpha=.2,lw=.4)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=4,
               frameon=False,bbox_to_anchor=(.5,0))
    fig.subplots_adjust(left=.095,right=.99,bottom=.28,top=.92,wspace=.43)
    save(fig,out,'forward-magnetic-errors')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flow',required=True,type=Path)
    parser.add_argument('--magnetic',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
        'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':8,
        'pdf.fonttype':42,'axes.linewidth':.65,'savefig.facecolor':'white'})
    evidence=Evidence(args.flow,args.magnetic)
    flow,magnetic,checks=validate(evidence)
    inlets(flow,args.output)
    for name in ['beta','nine']:
        maps(flow[name],args.output,name)
    paths(magnetic,args.output); errors(magnetic,args.output)
    manifest=dict(source_revisions={'flow':FLOW_REV,'magnetic':MAG_REV},
        checkpoint_sha256={'flow':FLOW_HASH,'magnetic':MAG_HASH},input_sha256=evidence.files,
        units=dict(flow='Already dimensionless; no pressure shift',magnetic=dict(
            X='x_m / 75e-6',Z='z_m / 0.04',tau='0.75 * time_s',error='absolute nondimensional difference')),
        validation=checks, output_sha256={p.name:sha(p) for p in sorted(args.output.glob('forward-*.pdf'))})
    (args.output/'forward-results-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Validated four flow cases and twelve magnetic cases; wrote five PDFs and manifest.')


if __name__=='__main__':
    main()
