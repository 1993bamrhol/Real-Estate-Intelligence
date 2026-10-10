from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.analytics import entity_period_market, opportunity_scores, weighted_average
from real_estate_intel.data_prep import load_snapshot
from real_estate_intel.forecasting import forecast_market
from real_estate_intel.metric_registry import metric_governance_frame
from real_estate_intel.sales import latest_sale_comparable, prepare_sale_market


class CoreMetricBindingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rentals = load_snapshot()
        cls.registry = metric_governance_frame().set_index("metric_id")
        cls.riyadh_studio = cls.rentals[
            cls.rentals["city_ar"].eq("الرياض")
            & cls.rentals["property_type"].eq("استديو")
        ].copy()

    def test_home_market_aggregate_anchor_is_20255(self) -> None:
        scope = self.riyadh_studio[self.riyadh_studio["period"].eq("2026 Q1")]
        value = weighted_average(scope, "average_rent", "total_deals")

        self.assertAlmostEqual(value, 20_254.958466660973, places=6)
        self.assertEqual(round(value), 20_255)

    def test_thulaim_raw_rent_qoq_period_pair_and_opportunity_anchors(self) -> None:
        thulaim_row = self.riyadh_studio[
            self.riyadh_studio["location_ar"].eq("الرياض - ثليم")
            & self.riyadh_studio["period"].eq("2026 Q1")
        ].iloc[0]
        scores = opportunity_scores(self.riyadh_studio)
        thulaim = scores[scores["location_ar"].eq("الرياض - ثليم")].iloc[0]
        murqab = scores[scores["location_ar"].eq("الرياض - المرقب")].iloc[0]

        self.assertAlmostEqual(float(thulaim_row["average_rent"]), 10_294.91, places=2)
        self.assertEqual(round(float(thulaim_row["average_rent"])), 10_295)
        self.assertAlmostEqual(float(thulaim["growth_pct"]), 5.893685718782171, places=9)
        self.assertEqual(thulaim["previous_period"], "2025 Q4")
        self.assertEqual(thulaim["period"], "2026 Q1")
        self.assertEqual(float(thulaim["period_gap"]), 1)
        self.assertEqual(round(float(thulaim["score"]), 1), 84.5)
        self.assertEqual(round(float(murqab["score"]), 1), 83.7)
        self.assertEqual(thulaim["score_classification"], "Inference")
        self.assertEqual(self.registry.loc["opportunity_score", "classification"], "Inference")

    def test_data_sufficiency_is_not_forecast_confidence(self) -> None:
        metric = self.registry.loc["data_sufficiency"]
        self.assertEqual(metric["indicator_ar"], "كفاية البيانات")
        self.assertEqual(metric["classification"], "Inference")
        self.assertIn("ليست ثقة إحصائية", metric["limitation_ar"])

    def test_missing_and_nonconsecutive_growth_stay_null(self) -> None:
        rows = [
            {
                "period_index": 2025 * 4 + 1,
                "period": "2025 Q1",
                "region_ar": "الرياض",
                "city_ar": "الرياض",
                "location_ar": "الرياض - حي اختبار",
                "property_type": "استديو",
                "average_rent": 10_000,
                "total_deals": 20,
            },
            {
                "period_index": 2025 * 4 + 3,
                "period": "2025 Q3",
                "region_ar": "الرياض",
                "city_ar": "الرياض",
                "location_ar": "الرياض - حي اختبار",
                "property_type": "استديو",
                "average_rent": 11_000,
                "total_deals": 25,
            },
        ]
        market = entity_period_market(pd.DataFrame(rows)).sort_values("period_index")

        self.assertTrue(pd.isna(market.iloc[0]["growth_pct"]))
        self.assertNotEqual(market.iloc[0]["growth_pct"], 0)
        self.assertEqual(float(market.iloc[1]["period_gap"]), 2)
        self.assertTrue(pd.isna(market.iloc[1]["growth_pct"]))

    def test_sales_comparison_requires_matching_property_coverage(self) -> None:
        sales = prepare_sale_market(
            pd.DataFrame(
                [
                    {
                        "city_ar": "الرياض",
                        "district_ar": "بدر",
                        "location_ar": "بدر",
                        "geography_level": "district",
                        "property_type": "قطعة أرض-سكني",
                        "year": 2026,
                        "quarter": 1,
                        "period_index": 2026 * 4 + 1,
                        "period": "2026 Q1",
                        "average_price_per_sqm": 3_000,
                        "deed_count": 10,
                    }
                ]
            )
        )

        self.assertIsNotNone(
            latest_sale_comparable(
                sales, city="الرياض", district="بدر", property_type="أرض سكنية", area=500
            )
        )
        self.assertIsNone(
            latest_sale_comparable(
                sales, city="الرياض", district="بدر", property_type="استديو", area=100
            )
        )

    def test_forecast_remains_backtested_high_error_secondary_scenario(self) -> None:
        result = forecast_market(self.rentals)
        metric = self.registry.loc["market_forecast"]

        self.assertEqual(result["validation_status"], "backtested_high_error")
        self.assertEqual(result["backtest"]["folds"], 8)
        self.assertAlmostEqual(float(result["backtest"]["rent_mape_pct"]), 18.989, places=3)
        self.assertAlmostEqual(float(result["backtest"]["demand_mape_pct"]), 45.383, places=3)
        self.assertEqual(metric["classification"], "Forecast")
        self.assertIn("سيناريو ثانوي عالي الخطأ", metric["limitation_ar"])
        self.assertIn("ليس ادعاء ثقة مرتفعة", metric["limitation_ar"])


if __name__ == "__main__":
    unittest.main()
