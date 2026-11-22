"""Plot only saved Master10 inverse experiments; no model/solver imports."""
import argparse,json,hashlib,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def read(root,case,name):return np.genfromtxt(root/case/(name+'.csv'),delimiter=',',names=True)
def save(fig,dest,name):
 fig.savefig(dest/(name+'.pdf'),metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
def main():
 p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);a=p.parse_args();root=a.results;dest=Path(__file__).parent
 plt.rcParams.update({'font.size':8,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'pdf.fonttype':42,'font.family':'DejaVu Sans'})
 fig,axes=plt.subplots(2,2,figsize=(6.27,3.65))
 for row,case in enumerate(['A_single','B_signed']):
  d=read(root,case,'controls');k=read(root,case,'knots');r=json.loads((root/case/'report.json').read_text())
  for col,c in enumerate(['L','R']):
   ax=axes[row,col];ax.plot(d['tau'],d[f'a_{c}_ref'],color='.15',ls='--',label='Reference')
   ax.plot(d['tau'],d[f'a_{c}_fit_aligned'],color='#9b3069',lw=1,label='Estimate (joint sign aligned)')
   ax.plot(k['tau'],r['sign']*k[f'a_{c}_raw'],'.',color='#9b3069',ms=3)
   ax.set(xlabel=r'$\tau$',ylabel=f'$a_{c}$',title=f'({chr(97+row*2+col)}) {case}');ax.grid(alpha=.2)
 fig.legend(*axes[0,0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
 fig.subplots_adjust(left=.09,right=.98,bottom=.19,top=.92,hspace=.65,wspace=.3);save(fig,dest,'inverse-master10-controls')
 fig,axes=plt.subplots(2,3,figsize=(6.27,3.95))
 for row,case in enumerate(['A_single','B_signed']):
  d=read(root,case,'replay');obs=read(root,case,'observations');spatial=axes[row,0]
  spatial.plot(d['Z_ref'],d['X_ref'],'k--',lw=1,label='Reference')
  spatial.plot(d['Z_fit'],d['X_fit'],color='#9b3069',lw=1,label='Master10')
  spatial.plot(d['Z_replay'],d['X_replay'],color='#24588b',lw=1,label='DOP853')
  spatial.plot(obs['Z_obs'][::8],obs['X_obs'][::8],'o',mfc='none',mec='.3',ms=3,label='Observed')
  spatial.set(xlabel=r'$Z=z/D$',ylabel=r'$X=x/R$')
  for col,c in enumerate(['X','Z'],1):
   ax=axes[row,col]
   for key,color,style in [('fit','#9b3069','--'),('replay','#24588b','-')]:
    ax.plot(d['tau'],1e5*np.abs(d[f'{c}_{key}']-d[f'{c}_ref']),color=color,ls=style,lw=1)
   ax.set(xlabel=r'$\tau$',ylabel=rf'$10^5 |\Delta {c}|$',ylim=(0,None))
  for col,ax in enumerate(axes[row]):ax.set_title(f'({chr(97+row*3+col)})'+(' '+case if col==0 else ''),loc='left',fontsize=8);ax.grid(alpha=.2)
 fig.legend(*spatial.get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,.04),fontsize=7.5)
 fig.text(.5,.012,'Trajectory zooms: independent X and Z reference lengths',ha='center',fontsize=7.5)
 fig.subplots_adjust(left=.10,right=.98,bottom=.23,top=.92,hspace=.65,wspace=.65);save(fig,dest,'inverse-master10-replay')
 d=read(root,'E_gap_sign','controls');q=read(root,'E_gap_sign','replay');fig,axes=plt.subplots(2,2,figsize=(6.27,3.55))
 for col,c in enumerate(['L','R']):
  ax=axes[0,col];ax.plot(d['tau'],d[f'a_{c}_1'],'k--',label='Pair 1');ax.plot(d['tau'],d[f'a_{c}_2'],color='#9b3069',lw=1,label='Pair 2');ax.set(xlabel=r'$\tau$',ylabel=f'$a_{c}$')
 axes[1,0].plot(q['Z_1'],q['X_1'],'k--');axes[1,0].plot(q['Z_2'],q['X_2'],color='#9b3069',lw=1)
 axes[1,0].set(xlabel=r'$Z=z/D$ (zoom)',ylabel=r'$X=x/R$')
 for c,color in [('X','#24588b'),('Z','#bc4a24')]:axes[1,1].plot(q['tau'],np.abs(q[f'{c}_1']-q[f'{c}_2']),color=color,label=c)
 report=json.loads((root/'E_gap_sign/report.json').read_text())
 upper=max(3*max(report['reference_refinement']['maximum']),1e-13)
 axes[1,1].set(xlabel=r'$\tau$',ylabel='Absolute replay difference',ylim=(0,upper));axes[1,1].legend(frameon=False)
 for i,ax in enumerate(axes.flat):ax.set_title(f'({chr(97+i)})',loc='left',fontsize=8);ax.grid(alpha=.2)
 fig.legend(*axes[0,0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
 fig.subplots_adjust(left=.10,right=.98,bottom=.18,top=.93,hspace=.6,wspace=.35);save(fig,dest,'inverse-master10-ambiguity')
 files=['summary.json','predeclared_config.json']+[f'{c}/{n}' for c in ['A_single','B_signed','E_gap_sign'] for n in ['report.json','controls.csv','replay.csv']]
 manifest={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}
 metadata=dict(research_commit=subprocess.check_output(['git','-C',str(root.parents[1]),'rev-parse','HEAD'],text=True).strip(),
  checkpoint_sha256=json.loads((root/'predeclared_config.json').read_text())['checkpoint_sha256'],inputs=manifest,
  outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.glob('inverse-master10-*.pdf')})
 (dest/'master10-inverse-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
if __name__=='__main__':main()
