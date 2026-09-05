from __future__ import annotations

import unittest
import sys
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.analytics import entity_period_market, opportunity_scores
from real_estate_intel.data_engine import (
    CLEAN_TABLE,
    WAREHOUSE_PATH,
    build_market_signals,
    build_sqlite_warehouse,
    restore_market_types,
)
from real_estate_intel.data_prep import (
    RENTAL_BUSINESS_KEY,
    deduplicate_rental_observations,
    load_snapshot,
)
from real_estate_intel.forecasting import forecast_market
from real_estate_intel.metric_registry import (
    VALID_CLASSIFICATIONS,
    investor_metric_lineage_frame,
    metric_governance_frame,
)
from real_estate_intel.sales import load_sale_snapshot


def _row(
    *,
    year: int,
    quarter: int,
    location: str,
    property_type: str = "شقة",
    rent: float = 1000,
    deals: float = 20,
) -> dict[str, object]:
    return {
        "year": year,
        "quarter": quarter,
        "period_index": year * 4 + quarter,
        "period": f"{year} Q{quarter}",
        "region_ar": "الرياض",
        "city_ar": "الرياض",
        "district_ar": location,
        "location_ar": location,
        "property_type": property_type,
        "property_class": "سكني",
        "average_rent": rent,
        "total_deals": deals,
        "dataset_id": "dataset-a",
        "resource_id": "resource-a",
        "source_updated_at": "2026-01-01T00:00:00Z",
    }


