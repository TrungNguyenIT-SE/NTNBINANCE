from collections.abc import Callable

import httpx2
import pytest

from ntnbinance.ingestion.rest import (
    BinanceRequestError,
    BinanceRestClient,
    RetryPolicy,
)


def make_client(
    handler: Callable[[httpx2.Request], httpx2.Response],
    *,
    retry: RetryPolicy | None = None,
    sleeps: list[float] | None = None,
) -> BinanceRestClient:
    transport = httpx2.MockTransport(handler)
    http_client = httpx2.Client(base_url="https://fapi.binance.com", transport=transport)
    return BinanceRestClient(
        client=http_client,
        retry=retry,
        sleep=(sleeps if sleeps is not None else []).append,
        jitter=lambda: 0.0,
    )


def test_success_parses_weight_and_retry_headers() -> None:
    client = make_client(
        lambda request: httpx2.Response(
            200,
            json={"ok": True},
            headers={"X-MBX-USED-WEIGHT-1M": "42", "Retry-After": "3"},
            request=request,
        )
    )

    result = client.get_json("/fapi/v1/time")

    assert result.data == {"ok": True}
    assert result.rate_limit.used_weight["x-mbx-used-weight-1m"] == 42
    assert result.rate_limit.retry_after_seconds == 3.0


def test_429_retries_and_honors_retry_after() -> None:
    statuses = iter((429, 200))
    sleeps: list[float] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        status = next(statuses)
        return httpx2.Response(
            status,
            json={"status": status},
            headers={"Retry-After": "2"},
            request=request,
        )

    client = make_client(handler, sleeps=sleeps)
    result = client.get_json("/fapi/v1/time")

    assert result.status_code == 200
    assert sleeps == [2.0]


def test_transport_error_retries_then_succeeds() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx2.ReadTimeout("late", request=request)
        return httpx2.Response(200, json=[], request=request)

    result = make_client(handler, sleeps=sleeps).get_json("/fapi/v1/klines")

    assert result.data == []
    assert attempts == 2
    assert sleeps == [0.25]


def test_retry_exhaustion_is_bounded() -> None:
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        return httpx2.Response(503, request=request)

    client = make_client(handler, retry=RetryPolicy(max_attempts=3))
    with pytest.raises(BinanceRequestError, match="exhausted 3 attempts"):
        client.get_json("/fapi/v1/time")
    assert attempts == 3


def test_non_retryable_error_fails_immediately() -> None:
    client = make_client(lambda request: httpx2.Response(400, request=request))
    with pytest.raises(BinanceRequestError, match="HTTP 400"):
        client.get_json("/fapi/v1/time")


def test_dynamic_limit_triggers_proactive_throttle() -> None:
    sleeps: list[float] = []
    client = make_client(
        lambda request: httpx2.Response(
            200, json={}, headers={"X-MBX-USED-WEIGHT-1M": "80"}, request=request
        ),
        sleeps=sleeps,
    )
    client.configure_limits(
        {
            "rateLimits": [
                {
                    "rateLimitType": "REQUEST_WEIGHT",
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 100,
                }
            ]
        }
    )
    client.get_json("/fapi/v1/time")
    client.get_json("/fapi/v1/time")
    assert sleeps == [1.0]


@pytest.mark.parametrize(
    "endpoint",
    ["https://example.com/fapi/v1/time", "/api/v3/time", "/fapi/v1/time?bad=1"],
)
def test_unapproved_endpoint_is_rejected(endpoint: str) -> None:
    client = make_client(lambda request: httpx2.Response(200, request=request))
    with pytest.raises(ValueError, match="approved public Binance path"):
        client.get_json(endpoint)


def test_credential_and_complex_query_values_are_rejected() -> None:
    client = make_client(lambda request: httpx2.Response(200, request=request))
    with pytest.raises(ValueError, match="credentials are forbidden"):
        client.get_json("/fapi/v1/time", {"signature": "secret"})
    with pytest.raises(ValueError, match="unsupported query parameter"):
        client.get_json("/fapi/v1/time", {"bad": ["value"]})


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="official Binance"):
        BinanceRestClient(base_url="https://example.com")
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError, match="delays"):
        RetryPolicy(base_delay_seconds=-1)
