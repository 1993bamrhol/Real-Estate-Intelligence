from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SALE_SNAPSHOT_PATH = PROJECT_ROOT / "data" / "processed" / "sale_market.csv.gz"

SALE_TEXT_COLUMNS = [
    "city_ar",
    "district_ar",
    "location_ar",
    "geography_level",
    "property_type",
    "period",
    "source_owner_ar",
    "source_url",
    "fetched_at",
]
SALE_NUMERIC_COLUMNS = [
    "year",
    "quarter",
    "period_index",
    "average_price_per_sqm",
    "deed_count",
    "average_area",
    "total_area",
    "average_sale_price",
    "total_sale_value",
]


def load_sale_snapshot(path: Path = SALE_SNAPSHOT_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return prepare_sale_market(pd.read_csv(path))


def prepare_sale_market(source: pd.DataFrame) -> pd.DataFrame:
    if source.empty:
        return pd.DataFrame(columns=SALE_TEXT_COLUMNS + SALE_NUMERIC_COLUMNS)

    sales = source.copy()
    for column in SALE_TEXT_COLUMNS:
        if column not in sales.columns:
            sales[column] = ""
        sales[column] = sales[column].fillna("").astype(str).str.strip()
    for column in SALE_NUMERIC_COLUMNS:
        if column not in sales.columns:
            sales[column] = pd.NA
        sales[column] = pd.to_numeric(sales[column], errors="coerce")

    required = [
        "city_ar",
        "location_ar",
        "property_type",
        "year",
        "quarter",
        "period_index",
        "average_price_per_sqm",
    ]
    sales = sales.dropna(subset=required).copy()
    sales = sales[
        sales["average_price_per_sqm"].gt(0)
        & sales["quarter"].between(1, 4)
        & sales["geography_level"].isin(["city", "district"])
    ].copy()
    for column in ["year", "quarter", "period_index"]:
        sales[column] = sales[column].astype("int64")

    key = ["city_ar", "geography_level", "location_ar", "property_type", "period_index"]
    sales = sales.sort_values(key + ["fetched_at"]).drop_duplicates(key, keep="last")
    return sales.sort_values(key).reset_index(drop=True)


def property_type_matches_sale_indicator(rental_type: str, sale_type: str) -> bool:
    """Prevent land indicators from being applied to apartments or buildings."""
    rental = _normalized(rental_type)
    sale = _normalized(sale_type)
    if "ارض" in sale:
        return "ارض" in rental
    return rental == sale


def latest_sale_comparable(
    sales: pd.DataFrame,
    *,
    city: str,
    district: str,
    property_type: str,
    area: float,
) -> dict[str, object] | None:
    if sales.empty:
        return None

    city_key = _normalized(city)
    district_key = _normalized(district)
    candidates = sales[
        sales["city_ar"].map(_normalized).eq(city_key)
        & sales["location_ar"].map(_normalized).eq(district_key)
    ].copy()
    candidates = candidates[
        candidates["property_type"].map(
            lambda sale_type: property_type_matches_sale_indicator(property_type, str(sale_type))
        )
    ].copy()
    if candidates.empty:
        return None

    latest_period = int(candidates["period_index"].max())
    latest = candidates[candidates["period_index"].eq(latest_period)].copy()
    weights = latest["deed_count"].clip(lower=0)
    if weights.sum() > 0:
        price_per_sqm = float((latest["average_price_per_sqm"] * weights).sum() / weights.sum())
    else:
        price_per_sqm = float(latest["average_price_per_sqm"].median())
    row = latest.iloc[0]
    return {
        "average_price_per_sqm": price_per_sqm,
        "estimated_sale_value": price_per_sqm * max(float(area), 0.0),
        "deed_count": float(latest["deed_count"].sum()),
        "period": str(row["period"]),
        "property_type": str(row["property_type"]),
        "source_url": str(row["source_url"]),
        "coverage": "district",
    }


def _normalized(value: object) -> str:
    return str(value or "").strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
