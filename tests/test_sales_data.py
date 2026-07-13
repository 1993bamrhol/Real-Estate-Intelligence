from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SRC = ROOT / "src"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fetch_sale_indicators import parse_sale_indicator_html
from real_estate_intel.sales import latest_sale_comparable, prepare_sale_market


class SaleIndicatorTests(unittest.TestCase):
    def test_parses_and_deduplicates_public_indicator_rows(self) -> None:
        row = (
            r'{\"AvgMeterPrice\":3200,\"DeedCount\":25,\"AvgArea\":450,'
            r'\"TotalArea\":11250,\"TotalRealEstatePrice\":36000000,'
            r'\"AvgRealEstatePrice\":1440000,\"type_category\":\"قطعة أرض-سكني\",'
            r'\"district_name\":\"النرجس\",\"YearNumber\":2026,\"QuarterNumber\":1}'
        )
        data = parse_sale_indicator_html(row + row, "الرياض", "https://example.test")
        self.assertEqual(len(data), 1)
        self.assertEqual(data.iloc[0]["district_ar"], "النرجس")
        self.assertEqual(data.iloc[0]["period"], "2026 Q1")
        self.assertEqual(data.iloc[0]["average_price_per_sqm"], 3200)

    def test_uses_only_matching_land_indicator(self) -> None:
        source = parse_sale_indicator_html(
            (
                r'{\"AvgMeterPrice\":3000,\"DeedCount\":10,\"AvgArea\":400,'
                r'\"TotalArea\":4000,\"TotalRealEstatePrice\":12000000,'
                r'\"AvgRealEstatePrice\":1200000,\"type_category\":\"قطعة أرض-سكني\",'
                r'\"district_name\":\"بدر\",\"YearNumber\":2026,\"QuarterNumber\":1}'
            ),
            "الرياض",
            "https://example.test",
        )
        sales = prepare_sale_market(source)

        land = latest_sale_comparable(
            sales,
            city="الرياض",
            district="بدر",
            property_type="أرض سكنية",
            area=500,
        )
        apartment = latest_sale_comparable(
            sales,
            city="الرياض",
            district="بدر",
            property_type="شقة",
            area=150,
        )

        self.assertIsNotNone(land)
        self.assertEqual(land["estimated_sale_value"], 1_500_000)
        self.assertIsNone(apartment)


if __name__ == "__main__":
    unittest.main()
