"""Fail-closed governance guard for the sealed final holdout."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_LOCKS = frozenset(
    {"feature_hash", "model_hash", "calibration_hash", "risk_policy_hash", "code_commit"}
)


def require_holdout_unlock(path: Path) -> dict[str, str]:
    """Validate an explicit Stage W project-owner unlock record."""

    if not path.is_file():
        raise PermissionError("final holdout is sealed; unlock record is absent")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PermissionError("holdout unlock record is invalid")
    if data.get("stage") != "W" or data.get("authorized_role") != "PROJECT_OWNER":
        raise PermissionError("holdout unlock requires Stage W project-owner authorization")
    if data.get("decision") != "OPEN_FINAL_HOLDOUT_ONCE":
        raise PermissionError("holdout unlock decision is invalid")
    locks = data.get("locked_artifacts")
    if not isinstance(locks, dict) or set(locks) != REQUIRED_LOCKS:
        raise PermissionError("all pipeline artifacts must be locked before holdout access")
    if not all(isinstance(value, str) and len(value) >= 7 for value in locks.values()):
        raise PermissionError("holdout artifact hashes are invalid")
    opened_at = data.get("opened_at_utc")
    if not isinstance(opened_at, str) or not opened_at.endswith("Z"):
        raise PermissionError("holdout unlock timestamp must be explicit UTC")
    return {key: str(value) for key, value in data.items() if isinstance(value, str)}
