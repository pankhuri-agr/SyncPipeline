from __future__ import annotations


from typing import Any
from src.errors import TransformError
from src.domain import InboundMessage, TransformedMessage
from src.config_loader import fetch_destinations
from src.transformer import transform
from src.validator import validate


def commit_offset(msg: InboundMessage) -> None:
    # stubbing
    print(f"  [kafka] commit event_id={msg.event_id}")


def process_internal_message(raw_message: dict[str, Any], config: dict[str, Any])\
        -> list[TransformedMessage]:
    """
    End-to-end processing of one inbound message. Returns the list of
    transformed messages that would be published to per-provider Kafka.
    """
    # Validate
    msg = validate(raw_message)
    print(f"[validate] ok event_id={msg.event_id} tenant={msg.tenant_id} "
          f"record={msg.record_id} op={msg.operation}")

    # Fetch destination config
    destinations = fetch_destinations(config, msg.tenant_id, msg.record_type)
    print(f"[config] resolved {len(destinations)} destination(s) "
          f"for tenant={msg.tenant_id} record_type={msg.record_type}")

    if not destinations:
        commit_offset(msg)
        return []

    # Transform per destination (fan-out)
    outputs: list[TransformedMessage] = []
    for dest in destinations:
        try:
            transformed = transform(msg, dest)
            outputs.append(transformed)
            print(f"[transform] ok destination={transformed.destination_id} "
                  f"provider={transformed.provider}")
        except TransformError as e:
            print(f"[transform] FAILED destination={dest.get('destination_id')}: {e}")

    commit_offset(msg)
    return outputs