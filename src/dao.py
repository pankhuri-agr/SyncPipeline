from __future__ import annotations
from typing import Any
from src.domain import TransformedMessage

# Sync state: keyed by (event_id, destination_id). Values: PENDING | IN_FLIGHT
# | DELIVERED | FAILED plus a version/attempt count.
SYNC_STATE: dict[tuple[str, str], dict[str, Any]] = {}


def sync_state_get(event_id: str, destination_id: str) -> dict[str, Any] | None:
    return SYNC_STATE.get((event_id, destination_id))

def sync_state_claim(msg: TransformedMessage) -> bool:
    key = (msg.event_id, msg.destination_id)
    existing = SYNC_STATE.get(key)
    if existing and existing["status"] in ("DELIVERED", "IN_FLIGHT"):
        return False
    SYNC_STATE[key] = {
        "status": "IN_FLIGHT",
        "attempts": (existing or {}).get("attempts", 0) + 1,
        "provider_record_id": (existing or {}).get("provider_record_id"),
    }
    return True

def sync_state_mark(msg: TransformedMessage, status: str, **extra: Any) -> None:
    key = (msg.event_id, msg.destination_id)
    state = SYNC_STATE.get(key, {"attempts": 0})
    state["status"] = status
    state.update(extra)
    SYNC_STATE[key] = state