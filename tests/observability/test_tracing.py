"""Tests for observability.tracing — OTel tracer factory."""

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from observability.tracing import configure_tracing, get_tracer, reset_for_testing


def setup_function() -> None:
    reset_for_testing()


def teardown_function() -> None:
    reset_for_testing()


def test_configure_returns_provider() -> None:
    exporter = InMemorySpanExporter()
    provider = configure_tracing(exporter=exporter)
    assert provider is not None


def test_configure_is_idempotent() -> None:
    exporter = InMemorySpanExporter()
    p1 = configure_tracing(exporter=exporter)
    p2 = configure_tracing(exporter=exporter)
    assert p1 is p2


def test_get_tracer_returns_tracer() -> None:
    tracer = get_tracer("test.tracer")
    assert tracer is not None


def test_spans_are_captured_by_in_memory_exporter() -> None:
    exporter = InMemorySpanExporter()
    configure_tracing(exporter=exporter)

    tracer = get_tracer("test.tracer")
    with tracer.start_as_current_span("rag.ask") as span:
        span.set_attribute("rag.track", "foundry")
        span.set_attribute("rag.question_length", 42)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "rag.ask"
    assert spans[0].attributes is not None
    assert spans[0].attributes.get("rag.track") == "foundry"
    assert spans[0].attributes.get("rag.question_length") == 42


def test_nested_spans_captured() -> None:
    exporter = InMemorySpanExporter()
    configure_tracing(exporter=exporter)

    tracer = get_tracer("test.nested")
    with tracer.start_as_current_span("rag.ask"):
        with tracer.start_as_current_span("rag.generate") as gen_span:
            gen_span.set_attribute("rag.model", "gpt-4o")

    spans = exporter.get_finished_spans()
    names = [s.name for s in spans]
    assert "rag.ask" in names
    assert "rag.generate" in names


def test_get_tracer_works_before_configure() -> None:
    """get_tracer() must not raise even if configure_tracing() was never called."""
    tracer = get_tracer("pre.configure.tracer")
    with tracer.start_as_current_span("test.span"):
        pass  # should not raise
