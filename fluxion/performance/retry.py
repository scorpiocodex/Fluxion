"""Retry classifier — categorises errors and determines retry strategy."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class RetryVerdict(str, enum.Enum):
    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_BACKOFF = "retry_backoff"
    RETRY_ALTERNATE = "retry_alternate"
    FATAL = "fatal"


@dataclass(frozen=True)
class RetryDecision:
    verdict: RetryVerdict
    delay_sec: float = 0.0
    reason: str = ""


# Status codes that are always retryable
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
# Status codes that should never be retried
_FATAL_STATUS = {400, 401, 403, 404, 405, 410, 451}


class RetryClassifier:
    """Classifies errors and HTTP responses to determine retry behaviour."""

    def __init__(
        self,
        max_retries: int = 3,
        base_backoff: float = 1.0,
        max_backoff: float = 30.0,
    ) -> None:
        self._max_retries = max_retries
        self._base_backoff = base_backoff
        self._max_backoff = max_backoff

    @property
    def max_retries(self) -> int:
        return self._max_retries

    def classify_status(self, status_code: int, attempt: int) -> RetryDecision:
        """Classify an HTTP status code."""
        if 200 <= status_code < 300:
            return RetryDecision(RetryVerdict.FATAL, reason="Success — no retry needed")

        if status_code in _FATAL_STATUS:
            return RetryDecision(
                RetryVerdict.FATAL,
                reason=f"HTTP {status_code} is not retryable",
            )

        if status_code == 429:
            delay = min(self._base_backoff * (2**attempt), self._max_backoff)
            return RetryDecision(
                RetryVerdict.RETRY_BACKOFF,
                delay_sec=delay,
                reason="Rate limited (429)",
            )

        if status_code in _RETRYABLE_STATUS:
            delay = min(self._base_backoff * (2 ** (attempt - 1)), self._max_backoff)
            return RetryDecision(
                RetryVerdict.RETRY_BACKOFF,
                delay_sec=delay,
                reason=f"HTTP {status_code} — retryable server error",
            )

        return RetryDecision(
            RetryVerdict.RETRY_BACKOFF,
            delay_sec=self._base_backoff,
            reason=f"Unexpected HTTP {status_code}",
        )

    def classify_exception(self, exc: Exception, attempt: int) -> RetryDecision:
        """Classify a connection-level exception."""
        exc_name = type(exc).__name__.lower()

        # Timeouts → retry with backoff
        if "timeout" in exc_name or "timedout" in str(exc).lower():
            delay = min(self._base_backoff * (2**attempt), self._max_backoff)
            return RetryDecision(
                RetryVerdict.RETRY_BACKOFF,
                delay_sec=delay,
                reason=f"Timeout: {exc}",
            )

        # Connection refused / reset → immediate retry
        if any(k in exc_name for k in ("refused", "reset", "broken", "aborted")):
            return RetryDecision(
                RetryVerdict.RETRY_IMMEDIATE,
                delay_sec=0.5,
                reason=f"Connection error: {exc}",
            )

        # DNS failures → fatal
        if "resolve" in exc_name or "dns" in exc_name or "gaierror" in exc_name:
            return RetryDecision(
                RetryVerdict.FATAL,
                reason=f"DNS resolution failure: {exc}",
            )

        # SSL errors → fatal
        if "ssl" in exc_name or "certificate" in exc_name:
            return RetryDecision(
                RetryVerdict.FATAL,
                reason=f"TLS/SSL error: {exc}",
            )

        delay = min(self._base_backoff * (2**attempt), self._max_backoff)
        return RetryDecision(
            RetryVerdict.RETRY_BACKOFF,
            delay_sec=delay,
            reason=f"Unknown error: {exc}",
        )

    def should_retry(self, decision: RetryDecision, attempt: int) -> bool:
        """Return True if the request should be retried."""
        if decision.verdict == RetryVerdict.FATAL:
            return False
        return attempt < self._max_retries
