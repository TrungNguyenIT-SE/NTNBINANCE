from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.splits.models import Partition, SplitConfig
from ntnbinance.splits.pipeline import (
    assert_no_cross_partition_overlap,
    build_split,
    intervals_overlap,
)

from .helpers import config, sample_windows


def test_primary_split_counts_boundaries_and_symbol_grouping() -> None:
    samples = sample_windows()
    assignments, folds, audit = build_split(samples, config())
    counts = {
        partition: sum(value is partition for value in assignments.values())
        for partition in Partition
    }
    assert counts == {
        Partition.TRAIN: 90,
        Partition.PURGED_TRAIN_VALIDATION: 6,
        Partition.VALIDATION: 26,
        Partition.EMBARGO_VALIDATION_TEST: 6,
        Partition.FINAL_HOLDOUT: 26,
    }
    assert audit["decision_gap_train_validation_ms"] == 3_600_000
    assert audit["decision_gap_validation_holdout_ms"] == 3_600_000
    assert audit["embargo_required_ms"] == 3_600_000
    assert len(folds) == 3
    assert [(len(f.train_ids), len(f.purged_ids), len(f.validation_ids)) for f in folds] == [
        (38, 6, 26),
        (64, 6, 26),
        (90, 6, 26),
    ]
    by_time: dict[int, set[Partition]] = {}
    for sample in samples:
        by_time.setdefault(sample.decision_time_ms, set()).add(assignments[sample.sample_id])
    assert all(len(partitions) == 1 for partitions in by_time.values())


def test_half_open_label_intervals_and_overlap_audit() -> None:
    samples = sample_windows(6)
    assert intervals_overlap(samples[0], samples[2])
    assert not intervals_overlap(samples[0], samples[8])  # exactly one 60m horizon later
    with pytest.raises(ValueError, match="label-window leakage"):
        assert_no_cross_partition_overlap([samples[0]], [samples[2]])
    assert_no_cross_partition_overlap([samples[0]], [samples[8]])


def test_invalid_dataset_shape_and_split_config_fail_closed() -> None:
    with pytest.raises(ValueError, match="empty"):
        build_split([], config())
    missing_symbol = sample_windows()
    missing_symbol.pop()
    with pytest.raises(ValueError, match="same symbol universe"):
        build_split(missing_symbol, config())
    wrong_horizon = sample_windows()
    wrong_horizon[0] = replace(
        wrong_horizon[0], vertical_barrier_time_ms=wrong_horizon[0].decision_time_ms + 1
    )
    with pytest.raises(ValueError, match="horizon"):
        build_split(wrong_horizon, config())
    with pytest.raises(ValueError, match="embargo"):
        replace(config(), embargo_minutes=15)
    with pytest.raises(ValueError, match="fraction"):
        replace(config(), validation_fraction=Decimal("0.8"))


def test_all_split_config_invariants_fail_closed() -> None:
    mutations: tuple[tuple[Callable[[], SplitConfig], str], ...] = (
        (lambda: replace(config(), version="2.0.0"), "version"),
        (lambda: replace(config(), base_interval_minutes=0), "positive"),
        (lambda: replace(config(), prediction_horizon_minutes=50), "align"),
        (lambda: replace(config(), final_holdout_fraction=Decimal(0)), "holdout fraction"),
        (lambda: replace(config(), walk_forward_folds=1), "walk-forward"),
        (lambda: replace(config(), final_holdout_open_stage="V"), "Stage W"),
        (lambda: replace(config(), final_holdout_authorized_role="MODEL_OWNER"), "project-owner"),
    )
    for mutate, message in mutations:
        with pytest.raises(ValueError, match=message):
            mutate()
