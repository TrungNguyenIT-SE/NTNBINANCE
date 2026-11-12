from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from ntnbinance.data_quality.pipeline import DataQualityPipeline
from ntnbinance.ingestion.raw_store import RawRecord, RawStore


def _raw_candle(minute: int) -> RawRecord:
    open_time = minute * 60_000
    close_time = open_time + 59_999
    return RawRecord.create(
        dataset="trade_klines",
        source="REST",
        endpoint="/fapi/v1/klines",
        request_params={"symbol": "BTCUSDT", "interval": "1m"},
        record_key=f"BTCUSDT|1m|{open_time}",
        event_time_ms=close_time,
        ingested_at=datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=close_time + 1),
        payload=[
            open_time,
            "100",
            "102",
            "99",
            "101",
            "10",
            close_time,
            "1000",
            2,
            "5",
            "500",
        ],
    )


def test_pipeline_publishes_partitioned_parquet_and_reuses_run(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    RawStore(raw_root).write_batch(
        [_raw_candle(minute) for minute in range(60)],
        batch_id="quality-test",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    pipeline = DataQualityPipeline(
        raw_root=raw_root,
        clean_root=tmp_path / "clean",
        quarantine_root=tmp_path / "quarantine",
    )
    first = pipeline.run()
    assert not first.reused
    assert first.stats.raw_records == 60
    assert first.stats.clean_base_candles == 60
    assert first.stats.resampled_candles == 5
    assert first.stats.quarantine_records == 0
    assert first.excluded_resample_buckets == {"15m": 0, "1h": 0}
    manifest = json.loads((first.clean_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == first.run_id
    parquet_glob = (first.clean_root / "**" / "*.parquet").as_posix()
    count = (
        duckdb.connect(":memory:")
        .execute(f"SELECT count(*) FROM read_parquet('{parquet_glob}', hive_partitioning=true)")
        .fetchone()
    )
    assert count == (65,)

    second = pipeline.run()
    assert second.reused
    assert second.run_id == first.run_id
    assert second.stats == first.stats
    assert second.coverage == first.coverage
    assert second.feature_coverage == first.feature_coverage


def test_pipeline_run_id_changes_with_raw_manifest(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    store = RawStore(raw_root)
    store.write_batch([_raw_candle(0)], batch_id="one", created_at=datetime(2026, 1, 1, tzinfo=UTC))
    pipeline = DataQualityPipeline(
        raw_root=raw_root,
        clean_root=tmp_path / "clean",
        quarantine_root=tmp_path / "quarantine",
    )
    first = pipeline.run()
    store.write_batch([_raw_candle(1)], batch_id="two", created_at=datetime(2026, 1, 2, tzinfo=UTC))
    second = pipeline.run()
    assert first.run_id != second.run_id
