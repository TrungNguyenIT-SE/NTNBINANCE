import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self

import pytest

import ntnbinance.ingestion.cli as cli
from ntnbinance.ingestion.backfill import BackfillSummary
from ntnbinance.ingestion.raw_store import AuditResult


class FakeClient:
    def __init__(self) -> None:
        self.closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.closed = True


class FakeBackfillService:
    def __init__(self) -> None:
        self.bootstrapped = False
        self.backfill_calls: list[tuple[str, str, datetime, datetime]] = []

    def bootstrap_exchange_limits(self) -> None:
        self.bootstrapped = True

    def server_time_ms(self) -> int:
        return int(datetime(2026, 11, 11, 12, 0, tzinfo=UTC).timestamp() * 1000)

    def backfill_stage_e_window(
        self, *, start: datetime, end: datetime
    ) -> dict[str, BackfillSummary]:
        assert end - start == timedelta(hours=24)
        return {"trade": BackfillSummary(requests=1, received=2, written=2)}

    def backfill_klines(
        self,
        *,
        dataset: str,
        instrument: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> BackfillSummary:
        self.backfill_calls.append((instrument, interval, start, end))
        assert dataset == "trade_klines"
        return BackfillSummary()


def test_run_backfill_bootstraps_and_uses_server_clock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = FakeClient()
    service = FakeBackfillService()
    monkeypatch.setattr(cli, "BinanceRestClient", lambda: client)
    monkeypatch.setattr(cli, "BackfillService", lambda active_client, store: service)

    result = cli.run_backfill(hours=24, data_root=tmp_path)

    assert service.bootstrapped
    assert result["trade"].written == 2
    assert client.closed


@pytest.mark.parametrize("hours", [0, 721])
def test_run_backfill_rejects_unsafe_window(hours: int, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="between 1 and 720"):
        cli.run_backfill(hours=hours, data_root=tmp_path)


def test_run_stream_reconciles_gap_and_closes_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = FakeClient()
    service = FakeBackfillService()

    class FakeReconciler:
        def __init__(self, store: object, recover: Callable[..., Awaitable[None]]) -> None:
            self.recover = recover

        async def process(self, message: str | bytes) -> None:
            assert message == "event"
            await self.recover("BTCUSDT", "1m", 60_000, 119_999)

    class FakeStream:
        def __init__(self, **kwargs: object) -> None:
            self.handler = kwargs["handler"]

        async def run(self) -> None:
            handler = self.handler
            assert callable(handler)
            await handler("event")

    monkeypatch.setattr(cli, "BinanceRestClient", lambda: client)
    monkeypatch.setattr(cli, "BackfillService", lambda active_client, store: service)
    monkeypatch.setattr(cli, "ClosedKlineReconciler", FakeReconciler)
    monkeypatch.setattr(cli, "BinanceKlineStream", FakeStream)

    asyncio.run(cli.run_stream(minutes=1, data_root=tmp_path))

    assert service.backfill_calls[0][:2] == ("BTCUSDT", "1m")
    assert client.closed


@pytest.mark.parametrize("minutes", [0, 1441])
def test_run_stream_rejects_unsafe_duration(minutes: int, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="between 1 and 1440"):
        asyncio.run(cli.run_stream(minutes=minutes, data_root=tmp_path))


def test_main_backfill_and_stream_commands(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli,
        "run_backfill",
        lambda **kwargs: {"sample": BackfillSummary(requests=1, received=1, written=1)},
    )
    assert cli.main(["backfill", "--hours", "1"]) == 0
    assert '"written": 1' in capsys.readouterr().out

    called: list[tuple[int, Path, str]] = []

    async def fake_stream(*, minutes: int, data_root: Path, interval: str) -> None:
        called.append((minutes, data_root, interval))

    monkeypatch.setattr(cli, "run_stream", fake_stream)
    assert cli.main(["stream", "--minutes", "1", "--interval", "5m"]) == 0
    assert called == [(1, Path("data/raw"), "5m")]
    assert "stream capture complete" in capsys.readouterr().out


def test_main_audit_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Store:
        def __init__(self, root: Path) -> None:
            assert root == tmp_path

        def audit(self) -> AuditResult:
            return AuditResult(files=1, records=2, identities=2, datasets={"x": 2})

    monkeypatch.setattr(cli, "RawStore", Store)
    assert cli.main(["audit", "--data-root", str(tmp_path)]) == 0
