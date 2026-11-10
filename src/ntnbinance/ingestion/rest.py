"""Bounded-retry Binance USDⓈ-M public REST client."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from random import random
from typing import Final

import httpx2

LOGGER = logging.getLogger(__name__)
RETRYABLE_STATUS: Final = frozenset({408, 418, 429, 500, 502, 503, 504})
ALLOWED_PREFIXES: Final = ("/fapi/v1/", "/futures/data/")


class BinanceRequestError(RuntimeError):
    """A public market-data request exhausted its safe retry policy."""


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 8.0
    jitter_seconds: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if min(self.base_delay_seconds, self.max_delay_seconds, self.jitter_seconds) < 0:
            raise ValueError("retry delays cannot be negative")


@dataclass(frozen=True, slots=True)
class RateLimitSnapshot:
    used_weight: dict[str, int] = field(default_factory=dict)
    retry_after_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class RestResult:
    data: object
    status_code: int
    rate_limit: RateLimitSnapshot


class BinanceRestClient:
    """Public GET-only client with timeout, backoff, jitter and header telemetry."""

    def __init__(
        self,
        *,
        base_url: str = "https://fapi.binance.com",
        retry: RetryPolicy | None = None,
        client: httpx2.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random,
    ) -> None:
        if base_url != "https://fapi.binance.com":
            raise ValueError("only the official Binance USDⓈ-M REST base URL is allowed")
        self.retry = retry or RetryPolicy()
        self._sleep = sleep
        self._jitter = jitter
        self._owns_client = client is None
        self._client = client or httpx2.Client(
            base_url=base_url,
            headers={"Accept": "application/json", "User-Agent": "NTNBINANCE/0.1"},
            timeout=httpx2.Timeout(10.0, connect=5.0),
            follow_redirects=False,
            trust_env=False,
        )
        self.weight_limit_per_minute: int | None = None
        self.last_rate_limit = RateLimitSnapshot()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> BinanceRestClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _snapshot(headers: Mapping[str, str]) -> RateLimitSnapshot:
        weights: dict[str, int] = {}
        for key, value in headers.items():
            lowered = key.lower()
            if lowered.startswith("x-mbx-used-weight-"):
                try:
                    weights[lowered] = int(value)
                except ValueError:
                    LOGGER.warning("ignored invalid Binance weight header %s", lowered)
        retry_after: float | None = None
        raw_retry = next(
            (value for key, value in headers.items() if key.lower() == "retry-after"), None
        )
        if raw_retry is not None:
            try:
                retry_after = max(0.0, float(raw_retry))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(raw_retry)
                    retry_after = max(0.0, retry_at.timestamp() - time.time())
                except TypeError, ValueError:
                    LOGGER.warning("ignored invalid Retry-After header")
        return RateLimitSnapshot(used_weight=weights, retry_after_seconds=retry_after)

    def configure_limits(self, exchange_info: object) -> None:
        if not isinstance(exchange_info, dict):
            return
        limits = exchange_info.get("rateLimits")
        if not isinstance(limits, list):
            return
        for item in limits:
            if (
                isinstance(item, dict)
                and item.get("rateLimitType") == "REQUEST_WEIGHT"
                and item.get("interval") == "MINUTE"
                and item.get("intervalNum") == 1
                and isinstance(item.get("limit"), int)
            ):
                self.weight_limit_per_minute = item["limit"]
                return

    def _proactive_throttle(self) -> None:
        limit = self.weight_limit_per_minute
        used = self.last_rate_limit.used_weight.get("x-mbx-used-weight-1m")
        if limit and used is not None and used / limit >= 0.8:
            self._sleep(1.0)

    def _delay(self, attempt: int, snapshot: RateLimitSnapshot | None = None) -> float:
        exponential: float = min(
            self.retry.max_delay_seconds,
            self.retry.base_delay_seconds * (2 ** (attempt - 1)),
        )
        delay: float = exponential + self.retry.jitter_seconds * self._jitter()
        if snapshot and snapshot.retry_after_seconds is not None:
            delay = max(delay, snapshot.retry_after_seconds)
        return delay

    def get_json(self, endpoint: str, params: Mapping[str, object] | None = None) -> RestResult:
        if not endpoint.startswith(ALLOWED_PREFIXES) or "?" in endpoint:
            raise ValueError("endpoint must be an approved public Binance path without query text")
        self._proactive_throttle()
        safe_params: dict[str, str | int | float | bool | None] = {}
        for key, value in (params or {}).items():
            if value is not None and not isinstance(value, str | int | float | bool):
                raise ValueError(f"unsupported query parameter type for {key}")
            safe_params[key] = value
        forbidden = {key.lower() for key in safe_params} & {
            "apikey",
            "api_key",
            "signature",
            "listenkey",
            "listen_key",
        }
        if forbidden:
            raise ValueError("credentials are forbidden in public market-data requests")

        last_error: Exception | None = None
        for attempt in range(1, self.retry.max_attempts + 1):
            try:
                response = self._client.get(endpoint, params=safe_params)
                snapshot = self._snapshot(response.headers)
                self.last_rate_limit = snapshot
                if response.status_code < 400:
                    return RestResult(
                        data=response.json(),
                        status_code=response.status_code,
                        rate_limit=snapshot,
                    )
                if response.status_code not in RETRYABLE_STATUS:
                    raise BinanceRequestError(
                        f"Binance GET {endpoint} failed with HTTP {response.status_code}"
                    )
                last_error = BinanceRequestError(
                    f"retryable Binance HTTP {response.status_code} on {endpoint}"
                )
                if attempt < self.retry.max_attempts:
                    LOGGER.warning(
                        "retrying public Binance endpoint=%s status=%s attempt=%s",
                        endpoint,
                        response.status_code,
                        attempt,
                    )
                    self._sleep(self._delay(attempt, snapshot))
            except (httpx2.TimeoutException, httpx2.NetworkError) as error:
                last_error = error
                if attempt < self.retry.max_attempts:
                    LOGGER.warning(
                        "retrying public Binance endpoint=%s transport_error attempt=%s",
                        endpoint,
                        attempt,
                    )
                    self._sleep(self._delay(attempt))
        raise BinanceRequestError(
            f"Binance GET {endpoint} exhausted {self.retry.max_attempts} attempts"
        ) from last_error
