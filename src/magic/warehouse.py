from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

from magic.domain import UnitSnapshot


LATEST_SNAPSHOTS_SQL = """
select distinct on (unit_code)
    project,
    unit_code,
    typology,
    current_price::float8 as current_price,
    days_in_stock,
    stock_units_typology,
    sales_30d_typology,
    separations_30d_typology,
    benchmark_price::float8 as benchmark_price,
    coalesce(target_gap_pct, 0)::float8 as target_gap_pct
from features.pricing_unit_snapshot
order by unit_code, snapshot_at desc
"""


@dataclass(frozen=True)
class WarehouseStatus:
    connected: bool
    message: str
    row_count: int = 0


class PricingWarehouse:
    """Read-only adapter from medallio_dw into the pricing domain."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")

    def status(self) -> WarehouseStatus:
        if not self.database_url:
            return WarehouseStatus(False, "DATABASE_URL no está configurado.")
        try:
            with psycopg.connect(self.database_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("select count(*) from features.pricing_unit_snapshot")
                    count = int(cur.fetchone()[0])
            if count == 0:
                return WarehouseStatus(
                    True,
                    "Conectado, pero features.pricing_unit_snapshot está vacío.",
                    0,
                )
            return WarehouseStatus(True, "Conectado a medallio_dw.", count)
        except Exception as exc:  # UI-facing diagnostic boundary
            return WarehouseStatus(False, f"No se pudo conectar al warehouse: {exc}")

    def latest_snapshots(self) -> list[UnitSnapshot]:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL no está configurado")

        with psycopg.connect(self.database_url, connect_timeout=8, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(LATEST_SNAPSHOTS_SQL)
                rows = cur.fetchall()

        return [UnitSnapshot(**row) for row in rows]
