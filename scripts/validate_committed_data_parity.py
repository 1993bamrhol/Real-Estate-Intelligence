from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "processed" / "rental_market.csv.gz"
SQLITE_PATH = ROOT / "data" / "warehouse" / "real_estate.sqlite"
CLEAN_TABLE = "rental_market_clean"

BUSINESS_KEY = [
    "year",
    "quarter",
    "region_ar",
    "city_ar",
    "district_ar",
    "property_type",
    "property_class",
]
REQUIRED_COLUMNS = BUSINESS_KEY + [
    "period",
    "period_index",
    "location_ar",
    "average_rent",
    "total_deals",
    "dataset_id",
    "resource_id",
    "source_updated_at",
]

# Compare the governed grain, time fields, measures, and source identity. Derived
# quality metadata is validated by governance tests when that metadata exists.
GOVERNED_COLUMNS = sorted(set(REQUIRED_COLUMNS))


def _fail(message: str) -> None:
    raise SystemExit(f"committed_data_parity=failed: {message}")


def _normalized_semantic_rows(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return (
        frame[columns]
        .fillna("")
        .astype(str)
        .sort_values(columns, kind="stable")
        .reset_index(drop=True)
    )


def main() -> None:
    if not CSV_PATH.is_file():
        _fail(f"missing committed CSV: {CSV_PATH.relative_to(ROOT)}")
    if not SQLITE_PATH.is_file():
        _fail(f"missing committed SQLite database: {SQLITE_PATH.relative_to(ROOT)}")

    csv_data = pd.read_csv(CSV_PATH)
    sqlite_uri = f"{SQLITE_PATH.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(sqlite_uri, uri=True)
    try:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?",
                ("table",),
            )
        }
        if CLEAN_TABLE not in tables:
            _fail(f"missing SQLite table: {CLEAN_TABLE}")
        sqlite_data = pd.read_sql_query(f"SELECT * FROM {CLEAN_TABLE}", connection)
    finally:
        connection.close()

    if integrity != "ok":
        _fail(f"SQLite integrity_check returned {integrity!r}")
    if csv_data.empty or sqlite_data.empty:
        _fail("committed market data is empty")

    missing_csv = sorted(set(REQUIRED_COLUMNS) - set(csv_data.columns))
    missing_sqlite = sorted(set(REQUIRED_COLUMNS) - set(sqlite_data.columns))
    if missing_csv or missing_sqlite:
        _fail(
            "required columns missing "
            f"(csv={missing_csv or 'none'}, sqlite={missing_sqlite or 'none'})"
        )
    if set(csv_data.columns) != set(sqlite_data.columns):
        _fail("CSV and SQLite schemas differ")
    if len(csv_data) != len(sqlite_data):
        _fail(f"row counts differ (csv={len(csv_data)}, sqlite={len(sqlite_data)})")

    csv_latest = int(pd.to_numeric(csv_data["period_index"]).max())
    sqlite_latest = int(pd.to_numeric(sqlite_data["period_index"]).max())
    if csv_latest != sqlite_latest:
        _fail(f"latest periods differ (csv={csv_latest}, sqlite={sqlite_latest})")

    csv_semantic = _normalized_semantic_rows(csv_data, GOVERNED_COLUMNS)
    sqlite_semantic = _normalized_semantic_rows(sqlite_data, GOVERNED_COLUMNS)
    if not csv_semantic.equals(sqlite_semantic):
        _fail("committed CSV and SQLite semantic rows differ")

    csv_duplicate_rows = int(csv_data.duplicated(BUSINESS_KEY, keep=False).sum())
    sqlite_duplicate_rows = int(sqlite_data.duplicated(BUSINESS_KEY, keep=False).sum())
    if csv_duplicate_rows != sqlite_duplicate_rows:
        _fail(
            "business-key duplicate counts differ "
            f"(csv={csv_duplicate_rows}, sqlite={sqlite_duplicate_rows})"
        )

    latest_periods = sorted(
        set(csv_data.loc[csv_data["period_index"].eq(csv_latest), "period"].astype(str))
    )
    print("committed_data_parity=ok")
    print(f"rows={len(csv_data):,}")
    print(f"latest_period={','.join(latest_periods)}")
    print(f"business_key_duplicate_rows={csv_duplicate_rows:,}")
    print(f"governed_columns_compared={len(GOVERNED_COLUMNS)}")
    print(f"sqlite_integrity={integrity}")


if __name__ == "__main__":
    main()
