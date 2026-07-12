from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_prep import SNAPSHOT_PATH, load_rental_data


def main() -> None:
    data = load_rental_data()
    if data.empty:
        raise SystemExit("No rental data found. Run scripts/fetch_rega_data.py first.")

    path = SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, encoding="utf-8-sig", compression="gzip")

    print(f"snapshot={path.relative_to(ROOT)}")
    print(f"rows={len(data):,}")
    print(f"regions={data['region_ar'].nunique():,}")
    print(f"locations={data['location_ar'].nunique():,}")
    print(f"datasets={data['dataset_id'].nunique():,}")
    print(f"latest_period={data.loc[data['period_index'].idxmax(), 'period']}")


if __name__ == "__main__":
    main()
