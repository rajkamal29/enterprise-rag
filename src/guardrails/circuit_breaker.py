from __future__ import annotations

from dataclasses import dataclass


class CircuitBreakerOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    reset_call_count: int = 2
    failure_count: int = 0
    state: str = "closed"
    success_after_open: int = 0

    def allow_request(self) -> bool:
        return self.state != "open"

    def record_success(self) -> None:
        if self.state == "half-open":
            self.success_after_open += 1
            if self.success_after_open >= self.reset_call_count:
                self.state = "closed"
                self.failure_count = 0
                self.success_after_open = 0
            return

        self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.success_after_open = 0
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def attempt_reset(self) -> None:
        if self.state == "open":
            self.state = "half-open"
            self.success_after_open = 0

    def guard(self) -> None:
        if not self.allow_request():
            raise CircuitBreakerOpenError("Circuit breaker is open.")
