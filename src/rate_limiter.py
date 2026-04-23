from typing import Any
import time

# Token bucket per (tenant, provider). Values: {tokens, capacity, rate, last_refill}.
RATE_LIMITS: dict[tuple[str, str], dict[str, Any]] = {}

def rate_limit_try_acquire(tenant_id: str, provider: str) -> bool:
    """
    Stub token bucket. 10 tokens, refills 5/sec.
    In actual implementation - redis will be used preferrably with lua scripting.
    """
    key = (tenant_id, provider)
    now = time.time()
    bucket = RATE_LIMITS.get(key)
    if bucket is None:
        bucket = {"tokens": 10.0, "capacity": 10.0, "rate": 5.0, "last_refill": now}
        RATE_LIMITS[key] = bucket
    # Refill tokens in bucket
    elapsed = now - bucket["last_refill"]
    bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + elapsed * bucket["rate"])
    bucket["last_refill"] = now
    if bucket["tokens"] >= 1.0:
        bucket["tokens"] -= 1.0
        return True
    return False

