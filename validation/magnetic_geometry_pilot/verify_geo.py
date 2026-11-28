import json
import numpy as np
from pathlib import Path
from geometric_pilot import CASES, TS, AMAX, make_target, physical_path
for name,q0,zend,law in CASES:
    report=json.loads(Path(f'out/{name}.json').read_text())
    d=np.load(f'out/{name}.npz',allow_pickle=False)
    knots, controls=d['knots'], d['controls']
    def command(t):
        return np.array([np.interp(t,knots,controls[:,i]) for i in range(2)])
    t,q=physical_path(command,q0,knots[-1],step=.00125)
    replay=np.interp(d['z'],q[:,1],q[:,0])
    assert d['z'][-1]==zend
    assert np.all(np.diff(q[:,1])>0) and q[-1,1]>=zend
    assert np.max(np.abs(controls).sum(axis=1))<=AMAX+1e-12
    assert np.max(np.abs(replay-d['x_replay']))*75<1e-4
    print(name, 'step check µm',np.max(np.abs(replay-d['x_replay']))*75,
          'RMSE NN / replay / off µm',*[round(75*report[k]['rmse_X'],7) for k in ('model','replay','zero_field')],
          'Max replay µm',75*report['replay']['max_X'],'time_s',report['time_s'],
          'excursion µm',75*report['transverse_span_X'],'peak',report['peak_total_amplitude'],
          'status',report['termination'])