class MetricGovernanceTests(unittest.TestCase):
    def test_deduplication_uses_newest_source_and_retains_conflict_metadata(self) -> None:
        older = _row(year=2025, quarter=4, location="حي أ", rent=1000, deals=20)
        newer = {**older, "average_rent": 1100, "dataset_id": "dataset-b", "source_updated_at": "2026-02-01T00:00:00Z"}
        result = deduplicate_rental_observations(pd.DataFrame([older, newer]))

        self.assertEqual(len(result), 1)
        self.assertEqual(float(result.iloc[0]["average_rent"]), 1100)
        self.assertEqual(int(result.iloc[0]["source_overlap_count"]), 2)
        self.assertTrue(bool(result.iloc[0]["source_measure_conflict"]))
        self.assertFalse(result.duplicated(RENTAL_BUSINESS_KEY).any())

    def test_growth_rejects_nonconsecutive_periods(self) -> None:
        data = pd.DataFrame(
            [
                _row(year=2025, quarter=1, location="حي أ", rent=1000),
                _row(year=2025, quarter=3, location="حي أ", rent=1200),
            ]
        )
        market = entity_period_market(data).sort_values("period_index")

        self.assertEqual(float(market.iloc[-1]["period_gap"]), 2)
        self.assertTrue(pd.isna(market.iloc[-1]["growth_pct"]))

    def test_market_signals_reject_nonconsecutive_periods(self) -> None:
        data = pd.DataFrame(
            [
                _row(year=2025, quarter=1, location="حي أ", rent=1000, deals=20),
                _row(year=2025, quarter=3, location="حي أ", rent=1200, deals=25),
            ]
        )
        signals = build_market_signals(data).sort_values("period_index")
        latest = signals.iloc[-1]

        self.assertEqual(float(latest["period_gap"]), 2)
        self.assertTrue(pd.isna(latest["rent_growth_pct"]))
        self.assertTrue(pd.isna(latest["deals_growth_pct"]))

    def test_opportunity_score_requires_eligible_prior_and_stable_type_cohort(self) -> None:
        rows = []
        for property_type, base in (("شقة", 1000), ("فيلا", 5000)):
            for location, multiplier in (("حي أ", 1.0), ("حي ب", 1.2)):
                rows.extend(
                    [
                        _row(year=2025, quarter=4, location=location, property_type=property_type, rent=base * multiplier, deals=20),
                        _row(year=2026, quarter=1, location=location, property_type=property_type, rent=base * multiplier * 1.05, deals=25),
                    ]
                )
        data = pd.DataFrame(rows)
        all_scores = opportunity_scores(data, min_deals=10)
        apartment_scores = opportunity_scores(data[data["property_type"].eq("شقة")], min_deals=10)
        joined = all_scores[all_scores["property_type"].eq("شقة")].merge(
            apartment_scores,
            on=["region_ar", "city_ar", "location_ar", "property_type"],
            suffixes=("_all", "_type"),
        )

        self.assertTrue(all_scores["period_gap"].eq(1).all())
        self.assertTrue(all_scores["previous_total_deals"].ge(10).all())
        self.assertTrue((joined["score_all"] - joined["score_type"]).abs().lt(1e-9).all())

    def test_registry_uses_only_governed_classifications(self) -> None:
        registry = metric_governance_frame()
        self.assertEqual(registry["metric_id"].nunique(), len(registry))
        self.assertEqual(set(registry["classification"]), VALID_CLASSIFICATIONS)
        self.assertTrue(registry[["formula", "period_rule", "cohort", "eligibility"]].notna().all().all())

    def test_forecast_registry_reflects_backtested_scenario_governance(self) -> None:
        registry = metric_governance_frame()
        forecast = registry.loc[registry["metric_id"].eq("market_forecast")].iloc[0]
        lineage = investor_metric_lineage_frame()
        description = lineage.loc[lineage["indicator_ar"].eq("توقع الإيجار والطلب"), "classification_ar"].iloc[0]

        self.assertEqual(forecast["classification"], "Forecast")
        self.assertEqual(description, "توقع سيناريو مختبر رجعيًا")
        self.assertIn("اختبار رجعي", forecast["limitation_ar"])
        self.assertIn("8 طيات", forecast["limitation_ar"])
        self.assertIn("18.989%", forecast["limitation_ar"])
        self.assertIn("45.383%", forecast["limitation_ar"])
        self.assertIn("عالي الخطأ", forecast["limitation_ar"])
        self.assertIn("ليس ادعاء ثقة مرتفعة", forecast["limitation_ar"])
        self.assertNotIn("ثقة", description)

    def test_forecast_reports_history_sufficiency_and_backtest_separately(self) -> None:
        data = pd.DataFrame(
            [
                _row(year=2023 + (index // 4), quarter=(index % 4) + 1, location="حي أ", rent=1000 + index * 20, deals=100 + index * 5)
                for index in range(12)
            ]
        )
        result = forecast_market(data)

        self.assertTrue(result["ready"])
        self.assertIn(result["history_sufficiency"], {"low", "medium", "high"})
        self.assertTrue(str(result["validation_status"]).startswith("backtested"))
        self.assertGreaterEqual(int(result["backtest"]["folds"]), 4)

    def test_sqlite_builder_removes_duplicate_business_keys(self) -> None:
        older = _row(year=2025, quarter=4, location="حي أ", rent=1000, deals=20)
        newer = {
            **older,
            "average_rent": 1100,
            "dataset_id": "dataset-b",
            "source_updated_at": "2026-02-01T00:00:00Z",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "baseline.sqlite"
            build_sqlite_warehouse(
                pd.DataFrame([older, newer]),
                db_path=db_path,
                sales_source=load_sale_snapshot(),
            )
            connection = sqlite3.connect(db_path)
            try:
                stored = pd.read_sql_query(f"select * from {CLEAN_TABLE}", connection)
            finally:
                connection.close()

        self.assertEqual(len(stored), 1)
        self.assertEqual(float(stored.iloc[0]["average_rent"]), 1100)
        self.assertFalse(stored.duplicated(RENTAL_BUSINESS_KEY).any())

    def test_published_csv_and_sqlite_have_semantic_parity(self) -> None:
        csv_data = load_snapshot()
        connection = sqlite3.connect(WAREHOUSE_PATH)
        try:
            sqlite_data = restore_market_types(
                pd.read_sql_query(f"select * from {CLEAN_TABLE}", connection)
            )
        finally:
            connection.close()

        self.assertEqual(len(csv_data), 44_455)
        self.assertEqual(len(sqlite_data), len(csv_data))
        self.assertFalse(csv_data.duplicated(RENTAL_BUSINESS_KEY).any())
        self.assertFalse(sqlite_data.duplicated(RENTAL_BUSINESS_KEY).any())
        self.assertEqual(int(sqlite_data["period_index"].max()), int(csv_data["period_index"].max()))

        csv_keys = set(
            csv_data[RENTAL_BUSINESS_KEY].fillna("").astype(str).itertuples(index=False, name=None)
        )
        sqlite_keys = set(
            sqlite_data[RENTAL_BUSINESS_KEY].fillna("").astype(str).itertuples(index=False, name=None)
        )
        self.assertEqual(sqlite_keys, csv_keys)
        self.assertAlmostEqual(float(sqlite_data["total_deals"].sum()), float(csv_data["total_deals"].sum()), places=6)
        self.assertAlmostEqual(
            float((sqlite_data["average_rent"] * sqlite_data["total_deals"]).sum()),
            float((csv_data["average_rent"] * csv_data["total_deals"]).sum()),
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
