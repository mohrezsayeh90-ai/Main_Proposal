# Particle trajectory validation report

The Persian report compares two case studies against the published numerical
references. The directory structure is preserved for Overleaf. Use XeLaTeX
with fontspec, Babel, bidi and Noto Naskh Arabic installed.

## Provenance

- Magnetic cases: a new CPU execution of the Master6 PINN code from
  [commit e216545](https://github.com/mohrezsayeh90-ai/Particle_Shape_Reconstruction/blob/e216545/evidence/master6-validation-2d-magnetic-pinn/master6-validation-2d-magnetic-pinn.ipynb).
  The code and training metadata are included. The re-execution used PyTorch
  2.7.1+cpu. The CSVs and metrics are from that run and differ slightly from
  the old saved notebook outputs. The reference curves are evaluated from
  Eq. (59) of Furlani and Ng (2006), DOI 10.1103/PhysRevE.73.061919.
- Wavy cases: saved numerical reproduction of Mao et al. (2023), DOI
  10.1017/jfm.2023.558. Figure 6 supplies the lift law. Figure 9(a-2)
  supplies the comparison data. The script used to extract these graphs from
  the official PDF and solve the residual equations is included. See
  data/wavy/reproduction_notes.md for the PDF link and source hash.

## Rebuild the report from saved data

    python -m pip install numpy scipy matplotlib
    python make_figures.py --magnetic data/magnetic --wavy data/wavy
    xelatex particle_benchmark_report.tex

For a new magnetic training run, install CPU PyTorch and run
rerun_magnetic.py. The script writes magnetic_run/. To recompute the wavy
study install PyMuPDF and run data/wavy/reproduce_fig9.py with the original
Cambridge PDF and a fresh output directory. The published references are
numerical, with the magnetic reference given analytically. The figures
report measured discrepancies from the simulated values and do not use a
fit of the plotted paths to the published trajectories.

## Presentation revision

The revised report adds cross-paper validation notes, labels the comparable
panels, and separates the capture-location error and downstream focusing
range into their own figures. Each capture error is verified against the
recorded absolute error, and all displayed metric definitions and original
reference data are retained.
