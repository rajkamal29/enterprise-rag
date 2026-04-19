"""Tests for guardrails.content_safety — ContentSafetyGuardrail."""

import pytest

from guardrails.content_safety import ContentSafetyError, ContentSafetyGuardrail


def test_noop_guardrail_passes_all_inputs() -> None:
    """No endpoint configured → check() should never raise."""
    guard = ContentSafetyGuardrail()
    guard.check("How do I deploy Azure OpenAI?")
    guard.check("What is the capital of France?")


def test_noop_guardrail_is_not_enabled() -> None:
    guard = ContentSafetyGuardrail()
    assert guard.is_enabled is False


def test_from_env_returns_noop_when_env_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_CONTENT_SAFETY_ENDPOINT", raising=False)
    guard = ContentSafetyGuardrail.from_env()
    assert guard.is_enabled is False


def test_from_env_reads_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_SAFETY_SEVERITY_THRESHOLD", "4")
    monkeypatch.delenv("AZURE_CONTENT_SAFETY_ENDPOINT", raising=False)
    guard = ContentSafetyGuardrail.from_env()
    # Threshold should be honoured even in no-op mode.
    assert guard._severity_threshold == 4  # noqa: SLF001


def test_content_safety_error_message() -> None:
    err = ContentSafetyError(category="Hate", severity=4)
    assert "Hate" in str(err)
    assert "4" in str(err)
    assert err.category == "Hate"
    assert err.severity == 4


def test_content_safety_error_is_value_error() -> None:
    err = ContentSafetyError(category="Violence", severity=2)
    assert isinstance(err, ValueError)


class _FakeResult:
    """Simulate one category result returned by the Azure SDK."""

    def __init__(self, category: str, severity: int) -> None:
        self.category = category
        self.severity = severity


class _FakeResponse:
    def __init__(self, results: list[_FakeResult]) -> None:
        self.categories_analysis = results


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def analyze_text(self, request: object) -> _FakeResponse:
        return self._response


def _make_guard_with_fake_client(
    results: list[_FakeResult], threshold: int = 2
) -> ContentSafetyGuardrail:
    """Build a guardrail with a fake client injected."""
    guard = ContentSafetyGuardrail.__new__(ContentSafetyGuardrail)
    guard._endpoint = "https://fake.cognitiveservices.azure.com/"  # noqa: SLF001
    guard._severity_threshold = threshold  # noqa: SLF001
    guard._client = _FakeClient(_FakeResponse(results))  # noqa: SLF001
    return guard


def test_raises_when_severity_meets_threshold() -> None:
    guard = _make_guard_with_fake_client([_FakeResult("Hate", 2)], threshold=2)
    with pytest.raises(ContentSafetyError) as exc_info:
        guard.check("some hateful text")
    assert exc_info.value.category == "Hate"
    assert exc_info.value.severity == 2


def test_raises_on_first_blocked_category() -> None:
    guard = _make_guard_with_fake_client(
        [_FakeResult("Safe", 0), _FakeResult("Violence", 4)],
        threshold=2,
    )
    with pytest.raises(ContentSafetyError) as exc_info:
        guard.check("some violent text")
    assert exc_info.value.category == "Violence"


def test_passes_when_severity_below_threshold() -> None:
    guard = _make_guard_with_fake_client([_FakeResult("Hate", 0)], threshold=2)
    guard.check("safe text")  # should not raise


def test_passes_all_safe_categories() -> None:
    guard = _make_guard_with_fake_client(
        [_FakeResult("Hate", 0), _FakeResult("Violence", 0), _FakeResult("Sexual", 0)],
        threshold=2,
    )
    guard.check("What is retrieval augmented generation?")
