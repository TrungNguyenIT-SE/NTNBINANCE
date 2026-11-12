# ADR-0005 — Stage H purged walk-forward and sealed holdout

- Status: `ACCEPTED`
- Date: `13/11/2026`
- Split version: `1.0.0`
- Source label run: `8780c5a42857c830`

## Context

Stage G labels span four future 15m candles, so adjacent samples share outcome information. Random splitting or adjacent train/validation rows would leak the same future price path into both partitions. Image augmentation can create another leakage path if derivatives of one origin are split independently.

## Decision

- Assign complete decision timestamps chronologically across both symbols.
- Use half-open label intervals and reject any cross-partition overlap.
- Separate usable partitions by a decision-time gap of at least 60 minutes.
- Lock three expanding walk-forward folds inside development data.
- Reserve the latest 13 timestamps as a sealed final holdout.
- Split origin samples before augmentation; all derivatives inherit origin membership.
- Restrict scaler/selector/model fitting to train and calibrator fitting to valid out-of-sample predictions.
- Permit first final-holdout access only at Stage W with project-owner authorization and locked artifact hashes.

## Consequences

- Twelve samples are deliberately unavailable to fit/score because they occupy purge/embargo boundaries.
- Final-holdout class distribution is not reported during development.
- The small v1 dataset validates mechanics, not statistical power.
- New data or a semantic change requires split v2; v1 cannot be overwritten.

## Rejected alternatives

- Random/stratified row split: breaks chronology and shares future paths.
- Symbol-independent split: can put contemporaneous BTC/ETH context on opposite sides.
- Zero-gap chronological split: adjacent four-bar labels overlap.
- Augment then split: variants of one image can leak across partitions.
- Repeated test inspection: turns final test into development data.
