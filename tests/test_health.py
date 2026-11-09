import pytest
from fastapi.testclient import TestClient

from ntnbinance import main
from ntnbinance.config import load_settings
from ntnbinance.main import create_app


def test_health_and_metadata_contract() -> None:
    app = create_app(load_settings("local-test"))

    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {
            "status": "ready",
            "profile": "local-test",
        }
        metadata = client.get("/api/v1/meta").json()

    assert metadata["scope"] == "local-private-research"
    assert metadata["trading_enabled"] is False


def test_run_uses_the_safe_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = load_settings("local-test")
    captured: dict[str, object] = {}

    def fake_run(_app: str, **kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(main, "load_settings", lambda: settings)
    monkeypatch.setattr(main, "uvicorn_run", fake_run)

    main.run()

    assert captured == {
        "host": "127.0.0.1",
        "port": 8010,
        "workers": 1,
        "reload": False,
        "log_level": "warning",
    }
