from typing import Any

from src.domain import TransformedMessage

# DLQ — in real impl a durable topic which can alert ops / oncall.
DLQ: list[dict[str, Any]] = []

def send_to_dlq(msg: TransformedMessage, reason: str) -> None:
    DLQ.append({"event_id": msg.event_id, "destination_id": msg.destination_id, "reason": reason})
    print(f"[dlq] event_id={msg.event_id} destination={msg.destination_id} reason={reason}")