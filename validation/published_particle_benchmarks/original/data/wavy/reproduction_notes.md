# Wavy-channel particle focusing
Reproduction of Figure 9(a-2) from Mao, Bischofberger & Hosoi (2023), DOI 10.1017/jfm.2023.558.

## Run
Download the official 42-page Cambridge PDF from
https://www.cambridge.org/core/services/aop-cambridge-core/content/view/785A73857C4EF4216EB2DCC2DDE3317A/S002211202300558Xa.pdf/particle-focusing-in-a-wavy-channel.pdf

SHA-256 of the PDF used: cc59e402669072496e4dc850b80c603d38f58ae7f0c575bffc59fd31f74dc208.

```sh
python -m pip install numpy scipy matplotlib pymupdf
OPENBLAS_NUM_THREADS=1 python reproduce_fig9.py particle-focusing-in-a-wavy-channel.pdf run
```

## Method
The carrier is the first-order Fourier perturbation to planar Poiseuille flow from Eq. 2.5. The vector path for the zeroth-order inertial lift at Rc=10 is extracted from Fig. 6 and interpolated by PCHIP. That force is an input and is not independently predicted. Eq. 5.4 is expressed in half-channel-width coordinates, so the relaxation coefficient is twice its value in full-width coordinates. Initial position is (X,Z)=(0,0.1), with initial particle velocity set equal to the local carrier velocity. The case uses Rc=10, omega=2 and epsilon=0.2.

The particle solver advances in axial position and uses windowed single-hidden-layer tanh networks. It determines the linear readout weights by collocating the equation residual, with each window's initial state built into the trial function. Figure 9 is used only after solving. LSODA provides an independent integration of the same equation. Both the neural resolution and the carrier mesh are refined. Fine neural runs use 1600 windows with 22 collocation points per window. Coarser runs use 1000 windows with 20 points.

## Output
The run folder includes PNG and vector PDF overlays, CSVs with trajectories, the lift input, the two envelope comparisons and JSON metrics. Wavy-case RMSE pools errors in both envelope bounds. Curves are reduced to one-period extrema. The published strokes have finite thickness, which is approximately corrected by subtracting half their vertical line thickness from the bounds. Three periods crossing a join in the PDF paths per wavy case are interpolated for display and excluded from metrics. The wavy error range excludes the outer 20 units of X, and the straight comparison excludes the outer 10. All reported coordinate errors are dimensionless in units of the mean half-width.

The results benchmark particle tracking against published numerical trajectories. There is no test here against laboratory data, and this does not verify the separate multi-particle release planner.
