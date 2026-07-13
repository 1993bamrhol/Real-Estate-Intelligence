from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_engine import (
    WAREHOUSE_PATH,
    build_pg_warehouse,
    build_sqlite_warehouse,
    create_postgres_engine,
    get_db_connection_string,
)
from real_estate_intel.data_prep import load_rental_data


def main() -> None:
    """
    Loads rental data and builds the data warehouse.
    Connects to PostgreSQL if DATABASE_URL is set, otherwise uses local SQLite.
    """
    print("Loading rental data from source files...")
    source_data = load_rental_data()
    if source_data.empty:
        raise SystemExit("Validation failed: no rental data loaded.")

    db_url = get_db_connection_string()
    if os.environ.get("DATABASE_URL", "").strip() and not db_url:
        raise SystemExit(
            "DATABASE_URL is configured but invalid. Store only the PostgreSQL URL "
            "or a DATABASE_URL = \"postgresql://...\" assignment."
        )
    if db_url:
        print("Connecting to PostgreSQL and building warehouse...")
        engine = create_postgres_engine(db_url)
        build_pg_warehouse(source_data, engine)
        print("PostgreSQL warehouse build complete.")
    else:
        print(f"Building local SQLite warehouse at: {WAREHOUSE_PATH}")
        build_sqlite_warehouse(source_data, WAREHOUSE_PATH)
        print("SQLite warehouse build complete.")


if __name__ == "__main__":
    main()
