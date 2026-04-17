"""Tests for the shared cost model estimator."""

from decimal import Decimal

import pytest

from cost_model.estimator import CostEstimate, CostEstimator, MonthlyProjection, RequestProfile


@pytest.fixture()
def estimator() -> CostEstimator:
    return CostEstimator()


@pytest.fixture()
def typical_profile() -> RequestProfile:
    """Realistic profile for a single agentic RAG request."""
    return RequestProfile(
        input_tokens=1_500,
        output_tokens=500,
        embedding_tokens=512,
        search_queries=2,
    )


# ── estimate_request ──────────────────────────────────────────────────────────

class TestEstimateRequest:
    def test_returns_cost_estimate(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.estimate_request(typical_profile)
        assert isinstance(result, CostEstimate)

    def test_total_is_sum_of_breakdown(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.estimate_request(typical_profile)
        b = result.breakdown
        expected = b.openai_input_usd + b.openai_output_usd + b.embedding_usd + b.search_usd
        assert result.total_usd == expected

    def test_zero_profile_costs_nothing(self, estimator: CostEstimator) -> None:
        zero = RequestProfile(search_queries=0)
        result = estimator.estimate_request(zero)
        assert result.total_usd == Decimal("0")

    def test_input_tokens_cost(self, estimator: CostEstimator) -> None:
        # 1 000 000 input tokens should cost exactly $5.00 (GPT-4o default)
        profile = RequestProfile(input_tokens=1_000_000)
        result = estimator.estimate_request(profile)
        assert result.breakdown.openai_input_usd == Decimal("5.00")

    def test_output_tokens_cost(self, estimator: CostEstimator) -> None:
        # 1 000 000 output tokens should cost exactly $15.00
        profile = RequestProfile(output_tokens=1_000_000)
        result = estimator.estimate_request(profile)
        assert result.breakdown.openai_output_usd == Decimal("15.00")

    def test_embedding_tokens_cost(self, estimator: CostEstimator) -> None:
        # 1 000 000 embedding tokens should cost $0.13
        profile = RequestProfile(embedding_tokens=1_000_000)
        result = estimator.estimate_request(profile)
        assert result.breakdown.embedding_usd == Decimal("0.13")

    def test_search_queries_cost(self, estimator: CostEstimator) -> None:
        # 1 000 queries should cost $0.001
        profile = RequestProfile(search_queries=1_000)
        result = estimator.estimate_request(profile)
        assert result.breakdown.search_usd == Decimal("0.001")

    def test_total_is_positive_for_typical_request(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.estimate_request(typical_profile)
        assert result.total_usd > Decimal("0")

    def test_profile_attached_to_estimate(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.estimate_request(typical_profile)
        assert result.profile is typical_profile

    def test_formatted_summary_contains_total(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.estimate_request(typical_profile)
        assert "Total" in result.formatted_summary

    def test_custom_prices_are_used(self) -> None:
        custom = CostEstimator(
            gpt4o_input_per_1m=Decimal("10.00"),
            gpt4o_output_per_1m=Decimal("30.00"),
        )
        profile = RequestProfile(input_tokens=1_000_000)
        result = custom.estimate_request(profile)
        assert result.breakdown.openai_input_usd == Decimal("10.00")


# ── project_monthly ───────────────────────────────────────────────────────────

class TestProjectMonthly:
    def test_returns_monthly_projection(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.project_monthly(typical_profile, daily_requests=100)
        assert isinstance(result, MonthlyProjection)

    def test_monthly_cost_scales_with_requests(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        low = estimator.project_monthly(typical_profile, daily_requests=100)
        high = estimator.project_monthly(typical_profile, daily_requests=200)
        # Doubling requests should at most differ by $0.01 from exact doubling
        # due to rounding at two decimal places.
        assert abs(high.monthly_usd - low.monthly_usd * 2) <= Decimal("0.01")

    def test_zero_requests_costs_nothing(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.project_monthly(typical_profile, daily_requests=0)
        assert result.monthly_usd == Decimal("0.00")

    def test_monthly_summary_contains_month_marker(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        result = estimator.project_monthly(typical_profile, daily_requests=50)
        assert "/month" in result.formatted_summary

    def test_days_per_month_is_configurable(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        month30 = estimator.project_monthly(typical_profile, daily_requests=100, days_per_month=30)
        month31 = estimator.project_monthly(typical_profile, daily_requests=100, days_per_month=31)
        assert month31.monthly_usd > month30.monthly_usd


# ── is_within_budget ──────────────────────────────────────────────────────────

class TestIsWithinBudget:
    def test_within_large_budget(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        assert estimator.is_within_budget(
            typical_profile,
            daily_requests=10,
            monthly_budget_usd=Decimal("1000.00"),
        )

    def test_exceeds_tiny_budget(
        self, estimator: CostEstimator, typical_profile: RequestProfile
    ) -> None:
        assert not estimator.is_within_budget(
            typical_profile,
            daily_requests=100_000,
            monthly_budget_usd=Decimal("0.01"),
        )

    def test_exact_budget_is_within(self, estimator: CostEstimator) -> None:
        # 1 input token costs $5 / 1M = $0.000005
        # 1 request/day × 30 days = 30 × $0.000005 = $0.00015
        profile = RequestProfile(input_tokens=1)
        projection = estimator.project_monthly(profile, daily_requests=1)
        assert estimator.is_within_budget(
            profile,
            daily_requests=1,
            monthly_budget_usd=projection.monthly_usd,
        )
