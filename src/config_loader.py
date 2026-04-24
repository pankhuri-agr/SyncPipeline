from typing import Any
from src.errors import ConfigError


def fetch_destinations(
        config: dict[str, Any],
        tenant_id: str,
        record_type: str,
) -> list[dict[str, Any]]:
    """
    Look up config and destination external systems for (tenant_id, record_type).
    Returns a list of destination configs, each with at minimum {destination_id, provider, field_map}.

    Raises ConfigError if the tenant has no routing config at all (distinct
    from "tenant is configured to sync zero destinations," which is a valid case and returns []).
    """
    tenants_config = config.get("tenants")
    if not isinstance(tenants_config, dict):
        raise ConfigError("config.tenants must be an object keyed by tenant_id")

    tenant_config = tenants_config.get(tenant_id)
    if tenant_config is None:
        raise ConfigError(f"no routing config for tenant '{tenant_id}'")

    routes = tenant_config.get("routes", [])
    if not isinstance(routes, list):
        raise ConfigError(f"tenants.{tenant_id}.routes must be a list")

    # Filter routes that apply to this record_type.
    matching = [r for r in routes if r.get("record_type") == record_type]
    return matching