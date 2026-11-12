# Dataset split and final-holdout policy v1

> Split version: `1.0.0`
>
> Engine version: `1.0.0`
>
> Status: locked
>
> Final holdout: `SEALED`

## 1. Objective

Stage H creates chronological membership for model development without random row splitting, overlapping target windows across boundaries or accidental use of the final test set. The split is based on Stage G origin samples before any image rendering, augmentation, resampling or class balancing.

The policy follows the purging and embargo principles documented in Chapter 7 of Marcos López de Prado's *Advances in Financial Machine Learning*. Wiley's official table of contents identifies the relevant sections as “Purging the Training Set” and “Embargo.” See the [publisher page](https://www.wiley.com/en-ca/advances-in-financial-machine-learning-p-9781119482086).

## 2. Unit of assignment

The atomic unit is an `origin_sample_id`, defined from:

```text
SHA256(label_run_id || symbol || decision_time_ms || label_config_hash)
```

Every BTCUSDT and ETHUSDT sample sharing one decision timestamp is assigned to the same partition. This prevents cross-symbol contemporaneous information from entering different sides of a boundary.

Each label interval is half-open:

```text
[decision_time, vertical_barrier_time)
```

Two samples overlap when each starts before the other ends. Feature lookback may reuse past observations; leakage control is based on concurrent label/outcome windows, while all features must still obey point-in-time availability.

## 3. Locked primary split

The source run has 77 decision timestamps and 154 samples. The primary chronological assignment is:

| Partition | UTC decision-time range | Timestamps | Samples | Use |
|---|---|---:|---:|---|
| TRAIN | 09/11 21:45 → 10/11 08:45 | 45 | 90 | fit scaler, selector and model |
| PURGED_TRAIN_VALIDATION | 10/11 09:00 → 09:30 | 3 | 6 | never fit or score |
| VALIDATION | 10/11 09:45 → 12:45 | 13 | 26 | model/threshold selection; calibrator inputs must be out-of-sample predictions |
| EMBARGO_VALIDATION_TEST | 10/11 13:00 → 13:30 | 3 | 6 | never fit or score |
| FINAL_HOLDOUT | 10/11 13:45 → 16:45 | 13 | 26 | sealed until Stage W authorization |

All times are UTC. The gap between the final assigned decision in one usable partition and the first decision in the next usable partition is exactly 60 minutes, equal to the primary prediction horizon. Consequently, the prior half-open label window ends exactly when the next partition begins and never overlaps it.

The 17% validation and 17% final-holdout fractions are applied to unique timestamps, not individual symbol rows.

## 4. Expanding purged walk-forward folds

Only development data before the final-holdout embargo is used:

| Fold | Train samples | Purged samples | Validation samples |
|---|---:|---:|---:|
| 1 | 38 | 6 | 26 |
| 2 | 64 | 6 | 26 |
| 3 | 90 | 6 | 26 |

Training expands chronologically. Validation always follows training, and each fold has a 60-minute decision-time separation created by three unassigned 15m timestamps. Fold 3 is the primary train/validation membership shown above.

No fold shuffles rows, trains on the future or accesses final-holdout labels.

## 5. Fit and selection scopes

| Operation | Allowed data |
|---|---|
| scaler/normalizer fit | current fold TRAIN only |
| feature selector fit | current fold TRAIN only |
| model fit | current fold TRAIN only |
| hyperparameter/model/threshold choice | compare current fold VALIDATION results only |
| calibrator fit | VALIDATION predictions produced by a model not fitted on those samples; alternatively TRAIN out-of-fold predictions |
| final metric | FINAL_HOLDOUT only after one-time unlock |

Test data may never fit a scaler, selector, imputer, feature threshold, model, calibrator, abstention threshold or risk policy. The executable `assert_fit_partition` guard fails closed for invalid fit scopes.

## 6. Augmentation and derived views

Split occurs before chart rendering, image augmentation, oversampling or synthetic theme generation. Every derivative must carry `origin_sample_id` and inherit its locked partition. A derivative without a known origin ID is rejected. Grouped 1H/15m images for one origin can never cross partitions.

## 7. Final-holdout seal

[`data/manifests/split-v1.json`](../data/manifests/split-v1.json) contains membership and timing but no target label field. It records:

- final-holdout membership SHA-256;
- `status = SEALED`, `opened = false`;
- first permitted open stage `W`;
- authorized role `PROJECT_OWNER`.

The holdout may be opened exactly once at Stage W, after the project owner creates an explicit UTC unlock record containing locked hashes for features, model, calibration, risk policy and code commit. Stage I–V feature/model/threshold work must not create that record. The holdout cannot be opened merely to debug, improve balance or raise a metric.

If a defect is found before opening, create a new split version and keep v1 sealed. If a defect is found after opening, v1 is permanently contaminated and cannot be presented as an untouched final test.

## 8. Reproducibility

The manifest binds the source label run, label JSONL SHA-256, label manifest SHA-256, split config hash and split engine version. Regeneration is idempotent only when bytes are identical; otherwise the pipeline refuses to overwrite the locked file.

The companion [`split-v1.sha256`](../data/manifests/split-v1.sha256) verifies the complete manifest.

## 9. Current-data limitation

The current capture spans roughly 19 hours of eligible decision timestamps. It is enough to verify split mechanics but not enough for a statistically credible final performance estimate. More data requires a new immutable split version; v1 membership and hashes must not be silently extended.
