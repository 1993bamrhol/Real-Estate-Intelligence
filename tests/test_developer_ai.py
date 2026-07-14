from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.developer_ai import (
    DevelopmentAssumptions,
    analyze_development,
    answer_developer_question,
    build_developer_brief,
    optimize_for_target_margin,
    project_snapshot,
    recommend_product_mix,
    stress_test_development,
)


def healthy_project(**overrides: float) -> DevelopmentAssumptions:
    values = {
        "land_area_sqm": 2_000,
        "land_cost": 4_000_000,
        "floor_area_ratio": 2.0,
        "saleable_efficiency_pct": 80,
        "average_unit_area_sqm": 100,
        "construction_cost_per_sqm": 2_000,
        "sale_price_per_sqm": 6_000,
        "annual_rent_per_unit": 45_000,
        "market_sample_size": 200,
        "demand_rank": 0.8,
    }
    values.update(overrides)
    return DevelopmentAssumptions(**values)


class DeveloperAITests(unittest.TestCase):
    def test_feasibility_calculates_project_economics(self) -> None:
        result = analyze_development(healthy_project())
        self.assertEqual(result["units"], 32)
        self.assertGreater(result["sale_revenue"], result["total_cost"])
        self.assertGreater(result["profit"], 0)
        self.assertGreater(result["max_land_bid"], 0)
        self.assertIn(result["decision"], {"proceed", "redesign", "reject"})

    def test_higher_land_cost_reduces_profit_and_score(self) -> None:
        base = analyze_development(healthy_project())
        expensive = analyze_development(healthy_project(land_cost=12_000_000))
        self.assertLess(expensive["profit"], base["profit"])
        self.assertLess(expensive["development_score"], base["development_score"])

    def test_downside_is_worse_than_base_and_upside(self) -> None:
        stress = stress_test_development(healthy_project())
        rows = {row["scenario"]: row for row in stress["scenarios"]}
        self.assertLess(rows["downside"]["profit"], rows["base"]["profit"])
        self.assertLess(rows["base"]["profit"], rows["upside"]["profit"])

    def test_product_mix_allocates_all_units(self) -> None:
        frame = pd.DataFrame(
            {
                "period_index": [1, 2, 1, 2, 1, 2],
                "period": ["2025 Q4", "2026 Q1"] * 3,
                "property_type": ["شقة", "شقة", "فيلا", "فيلا", "مكتب", "مكتب"],
                "average_rent": [40_000, 44_000, 90_000, 88_000, 55_000, 60_000],
                "total_deals": [100, 130, 30, 25, 40, 55],
            }
        )
        mix = recommend_product_mix(frame, total_units=37)
        self.assertEqual(int(mix["recommended_units"].sum()), 37)
        self.assertAlmostEqual(float(mix["allocation_pct"].sum()), 100.0)
        self.assertEqual(mix.iloc[0]["property_type"], "شقة")

    def test_brief_contains_decision_and_financials(self) -> None:
        result = analyze_development(healthy_project())
        stress = stress_test_development(healthy_project())
        brief = build_developer_brief(result, stress, pd.DataFrame())
        self.assertIn("توصية قرينة AI", brief)
        self.assertIn("القرار", brief)
        self.assertIn("سعر التعادل", brief)

    def test_optimizer_returns_three_explainable_levers(self) -> None:
        optimization = optimize_for_target_margin(healthy_project(), 25)
        self.assertEqual(len(optimization["levers"]), 3)
        self.assertGreater(optimization["required_sale_price_per_sqm"], 0)
        self.assertGreaterEqual(optimization["max_land_cost"], 0)
        self.assertGreaterEqual(optimization["max_construction_cost_per_sqm"], 0)

    def test_question_answer_extracts_requested_margin(self) -> None:
        assumptions = healthy_project()
        result = analyze_development(assumptions)
        stress = stress_test_development(assumptions)
        answer = answer_developer_question(
            "كيف أصل إلى هامش 25%؟", assumptions, result, stress, pd.DataFrame()
        )
        self.assertIn("25.0%", answer)
        self.assertIn("سعر البيع", answer)

    def test_project_snapshot_is_comparison_ready(self) -> None:
        assumptions = healthy_project()
        result = analyze_development(assumptions)
        stress = stress_test_development(assumptions)
        snapshot = project_snapshot("مشروع أ", assumptions, result, stress)
        self.assertEqual(snapshot["project"], "مشروع أ")
        self.assertEqual(snapshot["units"], 32)
        self.assertIn("downside_profit", snapshot)


if __name__ == "__main__":
    unittest.main()
