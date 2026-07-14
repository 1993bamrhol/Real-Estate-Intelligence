from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.brand import BRAND_NAME_AR, BRAND_TAGLINE, PRICING_PLANS, USE_CASES


class BrandTests(unittest.TestCase):
    def test_brand_has_a_clear_name_and_promise(self) -> None:
        self.assertTrue(BRAND_NAME_AR)
        self.assertIn("القرار", BRAND_TAGLINE)

    def test_pricing_covers_free_professional_and_team_paths(self) -> None:
        self.assertEqual(len(PRICING_PLANS), 3)
        self.assertEqual(len({plan.name for plan in PRICING_PLANS}), 3)
        self.assertTrue(any("مجاني" in plan.price for plan in PRICING_PLANS))
        self.assertTrue(all(plan.features for plan in PRICING_PLANS))

    def test_use_cases_are_examples_not_customer_claims(self) -> None:
        self.assertGreaterEqual(len(USE_CASES), 3)
        self.assertTrue(all(case.audience and case.question and case.outcome for case in USE_CASES))


if __name__ == "__main__":
    unittest.main()
