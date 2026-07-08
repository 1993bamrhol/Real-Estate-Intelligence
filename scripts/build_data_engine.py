from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_engine import build_sqlite_warehouse, warehouse_status
from real_estate_intel.data_prep import load_rental_data


def main() -> None:
    data = load_rental_data()
    build_sqlite_warehouse(data)
    status = warehouse_status()
    print("data_engine=ok")
    print(f"rows={status.get('rows', 0)}")
    print(f"locations={status.get('locations', 0)}")
    print(f"latest_period={status.get('latest_period', '')}")
    print(f"path={status.get('path', '')}")


if __name__ == "__main__":
    main()
