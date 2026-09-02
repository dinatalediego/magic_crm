from __future__ import annotations

from dataclasses import dataclass

from magic.domain import AbsorptionResult, PricingRecommendation, UnitSnapshot


@dataclass(frozen=True)
class AbsorptionWeights:
    sales_velocity: float = 0.45
    separation_velocity: float = 0.20
    scarcity: float = 0.20
    aging: float = 0.15


class AbsorptionEngine:
    """Transparent baseline model for typology-level absorption strength."""

    def __init__(self, weights: AbsorptionWeights | None = None) -> None:
        self.weights = weights or AbsorptionWeights()

    def score(self, unit: UnitSnapshot) -> AbsorptionResult:
        stock = max(unit.stock_units_typology, 1)
        sales_rate = unit.sales_30d_typology / stock
        separation_rate = unit.separations_30d_typology / stock

        sales_component = min(sales_rate / 0.50, 1.0)
        separation_component = min(separation_rate / 0.75, 1.0)
        scarcity_component = 1.0 / (1.0 + max(stock - 1, 0) / 8.0)
        aging_component = max(0.0, 1.0 - min(unit.days_in_stock / 240.0, 1.0))

        raw = (
            sales_component * self.weights.sales_velocity
            + separation_component * self.weights.separation_velocity
            + scarcity_component * self.weights.scarcity
            + aging_component * self.weights.aging
        )
        score = round(raw * 100, 2)

        reasons: list[str] = []
        if sales_rate >= 0.25:
            reasons.append("strong_sales_velocity")
        if separation_rate >= 0.35:
            reasons.append("strong_separation_velocity")
        if stock <= 4:
            reasons.append("low_typology_stock")
        if unit.days_in_stock >= 120:
            reasons.append("aging_inventory")
        if not reasons:
            reasons.append("neutral_absorption")

        return AbsorptionResult(
            score=score,
            monthly_absorption_rate=round(sales_rate, 4),
            demand_signal=round(separation_rate, 4),
            reason_codes=reasons,
        )


class PricingEngine:
    """Converts observable commercial signals into a constrained recommendation."""

    def __init__(self, absorption_engine: AbsorptionEngine | None = None) -> None:
        self.absorption_engine = absorption_engine or AbsorptionEngine()

    def recommend(self, unit: UnitSnapshot) -> PricingRecommendation:
        absorption = self.absorption_engine.score(unit)
        signal = absorption.score / 100.0

        # Baseline opportunity: strongest absorption can consume the configured cap.
        desired_increase = max(0.0, unit.max_increase_pct * ((signal - 0.35) / 0.65))
        desired_increase += max(0.0, min(unit.target_gap_pct, unit.max_increase_pct)) * 0.25
        desired_increase = min(desired_increase, unit.max_increase_pct)

        model_price = unit.current_price * (1.0 + desired_increase)
        recommended = model_price
        constraints: list[str] = []

        if unit.benchmark_price is not None and recommended > unit.benchmark_price:
            recommended = unit.benchmark_price
            constraints.append("benchmark_ceiling")
        if unit.max_price is not None and recommended > unit.max_price:
            recommended = unit.max_price
            constraints.append("commercial_max_price")
        if unit.min_price is not None and recommended < unit.min_price:
            recommended = unit.min_price
            constraints.append("commercial_min_price")

        recommended = round(recommended, 2)
        increase_pct = round(recommended / unit.current_price - 1.0, 6)
        confidence = round(min(0.95, 0.55 + abs(signal - 0.5) * 0.5), 3)

        reasons = list(absorption.reason_codes)
        if unit.target_gap_pct > 0:
            reasons.append("project_target_gap")
        if increase_pct <= 0:
            reasons.append("hold_price")
        else:
            reasons.append("price_increase_opportunity")

        return PricingRecommendation(
            project=unit.project,
            unit_code=unit.unit_code,
            typology=unit.typology,
            current_price=unit.current_price,
            model_price=round(model_price, 2),
            recommended_price=recommended,
            increase_pct=increase_pct,
            absorption_score=absorption.score,
            confidence=confidence,
            reason_codes=reasons,
            constraints_applied=constraints,
            metadata={
                "monthly_absorption_rate": absorption.monthly_absorption_rate,
                "demand_signal": absorption.demand_signal,
            },
        )
