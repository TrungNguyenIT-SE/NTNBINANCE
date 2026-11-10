import asyncio
from collections.abc import AsyncIterator

import pytest

import ntnbinance.ingestion.websocket as websocket_module
from ntnbinance.ingestion.websocket import BinanceKlineStream, build_kline_stream_url


class FakeSocket:
    def __init__(self, messages: list[str | bytes]) -> None:
        self.messages = messages

    async def __aiter__(self) -> AsyncIterator[str | bytes]:
        for message in self.messages:
            yield message


class FakeConnect:
    def __init__(self, sockets: list[FakeSocket]) -> None:
        self.sockets = sockets

    async def __aiter__(self) -> AsyncIterator[FakeSocket]:
        for socket in self.sockets:
            yield socket


def test_url_uses_required_routed_market_combined_stream() -> None:
    url = build_kline_stream_url(("BTCUSDT", "ETHUSDT"), "1m")
    assert url == (
        "wss://fstream.binance.com/market/stream?streams=btcusdt@kline_1m/ethusdt@kline_1m"
    )


@pytest.mark.parametrize("symbols", [(), ("BTC-USDT",), ("",)])
def test_invalid_symbols_are_rejected(symbols: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="symbol"):
        build_kline_stream_url(symbols, "1m")


def test_stream_processes_messages_and_notifies_on_reconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handled: list[str | bytes] = []
    reconnects: list[int] = []

    async def handler(message: str | bytes) -> None:
        handled.append(message)

    async def on_reconnect(count: int) -> None:
        reconnects.append(count)

    fake = FakeConnect([FakeSocket(["one"]), FakeSocket([b"two"])])
    monkeypatch.setattr(websocket_module, "connect", lambda *args, **kwargs: fake)
    stream = BinanceKlineStream(
        symbols=("BTCUSDT",), interval="1m", handler=handler, on_reconnect=on_reconnect
    )

    asyncio.run(stream.run(max_connections=2))

    assert handled == ["one", b"two"]
    assert reconnects == [2]
