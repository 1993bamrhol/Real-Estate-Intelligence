from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.underwriting import PropertyAssumptions, analyze_property, annual_debt_service


class UnderwritingTests(unittest.TestCase):
    def test_cash_purchase_metrics(self) -> None:
        result = analyze_property(
            PropertyAssumptions(
                purchase_price=1_000_000,
                annual_rent=80_000,
                occupancy_pct=90,
                operating_expense_pct=10,
                annual_maintenance=5_000,
                target_net_yield_pct=5,
            )
        )
        self.assertAlmostEqual(result["effective_income"], 72_000)
        self.assertAlmostEqual(result["noi"], 59_800)
        self.assertAlmostEqual(result["net_yield_pct"], 5.98)
        self.assertEqual(result["annual_debt_service"], 0)
        self.assertGreater(result["annual_cash_flow"], 0)

    def test_financing_uses_amortized_payment(self) -> None:
        payment = annual_debt_service(800_000, 5, 20)
        self.assertGreater(payment, 60_000)
        self.assertLess(payment, 65_000)

    def test_overpriced_negative_cash_flow_is_not_buy(self) -> None:
        result = analyze_property(
            PropertyAssumptions(
                purchase_price=2_000_000,
                annual_rent=70_000,
                occupancy_pct=80,
                operating_expense_pct=20,
                down_payment_pct=20,
                interest_rate_pct=7,
                market_fair_price=1_400_000,
                market_demand_rank=0.3,
            )
        )
        self.assertLess(result["annual_cash_flow"], 0)
        self.assertIn(result["decision"], {"negotiate", "reject"})
        self.assertTrue(math.isinf(result["payback_years"]))


if __name__ == "__main__":
    unittest.main()
