#!/usr/bin/env python3
"""Thesis-width revision: archived arrays only; no model, optimizer or ODE calls.

python figs/chapter4/plot_revision.py --flow FLOW --magnetic MAG
Requires NumPy, SciPy and Matplotlib. Research checkouts remain read-only.
Legacy plotting scripts and their pinned modes are intentionally preserved.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.interpolate import CubicSpline
import numpy as np

HERE = Path(__file__).resolve().parent
THESIS = HERE.parents[1]
FORM = THESIS/'New_Main_Results/runs/formation_20261112_cpu'
FWD = Path('results/diverse_profiles_2026_11_07')
GEOM = Path('flow_reconstruction_no_time')
BLUE, ORANGE, PINK = '#173f59', '#c88000', '#bb2888'
PC = [ORANGE, PINK]
WIDTH = 6.27
REVS = {'flow':'92897a6962e537a4bea88042609be102095db037',
        'magnetic':'639906f53a11934b3058fbbdb246e34a1dd001fd',
        'thesis':'9690560dd817fc3bea96007fd4c200a1141db712'}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


class Evidence:
    def __init__(self, roots):
        self.roots = roots
        self.inputs, self.figures, self.checks = {}, [], {}
        for name in ['flow','magnetic']:
            assert subprocess.check_output(['git','-C',str(roots[name]),'rev-parse','HEAD'],text=True).strip() == REVS[name]

    def path(self, source, relative):
        p = self.roots[source]/relative
        self.inputs[f'{source}/{relative}'] = sha(p)
        return p

    def js(self, source, relative): return json.loads(self.path(source,relative).read_text())
    def npz(self, source, relative):
        with np.load(self.path(source,relative),allow_pickle=False) as z:
            return {k:z[k].copy() for k in z.files}
    def csv(self, source, relative):
        return np.genfromtxt(self.path(source,relative),delimiter=',',names=True)
    def save(self, fig, name, cases, layout, source_page, conversion='Saved dimensionless quantities; no rescaling'):
        fig.savefig(HERE/(name+'.pdf'),dpi=450,metadata={'Title':name,'CreationDate':None,'ModDate':None})
        plt.close(fig)
        self.figures.append(dict(output=name+'.pdf',sha256=sha(HERE/(name+'.pdf')),cases=cases,
            layout=layout,source_page=source_page,scale_conversions=conversion,
            inputs_sha256=self.inputs.copy()))
        self.inputs.clear()


def title(ax, letter, text):
    ax.set_title(f'({letter}) {text}',loc='left',fontsize=8.5,pad=6)
    ax.grid(alpha=.15,lw=.4)
    ax.tick_params(length=2.5,pad=2)
    from matplotlib.ticker import ScalarFormatter
    for axis in [ax.xaxis,ax.yaxis]:
        formatter=axis.get_major_formatter()
        if isinstance(formatter,ScalarFormatter):
            formatter.set_scientific(False);formatter.set_useOffset(False)


def cmap(fig, ax, x, y, values, vmax, label, cmap_name='viridis', peers=None):
    # Mid-cell boundaries stay within the sampled domain, including nonuniform grids.
    xe=np.r_[x[0],(x[:-1]+x[1:])/2,x[-1]]
    ye=np.r_[y[0],(y[:-1]+y[1:])/2,y[-1]]
    im=ax.pcolormesh(xe,ye,values,shading='flat',vmin=0,vmax=vmax,cmap=cmap_name,rasterized=True)
    cb=fig.colorbar(im,ax=peers if peers is not None else ax,orientation='horizontal',pad=.23,fraction=.07,aspect=30)
    cb.set_label(label,fontsize=8); cb.ax.tick_params(labelsize=7)
    return im


def flow_forward(e):
    rows=e.js('flow',FWD/'metrics.json')['selected_forward_cases']
    assert len(rows)==7
    data={}
    for row in rows:
        a=e.npz('flow',FWD/f"data/{row['name']}.npz")
        assert sha(e.path('flow',FWD/f"data/{row['name']}.npz"))==row['data_sha256']
        assert len(a['xy'])==7081
        diff=a['prediction']-a['reference']
        ev=np.linalg.norm(diff[:,:2])/np.linalg.norm(a['reference'][:,:2])
        ep=np.linalg.norm(diff[:,2])/np.linalg.norm(a['reference'][:,2])
        np.testing.assert_allclose([ev,ep],[row['velocity_relative_l2'],row['pressure_relative_l2']],rtol=1e-12)
        e.checks[row['name']]=dict(velocity_percent=100*ev,pressure_percent=100*ep,
            transverse_rmse=float(np.sqrt(np.mean(diff[:,1]**2))),transverse_relative_l2=float(np.linalg.norm(diff[:,1])/np.linalg.norm(a['reference'][:,1])))
        data[row['name']]=a
    fig,axs=plt.subplots(2,4,figsize=(WIDTH,4.0),sharex=True,sharey=True)
    yy=np.linspace(0,1,2049)
    maxu=max(CubicSpline(a['inlet_y'],a['inlet_values'])(yy).max() for a in data.values())*1.06
    names=['Asymmetric','Twin peaks','Three-cycle','Four-cycle','Mixed','Shoulder','Nine-cycle']
    for i,(ax,row,name) in enumerate(zip(axs.flat,rows,names)):
        a=data[row['name']];u=CubicSpline(a['inlet_y'],a['inlet_values'])(yy)
        ax.plot(u,yy,color='#11687c',lw=1.3)
        ax.set(xlim=(0,maxu),ylim=(0,1),xlabel=r'$u/\bar{U}$',ylabel=r'$y/H$')
        title(ax,chr(97+i),f"{name}\nRe = {row['reynolds']:g}")
    axs.flat[-1].axis('off')
    fig.subplots_adjust(left=.08,right=.98,bottom=.12,top=.90,wspace=.35,hspace=.75)
    e.save(fig,'forward-flow-exploratory-gallery',[r['name'] for r in rows],'2 x 4, seven profiles','all_new_figures.pdf p.8')
    for row in rows:
        name=row['name'];a=data[name]
        # Three body cases and four supplementary cases preserve all seven chains.
        e.path('flow',FWD/'metrics.json'); e.path('flow',FWD/f'data/{name}.npz')
        x,y=(np.unique(a['xy'][:,i]) for i in range(2));ix=np.searchsorted(x,a['xy'][:,0]);iy=np.searchsorted(y,a['xy'][:,1])
        assert len(np.unique(ix*len(y)+iy))==len(a['xy'])
        def grid(v):
            z=np.empty((len(y),len(x)));z[iy,ix]=v;return z
        net=np.linalg.norm(a['prediction'][:,:2],axis=1);ref=np.linalg.norm(a['reference'][:,:2],axis=1)
        err=np.linalg.norm((a['prediction']-a['reference'])[:,:2],axis=1)
        fig=plt.figure(figsize=(WIDTH,4.75))
        gs=fig.add_gridspec(2,6,left=.085,right=.98,bottom=.13,top=.93,hspace=.95,wspace=1.1)
        axs=[fig.add_subplot(gs[0,s:s+2]) for s in [0,2,4]]+[fig.add_subplot(gs[1,:3]),fig.add_subplot(gs[1,3:])]
        axs[0].plot(CubicSpline(a['inlet_y'],a['inlet_values'])(yy),yy,color='#11687c');axs[0].set(xlabel=r'$u/\bar{U}$',ylabel=r'$y/H$',ylim=(0,1))
        vmax=max(net.max(),ref.max())
        for ax,v in zip(axs[1:3],[net,ref]):
            ax.pcolormesh(x,y,grid(v),shading='nearest',vmin=0,vmax=vmax,cmap='viridis',rasterized=True)
        # Shared map scale, with grid edges clipped to the sampled rectangle.
        for ax in axs[1:3]:ax.collections[0].remove()
        cmap(fig,axs[2],x,y,grid(ref),vmax,r'$|\mathbf{U}|/\bar{U}$',peers=axs[1:3])
        xe=np.r_[x[0],(x[:-1]+x[1:])/2,x[-1]];ye=np.r_[y[0],(y[:-1]+y[1:])/2,y[-1]]
        axs[1].pcolormesh(xe,ye,grid(net),shading='flat',vmin=0,vmax=vmax,cmap='viridis',rasterized=True)
        cmap(fig,axs[3],x,y,grid(err),err.max(),r'$\|\mathbf{U}_{net}-\mathbf{U}_{FEM}\|/\bar{U}$','magma')
        for ax in [axs[1],axs[2],axs[3]]:ax.set(xlim=(0,5),ylim=(0,1),xlabel=r'$x/H$',ylabel=r'$y/H$',xticks=[0,2.5,5],yticks=[0,.5,1])
        sections=[]
        for target,color in [(.05,'#0a7492'),(.2,ORANGE),(1.,'#8448a1')]:
            k=np.argmin(abs(x-target));sections.append(float(x[k]))
            axs[4].plot(grid(ref)[:,k],y,color=color,lw=1.1,label=f'$x/H={x[k]:.2f}$')
            axs[4].plot(grid(net)[:,k],y,color=color,lw=1,ls='--')
        axs[4].set(xlabel=r'$|\mathbf{U}|/\bar{U}$',ylabel=r'$y/H$',ylim=(0,1));axs[4].legend(fontsize=7,frameon=False,loc='best')
        for i,(ax,t) in enumerate(zip(axs,['Inlet','DeepONet','FEM','Vector error','Sections: FEM —, net --'])):title(ax,chr(97+i),t)
        e.checks[name]['cross_sections']=sections
        slug={'skew_b3':'skew-b3','twin_b3_r20':'twin-b3-r20'}.get(name,name)
        e.save(fig,'forward-flow-chain-'+slug,[name],'three top panels, two wider lower panels; stretched maps',f'all_new_figures.pdf p.{1+[r["name"] for r in rows].index(name)}')
    return rows


def magnetic_forward(e):
    base=Path('results/trained_presentation');report=e.js('magnetic',base/'validation.json')
    assert report['all_passed'] and len(report['cases'])==12
    all_data={}
    for row in report['cases']:
        d=e.csv('magnetic',base/(row['case']+'.csv'));tau=.75*d['time_s']
        assert len(d)==801 and np.all(np.diff(tau)>0)
        ex=np.abs(d['x_network_m']-d['x_numerical_m'])/75e-6;ez=np.abs(d['z_network_m']-d['z_numerical_m'])/.04
        np.testing.assert_allclose([ex.max(),ez.max()],[row['max_x_error_um']/75,row['max_z_error_um']/40000],rtol=1e-8)
        np.testing.assert_allclose((d['x_network_m']-d['x_numerical_m'])*1e6,d['error_x_um'],atol=1e-11)
        np.testing.assert_allclose((d['z_network_m']-d['z_numerical_m'])*1e6,d['error_z_um'],atol=1e-10)
        all_data[row['case']]=(d,row,ex,ez)
        e.checks[row['case']]=dict(X0=float(d['x_network_m'][0]/75e-6),Z0=float(d['z_network_m'][0]/.04),tau_f=float(tau[-1]),max_X=float(ex.max()),max_Z=float(ez.max()))
    shared=e.inputs.copy();e.inputs.clear()
    selected=['03_gaussian_pulse','08_alternating_pulses','09_slow_dual_chirp','11_downstream_switch','12_phase_interference']
    for name in selected:
        d,row,_,_=all_data[name];e.path('magnetic',base/'validation.json');e.path('magnetic',base/(name+'.csv'))
        t=.75*d['time_s'];x0=d['x_network_m'][0]/75e-6
        fig=plt.figure(figsize=(WIDTH,4.9));gs=fig.add_gridspec(2,6,left=.13,right=.98,bottom=.18,top=.94,wspace=1.1,hspace=1.05)
        axs=[fig.add_subplot(gs[0,s:s+2]) for s in [0,2,4]]+[fig.add_subplot(gs[1,:3]),fig.add_subplot(gs[1,3:])]
        axs[0].plot(t,d['a_left'],color=ORANGE,label='$a_L$');axs[0].plot(t,d['a_right'],color=PINK,ls='--',label='$a_R$')
        axs[0].set(xlabel=r'$\tau$',ylabel='$a_L,a_R$',ylim=(-.75,.75));axs[0].legend(frameon=False,fontsize=7)
        zlo=max(-2,min(d['z_network_m'].min(),d['z_numerical_m'].min())/.04-.05)
        zhi=min(1.7,max(d['z_network_m'].max(),d['z_no_B_m'].max(),d['z_numerical_m'].max())/.04+.05)
        z=np.linspace(zlo,zhi,180);w=x0*75e-6/.04+1j*z[None,:]
        field=abs(d['a_left'][:,None]/(1+w)**2-d['a_right'][:,None]/(1-w)**2)
        cmap(fig,axs[1],z,t,field,np.sqrt(.5),r'$|B^*|$')
        axs[1].set(xlabel='$Z$',ylabel=r'$\tau$')
        zz=np.linspace(-2,1.7,180);xx=np.linspace(-1,1,121);flow=row['parameters']['mean']/.015*(1-xx[:,None]**2)*np.ones((1,len(zz)))
        cmap(fig,axs[2],zz,xx,flow,row['parameters']['mean']/.015,r'$u_z/(2U_{ref})$')
        axs[2].set(xlabel='$Z$',ylabel='$X$',xlim=(-2,1.7),ylim=(-1,1),yticks=[-1,0,1])
        for ax,abscissa in [(axs[3],'space'),(axs[4],'time')]:
            for key,color,style,label in [('no_B',ORANGE,'--','No field'),('network',PINK,'-','Master10'),('numerical',BLUE,':','DOP853')]:
                tx=d[f'z_{key}_m']/.04 if abscissa=='space' else t
                ax.plot(tx,d[f'x_{key}_m']/75e-6,color=color,ls=style,lw=1.25,label=label,
                        marker='o' if key=='numerical' else None,markevery=80,ms=3,mfc='none')
            ax.set(xlabel='$Z$ (zoom)' if abscissa=='space' else r'$\tau$',ylabel='$X$')
        for i,(ax,s) in enumerate(zip(axs,['Sources',f'Field at $X_0={x0:g}$','Carrier','Spatial replay','Transverse response'])):title(ax,chr(97+i),s)
        fig.legend(*axs[3].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.045),ncol=3,frameon=False,fontsize=8)
        fig.text(.5,.015,'Trajectory zoom: X and Z use different reference lengths',ha='center',fontsize=7.5)
        e.save(fig,'forward-magnetic-chain-'+name[:2],[name],'three top, two wider lower; independent spatial scales',f'trained_cases_panels_1_to_5.pdf p.{int(name[:2])}',
            'X=x_m/75e-6; Z=z_m/0.04; tau=0.75*time_s; analytic field / B_s; carrier / (2 U_ref)')
    e.inputs.update(shared)
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,2.5))
    for name,color,style in zip([selected[i] for i in [0,1,2,4]],[BLUE,ORANGE,PINK,'#228833'],['-','--',':','-.']):
        d,_,ex,ez=all_data[name]
        for ax,err in zip(axs,[ex,ez]):ax.plot(.75*d['time_s'],1e5*err,color=color,ls=style,lw=1.1,label=name[:2])
    for ax,c in zip(axs,['X','Z']):ax.set(xlabel=r'$\tau$',ylabel=rf'$10^5|\Delta {c}|$',ylim=(0,None));ax.grid(alpha=.2)
    axs[0].legend(ncol=2,fontsize=7,frameon=False)
    fig.subplots_adjust(left=.09,right=.98,bottom=.24,top=.95,wspace=.4)
    e.save(fig,'forward-magnetic-errors',[selected[i] for i in [0,1,2,4]],'two time-error axes','magnetic pages 3,8,9,12','Absolute position differences / R,D; times *0.75')


def inverse_chain(e,name,geometry=False):
    root=(GEOM/'experiments'/name/'result') if geometry else (FWD/'data/inverse'/name)
    a=e.npz('flow',root/'reconstructed_flow.npz');inlet=e.csv('flow',root/'inlet_reference_units.csv')
    fig=plt.figure(figsize=(WIDTH,5.2 if geometry else 4.85))
    gs=fig.add_gridspec(2,3,left=.085,right=.98,bottom=.15,top=.94,wspace=.55,hspace=.85,width_ratios=[1,1,1.15 if geometry else 1])
    axs=[fig.add_subplot(gs[i//3,i%3]) for i in range(5)]
    if geometry:
        sub=gs[1,2].subgridspec(2,1,hspace=.23);clock=[fig.add_subplot(sub[0]),fig.add_subplot(sub[1])];axs.append(clock[0])
    else:axs.append(fig.add_subplot(gs[1,2]));clock=[]
    yy=np.linspace(0,1,2049);axs[1].plot(CubicSpline(inlet['y'],inlet['u'])(yy),yy,color='#11687c')
    axs[1].set(xlabel=r'Inferred $u/U_{ref}$',ylabel='$y/H$',ylim=(0,1))
    x,y=a['x'],a['y'];speed=np.hypot(a['u'],a['v']).T
    # One explicit colorbar beneath the top field; do not shrink a union of rows.
    colorpos=axs[2].get_position()
    colorax=fig.add_axes([colorpos.x0,.555,colorpos.width,.015])
    im=axs[2].pcolormesh(x,y,speed,shading='nearest',vmin=0,vmax=speed.max(),cmap='viridis',rasterized=True)
    im.remove()
    xe=np.r_[x[0],(x[:-1]+x[1:])/2,x[-1]];ye=np.r_[y[0],(y[:-1]+y[1:])/2,y[-1]]
    for axis in [axs[2],axs[3]]:
        im=axis.pcolormesh(xe,ye,speed,vmin=0,vmax=speed.max(),cmap='viridis',shading='flat',rasterized=True)
    cb=fig.colorbar(im,cax=colorax,orientation='horizontal')
    cb.set_label(r'$|\mathbf{U}|/U_{ref}$',fontsize=8,labelpad=1);cb.ax.tick_params(labelsize=7,pad=1)
    for ax in [axs[0],axs[2],axs[3],axs[4]]:ax.set(xlim=(0,5),ylim=(0,1),xlabel='$x/H$',ylabel='$y/H$',xticks=[0,2.5,5],yticks=[0,.5,1])
    rms=[]
    for i,color in enumerate(PC,1):
        obs=e.csv('flow',GEOM/f'experiments/{name}/input/curve_{i}.csv') if geometry else e.csv('flow',root/f'observed_track_{i}.csv')
        sim=e.csv('flow',root/f'track_{i}_forward.csv')
        axs[0].plot(obs['x'],obs['y'],'.-',ms=1.6,lw=.7,color=color,label=f'Particle {i}')
        axs[0].plot(obs['x'][0],obs['y'][0],'s',ms=3,color=color)
        axs[3].plot(sim['x'],sim['y'],color='black',lw=2.4)
        axs[3].plot(sim['x'],sim['y'],color=color,lw=1.3,marker='o',markevery=max(1,len(sim)//4),ms=3,mec='black',mew=.4)
        axs[4].plot(sim['x'],sim['y'],color=color,lw=1.2)
        axs[4].plot(obs['x'][::5],obs['y'][::5],'o',ms=2.5,mfc='none',mec=color,mew=.7)
        if geometry:
            timed=e.csv('flow',GEOM/f'comparisons/{name}/timed_track_{i}_dense.csv')
            axs[4].plot(timed['x'],timed['y'],color=color,ls='--',lw=.9)
            for ax,c in zip(clock,['x','y']):
                ax.plot(sim['inferred_t'],sim[c],color=color,lw=1.1)
                ax.plot(timed['t'],timed[c],color=color,lw=.9,ls='--');ax.set_ylabel(f'${c}/H$',labelpad=1);ax.grid(alpha=.15)
        else:
            np.testing.assert_array_equal(obs['t'],sim['t'])
            dist=np.hypot(obs['x']-sim['x'],obs['y']-sim['y']);rms.append(float(np.sqrt(np.mean(dist**2))))
            axs[5].plot(sim['t'],1e3*dist,color=color,lw=1,label=f'Particle {i}')
    headings=['Ordered paths' if geometry else 'Observed paths','Inferred inlet','Estimated field','Particles in field','Both replays' if geometry else 'Observed / replay','Original clocks' if geometry else 'Replay mismatch']
    for i,(ax,t) in enumerate(zip(axs,headings)):title(ax,chr(97+i),t)
    axs[0].legend(fontsize=7,frameon=False,loc='best')
    if geometry:
        clock[0].tick_params(labelbottom=False);clock[1].set_xlabel(r'$t^*=tU_{ref}/H$')
        fig.text(.5,.035,'Particle colors fixed; solid: geometry only; dashed: timed; circles: observations',ha='center',fontsize=7.1)
        e.path('flow',GEOM/'comparison_metrics.json');e.path('flow',GEOM/'arrival_time_comparison/metrics.json')
        prefix='inverse-geometry-chain-';slug={'oblique_beta5':'oblique','corners_beta4':'b','corners_beta5':'a'}[name]
        page={'corners_beta4':1,'corners_beta5':2,'oblique_beta5':3}[name]
        source=f'chains_only.pdf p.{page}'
    else:
        axs[5].set(xlabel=r'$t^*=tU_{ref}/H$',ylabel=r'$10^3\|\Delta\mathbf{r}\|/H$',ylim=(0,None))
        fig.text(.5,.025,'Colors: particle identity; open circles: observations; solid: independent ODE',ha='center',fontsize=7.5)
        e.checks['timed_'+name]={'euclidean_rms_percent_H':[100*v for v in rms], 'component_rms_times_1e4':[1e4*v/np.sqrt(2) for v in rms]}
        prefix='inverse-timed-chain-';slug={'corners_beta4':'b','corners_beta5':'a','oblique_beta5':'oblique'}[name]
        source=f'all_new_figures.pdf p.{dict(corners_beta4=13,corners_beta5=11,oblique_beta5=9)[name]}'
    e.save(fig,prefix+slug,[name],'2 x 3; shared field scale; original clocks',source,'Saved x/H,y/H, u/U_ref, tU_ref/H; no clock warping')


def particle_count(e):
    base=Path('results/particle_count');summary=e.js('flow',base/'summary.json')
    np.testing.assert_allclose(np.median(summary['inlet_errors_percent'],axis=0),summary['median_error_percent_by_N'],rtol=1e-12)
    fig,axs=plt.subplots(1,3,figsize=(WIDTH,2.75),sharey=True,sharex=True)
    for ax,name in zip(axs,['beta5','twin_b3_r30','flat30']):
        for n,color,style in [(2,PINK,':'),(5,BLUE,'--'),(6,'#228833','-.')]:
            d=e.csv('flow',base/f'fits/{name}/N{n}/inlet.csv')
            er=100*np.linalg.norm(d['estimated']-d['truth'])/np.linalg.norm(d['truth'])
            np.testing.assert_allclose(er,np.array(summary['inlet_errors_percent'])[summary['profile_order'].index(name),[2,3,4,5,6].index(n)],rtol=1e-12)
            ax.plot(d['estimated'],d['y'],color=color,ls=style,lw=1.1,label=f'N={n}')
        ax.plot(d['truth'],d['y'],'k-',lw=1,label='Reference');ax.set(xlabel=r'$u/U_{ref}$',ylim=(0,1),xlim=(0,2.9));ax.grid(alpha=.15)
    axs[0].set_ylabel('$y/H$')
    for i,(ax,t) in enumerate(zip(axs,['Narrow beta','Twin peaks','Near-flat'])):title(ax,chr(97+i),t)
    fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,fontsize=8)
    fig.subplots_adjust(left=.085,right=.98,bottom=.28,top=.87,wspace=.25)
    e.save(fig,'inverse-particle-count-profiles',['beta5','twin_b3_r30','flat30'],'three profiles, N=2,5,6','particle-count archived inlet.csv','Shared U_ref; no individual mean normalization')


def magnetic_inverse(e):
    base=Path('results/operator_inverse/A_single');d=e.csv('magnetic',base/'controls.csv');q=e.csv('magnetic',base/'replay.csv');report=e.js('magnetic',base/'report.json')
    assert np.max(np.abs(d['a_R_ref']))==0
    fig,axs=plt.subplots(2,2,figsize=(WIDTH,3.85))
    axs[0,0].plot(d['tau'],d['a_L_ref'],'k--',lw=1,label='Reference');axs[0,0].plot(d['tau'],d['a_L_fit_aligned'],color=PINK,lw=1.2,label='Recovered')
    axs[0,0].set(xlabel=r'$\tau$',ylabel='$a_L$');axs[0,0].legend(fontsize=7,frameon=False)
    for kind,color,style,label in [('ref','black','--','Reference'),('replay',BLUE,'-','Independent ODE')]:axs[0,1].plot(q['Z_'+kind],q['X_'+kind],color=color,ls=style,lw=1.1,label=label)
    axs[0,1].set(xlabel='$Z$ (zoom)',ylabel='$X$');axs[0,1].legend(fontsize=7,frameon=False)
    for ax,c in zip(axs[1],['X','Z']):
        err=np.abs(q[c+'_replay']-q[c+'_ref']);ax.plot(q['tau'],1e5*err,color=BLUE,lw=1.1)
        ax.set(xlabel=r'$\tau$',ylabel=rf'$10^5|\Delta {c}|$',ylim=(0,None))
        e.checks['A_single_'+c]=float(err.max())
    for i,(ax,t) in enumerate(zip(axs.flat,['Positive left source','Spatial replay','Transverse error','Axial error'])):title(ax,chr(97+i),t)
    fig.subplots_adjust(left=.09,right=.98,bottom=.16,top=.92,hspace=.75,wspace=.4)
    e.checks['A_single_report']=report
    e.save(fig,'inverse-master10-single',['A_single'],'2 x 2; source, path, independent replay errors','operator_inverse/A_single','Already dimensionless X,Z,tau; errors *1e5')


def formation(e):
    relative=FORM.relative_to(THESIS);register=e.js('thesis',relative/'figures_manifest.json')
    for v in register:
        if v['id'] in ['F04','F09','F10','F12']:
            for item in v['inputs']:
                assert sha(THESIS/'New_Main_Results'/item['path'])==item['sha256'],item['path']
    e.checks['formation_registered_hashes']='F04,F09,F10,F12 inputs verified'
    p=e.path('thesis',relative/'figure_inputs/summary.csv');rows=list(csv.DictReader(p.open()))
    case=relative/'cases/C1_a4b0b778723f';schedule=list(csv.DictReader(e.path('thesis',case/'release_schedule.csv').open()));e.path('thesis',case/'metrics.json')
    ports=['B1','B2','B3','T1','T2','T3'];counts=[sum(r['port_id']==p for r in schedule) for p in ports]
    assert counts==[5,4,3,6,5,1] and len(schedule)==24
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,2.65),gridspec_kw={'width_ratios':[1,1.35]})
    stats=[];executed=[]
    for j,cap in enumerate(['4','6','8','None']):
        part=[r for r in rows if r['group']=='C1' and r['N']=='24' and r['cap']==('' if cap=='None' else cap) and r['status'] in ['accepted','rejected']]
        assert len(part)==(3 if cap=='None' else 1),(cap,len(part))
        accepted=sum(r['accepted']=='True' for r in part);stats.append(accepted);executed.append(len(part))
        axs[0].plot(j,accepted/len(part),'o',color=BLUE);axs[0].text(j,accepted/len(part)+.08,f'{accepted}/{len(part)} pass',ha='center',fontsize=7);axs[0].text(j,.53,f'{len(part)}/3 done',ha='center',fontsize=7,color='.4')
    assert stats==[0,1,1,3] and executed==[1,1,1,3]
    axs[0].set(xticks=range(4),xticklabels=['4','6','8','unlimited'],xlabel='Configured per-port cap',ylabel='Accepted / executed',ylim=(-.05,1.3),yticks=[0,.5,1])
    axs[0].text(.03,.04,'Cap 3: structurally excluded\nN=48/100: separate pending grid',transform=axs[0].transAxes,fontsize=7,color='.4')
    for j,port in enumerate(ports):
        times=[float(r['release_time']) for r in schedule if r['port_id']==port]
        axs[1].plot(times,[j]*len(times),'|',ms=10,color=BLUE if j<3 else PINK)
        axs[1].text(1.015,j,str(counts[j]),transform=axs[1].get_yaxis_transform(),va='center',fontsize=8)
    axs[1].axhline(2.5,color='.7',lw=.5);axs[1].set(yticks=range(6),yticklabels=ports,xlabel='$t^*$',ylabel='Port',ylim=(-.6,5.8))
    title(axs[0],'a','N=24; six fixed ports');title(axs[1],'b','Selected schedule; cap = 6')
    fig.subplots_adjust(left=.09,right=.95,bottom=.22,top=.87,wspace=.45)
    e.checks['release_capacity']=dict(ports=ports,counts=counts,accepted=stats,executed=executed,planned=[3]*4)
    e.save(fig,'formation-release-capacity',['C1_a4b0b778723f'],'capacity fraction and release raster','FORM F04')
    ext=e.js('thesis',Path('figs/chapter4/formation-extension-manifest.json'))
    inputs=next(v for v in ext['figures'] if v['id']=='F09_F11')['inputs']
    fig=plt.figure(figsize=(WIDTH,4.5));gs=fig.add_gridspec(2,6,left=.09,right=.98,bottom=.12,top=.93,hspace=.85,wspace=1.2)
    ax=fig.add_subplot(gs[0,:3]);pen=fig.add_subplot(gs[0,3:]);snap=[fig.add_subplot(gs[1,j:j+2]) for j in [0,2,4]]
    for fold,color,label in [('historical_replays/dense_duck_six_fixed',BLUE,'Duck 42'),('cases/D1_93bf6b884031',PINK,'Fish 100')]:
        d=e.npz('thesis',relative/fold/'trajectories.npz');m=e.js('thesis',relative/fold/'metrics.json')
        assert (label!='Fish 100' or m['N']==100)
        for mode,style in [('reference','-'),('pinn','--')]:
            ax.plot(d['time'],d[mode+'_sampled_dmin'],color=color,ls=style,lw=1,label=label if mode=='reference' else None)
            mm=m['replays'][mode]['minimum'];ax.plot(mm['time'],mm['distance'],'o',mfc='none',mec=color,ms=4)
        e.checks[label+'_refined_min']=m['replays']['reference']['minimum']['distance']
    ax.axhline(.026,color='k',ls=':',lw=.8);ax.set(xlabel='$t^*$',ylabel='$d_{min}^*$',ylim=(.025,.05));ax.legend(fontsize=7,frameon=False)
    # Preserve the separate matched six-particle penalty experiment from its register.
    penalty=[]
    for item in inputs:
        if item['path'].endswith('/metrics.json') and '/cases/G2_' in item['path']:
            rel=Path('New_Main_Results')/item['path'];m=e.js('thesis',rel);c=e.js('thesis',rel.parent/'config.json')
            penalty.append((c,m))
    assert len(penalty)==6
    for c,m in penalty:
        yes=c['collision_aware'];pen.plot(int(yes),m['replays']['reference']['minimum']['distance'],'o' if m['accepted'] else 'x',color=BLUE if yes else PINK,ms=5)
    pen.axhline(.026,color='k',ls=':',lw=.8);pen.set(xticks=[0,1],xticklabels=['No penalty','With penalty'],ylabel='$d_{min}^*$',xlim=(-.4,1.4))
    ev=e.npz('thesis',relative/'historical_replays/dense_duck_six_fixed/critical_event_snapshots.npz');e.path('thesis',relative/'historical_replays/dense_duck_six_fixed/critical_event.json')
    pair=ev['reference_pair'].astype(int)-1;assert list(pair)==[6,29]
    mid=ev['reference_positions'][1,pair].mean(0)
    for j,axis in enumerate(snap):
        pts=ev['reference_positions'][j]
        for k,point in enumerate(pts):
            if np.isfinite(point).all():axis.add_patch(Circle(point,.0125,fc=PC[list(pair).index(k)] if k in pair else '.85',ec='black' if k in pair else '.7',lw=.6))
        for k in pair:axis.annotate(str(k+1),pts[k],xytext=(3,4),textcoords='offset points',fontsize=7)
        axis.set(xlim=(mid[0]-.055,mid[0]+.055),ylim=(max(0,mid[1]-.055),min(.3,mid[1]+.055)),aspect='equal',xlabel='$x^*$',ylabel='$y^*$')
        title(axis,chr(99+j),f"t* = {ev['reference_times'][j]:.5f}")
    title(ax,'a','Samples; open circles: refined');title(pen,'b','Separate N=6 penalty test')
    e.checks['critical_pair']=dict(one_based=ev['reference_pair'].tolist(),times=ev['reference_times'].tolist())
    e.save(fig,'formation-clearance-penalty',['duck42','D1_93bf6b884031','G2'],'two traces/penalty panels plus three identical event windows','FORM F09 and previous F09_F11','Physical radius 0.0125; one-based pair [7,30]; shared lifetimes only')
    comp=e.js('thesis',relative/'reflection/comparison.json');source=relative/'cases'/comp['source_case']
    base=e.npz('thesis',source/'trajectories.npz');mirror=e.npz('thesis',relative/'reflection/trajectories.npz')
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,2.9))
    for axis,mode,key in zip(axs,['reference','pinn'],['paired_reference_symmetry','frozen_PINN_asymmetry']):
        expected=base[mode+'_endpoints'].copy();expected[:,1]=.3-expected[:,1]
        residual=np.linalg.norm(mirror[mode+'_endpoints']-expected,axis=1).max()
        np.testing.assert_allclose(residual,comp[key]['max_endpoint_reflection_residual'],atol=1e-18)
        axis.scatter(expected[:,1],mirror[mode+'_endpoints'][:,1],s=9,color=BLUE);axis.plot([0,.3],[0,.3],'k:',lw=.8)
        axis.set(xlabel='Reflected nominal $y^*$',ylabel='Mirrored replay $y^*$',aspect='equal',xlim=(0,.3),ylim=(0,.3),title=f'{mode}: max residual {residual:.5g}')
    fig.subplots_adjust(left=.1,right=.98,bottom=.23,top=.86,wspace=.45)
    e.checks['reflection']=comp
    e.save(fig,'formation-reflection',[comp['source_case']],'two identity comparisons','FORM F10')
    scenarios=e.js('thesis',relative/'robustness/scenarios_manifest.json');selection=e.js('thesis',relative/'robustness/selection.json')
    fig,axs=plt.subplots(2,1,figsize=(WIDTH,5.6));kinds=[('nominal',0)]+[(k,l) for k in ['position','axial_velocity','transverse_velocity','timing','joint','port_misplacement'] for l in [1,2]]
    for axis,label in zip(axs,['low_margin','high_margin']):
        for j,(kind,level) in enumerate(kinds):
            entry=next(v for v in scenarios if v['label']==label and v['scenario']==kind and v['level']==level)
            assert entry['status']=='completed' and entry['draws']==64
            m=e.js('thesis',relative/f'robustness/{label}_{kind}_level{level}/metrics.json')
            assert m['draws']==64 and m['threshold']==.004
            assert m['unconditional_pass_fraction']==m['accepted']/64
            axis.plot(j-.12,m['unconditional_pass_fraction'],'o',color=BLUE,ms=4)
            conditional=m['bounds_conditional_pass_fraction']
            if m['within_bounds']:
                np.testing.assert_allclose(conditional,m['accepted']/m['within_bounds'])
                axis.plot(j+.12,conditional,'s',mfc='none',mec=PINK,ms=4)
            else:
                assert conditional is None
                axis.text(j,.1,'undef.',rotation=90,ha='center',fontsize=6.5)
            axis.text(j,1.02,str(m['within_bounds']),ha='center',fontsize=7)
        axis.set(xticks=range(13),xticklabels=['nom.']+[f'{k}\n{l}' for k in ['pos.','axial','trans.','time','joint','port'] for l in [1,2]],ylim=(-.04,1.14),ylabel='Acceptance fraction',title=f"{label}: {entry['caseid']}; T*={m['fixed_nominal_target_time']:.6f}")
        axis.tick_params(axis='x',labelsize=7);axis.grid(axis='y',alpha=.2)
    axs[0].plot([],[],'o',color=BLUE,label='All 64 draws');axs[0].plot([],[],'s',mfc='none',mec=PINK,label='Conditional on valid bounds')
    fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,fontsize=8)
    fig.text(.5,.065,'Numbers above markers: valid draws / 64; nominal target time fixed; threshold = 0.004',ha='center',fontsize=7.5)
    fig.subplots_adjust(left=.1,right=.98,bottom=.17,top=.94,hspace=.55)
    e.save(fig,'formation-release-sensitivity',[v['caseid'] for v in selection] if isinstance(selection,list) else [selection['low_margin'],selection['high_margin']],'two representatives, 13 scenarios each','FORM F12')


def main():
    p=argparse.ArgumentParser();p.add_argument('--flow',type=Path,required=True);p.add_argument('--magnetic',type=Path,required=True);args=p.parse_args()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':8.5,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'lines.linewidth':1.2})
    e=Evidence({'flow':args.flow,'magnetic':args.magnetic,'thesis':THESIS})
    for source,rel,expected in [('flow',FWD/'all_new_figures.pdf','a7ba122928951bea0a623eb038c060a2480036186a7133fb23c3ed0f239120d1'),('flow',GEOM/'chain_revision_xt_yt/chains_only.pdf','915167c612328630f4b30f8e84e83926a9a57dc0b93a03b9ca130adb690e9389'),('magnetic',Path('results/trained_presentation/trained_cases_panels_1_to_5.pdf'),'cd212c80a77b78bf43945b47de471a84a7333db20c1780dd4f9874278d46b6c8')]:assert sha(e.path(source,rel))==expected
    rows=flow_forward(e);magnetic_forward(e)
    for name in ['corners_beta4','corners_beta5','oblique_beta5']:
        inverse_chain(e,name);inverse_chain(e,name,True)
    particle_count(e);magnetic_inverse(e);formation(e)
    manifest=dict(revisions=REVS,refitting=False,training=False,ode_solves=False,figures=e.figures,checks=e.checks)
    (HERE/'revision-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Wrote {len(e.figures)} figures; all saved-data checks passed.')


if __name__=='__main__': main()
