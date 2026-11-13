#!/usr/bin/env python3
"""Section 4.3: validate and plot saved results; never fit, infer or integrate.

python figs/chapter4/plot_inverse_results.py --flow FLOW_CHECKOUT --magnetic MAG_CHECKOUT
Python 3.12, NumPy and Matplotlib; both checkouts must match the pinned revisions.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import string
import subprocess
import sys

# Importing the archived metric helper must not create files in its checkout.
sys.dont_write_bytecode = True

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import numpy as np

FLOW_REV = 'd5e9b5a1a08107cbfbce34fdd66932f2f99588df'
MAG_REV = 'a4fc9d722487a5af09b9a05c745f5184d1c87b22'
FLOW_SHA = 'ccf6fa2b3e179a22c443384083e2dec338fc497f9562a567ed7e0955d3c67bf8'
MAG_SHA = 'd5f428680f2e8cecc37b261463ea6cb410e15d9a73ea54347ef195413e551300'
BASE = Path('flow_reconstruction_no_time')
CASES = ['corners_beta4', 'corners_beta5', 'oblique_beta5']
LABELS = ['Corner B', 'Corner A', 'Oblique']
COLORS = ['#24588b', '#bc4a24']
R, D, WIDTH = 75e-6, .04, 6.27


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xy(a):
    return np.column_stack([a['x'], a['y']])


class Evidence:
    def __init__(self, flow, magnetic):
        self.roots = {'flow': flow, 'magnetic': magnetic}
        self.files = {}
        for name, revision in [('flow', FLOW_REV), ('magnetic', MAG_REV)]:
            actual = subprocess.check_output(['git','-C',str(self.roots[name]),'rev-parse','HEAD'],text=True).strip()
            if actual != revision:
                raise ValueError(f'{name}: expected {revision}, got {actual}')

    def path(self, root, relative):
        p = self.roots[root] / relative
        self.files[f'{root}/{relative}'] = sha(p)
        return p

    def json(self, root, relative):
        return json.loads(self.path(root, relative).read_text())

    def csv(self, root, relative):
        return np.genfromtxt(self.path(root, relative), delimiter=',', names=True, dtype=None, encoding='utf-8')


def validate(e):
    assert sha(e.path('flow', 'reports/experiments/pressure_long/output/selected_checkpoint.npz')) == FLOW_SHA
    assert sha(e.path('magnetic', 'results/master9/checkpoint.pt')) == MAG_SHA
    sources = e.json('flow', BASE/'comparison_sources.json')
    comparisons = e.json('flow', BASE/'comparison_metrics.json')['cases']
    compare = {c['case']:c for c in comparisons}
    duration = e.csv('flow', BASE/'arrival_time_comparison/durations.csv')
    duration_report = e.json('flow', BASE/'arrival_time_comparison/metrics.json')
    # Load only the archived geometry-metric module, without importing any solver.
    path = e.path('flow', BASE/'geometry.py')
    spec = importlib.util.spec_from_file_location('section43_geometry', path)
    geom = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = geom
    spec.loader.exec_module(geom)
    flow, checks = {}, {'timed':{}, 'geometric':{}, 'master9':{}}
    for name in CASES:
        source = Path(sources[name]); dest = BASE/'comparisons'/name
        report = e.json('flow', source/'report.json')
        model = e.json('flow', source/'fitted_model.json')
        assert report['forward_checkpoint_sha256'] == model['checkpoint_sha256'] == FLOW_SHA
        assert report['forward_training_step'] == 94000 and report['forward_weights_unchanged']
        assert not report['forward_operator_benchmark_accepted']
        candidate = next(c for c in report['candidates'] if c['start']==report['selected_start'])
        assert candidate['iterations'] == report['config']['max_iterations']
        assert not candidate['optimizer_success']
        truth_path = source/'truth_comparison.json' if name!='corners_beta4' else source.parent/'truth_comparison.json'
        truth = e.json('flow', truth_path)
        nt_report = e.json('flow', BASE/'experiments'/name/'result/report.json')
        assert nt_report['checkpoint_sha256'] == FLOW_SHA and nt_report['forward_weights_unchanged']
        assert not nt_report['measured_timestamps_used'] and not nt_report['timed_fit_initialization_used']
        assert nt_report['config']['max_iterations'] == 700
        assert all(c['iterations']==700 for c in nt_report['candidates'])
        assert sha(e.path('flow', source/'fitted_model.json')) == compare[name]['timed_fit_sha256']
        assert sha(e.path('flow', BASE/'experiments'/name/'result/report.json')) == compare[name]['fit_report_sha256']
        inlet = e.csv('flow', dest/'inlet_comparison.csv')
        diff = np.linalg.norm(inlet['no_time_u']-inlet['timed_u'])/np.linalg.norm(inlet['timed_u'])
        shape = np.linalg.norm(inlet['no_time_normalized']-inlet['timed_normalized'])/np.linalg.norm(inlet['timed_normalized'])
        np.testing.assert_allclose([diff,shape],[compare[name]['profile_relative_l2_difference'],compare[name]['normalized_profile_relative_l2_difference']],rtol=1e-12)
        tracks = []; rms = []; geometric = []
        for i in [1,2]:
            obs = e.csv('flow', source/f'observed_track_{i}.csv')
            replay = e.csv('flow', source/f'track_{i}_forward.csv')
            np.testing.assert_array_equal(obs['t'],replay['t'])
            rmse = np.sqrt(np.mean((xy(replay)-xy(obs))**2))
            np.testing.assert_allclose(rmse,report['trajectories'][i-1]['position_rmse'],rtol=1e-12)
            assert report['trajectories'][i-1]['completed']
            np.testing.assert_array_equal(xy(obs)[0],xy(replay)[0])
            timed = e.csv('flow', dest/f'timed_track_{i}_dense.csv')
            no_time = e.csv('flow', BASE/'experiments'/name/'result'/f'track_{i}_forward.csv')
            err = e.csv('flow', dest/f'geometric_error_{i}.csv')
            scores = {}
            for key, a in [('timed',timed),('without_time',no_time)]:
                metrics = geom.curve_metrics(xy(obs),xy(a),count=1001)
                for metric,value in metrics.items():
                    np.testing.assert_allclose(value,compare[name]['paths'][i-1][key][metric],rtol=1e-9,atol=1e-13)
                scores[key] = metrics
                q,s = geom.resample_curve(xy(obs),1001)
                distances = geom.point_polyline_distance(q,geom.resample_curve(xy(a),1001)[0])
                np.testing.assert_allclose(distances,err['timed_distance_H' if key=='timed' else 'no_time_distance_H'],rtol=1e-8,atol=1e-12)
                np.testing.assert_allclose(s/s[-1],err['normalized_arclength'],atol=1e-14)
            assert compare[name]['paths'][i-1]['timed_completed'] and compare[name]['paths'][i-1]['without_time_completed']
            row = duration[(duration['case']==name)&(duration['particle']==i)][0]
            np.testing.assert_allclose([obs['t'][-1]-obs['t'][0],no_time['inferred_t'][-1]-no_time['inferred_t'][0]],
                [row['timed_duration'],row['no_time_inferred_duration']],rtol=1e-12)
            np.testing.assert_allclose(row['relative_difference_percent'],100*(row['no_time_inferred_duration']/row['timed_duration']-1),atol=1e-12)
            np.testing.assert_allclose(row['no_time_endpoint_mismatch_H'],np.linalg.norm(xy(obs)[-1]-xy(no_time)[-1]),rtol=1e-10)
            tracks.append(dict(obs=obs,replay=replay,timed=timed,no_time=no_time,error=err))
            rms.append(float(rmse)); geometric.append(scores)
        arrays = None
        if name != 'corners_beta4':
            arrays = dict(np.load(e.path('flow',source/'truth_comparison.npz')))
            delta = arrays['prediction']-arrays['reference']
            computed = dict(velocity_relative_l2=np.linalg.norm(delta[:,:2])/np.linalg.norm(arrays['reference'][:,:2]),
                pressure_relative_l2=np.linalg.norm(delta[:,2])/np.linalg.norm(arrays['reference'][:,2]),
                inlet_relative_l2=np.linalg.norm(arrays['inlet_prediction']-arrays['inlet_truth'])/np.linalg.norm(arrays['inlet_truth']))
            for key,value in computed.items():
                np.testing.assert_allclose(value,truth[key],rtol=1e-12)
        checks['timed'][name] = dict(position_rmse=rms,mean_speed=report['mean_speed'],truth=truth,
                                    field_norms_recomputed=arrays is not None)
        checks['geometric'][name] = dict(paths=geometric,inlet_difference=float(diff),shape_difference=float(shape))
        flow[name] = dict(tracks=tracks,inlet=inlet,arrays=arrays)
    for row, data in zip(duration,duration_report['durations']):
        for key in ['timed_duration','no_time_inferred_duration','relative_difference_percent','no_time_endpoint_mismatch_H']:
            np.testing.assert_allclose(row[key],data[key],atol=1e-14)
    mag_report = e.json('magnetic','results/master9/control_tests.json')
    provenance = e.json('magnetic','results/master9/provenance.json')
    assert provenance['checkpoint_sha256'] == MAG_SHA and mag_report['all_passed']
    master9 = {}
    for name, report in mag_report.items():
        if name == 'all_passed': continue
        a = e.csv('magnetic',f'results/master9/control_{name}.csv')
        t=.75*a['time_s']; xn=a['x_PINN_m']/R; zn=a['z_PINN_m']/D
        xr=a['x_Radau_m']/R; zr=a['z_Radau_m']/D
        target=lambda z,x0=xn[0],z0=zn[0]: x0+.02*(np.tanh(2*(z+.3))-np.tanh(2*(z0+.3)))
        np.testing.assert_allclose(target(zn),a['target_x_at_PINN_z_m']/R,atol=1e-14)
        np.testing.assert_allclose(target(zr),a['target_x_at_Radau_z_m']/R,atol=1e-14)
        tracking=np.abs(xr-a['target_x_at_Radau_z_m']/R)
        dx=np.max(np.abs(xn-xr)); dz=np.max(np.abs(zn-zr))
        values=[tracking.max(),dx,dz]
        expected=[report['max_independent_tracking_error_um']*1e-6/R,
                  report['max_model_oracle_x_difference_um']*1e-6/R,
                  report['max_model_oracle_z_difference_um']*1e-6/D]
        np.testing.assert_allclose(values,expected,rtol=1e-8)
        np.testing.assert_allclose(np.diff(t),.025,atol=1e-12)
        assert len(a)==report['steps'] and a['u'][-1]==a['u'][-2]
        assert np.max(np.abs(a['u']))<=.5 and zn[-1]>=1.4 and zr[-1]>=1.4
        assert tracking.max()<.01 and dx<.0066667 and dz<.00375 and report['passed']
        checks['master9'][name]=dict(Re=report['Re'],tracking=float(tracking.max()),
            delta_X=float(dx),delta_Z=float(dz),Z_final=float(zr[-1]),rows=len(a),command_intervals=len(a)-1)
        master9[name]=dict(raw=a,t=t,xn=xn,zn=zn,xr=xr,zr=zr,target=target,tracking=tracking)
    return flow,duration,master9,checks


def save(fig,out,name):
    fig.savefig(out/(name+'.pdf'),dpi=500,metadata={'Title':name,'Creator':'Matplotlib; archived results only',
                                                 'CreationDate':None,'ModDate':None})
    plt.close(fig)


def decorate(ax,tag):
    ax.set_title(tag,loc='left',fontsize=8,pad=5)
    ax.grid(alpha=.18,lw=.4)
    ax.tick_params(length=2.5,pad=2)


def timed_replay(case,out):
    fig,axes=plt.subplots(2,2,figsize=(WIDTH,3.85))
    spatial,inlet,xt,yt=axes.flat
    for i,(a,color) in enumerate(zip(case['tracks'],COLORS)):
        o,r=a['obs'],a['replay']
        spatial.plot(r['x'],r['y'],color=color,lw=1.2)
        spatial.plot(o['x'],o['y'],ls='none',marker='o',ms=2.5,mfc='none',mec=color,mew=.7,markevery=5)
        spatial.plot(o['x'][0],o['y'][0],marker='s',ms=3.5,color=color,clip_on=False)
        for ax,key in [(xt,'x'),(yt,'y')]:
            ax.plot(r['t'],r[key],color=color,lw=1.2)
            ax.plot(o['t'],o[key],ls='none',marker='o',ms=2.5,mfc='none',mec=color,mew=.7,markevery=5)
            ax.set(xlim=(0,1.2),xlabel=r'$t^*$',ylabel=f'${key}^*$')
    spatial.set(xlim=(0,5),ylim=(0,1),aspect='equal',xlabel=r'$x^*$',ylabel=r'$y^*$')
    a=case['arrays']
    inlet.plot(a['inlet_truth'],a['inlet_y'],color='.1',ls='--',lw=1.2,label='FEM truth')
    inlet.plot(a['inlet_prediction'],a['inlet_y'],color='#9b3069',lw=1.2,label='Timed estimate')
    inlet.set(xlabel=r'$u_{\rm inlet}/U_{\rm ref}$',ylabel=r'$y^*$',ylim=(0,1));inlet.legend(frameon=False,fontsize=7)
    for tag,ax in zip(['(a)','(b)','(c)','(d)'],axes.flat):decorate(ax,tag)
    handles=[Line2D([],[],color=COLORS[i],lw=1.2,label=f'Particle {i+1}') for i in [0,1]]
    handles += [Line2D([],[],color='.2',marker='o',mfc='none',ls='none',ms=3,label='Observed'),
                Line2D([],[],color='.2',lw=1.2,label='Independent replay')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.52,0),ncol=4,frameon=False,fontsize=7.5)
    fig.subplots_adjust(left=.085,right=.985,bottom=.16,top=.95,wspace=.34,hspace=.6)
    save(fig,out,'inverse-timed-replay')


def fields(a,out):
    x,y=(np.unique(a['xy'][:,i]) for i in [0,1])
    assert (len(x),len(y))==(73,97)
    ix,iy=np.searchsorted(x,a['xy'][:,0]),np.searchsorted(y,a['xy'][:,1])
    assert len(np.unique(iy*len(x)+ix))==7081
    xe=np.r_[x[0],(x[1:]+x[:-1])/2,x[-1]];ye=np.r_[y[0],(y[1:]+y[:-1])/2,y[-1]]
    fig=plt.figure(figsize=(WIDTH,3.25))
    gs=fig.add_gridspec(3,6,width_ratios=[1,1,.055,.27,1,.055],left=.075,right=.915,
                        bottom=.13,top=.90,wspace=.20,hspace=.9)
    for row,symbol in enumerate([r'$u^*$',r'$v^*$',r'$p^*$']):
        values=[]
        for key in ['reference','prediction']:
            z=np.empty((len(y),len(x)));z[iy,ix]=a[key][:,row];values.append(z)
        values.append(values[1]-values[0])
        lo=min(z.min() for z in values[:2]);hi=max(z.max() for z in values[:2]);cmap='viridis'
        if row==1:hi=max(abs(lo),abs(hi));lo=-hi;cmap='RdBu_r'
        dm=np.max(np.abs(values[2]))
        for col,slot in enumerate([0,1,4]):
            ax=fig.add_subplot(gs[row,slot]);norm=Normalize(lo,hi) if col<2 else Normalize(-dm,dm)
            mesh=ax.pcolormesh(xe,ye,values[col],norm=norm,cmap=cmap if col<2 else 'RdBu_r',rasterized=True)
            ax.set(xlim=(0,5),ylim=(0,1),aspect='equal',xticks=[0,2.5,5],yticks=[0,1])
            ax.tick_params(labelsize=8,pad=1.5,length=2)
            ticks=ax.get_xticklabels();ticks[0].set_ha('left');ticks[-1].set_ha('right')
            ax.text(.02,1.13,f'({string.ascii_lowercase[row*3+col]})',transform=ax.transAxes,fontsize=7)
            if col==0:ax.set_ylabel(symbol+'\n'+r'$y^*$',labelpad=3)
            else:ax.tick_params(labelleft=False)
            if row==0:ax.set_title(['FEM','Reconstruction','Reconstruction − FEM'][col],fontsize=7.5,pad=19)
            if row==2:ax.set_xlabel(r'$x^*$',labelpad=1)
            if col>0:
                cax=fig.add_subplot(gs[row,2 if col==1 else 5]);pos=ax.get_position();cp=cax.get_position()
                cax.set_position([cp.x0,pos.y0,cp.width,pos.height])
                cb=fig.colorbar(mesh,cax=cax,ticks=np.linspace(norm.vmin,norm.vmax,3))
                cb.solids.set_rasterized(False);cb.ax.tick_params(labelsize=7.5,pad=1,length=2)
                cb.ax.yaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    save(fig,out,'inverse-timed-fields')


def geometry(flow,checks,out):
    fig,axes=plt.subplots(3,3,figsize=(WIDTH,4.95),gridspec_kw={'width_ratios':[1.25,1,1.15]})
    umax=max(max(a['inlet']['timed_u'].max(),a['inlet']['no_time_u'].max()) for a in flow.values())*1.05
    for row,(name,label) in enumerate(zip(CASES,LABELS)):
        spatial,inlet,error=axes[row];a=flow[name]
        for track,color in zip(a['tracks'],COLORS):
            for key,style in [('timed','--'),('no_time','-')]:
                r=track[key];spatial.plot(r['x'],r['y'],color=color,ls=style,lw=1)
                err=track['error'];error.plot(err['normalized_arclength'],1e4*err['timed_distance_H' if key=='timed' else 'no_time_distance_H'],color=color,ls=style,lw=.9)
            o=track['obs'];spatial.plot(o['x'],o['y'],ls='none',marker='o',mfc='none',mec=color,ms=2.2,mew=.6,markevery=8)
            spatial.plot(o['x'][0],o['y'][0],marker='s',ms=3,color=color,clip_on=False)
        spatial.set(xlim=(0,5),ylim=(0,1),aspect='equal',xlabel=r'$x^*$',ylabel=r'$y^*$')
        for key,style,color in [('timed_u','--','.15'),('no_time_u','-','#9b3069')]:
            inlet.plot(a['inlet'][key],a['inlet']['y'],ls=style,color=color,lw=1.1)
        inlet.set(xlim=(0,umax),ylim=(0,1),xlabel=r'$u_{\rm inlet}/U_{\rm ref}$',ylabel=r'$y^*$')
        inlet.text(.96,.97,r'$\Delta f$: '+f"{100*checks['geometric'][name]['inlet_difference']:.3f}%",transform=inlet.transAxes,ha='right',va='top',fontsize=7.5)
        error.set(xlim=(0,1),ylim=(0,None),xlabel='Input arc fraction',ylabel=r'$10^4 d_{\rm obs\to replay}/H$')
        error.yaxis.set_major_locator(MaxNLocator(3))
        for col,ax in enumerate(axes[row]):decorate(ax,f'({string.ascii_lowercase[row*3+col]})'+(' '+label if col==0 else ''))
    handles=[Line2D([],[],color=COLORS[i],lw=1.2,label=f'Particle {i+1}') for i in [0,1]]
    handles += [Line2D([],[],color='.15',ls='--',label='Timed estimate'),Line2D([],[],color='.15',label='Geometry estimate'),
                Line2D([],[],color='.15',ls='none',marker='o',mfc='none',ms=3,label='Observed')]
    fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.51,.005),fontsize=7.5)
    fig.subplots_adjust(left=.08,right=.98,bottom=.17,top=.96,hspace=.8,wspace=.67)
    save(fig,out,'inverse-geometry-comparison')


def durations(a,out):
    fig,axes=plt.subplots(1,2,figsize=(WIDTH,2.55),sharey=True)
    rows=np.arange(6)
    axes[0].hlines(rows,a['timed_duration'],a['no_time_inferred_duration'],color='.65',lw=1)
    axes[0].plot(a['timed_duration'],rows,'o',color='.15',ms=4,label='Observed (supplied)')
    axes[0].plot(a['no_time_inferred_duration'],rows,'D',color='#9b3069',mfc='none',ms=4,label='Geometry (inferred)')
    axes[0].set(xlim=(0,1.3),xlabel=r'$T^*$',yticks=rows,yticklabels=['B / 1','B / 2','A / 1','A / 2','Oblique / 1','Oblique / 2'])
    axes[0].invert_yaxis()
    axes[1].axvline(0,color='.5',ls=':',lw=.8)
    axes[1].plot(a['relative_difference_percent'],rows,'o',color='#24588b',ms=4)
    axes[1].set(xlim=(-2,5),xlabel=r'$100(T_{\rm geo}^*-T_{\rm obs}^*)/T_{\rm obs}^*$')
    for tag,ax in zip(['(a)','(b)'],axes):decorate(ax,tag)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.53,0),fontsize=7.5)
    fig.subplots_adjust(left=.15,right=.98,bottom=.28,top=.9,wspace=.26)
    save(fig,out,'inverse-geometry-duration')


def tracking(master9,out):
    fig,axes=plt.subplots(2,3,figsize=(WIDTH,3.75))
    for row,(name,label) in enumerate([('nominal','Nominal'),('low_speed_high_viscosity','Low speed / high viscosity')]):
        a=master9[name];spatial,command,error=axes[row];raw=a['raw']
        z=np.linspace(a['zn'][0],1.4,401)
        spatial.plot(z,a['target'](z),color='.12',ls='--',lw=1.1)
        end=max(a['zn'][-1],a['zr'][-1])
        ze=np.linspace(1.4,end,20);spatial.plot(ze,a['target'](ze),color='.5',ls=':',lw=1)
        spatial.plot(a['zn'],a['xn'],color='#24588b',lw=1.2)
        spatial.plot(a['zr'],a['xr'],color='#bc4a24',lw=.9,marker='o',mfc='none',ms=2.6,markevery=max(1,len(raw)//12))
        spatial.axvline(1.4,color='.6',ls=':',lw=.65)
        spatial.annotate(r'$Z=1.4$',xy=(1.4,.03),xycoords=('data','axes fraction'),
                         xytext=(-3,2),textcoords='offset points',rotation=90,ha='right',va='bottom',fontsize=7)
        spatial.set(xlabel=r'$Z=z/D$',ylabel=r'$X=x/R$')
        spatial.yaxis.set_major_locator(MaxNLocator(3))
        command.step(a['t'],raw['u'],where='post',color='#9b3069',lw=.95)
        command.set(xlim=(0,a['t'][-1]),xlabel=r'$\tau$',ylabel=r'$c(\tau)$')
        error.plot(a['t'],1e4*a['tracking'],color='#24588b',lw=1.1)
        error.set(xlim=(0,a['t'][-1]),ylim=(0,None),xlabel=r'$\tau$',ylabel=r'$10^4 |X_{\rm Radau}-X_{\rm target}|$')
        for col,ax in enumerate(axes[row]):decorate(ax,f'({string.ascii_lowercase[row*3+col]})'+(' '+label if col==0 else ''))
    handles=[Line2D([],[],color='.12',ls='--',label='Target'),Line2D([],[],color='#24588b',label='PINN'),
             Line2D([],[],color='#bc4a24',marker='o',mfc='none',ms=3,label='Radau')]
    fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.51,.065))
    fig.text(.5,.045,'Trajectory zooms: independent X and Z scales',ha='center',fontsize=7.5)
    fig.text(.5,.012,r'Effective command: $-0.5\leq c\leq0.5$ (zoomed ordinate)',ha='center',fontsize=7.5)
    fig.subplots_adjust(left=.1,right=.985,bottom=.24,top=.94,wspace=.65,hspace=.6)
    save(fig,out,'inverse-master9-tracking')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flow',required=True,type=Path);parser.add_argument('--magnetic',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
        'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':8,'axes.linewidth':.65,'pdf.fonttype':42})
    e=Evidence(args.flow,args.magnetic)
    flow,duration,master9,checks=validate(e)
    timed_replay(flow['corners_beta5'],args.output);fields(flow['corners_beta5']['arrays'],args.output)
    geometry(flow,checks,args.output);durations(duration,args.output);tracking(master9,args.output)
    manifest=dict(source_revisions=dict(flow=FLOW_REV,magnetic=MAG_REV),
        checkpoint_sha256=dict(flow=FLOW_SHA,master9=MAG_SHA),input_sha256=e.files,validation=checks,
        units=dict(flow='Stored common H, U_ref units; no additional A or A^2 scaling; no pressure shift',
                   master9='X=x_m/75e-6; Z=z_m/0.04; tau=0.75*time_s; error columns displayed times 10^4'),
        output_sha256={p.name:sha(p) for p in sorted(args.output.glob('inverse-*.pdf'))})
    (args.output/'inverse-results-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Validated six timed replays, twelve geometric scores, six durations, four Master9 cases; wrote five PDFs.')


if __name__=='__main__':main()
