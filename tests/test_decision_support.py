from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.decision_support import rank_alternatives


class DecisionSupportTests(unittest.TestCase):
    def test_excludes_selected_neighborhood_and_returns_three_options(self) -> None:
        scores = pd.DataFrame(
            {
                "neighborhood": ["النرجس", "الياسمين", "العارض", "الملقا"],
                "property_type": ["شقة"] * 4,
                "average_rent": [55_000, 65_000, 60_000, 58_000],
                "total_deals": [80, 120, 100, 90],
                "risk_score": [60, 80, 75, 70],
            }
        )
        result = rank_alternatives(
            scores,
            selected_neighborhood="النرجس",
            property_type="شقة",
            purchase_price=1_000_000,
        )
        self.assertEqual(len(result), 3)
        self.assertNotIn("النرجس", result["neighborhood"].tolist())
        self.assertEqual(result.iloc[0]["neighborhood"], "الياسمين")
        self.assertIn("عائد أعلى", result.iloc[0]["why_ar"])


if __name__ == "__main__":
    unittest.main()
