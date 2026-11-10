"""Auto-reconnecting client for Binance routed market WebSocket streams."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable
from urllib.parse import quote

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

LOGGER = logging.getLogger(__name__)
MessageHandler = Callable[[str | bytes], Awaitable[object]]
ReconnectHandler = Callable[[int], Awaitable[None]]


def build_kline_stream_url(symbols: Iterable[str], interval: str) -> str:
    normalized = tuple(symbol.upper() for symbol in symbols)
    if not normalized or any(not symbol.isalnum() for symbol in normalized):
        raise ValueError("at least one uppercase alphanumeric symbol is required")
    streams = "/".join(f"{symbol.lower()}@kline_{interval}" for symbol in normalized)
    return f"wss://fstream.binance.com/market/stream?streams={quote(streams, safe='/@_')}"


class BinanceKlineStream:
    """Reconnect by URL subscription; the routed combined stream is re-subscribed each time."""

    def __init__(
        self,
        *,
        symbols: tuple[str, ...],
        interval: str,
        handler: MessageHandler,
        on_reconnect: ReconnectHandler | None = None,
    ) -> None:
        self.url = build_kline_stream_url(symbols, interval)
        self.handler = handler
        self.on_reconnect = on_reconnect

    async def run(self, *, max_connections: int | None = None) -> None:
        """Run until cancelled, reconnecting with library-provided bounded backoff."""

        connection_count = 0
        async for websocket in connect(
            self.url,
            open_timeout=10,
            ping_interval=150,
            ping_timeout=30,
            close_timeout=5,
            max_size=1_048_576,
            max_queue=32,
            proxy=None,
        ):
            connection_count += 1
            if connection_count > 1 and self.on_reconnect is not None:
                await self.on_reconnect(connection_count)
            try:
                async for message in websocket:
                    await self.handler(message)
            except ConnectionClosed:
                LOGGER.warning("Binance market stream disconnected; reconnecting")
            if max_connections is not None and connection_count >= max_connections:
                return
