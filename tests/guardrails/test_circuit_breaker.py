import pytest

from guardrails.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def test_opens_after_threshold_failures() -> None:
    breaker = CircuitBreaker(failure_threshold=2)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == "open"


def test_guard_raises_when_open() -> None:
    breaker = CircuitBreaker(failure_threshold=1)
    breaker.record_failure()
    with pytest.raises(CircuitBreakerOpenError):
        breaker.guard()


def test_half_open_resets_after_successes() -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_call_count=2)
    breaker.record_failure()
    breaker.attempt_reset()
    breaker.record_success()
    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.failure_count == 0
