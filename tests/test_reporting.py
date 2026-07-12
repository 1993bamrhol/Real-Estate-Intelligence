from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.reporting import build_investment_memo_html


class ReportingTests(unittest.TestCase):
    def test_memo_contains_decision_metrics_and_scenarios(self) -> None:
        html = build_investment_memo_html(
            property_details={"city": "الرياض", "district": "النرجس", "property_type": "شقة", "area": 150, "price": 900_000},
            assumptions={"annual_rent": 60_000, "occupancy_pct": 90, "operating_expense_pct": 15, "annual_maintenance": 4_000, "down_payment_pct": 30, "interest_rate_pct": 5.5},
            analysis={"decision": "negotiate", "deal_score": 64, "net_yield_pct": 4.8, "annual_cash_flow": 12_000, "cash_on_cash_pct": 3.4, "dscr": 1.25, "break_even_occupancy_pct": 72},
            stress_test={"confidence": "medium", "risk_adjusted_max_offer": 820_000, "scenarios": [{"label": "الأساسي", "annual_cash_flow": 12_000, "net_yield_pct": 4.8, "dscr": 1.25, "deal_score": 64, "decision": "negotiate"}]},
            market_context={"period": "2026 Q1"},
        )
        self.assertIn("مذكرة قرار استثماري", html)
        self.assertIn("القرار: تفاوض", html)
        self.assertIn("النرجس", html)
        self.assertIn("820,000 ر.س", html)
        self.assertIn("اختبار الضغط", html)
        self.assertNotIn("None", html)


if __name__ == "__main__":
    unittest.main()
