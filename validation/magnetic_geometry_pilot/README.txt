Master10 geometry-only inverse design pilot
Source https://github.com/mohrezsayeh90-ai/Master_Magnetic/tree/639906f53a11934b3058fbbdb246e34a1dd001fd
Place geometric_pilot.py and verify_geo.py in the root of that checkout.
Use the original results/operator/checkpoint.pt and install the repository dependencies.
Run python geometric_pilot.py CASE for each case, then python verify_geo.py.
Cases: constant_left, source_switch, alternating, short_pulse.
Each NPZ contains shared axial grid z (dimensionless Z=z/D), x_target/x_nn/x_replay
(dimensionless X=x/R), replay and predicted_path ([X,Z]), time in tau=t/TS,
piecewise-linear control knot times in tau and controls [a_L,a_R], tau_hit (target
first arrival), and B_T (two components in tesla along the independent replay).
Time/field arrays extend to the fitting safety horizon. Crop to tau_hit to show
only the designed traversal. The target clock and source commands are excluded
from the optimizer inputs. The JSON files capture numerical metrics and termination.

Thesis figures and numerical cross-check
From the thesis root, run:
    python validation/magnetic_geometry_pilot/render.py
The axes use the dimensionless X=x/R, Z=z/D and tau=t/TS.
The field panels use Bx/BS and Bz/BS along the independent replay.
The summary CSV converts X and tau to micrometres and seconds, respectively.
Plotting and the summary CSV use the four archived results. The plotting
script checks these arrays and metrics without running the optimizer.
Frozen checkpoint SHA-256:
080b7e5dd76c98a75fca7f92cc4ec314907a7f7340c809b739b1e2eabc0e3133
