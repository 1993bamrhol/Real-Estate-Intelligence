from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.forecasting import forecast_market


class ForecastingTests(unittest.TestCase):
    def test_builds_three_scenarios_for_four_quarters(self) -> None:
        data = pd.DataFrame(
            {
                "period_index": list(range(8097, 8105)),
                "period": [f"{2024 + (index // 4)} Q{index % 4 + 1}" for index in range(8)],
                "average_rent": [50_000, 51_000, 51_500, 52_000, 53_000, 54_000, 55_000, 56_000],
                "total_deals": [80, 82, 78, 85, 88, 90, 92, 95],
            }
        )
        result = forecast_market(data)
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["forecast"]), 12)
        self.assertEqual(set(result["forecast"]["scenario"]), {"pessimistic", "base", "optimistic"})
        self.assertGreater(result["forecast_rent"], result["current_rent"])

    def test_rejects_short_history(self) -> None:
        data = pd.DataFrame(
            {"period_index": [1, 2, 3], "period": ["1 Q1", "1 Q2", "1 Q3"], "average_rent": [1, 2, 3], "total_deals": [2, 3, 4]}
        )
        self.assertFalse(forecast_market(data)["ready"])


if __name__ == "__main__":
    unittest.main()
