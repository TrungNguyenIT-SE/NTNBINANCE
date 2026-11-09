"""Typed, fail-closed local profile configuration."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ALLOWED_PROFILES: Final[frozenset[str]] = frozenset({"local-dev", "local-test", "local-release"})
LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"127.0.0.1", "localhost", "::1"})
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]


class ConfigurationError(ValueError):
    """Raised when a local profile is absent, malformed, or unsafe."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings loaded from a versioned TOML profile."""

    profile: str
    host: str
    port: int
    debug: bool
    log_level: str
    data_root: Path
    runtime_root: Path
    max_upload_bytes: int
    workers: int


def _resolve_local_path(value: object, field_name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field_name} must be a non-empty relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ConfigurationError(f"{field_name} must remain inside the project root")
    return (PROJECT_ROOT / candidate).resolve()


def load_settings(profile: str | None = None, config_dir: Path | None = None) -> Settings:
    """Load one of the three approved local profiles and reject unsafe bindings."""

    selected = profile or os.getenv("NTN_PROFILE", "local-dev")
    if selected not in ALLOWED_PROFILES:
        raise ConfigurationError(f"Unsupported profile: {selected}")

    directory = config_dir or PROJECT_ROOT / os.getenv("NTN_CONFIG_DIR", "configs")
    config_path = (directory / f"{selected}.toml").resolve()
    if not config_path.is_file():
        raise ConfigurationError(f"Profile file not found: {config_path}")

    with config_path.open("rb") as stream:
        raw = tomllib.load(stream)

    if raw.get("profile") != selected:
        raise ConfigurationError("Profile name does not match its filename")

    host = raw.get("host")
    if host not in LOOPBACK_HOSTS:
        raise ConfigurationError("MVP profiles must bind to a loopback host")

    port = raw.get("port")
    workers = raw.get("workers")
    max_upload_bytes = raw.get("max_upload_bytes")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ConfigurationError("port must be between 1 and 65535")
    if workers != 1:
        raise ConfigurationError("Stage C resource policy requires exactly one worker")
    if not isinstance(max_upload_bytes, int) or max_upload_bytes <= 0:
        raise ConfigurationError("max_upload_bytes must be a positive integer")

    debug = raw.get("debug")
    log_level = raw.get("log_level")
    if not isinstance(debug, bool):
        raise ConfigurationError("debug must be boolean")
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("Unsupported log level")

    return Settings(
        profile=selected,
        host=host,
        port=port,
        debug=debug,
        log_level=log_level,
        data_root=_resolve_local_path(raw.get("data_root"), "data_root"),
        runtime_root=_resolve_local_path(raw.get("runtime_root"), "runtime_root"),
        max_upload_bytes=max_upload_bytes,
        workers=workers,
    )
