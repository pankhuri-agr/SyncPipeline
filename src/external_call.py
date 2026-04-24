from __future__ import annotations
import random

from src.domain import TransformedMessage

def crm_send(msg: TransformedMessage) -> tuple[str, str | None]:
    """
    Mock CRM external call.
    Response is returned based on random number generated.
    """
    # Deterministic-ish outcome for the demo: mostly success, some failures.

    random.seed(10)  # deterministic demo outcomes # comment this for different results
    r = random.random()
    # print(r)
    if r < 0.75:
        return "SUCCESS", f"{msg.provider}_{msg.event_id[:8]}"
    if r < 0.85:
        return "RATE_LIMITED", None
    if r < 0.95:
        return "TRANSIENT", None
    return "PERMANENT", None
