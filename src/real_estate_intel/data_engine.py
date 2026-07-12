from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

from sqlalchemy import create_engine, text
from real_estate_intel.analytics import aggregate_market, opportunity_scores
from real_estate_intel.official_sources import metric_lineage_frame, official_sources_frame


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "real_estate.sqlite"
CLEAN_TABLE = "rental_market_clean"
SIGNALS_TABLE = "rental_market_signals"
QUALITY_TABLE = "data_quality_summary"
SOURCE_REGISTRY_TABLE = "official_source_registry"
METRIC_LINEAGE_TABLE = "metric_lineage"


def get_db_connection_string() -> str | None:
    """
    Returns a PostgreSQL connection string from environment variables if available.
    Example: "postgresql://user:password@host:port/database"
    """
    value = os.environ.get("DATABASE_URL", "").strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value.removeprefix("postgres://")
    return value or None


def create_postgres_engine(db_url: str):
    """Create a resilient SQLAlchemy engine for Supabase or PostgreSQL."""
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 15},
    )


def load_local_fallback() -> pd.DataFrame:
    """Load SQLite first, then the published CSV snapshot."""
    if WAREHOUSE_PATH.exists():
        try:
            with sqlite3.connect(WAREHOUSE_PATH) as connection:
                data = pd.read_sql_query(f"select * from {CLEAN_TABLE}", connection)
            if not data.empty:
                return restore_market_types(data)
        except (sqlite3.Error, pd.errors.DatabaseError):
            pass

    from real_estate_intel.data_prep import load_rental_data

    return restore_market_types(load_rental_data())


def load_market_data() -> pd.DataFrame:
    db_url = get_db_connection_string()
    if db_url:
        try:
            engine = create_postgres_engine(db_url)
            with engine.connect() as connection:
                if not pd.io.sql.has_table(CLEAN_TABLE, connection, schema=None):
                    return load_local_fallback()
                data = pd.read_sql_query(text(f"select * from {CLEAN_TABLE}"), connection)
            return restore_market_types(data)
        except Exception as exc:
            print(f"PostgreSQL unavailable; using local data fallback: {exc}")

    return load_local_fallback()


def build_pg_warehouse(source: pd.DataFrame, engine) -> None:
    """Builds and populates the PostgreSQL database."""
    clean = prepare_clean_market(source)
    signals = build_market_signals(clean)
    quality = build_quality_summary(clean)
    source_registry = official_sources_frame()
    metric_lineage = metric_lineage_frame()

    with engine.connect() as connection:
        # Using transactions for robustness
        with connection.begin():
            clean.to_sql(CLEAN_TABLE, connection, if_exists="replace", index=False, method="multi")
            signals.to_sql(SIGNALS_TABLE, connection, if_exists="replace", index=False, method="multi")
            quality.to_sql(QUALITY_TABLE, connection, if_exists="replace", index=False, method="multi")
            source_registry.to_sql(SOURCE_REGISTRY_TABLE, connection, if_exists="replace", index=False, method="multi")
            metric_lineage.to_sql(METRIC_LINEAGE_TABLE, connection, if_exists="replace", index=False, method="multi")
            connection.execute(text(f"create index if not exists idx_clean_period_city on {CLEAN_TABLE}(period_index, city_ar)"))
            connection.execute(text(f"create index if not exists idx_clean_location on {CLEAN_TABLE}(location_ar)"))
            connection.execute(text(f"create index if not exists idx_signals_entity on {SIGNALS_TABLE}(location_ar, property_type)"))


