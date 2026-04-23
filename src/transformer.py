from typing import Any
from src.errors import TransformError
from src.domain import InboundMessage, TransformedMessage


def transform(
        msg: InboundMessage,
        destination: dict[str, Any],
) -> TransformedMessage:
    """
    Map internal payload fields to the destination's expected shape using
    the field_map from config. Missing required fields → TransformError.
    """
    destination_id = destination.get("destination_id")
    provider = destination.get("provider")
    field_map = destination.get("field_map", {})

    if not destination_id or not provider:
        raise TransformError(f"destination missing destination_id or provider: {destination}")

    provider_payload: dict[str, Any] = {}
    for internal_field, external_field in field_map.items():
        # Support dotted paths (e.g., "fields.email") for nested lookups.
        value = _get_nested(msg.payload, internal_field)
        if value is None:
            # Missing field in payload — only fail if the destination marked
            # it required. Minor nicety that makes the stub feel real.
            if internal_field in destination.get("required_fields", []):
                raise TransformError(
                    f"destination '{destination_id}' requires field '{internal_field}', "
                    f"not present in payload"
                )
            continue
        provider_payload[external_field] = value

    return TransformedMessage(
        event_id=msg.event_id,
        tenant_id=msg.tenant_id,
        destination_id=destination_id,
        provider=provider,
        record_id=msg.record_id,
        operation=msg.operation,
        provider_payload=provider_payload,
        source_version=msg.source_version,
    )


def _get_nested(obj: dict[str, Any], path: str) -> Any:
    """Support 'a.b.c' style paths for field_map lookups."""
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur
