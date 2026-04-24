from __future__ import annotations

import pytest
import time

from src.rate_limiter import rate_limit_try_acquire, RATE_LIMITS


def teardown_function():
    # clear bucket after each test
    RATE_LIMITS.clear()

def test_first_call_always_succeeds():
    assert rate_limit_try_acquire("a", "abc") is True


def test_bucket_limit_exhaustion():
    # 10 shoudl pass
    for i in range(10):
        assert rate_limit_try_acquire("a", "abc") is True
    # 11th should be denied
    assert rate_limit_try_acquire("a", "abc") is False


def test_tenant_isolation():
    # utilize bucket for a
    for _ in range(10):
        rate_limit_try_acquire("a", "abc")

    # test for b
    assert rate_limit_try_acquire("b", "abc") is True


def test_same_tenant_different_crm():
    for _ in range(10):
        rate_limit_try_acquire("a", "abc")

    # same tenant on hubspot bucket is separate, should still pass
    assert rate_limit_try_acquire("a", "xyz") is True


def test_token_refill():
    for _ in range(10):
        rate_limit_try_acquire("a", "abc")

    assert rate_limit_try_acquire("a", "abc") is False

    # rate is 5 tokens/sec, 0.3s → ~1.5 token
    time.sleep(0.3)

    assert rate_limit_try_acquire("a", "abc") is True


