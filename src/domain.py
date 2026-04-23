from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class InboundMessage:
    """What we read from the inbound Kafka partition."""
    event_id: str
    tenant_id: str
    record_id: str
    record_type: str
    operation: str  # create | update | delete
    payload: dict[str, Any]
    source_version: str | None = None


@dataclass
class TransformedMessage:
    """What we publish to per-provider Kafka (one per destination)."""
    event_id: str  # stable across destinations — same source event
    tenant_id: str
    destination_id: str  # identifies which destination config this is
    provider: str  # e.g., "salesforce", "hubspot"
    record_id: str
    operation: str
    provider_payload: dict[str, Any]
    source_version: str | None