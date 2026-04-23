from __future__ import annotations

import json
import sys

from pathlib import Path
from typing import Any
from src.errors import ValidationError, ConfigError, TransformError
from src.domain import InboundMessage, TransformedMessage
from src.config_loader import fetch_destinations
from src.transformer import transform
from src.validator import validate

# Stub file paths — in real code these would be Kafka + a config service.
STUB_DIR = Path(__file__).parent / "stubs"
MESSAGE_FILE = STUB_DIR / "internal_message.json"
CONFIG_FILE = STUB_DIR / "config.json"


def commit_offset(msg: InboundMessage) -> None:
    """In real impl: consumer.commit(). Here: print."""
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
        # No destinations configured for this record type.
        # Still commit so we don't re-read this message.
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
            # In real impl: send this destination's attempt to DLQ, continue others.
            print(f"[transform] FAILED destination={dest.get('destination_id')}: {e}")

    # Commit offset to kafka
    commit_offset(msg)

    return outputs


def main() -> int:
    # Load stub inputs.
    try:
        raw_message = json.loads(MESSAGE_FILE.read_text())
    except FileNotFoundError:
        print(f"ERROR: stub message file not found: {MESSAGE_FILE}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: stub message is not valid JSON: {e}", file=sys.stderr)
        return 1

    try:
        config = json.loads(CONFIG_FILE.read_text())
    except FileNotFoundError:
        print(f"ERROR: stub config file not found: {CONFIG_FILE}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: stub config is not valid JSON: {e}", file=sys.stderr)
        return 1

    print("=" * 72)
    print("First consumer stub — processing one message")
    print("=" * 72)

    try:
        outputs = process_internal_message(raw_message, config)
    except ValidationError as e:
        print(f"[validate] FAILED: {e} — would DLQ in real impl", file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"[config] FAILED: {e} — would retry in real impl", file=sys.stderr)
        return 3

    print("-" * 72)
    print(f"Result: {len(outputs)} message(s) to publish to per-provider Kafka:")
    for out in outputs:
        print(json.dumps(out.__dict__))

    return 0


if __name__ == "__main__":
    sys.exit(main())