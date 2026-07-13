from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.reporting import _arabic_font_path, build_investment_memo_html, build_investment_memo_pdf


class ReportingTests(unittest.TestCase):
    def test_pdf_uses_the_bundled_arabic_font(self) -> None:
        font_path = _arabic_font_path()
        self.assertEqual(font_path.name, "DejaVuSans.ttf")
        self.assertIn("assets", font_path.parts)
        self.assertTrue(font_path.is_file())

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

    def test_pdf_is_generated_as_shareable_document(self) -> None:
        pdf = build_investment_memo_pdf(
            property_details={"city": "الرياض", "district": "النرجس", "property_type": "شقة", "area": 150, "price": 900_000},
            assumptions={"annual_rent": 60_000, "occupancy_pct": 90},
            analysis={"decision": "buy", "deal_score": 78, "net_yield_pct": 5.2, "annual_cash_flow": 18_000, "cash_on_cash_pct": 4.1, "dscr": 1.4, "break_even_occupancy_pct": 68},
            stress_test={"confidence": "medium", "risk_adjusted_max_offer": 850_000, "scenarios": []},
            market_context={"period": "2026 Q1"},
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1_000)


if __name__ == "__main__":
    unittest.main()
