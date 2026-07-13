from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "processed" / "sale_market.csv.gz"
BASE_URL = "https://rei.rega.gov.sa/ar/cities"
SOURCE_OWNER = "الهيئة العامة للعقار - وزارة العدل والسجل العقاري"
ROW_PATTERN = re.compile(r'\{\\"AvgMeterPrice\\":.*?\}')


def parse_sale_indicator_html(html: str, requested_city: str, source_url: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    fetched_at = datetime.now(timezone.utc).isoformat()
    for match in ROW_PATTERN.findall(html):
        try:
            raw = json.loads(match.replace('\\"', '"'))
        except json.JSONDecodeError:
            continue
        if not required_sale_fields(raw):
            continue

        location = str(raw.get("district_name") or requested_city).strip()
        level = "city" if location == requested_city else "district"
        key = (
            requested_city,
            location,
            raw.get("type_category"),
            raw.get("YearNumber"),
            raw.get("QuarterNumber"),
        )
        if key in seen:
            continue
        seen.add(key)
        year = int(raw["YearNumber"])
        quarter = int(raw["QuarterNumber"])
        rows.append(
            {
                "city_ar": requested_city,
                "district_ar": "" if level == "city" else location,
                "location_ar": location,
                "geography_level": level,
                "property_type": str(raw["type_category"]).strip(),
                "year": year,
                "quarter": quarter,
                "period_index": year * 4 + quarter,
                "period": f"{year} Q{quarter}",
                "average_price_per_sqm": float(raw["AvgMeterPrice"]),
                "deed_count": float(raw.get("DeedCount") or 0),
                "average_area": float(raw.get("AvgArea") or 0),
                "total_area": float(raw.get("TotalArea") or 0),
                "average_sale_price": float(raw.get("AvgRealEstatePrice") or 0),
                "total_sale_value": float(raw.get("TotalRealEstatePrice") or 0),
                "source_owner_ar": SOURCE_OWNER,
                "source_url": source_url,
                "fetched_at": fetched_at,
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["city_ar", "geography_level", "location_ar", "property_type", "period_index"]
    ).reset_index(drop=True)


def required_sale_fields(row: dict[str, object]) -> bool:
    return all(
        row.get(field) is not None
        for field in ("AvgMeterPrice", "type_category", "YearNumber", "QuarterNumber")
    )


def fetch_city(city: str, timeout: int) -> pd.DataFrame:
    url = f"{BASE_URL}/{quote(city)}"
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "Real-Estate-Intelligence/1.0 (official public indicator refresh)",
            "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.7",
        },
    )
    response.raise_for_status()
    return parse_sale_indicator_html(response.text, city, url)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch public REGA sale-price indicators.")
    parser.add_argument("--cities", nargs="+", default=["الرياض"])
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frames = [fetch_city(city, args.timeout) for city in args.cities]
    data = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    if data.empty:
        raise SystemExit("No public sale indicators were extracted from REGA.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False, encoding="utf-8-sig", compression="gzip")
    print(f"sale_snapshot={args.output.relative_to(ROOT)}")
    print(f"rows={len(data):,}")
    print(f"cities={data['city_ar'].nunique():,}")
    print(f"districts={data.loc[data['geography_level'].eq('district'), 'district_ar'].nunique():,}")
    print(f"property_types={data['property_type'].nunique():,}")
    print(f"latest_period={data.loc[data['period_index'].idxmax(), 'period']}")


if __name__ == "__main__":
    main()
