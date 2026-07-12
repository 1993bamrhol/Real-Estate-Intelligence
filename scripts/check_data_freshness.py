from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_prep import load_rental_data


def current_period_index() -> int:
    now = datetime.now(timezone.utc)
    quarter = (now.month - 1) // 3 + 1
    return now.year * 4 + quarter


def validate_freshness(
    max_quarter_lag: int = 4,
    min_rows: int = 40_000,
    min_regions: int = 13,
) -> dict[str, object]:
    data = load_rental_data()
    if data.empty:
        raise SystemExit("Freshness check failed: no rental data loaded.")

    latest_index = int(data["period_index"].max())
    latest_rows = data[data["period_index"].eq(latest_index)]
    latest_period = str(latest_rows["period"].iloc[0])
    quarter_lag = current_period_index() - latest_index
    regions = int(data["region_ar"].nunique())

    if quarter_lag < 0:
        raise SystemExit(f"Freshness check failed: future period detected ({latest_period}).")
    if quarter_lag > max_quarter_lag:
        raise SystemExit(
            f"Freshness check failed: latest period {latest_period} is {quarter_lag} quarters behind."
        )
    if len(data) < min_rows:
        raise SystemExit(
            f"Freshness check failed: row count regressed to {len(data):,} (minimum {min_rows:,})."
        )
    if regions < min_regions:
        raise SystemExit(
            f"Freshness check failed: region coverage regressed to {regions} (minimum {min_regions})."
        )

    return {
        "rows": len(data),
        "regions": regions,
        "latest_period": latest_period,
        "quarter_lag": quarter_lag,
        "datasets": int(data["dataset_id"].nunique()) if "dataset_id" in data else 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reject stale or regressed rental data releases.")
    parser.add_argument("--max-quarter-lag", type=int, default=4)
    parser.add_argument("--min-rows", type=int, default=40_000)
    parser.add_argument("--min-regions", type=int, default=13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status = validate_freshness(args.max_quarter_lag, args.min_rows, args.min_regions)
    print("freshness_validation=ok")
    for key, value in status.items():
        print(f"{key}={value:,}" if isinstance(value, int) else f"{key}={value}")


if __name__ == "__main__":
    main()
