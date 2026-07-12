from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.underwriting import (
    PropertyAssumptions,
    analyze_property,
    annual_debt_service,
    stress_test_property,
)


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

    def test_stress_test_orders_cash_flow_by_severity(self) -> None:
        stress = stress_test_property(
            PropertyAssumptions(
                purchase_price=1_000_000,
                annual_rent=100_000,
                occupancy_pct=95,
                operating_expense_pct=10,
                down_payment_pct=40,
                interest_rate_pct=4.5,
                market_fair_price=1_000_000,
                market_sample_size=150,
            )
        )
        rows = stress["scenarios"]
        self.assertGreater(rows[0]["annual_cash_flow"], rows[1]["annual_cash_flow"])
        self.assertGreater(rows[1]["annual_cash_flow"], rows[2]["annual_cash_flow"])
        self.assertGreater(stress["risk_adjusted_max_offer"], 0)
        self.assertIn(stress["confidence"], {"high", "medium", "low"})

    def test_max_offer_is_lower_for_high_interest(self) -> None:
        base = PropertyAssumptions(
            purchase_price=1_000_000,
            annual_rent=90_000,
            down_payment_pct=30,
            interest_rate_pct=4,
            market_fair_price=1_000_000,
        )
        low_rate = stress_test_property(base)["risk_adjusted_max_offer"]
        high_rate = stress_test_property(PropertyAssumptions(**{**base.__dict__, "interest_rate_pct": 9}))[
            "risk_adjusted_max_offer"
        ]
        self.assertLess(high_rate, low_rate)


if __name__ == "__main__":
    unittest.main()
