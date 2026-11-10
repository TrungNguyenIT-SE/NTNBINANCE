"""Command-line operations for the Stage E public-data pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ntnbinance.ingestion.backfill import BackfillService, BackfillSummary
from ntnbinance.ingestion.raw_store import RawStore
from ntnbinance.ingestion.reconcile import ClosedKlineReconciler
from ntnbinance.ingestion.rest import BinanceRestClient
from ntnbinance.ingestion.websocket import BinanceKlineStream


def _summary_json(results: dict[str, BackfillSummary]) -> str:
    return json.dumps(
        {
            name: {
                "duplicates": summary.duplicates,
                "received": summary.received,
                "requests": summary.requests,
                "written": summary.written,
            }
            for name, summary in sorted(results.items())
        },
        indent=2,
        sort_keys=True,
    )


def run_backfill(*, hours: int, data_root: Path) -> dict[str, BackfillSummary]:
    if hours < 1 or hours > 24 * 30:
        raise ValueError("hours must be between 1 and 720")
    store = RawStore(data_root)
    with BinanceRestClient() as client:
        service = BackfillService(client, store)
        service.bootstrap_exchange_limits()
        end = datetime.fromtimestamp(service.server_time_ms() / 1000, tz=UTC)
        start = end - timedelta(hours=hours)
        return service.backfill_stage_e_window(start=start, end=end)


async def run_stream(*, minutes: int, data_root: Path, interval: str = "1m") -> None:
    if minutes < 1 or minutes > 24 * 60:
        raise ValueError("minutes must be between 1 and 1440")
    store = RawStore(data_root)
    client = BinanceRestClient()
    service = BackfillService(client, store)

    async def recover(symbol: str, gap_interval: str, start_ms: int, end_ms: int) -> None:
        service.backfill_klines(
            dataset="trade_klines",
            instrument=symbol,
            interval=gap_interval,
            start=datetime.fromtimestamp(start_ms / 1000, tz=UTC),
            end=datetime.fromtimestamp(end_ms / 1000, tz=UTC),
        )

    reconciler = ClosedKlineReconciler(store, recover)
    stream = BinanceKlineStream(
        symbols=("BTCUSDT", "ETHUSDT"), interval=interval, handler=reconciler.process
    )
    try:
        async with asyncio.timeout(minutes * 60):
            await stream.run()
    except TimeoutError:
        return
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ntnbinance-ingest", description="Public-only Binance USDⓈ-M ingestion"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    backfill = subcommands.add_parser("backfill", help="Backfill the Stage E dataset window")
    backfill.add_argument("--hours", type=int, default=24)
    backfill.add_argument("--data-root", type=Path, default=Path("data/raw"))
    stream = subcommands.add_parser("stream", help="Capture and reconcile closed kline events")
    stream.add_argument("--minutes", type=int, default=2)
    stream.add_argument("--interval", choices=("1m", "5m", "15m", "1h"), default="1m")
    stream.add_argument("--data-root", type=Path, default=Path("data/raw"))
    audit = subcommands.add_parser("audit", help="Verify raw files against the manifest")
    audit.add_argument("--data-root", type=Path, default=Path("data/raw"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "backfill":
        results = run_backfill(hours=args.hours, data_root=args.data_root)
        print(_summary_json(results))
        return 0
    if args.command == "audit":
        result = RawStore(args.data_root).audit()
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
        return 0
    asyncio.run(run_stream(minutes=args.minutes, data_root=args.data_root, interval=args.interval))
    print("stream capture complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
