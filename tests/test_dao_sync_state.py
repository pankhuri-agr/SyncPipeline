import pytest
from src.dao import sync_state_get, sync_state_claim, sync_state_mark, SYNC_STATE
from src.domain import TransformedMessage

def teardown_function():
    SYNC_STATE.clear()


def make_msg(event_id="evt_1", destination_id="dest1"):
    return TransformedMessage(
        event_id=event_id,
        tenant_id="id1",
        destination_id=destination_id,
        provider="abc",
        record_id="rec_1",
        operation="update",
        provider_payload={"Email": "a@b.com"},
        source_version="v1",
    )

def test_get_returns_none_if_never_seen():
    assert sync_state_get("new", "dest1") is None

def test_get_returns_state_after_claim():
    msg = make_msg()
    sync_state_claim(msg)
    state = sync_state_get(msg.event_id, msg.destination_id)
    assert state is not None
    assert state["status"] == "IN_FLIGHT"

def test_claim_succeeds_for_new_message():
    msg = make_msg()
    assert sync_state_claim(msg) is True

def test_claim_sets_status_to_in_flight():
    msg = make_msg()
    sync_state_claim(msg)
    assert SYNC_STATE[(msg.event_id, msg.destination_id)]["status"] == "IN_FLIGHT"

def test_claim_blocked_if_already_in_flight():
    msg = make_msg()
    # first call is success
    assert sync_state_claim(msg) is True
    # second / parallel call fails
    assert sync_state_claim(msg) is False