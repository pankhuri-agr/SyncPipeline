from __future__ import annotations


from src.domain import TransformedMessage
from src.dao import SYNC_STATE, sync_state_get, sync_state_claim, sync_state_mark
from src.rate_limiter import rate_limit_try_acquire
from src.external_call import crm_send
from src.response_parser import classify_status
from src.dlq import send_to_dlq


def commit_offset_cg2(msg: TransformedMessage) -> None:
    print(f"[kafka2] commit event_id={msg.event_id} destination={msg.destination_id}")


def process_consumer_group2_message(msg: TransformedMessage) -> None:
    """
    Deliver one transformed message to its external system.

    Pipeline:
      1. Idempotency check — if already DELIVERED, skip and commit.
      2. Rate limit acquire — if no quota, back off; do not commit.
      3. Claim IN_FLIGHT — conditional state transition prevents races.
      4. CRM send — mocked in this impl.
      5. Classify outcome — uccess / retry / permanent.
      6. Persist state + commit offset (or DLQ for permanent failures).

    Returns nothing; side effects are on SYNC_STATE and DLQ.
    """
    ctx = f"event_id={msg.event_id} destination={msg.destination_id}"
    print(f"[cg2] received {ctx}")

    # Idempotency check
    state = sync_state_get(msg.event_id, msg.destination_id)
    if state and state["status"] == "DELIVERED":
        print(f"[idempotency] already DELIVERED; committing without resend  {ctx}")
        commit_offset_cg2(msg)
        return

    # Rate limit acquire — per (tenant, provider).
    if not rate_limit_try_acquire(msg.tenant_id, msg.provider):
        # Do NOT commit offset — the message stays on the partition and will
        # be re-polled.
        print(f"[rate_limit] no quota for tenant={msg.tenant_id} provider={msg.provider}; not committing  {ctx}")
        return

    # Claim IN_FLIGHT — prevents two workers from duplicate sending
    if not sync_state_claim(msg):
        print(f"[claim] lost race; skipping {ctx}")
        commit_offset_cg2(msg)
        return

    attempt = SYNC_STATE[(msg.event_id, msg.destination_id)]["attempts"]

    # Send to CRM
    outcome, provider_record_id = crm_send(msg)
    print(f"[crm] outcome={outcome} attempt={attempt}  {ctx}")

    # Classify
    decision = classify_status(outcome, attempt)

    if decision == "DONE":
        sync_state_mark(msg, "DELIVERED", provider_record_id=provider_record_id)
        print(f"  [state] DELIVERED provider_record_id={provider_record_id}  {ctx}")
        commit_offset_cg2(msg)
        return

    if decision == "PERMANENT":
        sync_state_mark(msg, "FAILED", last_error=outcome)
        send_to_dlq(msg, reason=outcome)
        commit_offset_cg2(msg)
        return

    # in all other cases message will be retried automatically when it will be polled by another consumer
    # hence not committed
    sync_state_mark(msg, "PENDING", last_error=outcome)
    print(f"[retry] scheduled for (attempt {attempt}); not committing  {ctx}")