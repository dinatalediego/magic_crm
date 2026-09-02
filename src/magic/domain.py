from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class ModelStatus(StrEnum):
    RESEARCH = "research"
    CHALLENGER = "challenger"
    CHAMPION = "champion"
    RETIRED = "retired"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    OBSERVED = "observed"


class UnitSnapshot(BaseModel):
    project: str
    unit_code: str
    typology: str
    current_price: float = Field(gt=0)
    days_in_stock: int = Field(ge=0)
    stock_units_typology: int = Field(ge=0)
    sales_30d_typology: int = Field(ge=0)
    separations_30d_typology: int = Field(ge=0)
    benchmark_price: float | None = Field(default=None, gt=0)
    target_gap_pct: float = 0.0
    max_increase_pct: float = Field(default=0.03, ge=0, le=0.25)
    min_price: float | None = Field(default=None, gt=0)
    max_price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "UnitSnapshot":
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot exceed max_price")
        return self


class AbsorptionResult(BaseModel):
    score: float = Field(ge=0, le=100)
    monthly_absorption_rate: float = Field(ge=0)
    demand_signal: float = Field(ge=0)
    reason_codes: list[str]


class PricingRecommendation(BaseModel):
    recommendation_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    project: str
    unit_code: str
    typology: str
    current_price: float
    model_price: float
    recommended_price: float
    increase_pct: float
    absorption_score: float
    confidence: float = Field(ge=0, le=1)
    reason_codes: list[str]
    constraints_applied: list[str]
    model_name: str = "absorption_rule_engine"
    model_version: str = "0.1.0"
    decision_status: DecisionStatus = DecisionStatus.PROPOSED
    metadata: dict[str, Any] = Field(default_factory=dict)
