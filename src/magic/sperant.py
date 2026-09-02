from __future__ import annotations

from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field


class SperantWebhookEvent(BaseModel):
    event_type: str
    event_id: str | None = None
    occurred_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SperantGateway(Protocol):
    def get_unit(self, unit_code: str) -> dict[str, Any]: ...

    def push_pricing_recommendation(
        self, unit_code: str, recommended_price: float, metadata: dict[str, Any]
    ) -> dict[str, Any]: ...


class HttpSperantGateway:
    """HTTP adapter kept outside the pricing core.

    Endpoint paths are intentionally configurable because Sperant account/API
    contracts can differ. Real credentials must be supplied by environment.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        unit_path: str = "/units/{unit_code}",
        recommendation_path: str = "/units/{unit_code}/pricing-recommendation",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.unit_path = unit_path
        self.recommendation_path = recommendation_path
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout_seconds,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )

    def get_unit(self, unit_code: str) -> dict[str, Any]:
        response = self.client.get(self.unit_path.format(unit_code=unit_code))
        response.raise_for_status()
        return response.json()

    def push_pricing_recommendation(
        self, unit_code: str, recommended_price: float, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        response = self.client.post(
            self.recommendation_path.format(unit_code=unit_code),
            json={"recommended_price": recommended_price, "metadata": metadata},
        )
        response.raise_for_status()
        return response.json()


def classify_webhook(event: SperantWebhookEvent) -> str:
    """Map CRM events to the minimum recomputation domain."""
    event = event.event_type.lower()
    if any(token in event for token in ("sale", "venta", "separation", "separacion", "unit")):
        return "recompute_pricing"
    if any(token in event for token in ("lead", "proforma")):
        return "refresh_demand_features"
    return "store_only"
