from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_prep import load_snapshot
from real_estate_intel.ui.home import arabic_period_label, build_home_view_model


class HomeViewModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.view_model = build_home_view_model(load_snapshot())

    def test_home_metrics_are_bound_to_the_governed_scope(self) -> None:
        view_model = self.view_model
        metrics = {metric.metric_id: metric for metric in view_model.metrics}

        self.assertTrue(view_model.available)
        self.assertEqual(view_model.scope_ar, "الرياض · كل الأحياء · استديو · الربع الأول 2026")
        self.assertEqual(metrics["weighted_average_rent"].value_ar, "20,255 ر.س")
        self.assertEqual(metrics["rental_deals"].value_ar, "11,713")
        self.assertEqual(metrics["quarterly_rent_growth"].value_ar, "+0.2%")
        self.assertEqual(
            metrics["quarterly_rent_growth"].context_ar,
            "من الربع الرابع 2025 إلى الربع الأول 2026",
        )

    def test_home_opportunities_are_contextual_inferences_not_absolute_claims(self) -> None:
        opportunities = self.view_model.opportunities

        self.assertEqual([item.segment_ar for item in opportunities], ["ثليم", "المرقب"])
        self.assertEqual([item.score_ar for item in opportunities], ["84.5/100", "83.7/100"])
        self.assertTrue(all(item.evidence_ar == "استنتاج تحليلي" for item in opportunities))
        self.assertTrue(all(item.rent_evidence_ar == "بيانات مباشرة" for item in opportunities))
        self.assertTrue(all(item.growth_evidence_ar == "مؤشر محسوب" for item in opportunities))
        self.assertTrue(all("داخل مجموعة أحياء الرياض" in item.cohort_ar for item in opportunities))
        self.assertEqual(opportunities[0].rank_context_ar, "الأعلى ضمن المقارنة الحالية")
        self.assertNotIn("الأفضل", " ".join(item.rank_context_ar for item in opportunities))
        self.assertNotIn("مضمون", " ".join(item.rank_context_ar for item in opportunities))

    def test_period_labels_are_arabic(self) -> None:
        self.assertEqual(arabic_period_label("2026 Q1"), "الربع الأول 2026")


class HomeStreamlitTests(unittest.TestCase):
    def test_home_smoke_and_cta_routing(self) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        app_test.run()
        self.assertFalse(app_test.exception)
        buttons = {button.label: button for button in app_test.button}
        self.assertIn("حلّل صفقة", buttons)
        self.assertIn("استكشف السوق", buttons)
        self.assertIn("راجع البيانات والمنهجية", buttons)
        self.assertEqual(app_test.tabs, [])

        visible_markup = " ".join(item.value for item in app_test.markdown)
        for internal_term in (
            "Raw",
            "Calculated",
            "Inference",
            "Data Sufficiency",
            "QAREENA",
            "SUPABASE_URL",
        ):
            self.assertNotIn(internal_term, visible_markup)
        self.assertNotIn("قارن بدائل", visible_markup)

        buttons["استكشف السوق"].click()
        app_test.run(timeout=60)
        self.assertFalse(app_test.exception)
        self.assertEqual(app_test.session_state["core.route"], "market_exploration")

        navigation = next(item for item in app_test.radio if item.label == "وجهات قرينة")
        navigation.set_value("home")
        app_test.run(timeout=60)
        next(item for item in app_test.button if item.label == "حلّل صفقة").click()
        app_test.run(timeout=60)
        self.assertFalse(app_test.exception)
        self.assertEqual(app_test.session_state["core.route"], "deal_analysis")

        navigation = next(item for item in app_test.radio if item.label == "وجهات قرينة")
        navigation.set_value("home")
        app_test.run(timeout=60)
        next(item for item in app_test.button if item.label == "راجع البيانات والمنهجية").click()
        app_test.run(timeout=60)
        self.assertFalse(app_test.exception)
        self.assertEqual(app_test.session_state["core.route"], "data_methodology")


if __name__ == "__main__":
    unittest.main()
