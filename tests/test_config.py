from pathlib import Path

import pytest

from ntnbinance.config import ConfigurationError, load_settings


def write_profile(tmp_path: Path, **overrides: object) -> None:
    values: dict[str, object] = {
        "profile": "local-test",
        "host": "127.0.0.1",
        "port": 8010,
        "debug": False,
        "log_level": "WARNING",
        "data_root": "data",
        "runtime_root": "var/test",
        "max_upload_bytes": 1048576,
        "workers": 1,
    }
    values.update(overrides)
    lines = []
    for key, value in values.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        else:
            lines.append(f"{key} = {value}")
    (tmp_path / "local-test.toml").write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("profile", ["local-dev", "local-test", "local-release"])
def test_versioned_profiles_are_safe(profile: str) -> None:
    settings = load_settings(profile)

    assert settings.profile == profile
    assert settings.host == "127.0.0.1"
    assert settings.workers == 1
    assert settings.data_root.is_absolute()
    assert settings.runtime_root.is_absolute()


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="Unsupported profile"):
        load_settings("production")


def test_missing_profile_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_settings("local-test", config_dir=tmp_path)


def test_non_loopback_binding_is_rejected(tmp_path: Path) -> None:
    write_profile(tmp_path, host="0.0.0.0")

    with pytest.raises(ConfigurationError, match="loopback"):
        load_settings("local-test", config_dir=tmp_path)


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    write_profile(tmp_path, data_root="../outside")

    with pytest.raises(ConfigurationError, match="project root"):
        load_settings("local-test", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"profile": "local-dev"}, "does not match"),
        ({"port": 0}, "port"),
        ({"workers": 2}, "one worker"),
        ({"max_upload_bytes": 0}, "positive integer"),
        ({"debug": 1}, "debug must be boolean"),
        ({"log_level": "TRACE"}, "log level"),
        ({"data_root": ""}, "non-empty relative path"),
    ],
)
def test_malformed_profile_is_rejected(
    tmp_path: Path, overrides: dict[str, object], message: str
) -> None:
    write_profile(tmp_path, **overrides)

    with pytest.raises(ConfigurationError, match=message):
        load_settings("local-test", config_dir=tmp_path)
