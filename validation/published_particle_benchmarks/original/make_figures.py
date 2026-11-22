"""Render vector figures and derive report metrics from the two benchmark runs."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from scipy.optimize import brentq

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#a6b5c1", "axes.labelcolor": "#182e3e",
    "xtick.color": "#263e4f", "ytick.color": "#263e4f",
    "text.color": "#182e3e", "axes.grid": True, "grid.color": "#e2e9ee",
    "grid.linewidth": .55, "axes.axisbelow": True, "pdf.fonttype": 42,
    "legend.frameon": False, "figure.dpi": 120,
})
INK = "#193b50"
TEAL = "#00746b"
REF = "#596e80"
ACCENT = "#bf5936"
COLORS = ["#1b5684", "#148579", "#8463a2", "#ad542a", "#35434b"]
MARKERS = ["o", "s", "^", "D", "v"]
BASE = Path(__file__).resolve().parent


def save(fig, name):
    for suffix in ("pdf", "png"):
        path = BASE / "assets" / f"{name}.{suffix}"
        fig.savefig(path, dpi=235, facecolor="white", metadata={"Creator": "Matplotlib"})
    plt.close(fig)


def double_arrow(ax, start, end, label, text_at):
    ax.annotate("", end, start, arrowprops={"arrowstyle": "<->", "color": INK, "lw": .85})
    ax.text(*text_at, label, ha="center", va="center", color=INK)


def geometry():
    fig, ax = plt.subplots(figsize=(7.5, 2.05), layout="constrained")
    ax.set(xlim=(-.35, 10.45), ylim=(-1.93, 1.09))
    ax.axis("off")
    ax.add_patch(Rectangle((0, -.48), 10, .96, color="#e4f1f5", zorder=0))
    ax.hlines([-.48,.48], 0, 10, color=INK, lw=1.3)
    ax.hlines(0, 0, 10, linestyle="--", color="#8ca7ba", lw=.8)
    ax.add_patch(Circle((5.72, -1.36), .47, fc="#f0c2b2", ec=ACCENT, lw=1.25))
    ax.plot(5.72, -1.36, ".", c=ACCENT)
    ax.annotate("", (2.25, .0), (.48, .0), arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 1.7})
    ax.text(1.35,.22,"Poiseuille flow",ha="center",c=TEAL)
    ax.plot(2.7, 0, "o", c=TEAL, ms=5)
    ax.text(2.7,.68,"release",ha="center")
    ax.annotate("", (6.55,-.38), (5.05,-.05),
                arrowprops={"arrowstyle":"->","color":TEAL,"lw":1.6,
                            "connectionstyle":"arc3,rad=.16"})
    double_arrow(ax,(7.15,0),(7.15,-1.36),r"$d$",(7.4,-.68))
    double_arrow(ax,(9.15,0),(9.15,.48),r"$R_v$",(9.49,.23))
    ax.annotate(r"$R_{\mathrm{mag}}$", (6,-1.15),(6.5,-1.59),
                arrowprops={"arrowstyle":"-","color":ACCENT}, c=ACCENT)
    ax.text(4.86,-1.39,"Cylinder axis normal to view",ha="right",c=ACCENT,size=8.5)
    ax.annotate(r"$z$", (9.9,.78),(8.9,.78), arrowprops={"arrowstyle":"->","color":INK})
    ax.annotate(r"$x$", (8.55,1.02),(8.55,.67), arrowprops={"arrowstyle":"->","color":INK})
    ax.text(0,-1.76,"Schematic · not to scale",fontsize=8,c=REF)
    save(fig, "magnetic_geometry")

    fig, ax = plt.subplots(figsize=(7.5, 2.05), layout="constrained")
    xx = np.linspace(0, 3*np.pi, 701)
    walls = 1-.1*np.cos(2*xx)
    ax.fill_between(xx,-walls,walls,color="#e4f1f5")
    ax.plot(xx,walls,c=INK,lw=1.45)
    ax.plot(xx,-walls,c=INK,lw=1.45)
    ax.axhline(0,c="#8ca7ba",ls="--",lw=.82)
    ax.axhline(1,c="#aec1cf",ls=":",lw=.8)
    ax.axhline(-1,c="#aec1cf",ls=":",lw=.8)
    ax.plot(0,.1,"o",c=TEAL,clip_on=False,ms=5)
    ax.annotate(r"release $(0,0.1)$",(0,.1),(0.72,.4),
                arrowprops={"arrowstyle":"-","color":TEAL},c=TEAL)
    ax.annotate("",(4.8,.25),(2.65,.25),arrowprops={"arrowstyle":"->","color":TEAL,"lw":1.45})
    ax.text(3.7,.42,"Pressure-driven flow",ha="center",c=TEAL)
    double_arrow(ax,(.07,1.28),(np.pi+.07,1.28),r"$\lambda/h=2\pi/\omega$", (1.65,1.49))
    double_arrow(ax,(7.85,0),(7.85,1),r"$h$", (8.08,.50))
    ax.text(9.35,1.27,r"$Z=\pm[1-\epsilon_w\cos(\omega X)]$",ha="right")
    ax.text(0,-1.31,r"Geometry shown for $\epsilon_w=0.10$",fontsize=8,c=REF)
    ax.set(xlim=(-.18,9.6),ylim=(-1.48,1.62))
    ax.axis("off")
    save(fig, "wavy_geometry")


def lift_integral(z):
    return 3*np.arctan(z)/8 + z*(3*z*z+5)/(8*(1+z*z)**2)


def magnetic(folder):
    report = json.loads((folder/"validation.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.15), layout="constrained", sharey=True)
    ef, errors = plt.subplots(1, 2, figsize=(7.5, 2.85), layout="constrained", sharey=True)
    capture = []
    eta = 0.003276913272013514
    for i, row in enumerate(report["results"]):
        beta, radius = row["beta"], row["radius_nm"]
        color = COLORS[i%5]
        ax, ea = axes[i//5], errors[i//5]
        case = np.loadtxt(folder/f"case_{i:02d}.csv", delimiter=",", skiprows=1)
        cmp = np.loadtxt(folder/f"comparison_{i:02d}.csv", delimiter=",", skiprows=1)
        constant = (4*np.pi*1e-7)*(radius*1e-9)**2*3e12/(18*eta*75e-6*.015*(1+beta)**4)
        z0 = -4/(1+beta)
        def relation(z):
            return -constant*(lift_integral(z)-lift_integral(z0))
        z1 = 4/(1+beta)
        if row["reference_captured"]:
            z1 = brentq(lambda z: relation(z)+2/3,z0,z1)
            capture_error = (case[-1, 2]-z1)*(1+beta)*20000
            np.testing.assert_allclose(abs(capture_error), 20000*row["capture_location_error_Rmag"],
                                       atol=1e-7, rtol=1e-7)
            capture.append((beta, radius, capture_error))
        zref = np.linspace(z0,z1,900)
        href = np.clip(relation(zref),-2/3,0)
        xref = 2*np.sin(np.arcsin(1.5*href)/3)
        np.testing.assert_allclose(cmp[:,2],2*np.sin(np.arcsin(1.5*relation(cmp[:,0]/(1+beta)))/3),
                                   atol=1e-10,rtol=1e-10)
        ax.plot(zref*(1+beta),-xref,c="black",ls=(0,(4,2.6)),lw=1.15,zorder=2)
        ids = np.unique(np.r_[np.linspace(0,len(case)-1,19,dtype=int),len(case)-1])
        ax.plot(case[ids,2]*(1+beta),-case[ids,1],ls="",marker=MARKERS[i%5],mec=color,
                mfc="white",ms=3.45,mew=.98,zorder=3)
        ea.semilogy(cmp[:,0],np.maximum(cmp[:,3],1e-8),c=color,lw=.85,
                    marker=MARKERS[i%5],markevery=(i%5*15,170),ms=2.6,mfc="white")
        np.testing.assert_allclose([np.max(cmp[:,3]),np.sqrt(np.mean(cmp[:,3]**2))],
                                   [row["max_error_Rv"],row["rms_error_Rv"]])
    for index, (ax, ea, beta) in enumerate(zip(axes,errors,[1,1.25])):
        label = f"({chr(97+index)})"
        ax.set(xlim=(-4.1,4.1),ylim=(-.015,1.04),xticks=[-4,-2,0,2,4],
               xlabel=r"$z/R_{\rm mag}$")
        ax.set_title(label,loc="left",fontweight="bold")
        ax.set_title(rf"$\beta={beta:g}$",loc="center")
        ax.axhline(1,color="#9aabb7",lw=.6,ls=":")
        ea.set(xlim=(-4.1,4.1),ylim=(1e-8,1e-2),xticks=[-4,-2,0,2,4],
               xlabel=r"$z/R_{\rm mag}$")
        ea.set_title(label,loc="left",fontweight="bold")
        ea.set_title(rf"$\beta={beta:g}$",loc="center")
        ea.axhline(.005,color=REF,ls="--",lw=.7)
    axes[0].set_ylabel(r"$|x|/R_v$")
    errors[0].set_ylabel(r"$|X_{\rm PINN}-X_{\rm ref}|$")
    handles = [Line2D([],[],color=c,marker=m,mfc="white",markersize=3,label=f"{r} nm")
               for c,m,r in zip(COLORS,MARKERS,range(400,601,50))]
    radius_handles = [Line2D([],[],color=c,marker=m,mfc="white",ls="",markersize=4,
                              label=f"{r} nm")
                      for c,m,r in zip(COLORS,MARKERS,range(400,601,50))]
    fig.legend(handles=radius_handles+[Line2D([],[],c="black",ls=(0,(4,2.6)),label="Eq. (59)")],
               title="Colored markers: PINN",loc="outside lower center",ncol=6,
               fontsize=8,title_fontsize=8,labelspacing=.35)
    ef.legend(handles=handles+[Line2D([],[],c=REF,ls="--",label="Archive tolerance")],
              loc="outside lower center",ncol=6,fontsize=8)
    save(fig, "magnetic_comparison")
    save(ef, "magnetic_error")
    capture_plot(capture)
    return report


def capture_plot(capture):
    fig, ax = plt.subplots(figsize=(7.5, 1.8), layout="constrained")
    for beta, marker, color in ((1., "o", TEAL), (1.25, "D", ACCENT)):
        values = [(radius, error) for b,radius,error in capture if b == beta]
        radius, error = np.array(values).T
        ax.scatter(radius, error, marker=marker, s=28, color=color,
                   label=rf"$\beta={beta:g}$", zorder=3)
    ax.axhline(0,color=REF,lw=.8,ls="--")
    ax.set(xlim=(380,620),ylim=(-1.15,1.15),xticks=[400,450,500,550,600],
           yticks=[-1,-.5,0,.5,1],xlabel=r"Particle radius $R_p$ (nm)",
           ylabel=r"$\Delta z_{\rm cap}$ ($\mu$m)")
    ax.legend(loc="upper left",ncol=2,fontsize=8)
    save(fig,"magnetic_capture")


def wavy(folder):
    report = json.loads((folder/"metrics.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.7), layout="constrained", sharey=True)
    ef, errors = plt.subplots(1, 3, figsize=(7.5, 2.45), layout="constrained", sharey=True)
    for i, (ax, ea, amp, row) in enumerate(zip(axes,errors,(0.,.05,.1),report["cases"])):
        ax.set(xlabel=r"$X_p$",xlim=(0,2000),
               xticks=[0,500,1000,1500,2000],ylim=(.08,.70))
        ea.set(xlabel=r"$X_p$",xlim=(0,2000),
               xticks=[0,500,1000,1500,2000],ylim=(-.004,.020))
        for axis in (ax, ea):
            axis.set_title(f"({chr(97+i)})",loc="left",fontweight="bold")
            axis.set_title(rf"$\epsilon_w={amp:g}$",loc="center")
        ea.axhline(0,c=REF,lw=.75,ls=":")
        if amp == 0:
            x,z,ode,ref = np.loadtxt(folder/"trajectory_0.csv",delimiter=",",skiprows=1,unpack=True)
            ax.plot(x,ref,c=REF,lw=1.4,ls="--")
            ax.plot(x,z,c=TEAL,lw=.95)
            mask = (x >= 10)&(x <= 1990)
            delta = z[mask]-ref[mask]
            np.testing.assert_allclose(np.sqrt(np.mean(delta**2)),row["figure_rmse"])
            ea.plot(x[mask],delta,c=TEAL,lw=1.1)
        else:
            x,lo,hi,nlo,nhi,mask = np.loadtxt(folder/f"envelope_{amp:g}.csv",delimiter=",",skiprows=1,unpack=True)
            ax.fill_between(x,lo,hi,color="#c4d3df",alpha=.7)
            ax.plot(x,lo,c=REF,lw=.65,ls="--")
            ax.plot(x,hi,c=REF,lw=.65,ls="--")
            ax.plot(x,nlo,c=TEAL,lw=1.)
            ax.plot(x,nhi,c=TEAL,lw=1.)
            low, high = nlo-lo, nhi-hi
            active = mask.astype(bool)
            np.testing.assert_allclose(np.sqrt(np.mean(np.r_[low[active],high[active]]**2)),
                                       row["figure_envelope_rmse"])
            ea.plot(x,np.where(active,low,np.nan),c=TEAL,lw=.9)
            ea.plot(x,np.where(active,high,np.nan),c=ACCENT,lw=.9,ls="--")
    axes[0].set_ylabel(r"$Z_p$")
    errors[0].set_ylabel(r"Signed $Z_p$ error")
    fig.legend(handles=[Line2D([],[],c=TEAL,label="PINN trajectory / envelope"),
                        Line2D([],[],c=REF,ls="--",label="Mao et al., Fig. 9(a-2)")],
               loc="outside lower center",ncol=2,fontsize=8)
    ef.legend(handles=[Line2D([],[],c=TEAL,label="Straight trajectory / lower bound"),
                       Line2D([],[],c=ACCENT,ls="--",label="Upper bound")],
              loc="outside lower center",ncol=2,fontsize=8)
    save(fig, "wavy_comparison")
    save(ef, "wavy_error")
    focusing_plot(report["cases"])
    return report


def focusing_plot(cases):
    fig, ax = plt.subplots(figsize=(7.5, 1.86),layout="constrained")
    for index, case in enumerate(cases):
        for key, color, marker, offset, label in (
            ("published_plateau", REF, "o", .125, "Published"),
            ("neural_plateau", TEAL, "D", -.125, "PINN"),
        ):
            values = np.atleast_1d(case[key])
            yy = index+offset
            ax.hlines(yy, values[0], values[-1], color=color,linewidth=1.6)
            ax.plot(values, np.full(len(values),yy),ls="",marker=marker,ms=3.6,
                    color=color,mfc="white",label=label if index==0 else None)
    ax.set(xlim=(.565,.680),ylim=(2.36,-.43),yticks=range(3),
           yticklabels=["0","0.05","0.10"],xlabel=r"Final transverse position $Z_p$",
           ylabel=r"$\epsilon_w$")
    ax.legend(loc="upper left",fontsize=8)
    save(fig,"wavy_focusing")


def table_rows(mag, wave):
    rows = []
    for row in mag["results"]:
        max_error = 75*row["max_error_Rv"]
        rmse = 75*row["rms_error_Rv"]
        event = "Capture" if row["pinn_captured"] else "Pass"
        capture_error = row["capture_location_error_Rmag"]
        location = f"{2e4*capture_error:.3f}" if capture_error is not None else "--"
        values = (f'{row["beta"]:g}', f'{row["radius_nm"]:.0f}', f"{rmse:.5f}", f"{max_error:.5f}", event, location)
        rows.append(r"\MagRow"+ "".join("{"+v+"}" for v in values))
    (BASE/"data"/"magnetic_rows.tex").write_text("\n".join(rows)+"\n")
    rows = []
    for row in wave["cases"]:
        def plateau(p):
            return f"{p:.4f}" if isinstance(p,float) else f"{p[0]:.4f}--{p[1]:.4f}"
        maximum = row.get("figure_max_abs_error",row.get("figure_envelope_max_abs_error"))
        rmse = row.get("figure_rmse",row.get("figure_envelope_rmse"))
        values = (f'{row["waviness"]:g}', plateau(row["published_plateau"]), plateau(row["neural_plateau"]), f"{rmse:.5f}", f"{maximum:.5f}")
        rows.append(r"\WaveRow"+ "".join("{"+v+"}" for v in values))
    (BASE/"data"/"wavy_rows.tex").write_text("\n".join(rows)+"\n")
    peak = max(r["max_error_Rv"] for r in mag["results"])
    cap = max(r["capture_location_error_Rmag"] or 0 for r in mag["results"])
    defs = {"MagMax":f"{75*peak:.4f}","MagPct":f"{100*peak:.3f}",
            "MagCaptureMax":f"{20000*cap:.3f}",
            "MagCaptureCount":str(sum(r["pinn_captured"] for r in mag["results"])),
            "WavyODEMax":f'{max(r["max_pinn_vs_ode"] for r in wave["cases"]):.2e}'}
    (BASE/"data"/"stats.tex").write_text("\n".join("\\newcommand{\\"+k+"}{"+v+"}" for k,v in defs.items())+"\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--magnetic",type=Path)
    cli.add_argument("--wavy",type=Path,required=True)
    args = cli.parse_args()
    geometry()
    wav = wavy(args.wavy)
    if args.magnetic:
        mag = magnetic(args.magnetic)
        table_rows(mag,wav)
