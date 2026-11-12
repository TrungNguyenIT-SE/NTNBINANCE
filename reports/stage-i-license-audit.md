# Stage I Python dependency and license audit

> Audit date: `13/11/2026` (Asia/Saigon)
>
> Scope: packages added for reproducible tabular baselines
>
> Result: **PASS for local Stage I use; retain bundled notices at release packaging**

## Locked packages

| Package | Version | Role | Installed artifact license identity |
|---|---:|---|---|
| scikit-learn | 1.9.1 | scaler, Logistic Regression, metrics | BSD-3-Clause; `COPYING` present |
| xgboost-cpu | 3.4.1 | CPU-only boosted-tree baseline | Apache-2.0; `LICENSE` present |
| NumPy | 2.5.4 | arrays/numeric runtime | BSD-3-Clause plus bundled permissive notices |
| SciPy | 1.18.1 | scikit-learn numeric runtime | BSD-3-Clause plus bundled component notices |
| joblib | 1.6.0 | scikit-learn runtime | BSD-3-Clause; license file present |
| cloudpickle | 3.1.2 | joblib runtime | BSD-3-Clause; license file present |
| narwhals | 2.28.0 | scikit-learn runtime | MIT; license file present |
| threadpoolctl | 3.8.0 | local native thread control | BSD-3-Clause; license file present |

Versions come from `requirements.lock`; identities and license-file presence were read from the
installed wheels in the project-local Python 3.14.2 environment. SciPy/NumPy wheels contain detailed
third-party notices (including native numeric libraries); those notices must be carried into any
future bundled distribution and re-audited at Stage Z. No model weight or paid dataset was added.

## Compatibility and cost

- Official CPython 3.14 Windows wheels installed successfully; no source compilation occurred.
- XGBoost uses the smaller `xgboost-cpu` distribution, `n_jobs=1`; CUDA is not required.
- `pip check` reports no broken requirements.
- Training and inference run on the existing local computer with no hosted service, API key,
  subscription, cloud GPU or new payment. New cash cost remains **0 VNĐ**.

This is a project dependency record, not legal advice.
