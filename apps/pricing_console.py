from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from magic.domain import DecisionStatus, UnitSnapshot
from magic.pricing import PricingEngine
from magic.warehouse import PricingWarehouse

DECISION_LOG = Path("data/local/pricing_decisions.jsonl")


def money(value: float) -> str:
    return f"S/ {value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def append_decision(recommendation, status: DecisionStatus, note: str) -> None:
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    payload = recommendation.model_dump(mode="json")
    payload["decision_status"] = status.value
    payload["decision_note"] = note.strip() or None
    payload["decided_at"] = datetime.now(UTC).isoformat()
    with DECISION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_decisions() -> list[dict]:
    if not DECISION_LOG.exists():
        return []
    with DECISION_LOG.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


st.set_page_config(page_title="MAGIC Pricing Console", page_icon="◈", layout="wide")
st.title("MAGIC · Pricing Console")
st.caption("Warehouse → recomendación → decisión → memoria. Sin ejecución automática en CRM.")

warehouse = PricingWarehouse()
warehouse_status = warehouse.status()
source_default = 0 if warehouse_status.connected and warehouse_status.row_count > 0 else 1

with st.sidebar:
    st.header("Fuente")
    source = st.radio(
        "Datos de pricing",
        ["Data warehouse", "Demo manual"],
        index=source_default,
        help="Data warehouse lee features.pricing_unit_snapshot usando DATABASE_URL.",
    )

    if source == "Data warehouse":
        if warehouse_status.connected:
            st.success(warehouse_status.message)
        else:
            st.error(warehouse_status.message)
        st.caption(f"Snapshots disponibles: {warehouse_status.row_count}")

if source == "Data warehouse":
    if not warehouse_status.connected or warehouse_status.row_count == 0:
        st.warning(
            "La consola no hará fallback silencioso al demo. Configura DATABASE_URL y carga "
            "features.pricing_unit_snapshot para operar con datos reales."
        )
        st.stop()

    snapshots = warehouse.latest_snapshots()
    projects = sorted({row.project for row in snapshots})
    with st.sidebar:
        st.header("Unidad real")
        project_filter = st.selectbox("Proyecto", projects)
        project_rows = [row for row in snapshots if row.project == project_filter]
        unit_code = st.selectbox(
            "Código de unidad",
            [row.unit_code for row in project_rows],
        )
        snapshot = next(row for row in project_rows if row.unit_code == unit_code)
        st.caption(f"Tipología: {snapshot.typology}")
        st.caption(f"Precio actual: {money(snapshot.current_price)}")
        max_increase_pct = st.number_input(
            "Máximo aumento (%)", min_value=0.0, value=3.0, step=0.1
        ) / 100
        snapshot = snapshot.model_copy(update={"max_increase_pct": max_increase_pct})
else:
    with st.sidebar:
        st.header("Unidad")
        project = st.text_input("Proyecto", "Demo Project")
        unit_code = st.text_input("Código de unidad", "1204")
        typology = st.text_input("Tipología", "2D")
        current_price = st.number_input("Precio actual", min_value=1.0, value=615000.0, step=1000.0)

        st.header("Señales comerciales")
        days_in_stock = st.number_input("Días en stock", min_value=0, value=45, step=1)
        stock_units = st.number_input("Stock tipología", min_value=0, value=4, step=1)
        sales_30d = st.number_input("Ventas 30d tipología", min_value=0, value=2, step=1)
        separations_30d = st.number_input("Separaciones 30d tipología", min_value=0, value=2, step=1)
        target_gap_pct = st.number_input("Gap a meta (%)", value=2.4, step=0.1) / 100
        max_increase_pct = st.number_input("Máximo aumento (%)", min_value=0.0, value=3.0, step=0.1) / 100

    snapshot = UnitSnapshot(
        project=project,
        unit_code=unit_code,
        typology=typology,
        current_price=current_price,
        days_in_stock=int(days_in_stock),
        stock_units_typology=int(stock_units),
        sales_30d_typology=int(sales_30d),
        separations_30d_typology=int(separations_30d),
        target_gap_pct=target_gap_pct,
        max_increase_pct=max_increase_pct,
    )

recommendation = PricingEngine().recommend(snapshot)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Precio actual", money(recommendation.current_price))
col2.metric("Precio recomendado", money(recommendation.recommended_price), pct(recommendation.increase_pct))
col3.metric("Absorption Score", f"{recommendation.absorption_score:.1f}/100")
col4.metric("Confianza", f"{recommendation.confidence * 100:.0f}%")

st.subheader("Por qué")
reason_map = {
    "strong_sales_velocity": "Ventas recientes fuertes",
    "strong_separation_velocity": "Separaciones recientes fuertes",
    "low_typology_stock": "Stock bajo en la tipología",
    "project_target_gap": "Existe gap contra la meta del proyecto",
    "price_increase_opportunity": "Existe oportunidad de incremento",
    "hold_price": "La evidencia no justifica un incremento",
}
for reason in recommendation.reason_codes:
    st.write(f"• {reason_map.get(reason, reason)}")

if recommendation.constraints_applied:
    st.warning("Guardrails aplicados: " + ", ".join(recommendation.constraints_applied))
else:
    st.success("La recomendación no chocó con guardrails adicionales.")

st.subheader("Decisión")
note = st.text_area("Nota del analista")
approve_col, reject_col, _ = st.columns([1, 1, 2])
if approve_col.button("Aprobar recomendación", type="primary", use_container_width=True):
    append_decision(recommendation, DecisionStatus.APPROVED, note)
    st.success("Aprobada y registrada. No se modificó Sperant.")
if reject_col.button("Rechazar", use_container_width=True):
    append_decision(recommendation, DecisionStatus.REJECTED, note)
    st.info("Rechazada y registrada.")

with st.expander("Detalle técnico"):
    st.json(recommendation.model_dump(mode="json"))

st.subheader("Decision Memory local")
decisions = list(reversed(read_decisions()))
if decisions:
    st.dataframe(decisions[:25], use_container_width=True, hide_index=True)
else:
    st.caption("Aún no hay decisiones registradas.")

if os.getenv("VERCEL"):
    st.caption("Nota: Streamlit no es la interfaz desplegada por Vercel; allí se usa la API FastAPI.")
