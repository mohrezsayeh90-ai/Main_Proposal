import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
from magnetic_operator.inverse import Rollout, decode, feasible
from magnetic_operator.physics import AMAX, BS, D, R, TS, Parameters, numpy_field_force, numpy_rhs
from magnetic_operator.train import load

H = .0125
ROOT = Path(__file__).resolve().parent
CASES = [
    ("constant_left", [.05, -.65], .55, lambda t: (.46, 0.)),
    ("source_switch", [.12, -.60], .64, lambda t: (.24*(1-np.tanh((t-.59)/.16)), .24*(1+np.tanh((t-.59)/.16)))),
    ("alternating", [-.10, -.55], .65, lambda t: (.26+.18*np.sin(4*np.pi*t/1.2), .26-.18*np.sin(4*np.pi*t/1.2))),
    ("short_pulse", [.08, -.75], .60, lambda t: (.12+.46*np.exp(-((t-.49)/.065)**2), .20)),
]
# Keep total amplitude below the declared limit, including the short pulse.
CASES[-1] = ("short_pulse", [.08, -.75], .60,
             lambda t: (.12+.37*np.exp(-((t-.49)/.065)**2), .20))
PAR = Parameters()
TOL = .01  # in X, equivalent to .75 micrometres for this tube

def physical_path(law, q0, duration, z_end=None, step=.0025):
    def rhs(t, q):
        return numpy_rhs(q, law(t), PAR)
    def exit_event(t, q):
        return q[1] - z_end
    exit_event.terminal = True
    exit_event.direction = 1
    sol = solve_ivp(rhs, [0, duration], q0, method="DOP853", rtol=2e-10,
                    atol=2e-12, max_step=step, dense_output=True,
                    events=exit_event if z_end is not None else None)
    if not sol.success or (z_end is not None and len(sol.t_events[0]) != 1):
        raise RuntimeError("Independent solver failed to reach the target end.")
    times = np.linspace(0, sol.t[-1], 6001)
    return times, sol.sol(times).T

def make_target(q0, z_end, law):
    times, path = physical_path(law, q0, 3.2, z_end=z_end)
    if not feasible(path) or np.any(np.diff(path[:, 1]) <= 0):
        raise ValueError("Reference target must be admissible and axially monotone.")
    if max(np.abs(law(t)).sum() for t in times) > AMAX:
        raise ValueError("Reference command exceeded its amplitude limit.")
    z = np.linspace(q0[1], z_end, 401)
    return z, np.interp(z, path[:, 1], path[:, 0])

