#!/usr/bin/env python3
"""Thesis-only plots from the pinned particle-count archive; no inference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REVISION = '92897a6962e537a4bea88042609be102095db037'
CHECKPOINT = 'ccf6fa2b3e179a22c443384083e2dec338fc497f9562a567ed7e0955d3c67bf8'
LABELS = {'parabolic':'Parabolic', 'skew_b3':'Asymmetric', 'beta5':'Narrow beta',
          'twin_b3_r30':'Twin peaks', 'mixed':'Mixed scales', 'shoulder':'Shoulder',
          'waves3_r30':'Three-cycle', 'lobes4_r30':'Four-cycle', 'flat30':'Near-flat',
          'nine30':'Nine-cycle'}
COLORS = ['#4477AA','#EE6677','#228833','#AA3377','#AA8800']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Archive:
    def __init__(self, repo):
        self.repo = repo
        self.root = repo/'results/particle_count'
        self.hashes = {}
        actual = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        if actual != REVISION:
            raise ValueError(f'Expected pinned revision {REVISION}; got {actual}')

    def path(self, relative):
        path = self.root/relative
        self.hashes[str(relative)] = digest(path)
        return path

    def json(self, relative):
        return json.loads(self.path(relative).read_text())

    def csv(self, relative):
        return np.genfromtxt(self.path(relative),delimiter=',',names=True)


def verify(a):
    summary = a.json('summary.json')
    design = a.json('design.json')
    audit = a.json('audit.json')
    assert audit['fits']==50 and audit['replays_recomputed']==200
    assert summary['checkpoint_sha256']==CHECKPOINT
    assert digest(a.repo/'models/candidates/pressure_long/checkpoint.npz')==CHECKPOINT
    assert design['particle_counts']==summary['N']==[2,3,4,5,6]
    assert design['reference_reynolds']==30 and design['reference_mean_speed']==1
    with a.path('summary.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows)==summary['cases']==50
    lookup = {(v['profile'],int(v['N'])):v for v in rows}
    assert len(lookup)==50
    order = summary['profile_order']
    roughness = [a.json(f'reference/{name}/metadata.json')['roughness'] for name in order]
    assert roughness==sorted(roughness) and len(set(order))==10
    matrix = np.array(summary['inlet_errors_percent'])
    inlets = {}; replay_count = 0; stops = {}; norm_differences = []
    common_config = None
    for i,name in enumerate(order):
        for j,n in enumerate(summary['N']):
            row = lookup[name,n]
            np.testing.assert_allclose(float(row['inlet_error_percent']),matrix[i,j],rtol=1e-13)
            data = a.csv(f'fits/{name}/N{n}/inlet.csv')
            assert len(data)==4097
            np.testing.assert_allclose(data['y'],np.linspace(0,1,4097),atol=1e-14)
            if n>2:
                np.testing.assert_array_equal(data['truth'],inlets[name,2]['truth'])
            error = 100*np.linalg.norm(data['estimated']-data['truth'])/np.linalg.norm(data['truth'])
            np.testing.assert_allclose(error,matrix[i,j],rtol=1e-12)
            norm_differences.append(abs(error-matrix[i,j]))
            report = a.json(f'fits/{name}/N{n}/report.json')
            assert report['status']=='completed' and report['checkpoint_sha256']==CHECKPOINT
            assert len(report['candidates'])==2 and report['config']['max_iterations']==200
            assert report['config']['profile_points']==65
            if common_config is None:
                common_config = report['config']
            assert report['config']==common_config
            selected = report['candidates'][report['selected_start']]
            assert not selected['optimizer_success']
            assert selected['valid_inlet']
            assert selected['objective']==min(c['objective'] for c in report['candidates'] if c['valid_inlet'])
            stops[selected['reason']] = stops.get(selected['reason'],0)+1
            assert len(report['trajectories'])==n and all(t['completed'] for t in report['trajectories'])
            replay_count += n
            inlets[name,n] = data
    median = np.median(matrix,axis=0)
    np.testing.assert_allclose(median,summary['median_error_percent_by_N'],rtol=1e-13)
    assert int((np.diff(matrix,axis=1)<0).sum())==29
    assert int(np.all(np.diff(matrix,axis=1)<0,axis=1).sum())==2
    assert np.all(matrix[:,-1]<matrix[:,0]) and replay_count==200
    assert summary['improving_steps']==29 and summary['total_steps']==40
    assert summary['strictly_monotonic_profiles']==['waves3_r30','flat30']
    assert summary['N6_better_than_N2']==10 and summary['selected_optimizer_converged']==0
    return summary,inlets,dict(matrix=matrix.tolist(),medians=median.tolist(),
        fits_checked=50,grid_points=4097,improving_steps=29,total_steps=40,
        maximum_norm_difference_percent=max(norm_differences),
        replays_completed=replay_count,selected_converged=0,selected_stops=stops,
        nine_difference_percentage_points=float(matrix[order.index('nine30'),0]-matrix[order.index('nine30'),-1]))


def save(fig,out,name):
    fig.savefig(out/(name+'.pdf'),metadata={'Title':name,'CreationDate':None,'ModDate':None})
    plt.close(fig)


def design_plot(a,out):
    fig,ax = plt.subplots(figsize=(6.27,2.12))
    markers = ['o','s','^','D','v','P']
    design = a.json('design.json')
    for i in range(1,7):
        d = a.csv(f'observations/nine30/clean_{i}.csv')
        assert len(d)==81
        np.testing.assert_allclose(d['t'],np.linspace(0,design['horizon'],81),atol=1e-14)
        np.testing.assert_allclose([d['x'][0],d['y'][0]],design['launches'][i-1][0],atol=1e-14)
        line, = ax.plot(d['x'],d['y'],lw=1.1,label=f'Path {i}')
        ax.plot(d['x'][0],d['y'][0],marker=markers[i-1],ms=4,color=line.get_color(),clip_on=False)
        ax.annotate(str(i),(d['x'][0],d['y'][0]),xytext=(6,-7) if i!=2 else (-10,6),
                    textcoords='offset points',fontsize=8,color=line.get_color(),fontweight='bold')
    ax.set(xlim=(0,5),ylim=(0,1),aspect='equal',xlabel=r'$x/H$',ylabel=r'$y/H$',
           xticks=[0,1,2,3,4,5],yticks=[0,.5,1])
    ax.grid(alpha=.15,lw=.4)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',ncol=6,frameon=False,fontsize=7.5)
    fig.subplots_adjust(left=.075,right=.985,bottom=.31,top=.96)
    save(fig,out,'inverse-particle-count-design')


def errors_plot(summary,out):
    matrix = np.asarray(summary['inlet_errors_percent'])
    order = summary['profile_order'];counts = summary['N']
    fig = plt.figure(figsize=(6.27,4.2))
    gs = fig.add_gridspec(1,2,width_ratios=[1.35,1],left=.17,right=.985,
                          bottom=.28,top=.92,wspace=.55)
    ax = fig.add_subplot(gs[0,0]);curves=fig.add_subplot(gs[0,1])
    bar = fig.add_axes([.17,.155,.367,.025])
    im = ax.pcolormesh(np.arange(6)-.5,np.arange(11)-.5,matrix,
                       cmap='magma_r',vmin=0,vmax=matrix.max(),rasterized=False)
    ax.set(xlim=(-.5,4.5),ylim=(9.5,-.5),xticks=range(5),xticklabels=counts,yticks=range(10),
           yticklabels=[LABELS[name] for name in order],xlabel=r'$N_p$')
    ax.set_title('(a)',loc='left',fontsize=8)
    ax.tick_params(labelsize=8,pad=2,length=2)
    for i in range(10):
        for j in range(5):
            value=matrix[i,j];text=f'{value:.4f}' if value<.01 else f'{value:.2f}'
            ax.text(j,i,text,ha='center',va='center',fontsize=7.5,
                    color='white' if value>.6*matrix.max() else 'black')
    cb=fig.colorbar(im,cax=bar,orientation='horizontal')
    cb.set_label('Inlet relative L2 error (%)',fontsize=8,labelpad=2)
    cb.ax.tick_params(labelsize=7.5,pad=1,length=2)
    cb.solids.set_rasterized(False)
    cb.solids.set_edgecolor('face')
    for name,color,style in [('beta5','#4477AA','--'),('lobes4_r30','#AA3377','-.'),('nine30','#AA8800',':')]:
        curves.plot(counts,matrix[order.index(name)],color=color,ls=style,marker='o',ms=2.5,lw=1,label=LABELS[name])
    curves.plot(counts,np.median(matrix,axis=0),'k-',lw=2,marker='s',ms=3,label='Median')
    curves.set(xlabel=r'$N_p$',ylabel='Inlet relative L2 error (%)',xticks=counts,ylim=(0,46))
    curves.set_title('(b)',loc='left',fontsize=8);curves.grid(alpha=.2,lw=.4)
    curves.tick_params(labelsize=8,pad=2,length=2)
    fig.legend(*curves.get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,
               bbox_to_anchor=(.54,.015),fontsize=7.5,columnspacing=1.2,handlelength=2.2)
    save(fig,out,'inverse-particle-count-errors')


def profiles_plot(inlets,out):
    names=['beta5','lobes4_r30','flat30','nine30']
    fig,axes=plt.subplots(2,2,figsize=(6.27,4.35),sharex=True,sharey=True)
    maximum=max(float(inlets[name,n][key].max()) for name in names for n in range(2,7)
                for key in ['truth','estimated'])
    for index,(name,ax) in enumerate(zip(names,axes.flat)):
        for n,color,style in zip(range(2,7),COLORS,['-','--','-.',':','-']):
            d=inlets[name,n]
            ax.plot(d['y'],d['estimated'],color=color,ls=style,lw=1.05,
                    marker='o' if n==6 else None,markevery=256,ms=2,label=f'{n} particles')
        ax.plot(d['y'],d['truth'],'k--',lw=1.7,label='Reference',zorder=10)
        ax.set(xlim=(0,1),ylim=(0,maximum*1.04),xlabel=r'$y/H$',ylabel=r'$u/U_{\rm ref}$')
        ax.set_title(f'({chr(97+index)}) {LABELS[name]}',loc='left',fontsize=8)
        ax.grid(alpha=.18,lw=.4);ax.tick_params(pad=2,length=2.5)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend([handles[-1]]+handles[:-1],[labels[-1]]+labels[:-1],loc='lower center',
               ncol=3,frameon=False,bbox_to_anchor=(.53,.01),fontsize=8,columnspacing=1.8)
    fig.subplots_adjust(left=.09,right=.985,bottom=.20,top=.94,wspace=.23,hspace=.45)
    save(fig,out,'inverse-particle-count-profiles')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
        'xtick.labelsize':8,'ytick.labelsize':8,'axes.linewidth':.65,'pdf.fonttype':42})
    a=Archive(args.source);summary,inlets,checks=verify(a)
    design_plot(a,args.output);errors_plot(summary,args.output);profiles_plot(inlets,args.output)
    manifest=dict(source_revision=REVISION,checkpoint_sha256=CHECKPOINT,
        units='Stored y/H, x/H, t* and u/U_ref; estimated_own_mean not used',
        input_sha256=a.hashes,validation=checks,output_sha256={p.name:digest(p) for p in
        sorted(args.output.glob('inverse-particle-count-*.pdf'))})
    (args.output/'particle-count-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Verified 50 norms, 50 CSV/JSON matrix cells, 200 completed replays, zero selected convergences; wrote three PDFs.')


if __name__=='__main__':main()