def build_sqlite_warehouse(source: pd.DataFrame, db_path: Path = WAREHOUSE_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    clean = prepare_clean_market(source)
    signals = build_market_signals(clean)
    quality = build_quality_summary(clean)
    source_registry = official_sources_frame()
    metric_lineage = metric_lineage_frame()

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        with connection.begin():
            clean.to_sql(CLEAN_TABLE, connection, if_exists="replace", index=False)
            signals.to_sql(SIGNALS_TABLE, connection, if_exists="replace", index=False)
            quality.to_sql(QUALITY_TABLE, connection, if_exists="replace", index=False)
            source_registry.to_sql(SOURCE_REGISTRY_TABLE, connection, if_exists="replace", index=False)
            metric_lineage.to_sql(METRIC_LINEAGE_TABLE, connection, if_exists="replace", index=False)
            connection.execute(text(f"create index if not exists idx_clean_period_city on {CLEAN_TABLE}(period_index, city_ar)"))
            connection.execute(text(f"create index if not exists idx_clean_location on {CLEAN_TABLE}(location_ar)"))
            connection.execute(text(f"create index if not exists idx_signals_entity on {SIGNALS_TABLE}(location_ar, property_type)"))


def prepare_clean_market(source: pd.DataFrame) -> pd.DataFrame:
    clean = source.copy()
    text_columns = [
        "region_ar",
        "city_ar",
        "district_ar",
        "location_ar",
        "property_type",
        "property_class",
        "dataset_id",
        "resource_id",
        "dataset_title_ar",
        "dataset_title_en",
        "source_updated_at",
        "period",
    ]
    for column in text_columns:
        if column not in clean.columns:
            clean[column] = ""
        clean[column] = clean[column].fillna("").astype(str).str.strip()

    numeric_columns = ["year", "quarter", "period_index", "total_deals", "average_rent"]
    for column in numeric_columns:
        if column in clean.columns:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")

    clean = clean.dropna(subset=["year", "quarter", "period_index", "average_rent"]).copy()
    clean["year"] = clean["year"].astype("int64")
    clean["quarter"] = clean["quarter"].astype("int64")
    clean["period_index"] = clean["period_index"].astype("int64")
    clean["total_deals"] = clean["total_deals"].fillna(0).astype("float64")
    clean["average_rent"] = clean["average_rent"].astype("float64")
    return clean.sort_values(["period_index", "region_ar", "city_ar", "location_ar", "property_type"])


def build_market_signals(clean: pd.DataFrame) -> pd.DataFrame:
    if clean.empty:
        return pd.DataFrame()

    market = aggregate_market(
        clean,
        ["period_index", "period", "region_ar", "city_ar", "location_ar", "property_type"],
    )
    if market.empty:
        return market

    market = market.sort_values(["region_ar", "city_ar", "location_ar", "property_type", "period_index"]).copy()
    grouped = market.groupby(["region_ar", "city_ar", "location_ar", "property_type"], dropna=False)
    market["previous_period"] = grouped["period"].shift(1)
    market["previous_average_rent"] = grouped["average_rent"].shift(1)
    market["previous_total_deals"] = grouped["total_deals"].shift(1)
    market["rent_growth_pct"] = (
        (market["average_rent"] - market["previous_average_rent"])
        / market["previous_average_rent"]
        * 100
    )
    market.loc[market["previous_average_rent"].le(0), "rent_growth_pct"] = pd.NA
    market["deals_growth_pct"] = (
        (market["total_deals"] - market["previous_total_deals"])
        / market["previous_total_deals"]
        * 100
    )
    market.loc[market["previous_total_deals"].le(0), "deals_growth_pct"] = pd.NA
    return market


def build_quality_summary(clean: pd.DataFrame) -> pd.DataFrame:
    if clean.empty:
        return pd.DataFrame(
            [{"metric": "rows", "value": 0}, {"metric": "latest_period", "value": ""}]
        )

    latest_period = int(clean["period_index"].max())
    latest = clean[clean["period_index"] == latest_period]
    rows = [
        {"metric": "rows", "value": len(clean)},
        {"metric": "latest_period", "value": str(latest["period"].iloc[0]) if not latest.empty else ""},
        {"metric": "regions", "value": clean["region_ar"].nunique()},
        {"metric": "cities", "value": clean["city_ar"].nunique()},
        {"metric": "locations", "value": clean["location_ar"].nunique()},
        {"metric": "property_types", "value": clean["property_type"].nunique()},
        {"metric": "total_deals", "value": float(clean["total_deals"].sum())},
        {"metric": "sources", "value": clean["dataset_id"].nunique() if "dataset_id" in clean else 0},
    ]
    return pd.DataFrame(rows)


def restore_market_types(data: pd.DataFrame) -> pd.DataFrame:
    for column in ["year", "quarter", "period_index"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    for column in ["total_deals", "average_rent"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def warehouse_status() -> dict[str, object]:
    db_url = get_db_connection_string()
    if db_url:
        return pg_warehouse_status(db_url)

    if not WAREHOUSE_PATH.exists():
        return {"ready": False, "path": str(WAREHOUSE_PATH), "type": "SQLite"}
    try:
        with sqlite3.connect(WAREHOUSE_PATH) as connection:
            quality = pd.read_sql_query(f"select metric, value from {QUALITY_TABLE}", connection)
            source_registry = pd.read_sql_query(
                f"select source_id, active from {SOURCE_REGISTRY_TABLE}",
                connection,
            )
    except sqlite3.Error:
        return {"ready": False, "path": str(WAREHOUSE_PATH), "type": "SQLite"}

    values = {str(row["metric"]): row["value"] for _, row in quality.iterrows()}
    active_sources = int(source_registry["active"].astype(bool).sum()) if not source_registry.empty else 0
    return {
        "ready": True,
        "path": str(WAREHOUSE_PATH),
        "type": "SQLite",
        "rows": values.get("rows", 0),
        "latest_period": values.get("latest_period", ""),
        "locations": values.get("locations", 0),
        "sources": values.get("sources", 0),
        "official_sources": active_sources,
    }


def pg_warehouse_status(db_url: str) -> dict[str, object]:
    engine = create_postgres_engine(db_url)
    try:
        with engine.connect() as connection:
            if not pd.io.sql.has_table(QUALITY_TABLE, connection, schema=None):
                return {"ready": False, "path": "PostgreSQL", "type": "PostgreSQL"}
            quality = pd.read_sql_query(text(f"select metric, value from {QUALITY_TABLE}"), connection)
            source_registry = pd.read_sql_query(text(f"select source_id, active from {SOURCE_REGISTRY_TABLE}"), connection)
    except Exception:
        return {"ready": False, "path": "PostgreSQL", "type": "PostgreSQL"}

    values = {str(row["metric"]): row["value"] for _, row in quality.iterrows()}
    active_sources = int(source_registry["active"].astype(bool).sum()) if not source_registry.empty else 0
    return {
        "ready": True, "path": "PostgreSQL", "type": "PostgreSQL", **values, "official_sources": active_sources
    }
