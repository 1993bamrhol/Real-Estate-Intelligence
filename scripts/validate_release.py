from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PYTHON_FILES = [
    ROOT / "app.py",
    ROOT / "scripts" / "fetch_rega_data.py",
    ROOT / "scripts" / "fetch_sale_indicators.py",
    ROOT / "scripts" / "build_data_snapshot.py",
    ROOT / "scripts" / "check_data_freshness.py",
    ROOT / "src" / "real_estate_intel" / "analytics.py",
    ROOT / "src" / "real_estate_intel" / "catalog.py",
    ROOT / "src" / "real_estate_intel" / "data_engine.py",
    ROOT / "src" / "real_estate_intel" / "decision_support.py",
    ROOT / "src" / "real_estate_intel" / "forecasting.py",
    ROOT / "src" / "real_estate_intel" / "official_sources.py",
    ROOT / "src" / "real_estate_intel" / "data_prep.py",
    ROOT / "src" / "real_estate_intel" / "rega_client.py",
    ROOT / "src" / "real_estate_intel" / "reporting.py",
    ROOT / "src" / "real_estate_intel" / "underwriting.py",
    ROOT / "src" / "real_estate_intel" / "sales.py",
]


def main() -> None:
    for path in PYTHON_FILES:
        py_compile.compile(str(path), doraise=True)

    from real_estate_intel.data_prep import load_rental_data
    from real_estate_intel.sales import load_sale_snapshot

    data = load_rental_data()
    if data.empty:
        raise SystemExit("Validation failed: no rental data loaded.")
    required_columns = {"region_ar", "city_ar", "location_ar", "property_type", "average_rent", "total_deals"}
    missing = required_columns.difference(data.columns)
    if missing:
        raise SystemExit(f"Validation failed: missing columns {sorted(missing)}.")
    if data["region_ar"].nunique() < 5:
        raise SystemExit("Validation failed: market coverage is too narrow.")

    sales = load_sale_snapshot()
    if sales.empty:
        raise SystemExit("Validation failed: no official sale indicators loaded.")
    sale_key = ["city_ar", "geography_level", "location_ar", "property_type", "period_index"]
    if sales.duplicated(sale_key).any():
        raise SystemExit("Validation failed: duplicate sale-indicator grain.")
    if sales["average_price_per_sqm"].le(0).any():
        raise SystemExit("Validation failed: invalid sale price per sqm.")

    from check_data_freshness import validate_freshness

    validate_freshness()

    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_file(str(ROOT / "app.py"))
    app_test.run(timeout=45)
    if app_test.exception:
        errors = [str(item.value) for item in app_test.exception]
        raise SystemExit(f"Validation failed: Streamlit exceptions {errors}.")

    print("release_validation=ok")
    print(f"rows={len(data):,}")
    print(f"regions={data['region_ar'].nunique():,}")
    print(f"locations={data['location_ar'].nunique():,}")
    print(f"latest_period={data.loc[data['period_index'].idxmax(), 'period']}")
    print(f"sale_rows={len(sales):,}")
    print(f"sale_latest_period={sales.loc[sales['period_index'].idxmax(), 'period']}")


if __name__ == "__main__":
    main()
