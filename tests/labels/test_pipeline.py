from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ntnbinance.data_quality.storage import publish_parquet
from ntnbinance.ingestion.raw_store import RawRecord, RawStore
from ntnbinance.labels.pipeline import LabelPipeline

from .helpers import CONFIG_PATH, candle


def _prepare_clean(root: Path) -> Path:
    clean = root / "clean"
    base = [
        candle(
            minute,
            interval="15m",
            open_value="100",
            high="101",
            low="99",
            close="100",
            identity=f"base-{minute}",
        )
        for minute in range(0, 300, 15)
    ]
    intrabars = [
        candle(
            minute,
            interval="1m",
            open_value="100",
            high="101",
            low="99",
            close="100",
            identity=f"intra-{minute}",
        )
        for minute in range(300)
    ]
    publish_parquet(
        candles=[*base, *intrabars],
        quarantine=[],
        clean_root=clean,
        quarantine_root=root / "quarantine",
        summary={"fixture": True},
    )
    return clean


def _prepare_raw(root: Path) -> Path:
    raw = root / "raw"
    record = RawRecord.create(
        dataset="funding_rates",
        source="REST",
        endpoint="/fapi/v1/fundingRate",
        request_params={"symbol": "BTCUSDT"},
        record_key="BTCUSDT|28800000|Regular",
        event_time_ms=28_800_000,
        ingested_at=datetime(1970, 1, 1, 8, tzinfo=UTC),
        payload={
            "symbol": "BTCUSDT",
            "fundingTime": 28_800_000,
            "fundingRate": "0.0001",
        },
    )
    RawStore(raw).write_batch(
        [record], batch_id="funding", created_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
    return raw


def test_pipeline_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    pipeline = LabelPipeline(
        clean_root=_prepare_clean(tmp_path),
        raw_root=_prepare_raw(tmp_path),
        output_root=tmp_path / "labels",
        config_path=CONFIG_PATH,
    )
    first = pipeline.run()
    assert not first.reused
    assert first.sample_count == 2
    assert first.excluded_windows == 0
    assert first.distribution == {"NO_TRADE": 2}
    assert (first.output_root / "labels.jsonl").read_text(encoding="utf-8").count("\n") == 2

    second = pipeline.run()
    assert second.reused
    assert second.run_id == first.run_id
    assert second.distribution == first.distribution
    assert second.excluded_windows == 0
