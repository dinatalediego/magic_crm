from __future__ import annotations

import json

from magic.domain import UnitSnapshot
from magic.pricing import PricingEngine


def main() -> None:
    unit = UnitSnapshot(
        project="Demo Project",
        unit_code="1204",
        typology="2D",
        current_price=615000,
        days_in_stock=45,
        stock_units_typology=4,
        sales_30d_typology=2,
        separations_30d_typology=2,
        benchmark_price=635000,
        target_gap_pct=0.024,
        max_increase_pct=0.03,
    )
    recommendation = PricingEngine().recommend(unit)
    print(json.dumps(recommendation.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
