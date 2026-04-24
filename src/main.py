from __future__ import annotations

from pathlib import Path
import json
import random
import sys

from src.errors import ValidationError, ConfigError
from src.consumers.group1 import process_internal_message
from src.consumers.group2 import process_consumer_group2_message
from src.dao import SYNC_STATE
from src.dlq import DLQ

# Stub file paths — in real code these would be Kafka + a config service.
STUB_DIR = Path(__file__).parent / "stubs"
MESSAGE_FILE = STUB_DIR / "internal_message.json"
CONFIG_FILE = STUB_DIR / "config.json"

# ---------------------------------------------------------------------------
# Main — runs both consumer groups back-to-back with stub inputs
# ---------------------------------------------------------------------------

def main() -> int:
    # Load stub inputs.
    try:
        raw_message = json.loads(MESSAGE_FILE.read_text())
        config = json.loads(CONFIG_FILE.read_text())
    except FileNotFoundError as e:
        print(f"ERROR: stub file not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: stub file is not valid JSON: {e}", file=sys.stderr)
        return 1

    # Consumer Group 1: internal → per-destination transformed messages
    print("=" * 72)
    print("Consumer Group 1 — processing one internal message")
    print("=" * 72)

    try:
        outputs = process_internal_message(raw_message, config)
    except ValidationError as e:
        print(f"[validate] FAILED: {e} — would DLQ in real impl", file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"[config] FAILED: {e} — would retry in real impl", file=sys.stderr)
        return 3

    print(f"\n→ {len(outputs)} transformed message(s) published to kafka2")

    # Consumer Group 2: deliver each transformed message to its CRM
    print("\n" + "=" * 72)
    print("Consumer Group 2 — delivering transformed messages to external systems")
    print("=" * 72)

    for out in outputs:
        process_consumer_group2_message(out)

    # Final state snapshot
    print("\n" + "-" * 72)
    print(f"Sync state: {len(SYNC_STATE)} entries")
    for (event_id, dest_id), state in SYNC_STATE.items():
        print(f"  ({event_id}, {dest_id}) → {state}")
    print(f"DLQ: {len(DLQ)} entries")
    for entry in DLQ:
        print(f"  {entry}")

    return 0


if __name__ == "__main__":
    sys.exit(main())