def fit_geometry(model, z, x, q0):
    # Derive a safety horizon from geometry and axial carrier speed, not from the source timing.
    estimate = (z[-1]-z[0])/(PAR.mean/.015*(1-np.max(np.abs(x))**2))
    intervals = int(np.ceil((estimate+.075)/.15))
    stop = round(intervals*.15, 10)
    times = np.linspace(0, stop, round(stop/H)*4+1)
    knots = np.linspace(0, stop, intervals+1)
    roll = Rollout(model, times, q0, PAR, knots, H)
    zg = torch.tensor(z[::4])
    xg = torch.tensor(x[::4])
    scale = .002

    def objective(y):
        yt = torch.tensor(y, dtype=torch.float64, requires_grad=True)
        a = decode(yt, "signed")
        pred, states = roll(a)
        px, pz = pred[:, 0].contiguous(), pred[:, 1].contiguous()
        right = torch.searchsorted(pz.detach(), zg, right=True).clamp(1, len(pz)-1)
        left = right-1
        alpha = ((zg-pz[left])/(pz[right]-pz[left]).clamp_min(1e-8)).clamp(0, 1)
        xc = px[left] + alpha*(px[right]-px[left])
        geom = ((xc-xg)/scale).square().mean()
        smooth = .02*(torch.diff(a,dim=0).square().sum())/.15
        lack = (torch.relu(zg[-1]+.002-pz[-1])/.002).square()*10
        monotone = 1e8*torch.relu(1e-7-torch.diff(pz)).square().sum()
        wall = 1e8*(torch.relu(states[:,0].abs()-.7).square().sum()
                    +torch.relu(-2-states[:,1]).square().sum()
                    +torch.relu(states[:,1]-1.7).square().sum())
        loss = geom + smooth + lack + monotone + wall
        grad = torch.autograd.grad(loss, yt)[0]
        return loss.item(), grad.numpy()

    rng = np.random.default_rng(932)
    starts = [np.tile([.31,.12], len(knots)),
              (np.tile([.31,-.12],len(knots))+rng.normal(0,.04,len(knots)*2))]
    trial = []
    for i, y in enumerate(starts):
        fit = minimize(objective, y, jac=True, method="L-BFGS-B",
                       bounds=[(-AMAX, AMAX)]*len(y),
                       options={"maxiter": 85, "ftol": 1e-12, "gtol": 1e-8})
        with torch.no_grad():
            controls = decode(torch.tensor(fit.x),"signed")
            pred,states = roll(controls)
        pred = pred.numpy()
        ok = feasible(states.numpy()) and np.all(np.diff(pred[:,1])>0) and pred[-1,1]>=z[-1]
        print("start",i,"iterations",fit.nit,"cost",fit.fun,"feasible",ok,flush=True)
        if ok:
            trial.append((fit.fun, controls.numpy(),pred,fit.nit,bool(fit.success),str(fit.message)))
    if not trial:
        raise RuntimeError("No fitted command reached the full target within the model constraints.")
    return knots,times,min(trial,key=lambda row:row[0])

def run(case, output):
    name,q0,zend,law = case
    z,x = make_target(q0,zend,law)
    net = load(ROOT/"results/operator")
    knots,times,(_,a,pred,nit,success,reason)=fit_geometry(net,z,x,q0)
    def command(t):
        return np.array([np.interp(t,knots,a[:,i]) for i in range(2)])
    tr,replay = physical_path(command,q0,knots[-1])
    if not feasible(replay) or not np.all(np.diff(replay[:,1])>0) or replay[-1,1]<zend:
        raise RuntimeError("Independent replay failed domain, traversal, or endpoint acceptance.")
    rr=np.interp(z,replay[:,1],replay[:,0])
    pp=np.interp(z,pred[:,1],pred[:,0])
    hit=float(np.interp(zend,replay[:,1],tr))
    pduration=float(np.interp(zend,pred[:,1],times))
    def errors(v):
        return {"rmse_X":float(np.sqrt(np.mean((v-x)**2))), "max_X":float(np.max(np.abs(v-x)))}
    field=np.array([BS*numpy_field_force(q,command(t))[0] for q,t in zip(replay,tr)])
    np.savez_compressed(output/(name+".npz"),z=z,x_target=x,x_nn=pp,x_replay=rr,
                        tau=tr,replay=replay,B_T=field,
                        controls=a,knots=knots, tau_hit=hit,
                        predicted_time=times, predicted_path=pred)
    report=dict(name=name, checkpoint_sha256=hashlib.sha256((ROOT/"results/operator/checkpoint.pt").read_bytes()).hexdigest(),
                model=errors(pp), replay=errors(rr), zero_field=errors(np.full_like(x,q0[0])),
                model_replay_rmse_X=float(np.sqrt(np.mean((pp-rr)**2))),
                time_s=hit*TS, model_time_s=pduration*TS, target_z_end=zend,
                transverse_span_X=float(np.ptp(x)),
                min_axial_velocity_replay=float(np.min(np.diff(replay[:,1])/np.diff(tr))),
                peak_total_amplitude=float(np.max(np.abs(a).sum(axis=1))),
                pilot_pass=bool(np.max(np.abs(rr-x))<=TOL),
                iterations=nit, optimizer_converged=success, termination=reason)
    (output/(name+".json")).write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("case",choices=[c[0] for c in CASES])
    parser.add_argument("--output",type=Path,default=ROOT/"out")
    args=parser.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    torch.set_num_threads(1)
    run(next(c for c in CASES if c[0]==args.case),args.output)
