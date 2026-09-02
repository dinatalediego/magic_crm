from magic.domain import UnitSnapshot
from magic.pricing import AbsorptionEngine, PricingEngine


def strong_unit(**overrides):
    values = dict(
        project="Torre Demo",
        unit_code="1204",
        typology="2D",
        current_price=615000,
        days_in_stock=45,
        stock_units_typology=4,
        sales_30d_typology=2,
        separations_30d_typology=2,
        target_gap_pct=0.024,
        max_increase_pct=0.03,
    )
    values.update(overrides)
    return UnitSnapshot(**values)


def test_absorption_score_is_bounded_and_explainable():
    result = AbsorptionEngine().score(strong_unit())
    assert 0 <= result.score <= 100
    assert result.score > 75
    assert "strong_sales_velocity" in result.reason_codes
    assert "low_typology_stock" in result.reason_codes


def test_pricing_engine_recommends_increase_for_strong_absorption():
    result = PricingEngine().recommend(strong_unit())
    assert result.recommended_price > result.current_price
    assert result.increase_pct <= 0.03
    assert "price_increase_opportunity" in result.reason_codes


def test_benchmark_is_a_hard_ceiling():
    result = PricingEngine().recommend(strong_unit(benchmark_price=620000))
    assert result.recommended_price == 620000
    assert "benchmark_ceiling" in result.constraints_applied


def test_commercial_max_price_is_a_hard_ceiling():
    result = PricingEngine().recommend(strong_unit(max_price=618000))
    assert result.recommended_price == 618000
    assert "commercial_max_price" in result.constraints_applied


def test_weak_absorption_does_not_force_increase():
    unit = strong_unit(
        stock_units_typology=20,
        sales_30d_typology=0,
        separations_30d_typology=0,
        days_in_stock=220,
        target_gap_pct=0,
    )
    result = PricingEngine().recommend(unit)
    assert result.recommended_price == unit.current_price
    assert "hold_price" in result.reason_codes
