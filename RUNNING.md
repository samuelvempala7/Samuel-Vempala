# Reproduce the analyses

The checked-in CSVs, figures, and Tableau PDF are readable on GitHub. To rerun the analyses locally, start at the repository root with Python 3.12 and the versions in `requirements.txt`.

```bash
python -m venv .venv
```

On Windows PowerShell activate with `.venv\Scripts\Activate.ps1`. On macOS or Linux use `source .venv/bin/activate`. Run the following commands in the activated environment.

```bash
python -m pip install -r requirements.txt
python data/fetch.py
```

The download script retrieves the CDNOW sample, South German Credit file, and BANKING77 train and test files. It verifies each file against a SHA-256 digest. Source descriptions and citations are in the individual case studies. The other four analyses carry their own inputs.

| Project | Command from the repository root | Output |
| --- | --- | --- |
| Repeat purchase | `python projects/repeat-purchase/analyze.py` | Two time-window backtests |
| Credit calibration | `python projects/credit-calibration/analyze.py` | Score table, five bands per model, calibration plot |
| Banking intents | `python projects/banking-intents/analyze.py` | Coverage, accuracy, and accepted misroutes |
| Fraud review | `python projects/fraud-review/analyze.py` | Capture rates across four queue capacities |
| Release latency | `python projects/release-latency/analyze.py` | Segment metrics and held-out test results |
| Payment reconciliation | `python projects/payment-reconciliation/replay.py` | Two reconciliations with replay checks |
| Supermarket sales | `python projects/supermarket-sales/check.py` | Cash totals and member mean comparison |

The supermarket PDF can be viewed directly. Open `dashboard.twbx` in Tableau Desktop or Tableau Public desktop authoring to explore the sheets. Numerical outputs use fixed seeds where randomness is involved. Tiny floating-point differences can occur across platforms.
