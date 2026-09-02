from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from magic.domain import UnitSnapshot  # noqa: E402
from magic.pricing import PricingEngine  # noqa: E402

app = FastAPI(title="MAGIC CRM Pricing API", version="0.2.0")


class RecommendationRequest(BaseModel):
    project: str = "Demo Project"
    unit_code: str = "1204"
    typology: str = "2D"
    current_price: float = 615000
    days_in_stock: int = 45
    stock_units_typology: int = 4
    sales_30d_typology: int = 2
    separations_30d_typology: int = 2
    target_gap_pct: float = 0.024
    max_increase_pct: float = 0.03


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "magic-pricing"}


@app.post("/api/recommendation")
def recommendation(payload: RecommendationRequest) -> dict:
    snapshot = UnitSnapshot(**payload.model_dump())
    result = PricingEngine().recommend(snapshot)
    return result.model_dump(mode="json")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MAGIC Pricing</title>
  <style>
    body{font-family:Inter,system-ui,sans-serif;background:#0b0d12;color:#f4f4f5;margin:0;padding:40px}
    main{max-width:920px;margin:auto}.card{background:#151821;border:1px solid #272a35;border-radius:18px;padding:24px;margin:16px 0}
    h1{font-size:32px;margin-bottom:6px}.muted{color:#a1a1aa}.ok{color:#86efac}code{background:#0f1118;padding:4px 7px;border-radius:7px}
  </style>
</head>
<body><main>
  <h1>MAGIC · Pricing Decision Engine</h1>
  <p class="muted">Vercel runtime activo. La consola Streamlit sigue siendo la interfaz local de análisis.</p>
  <div class="card"><h2 class="ok">API operativa</h2><p><code>GET /api/health</code></p><p><code>POST /api/recommendation</code></p></div>
  <div class="card"><h2>Siguiente capa</h2><p>Conectar un PostgreSQL accesible desde Internet mediante <code>DATABASE_URL</code> y publicar la consola web sobre esta API.</p></div>
</main></body></html>
"""
