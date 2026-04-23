from typing import Any
from src.errors import ValidationError
from src.domain import InboundMessage

REQUIRED_FIELDS = ("event_id", "tenant_id", "record_id", "record_type", "operation", "payload")
VALID_OPERATIONS = {"create", "update", "delete"}


def validate(raw: dict[str, Any]) -> InboundMessage:
    """
    Validate that required fields are present and well-typed.
    In production this would be a pydantic model.
    """
    for field in REQUIRED_FIELDS:
        if field not in raw:
            raise ValidationError(f"missing required field: {field}")

    if not isinstance(raw["payload"], dict):
        raise ValidationError(f"payload must be a dict, got {type(raw['payload'])}")

    if raw["operation"] not in VALID_OPERATIONS:
        raise ValidationError(
            f"invalid operation '{raw['operation']}'; must be one of {VALID_OPERATIONS}"
        )

    return InboundMessage(
        event_id=raw["event_id"],
        tenant_id=raw["tenant_id"],
        record_id=raw["record_id"],
        record_type=raw["record_type"],
        operation=raw["operation"],
        payload=raw["payload"],
        source_version=raw.get("source_version"), # because source version can be none
    )
