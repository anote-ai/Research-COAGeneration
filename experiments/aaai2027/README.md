# AAAI 2027 Experiments

- `run_executable.py`: generate splits, fit and calibrate the raw-text router,
  run eight held-out policies, and export task-level traces and paired tests.
- `run_ablations.py`: evaluate character features, calibration, composition,
  and budget enforcement.
- `plot_executable.py`: generate the paper tradeoff figure from exported CSVs.
- `run_sensitivity.py`: evaluate training-set size and route-threshold sensitivity
  on standard and locked challenge splits.
- `prepare_submission.py`: compile with PDFLaTeX, clear PDF metadata, scan for
  identity strings, verify page size/count and font embedding, and write the
  two OpenReview PDFs.

Run from the repository root after `pip install -e ".[dev]"`. These experiments
use machine-checked executable outcomes. The earlier DAI seeded simulator is not
used as AAAI evidence.
