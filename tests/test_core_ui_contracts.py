from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.ui.contracts import (
    CORE_ROUTES,
    CORE_STATE_DEFAULTS,
    PRESENTATION_TERMS_AR,
    ROUTE_IDS,
    ROUTE_LABELS_AR,
    ChartDataContract,
    ComparisonCandidate,
    MarketComparisonPayload,
    apply_market_comparison_payload,
    build_chart_data_contract,
    deal_result_is_visible,
    edit_deal,
    initialize_core_state,
    map_safety_contract,
    normalize_route,
    presentation_term_ar,
    submit_deal,
    update_deal_input,
    validate_comparison,
    validate_core_state,
)
from real_estate_intel.ui.shell import dispatch_route


def _candidate(**overrides: str) -> ComparisonCandidate:
    values = {
        "city": "الرياض",
        "property_type": "استديو",
        "period": "2026 Q1",
        "geographic_level": "district",
        "segment": "ثليم",
    }
    values.update(overrides)
    return ComparisonCandidate(**values)


class CoreRouteAndStateContractTests(unittest.TestCase):
    def test_six_routes_have_unique_internal_ids_and_arabic_labels(self) -> None:
        self.assertEqual(len(CORE_ROUTES), 6)
        self.assertEqual(len(ROUTE_IDS), len(set(ROUTE_IDS)))
        self.assertEqual(len(ROUTE_LABELS_AR.values()), len(set(ROUTE_LABELS_AR.values())))
        self.assertTrue(all(route.label_ar.strip() for route in CORE_ROUTES))
        self.assertEqual(normalize_route("unknown"), "home")

    def test_state_schema_initializes_only_base_state_and_rejects_derived_cohort(self) -> None:
        state: dict[str, object] = {}
        initialize_core_state(state)

        self.assertEqual(state, CORE_STATE_DEFAULTS)
        self.assertNotIn("comparison.cohort", state)
        self.assertEqual(validate_core_state(state), ())
        state["comparison.cohort"] = "derived-value"
        self.assertIn("unknown_core_state_key:comparison.cohort", validate_core_state(state))

    def test_state_schema_rejects_invalid_enums_but_allows_deal_input_keys(self) -> None:
        state = dict(CORE_STATE_DEFAULTS)
        state["market.view_mode"] = "globe"
        state["deal.input.purchase_price"] = 900_000

        self.assertEqual(validate_core_state(state), ("invalid_state_value:market.view_mode",))

    def test_route_state_persists_and_dispatches_exactly_one_renderer(self) -> None:
        state: dict[str, object] = {"core.route": "comparison"}
        initialize_core_state(state)
        calls: list[str] = []
        renderers = {route.route_id: lambda route_id=route.route_id: calls.append(route_id) for route in CORE_ROUTES}

        active = dispatch_route(state["core.route"], renderers)

        self.assertEqual(state["core.route"], "comparison")
        self.assertEqual(active, "comparison")
        self.assertEqual(calls, ["comparison"])


class ComparisonAndDealContractTests(unittest.TestCase):
    def test_comparison_eligibility_accepts_only_equivalent_scope(self) -> None:
        valid = validate_comparison(_candidate(), _candidate(segment="المرقب"), uses_opportunity=True)
        self.assertTrue(valid.eligible)

        cases = {
            "mismatched_type": (_candidate(), _candidate(property_type="شقة"), "property_type_mismatch"),
            "mismatched_level": (_candidate(), _candidate(geographic_level="city"), "geographic_level_mismatch"),
            "missing_period": (_candidate(), _candidate(period=""), "missing_period:secondary"),
            "non_comparable_period": (_candidate(), _candidate(period="2026"), "non_comparable_period:secondary"),
            "different_period": (_candidate(), _candidate(period="2025 Q4"), "period_mismatch"),
            "different_opportunity_cohort": (_candidate(), _candidate(city="جدة"), "opportunity_cohort_mismatch"),
        }
        for name, (primary, secondary, reason) in cases.items():
            with self.subTest(name=name):
                result = validate_comparison(primary, secondary, uses_opportunity=True)
                self.assertFalse(result.eligible)
                self.assertIn(reason, result.reasons)

    def test_market_payload_round_trip_preserves_scope_and_sets_primary_only(self) -> None:
        state: dict[str, object] = dict(CORE_STATE_DEFAULTS)
        state.update(
            {
                "market.city": "الرياض",
                "market.property_type": "استديو",
                "market.period": "2026 Q1",
                "market.geographic_level": "district",
                "market.selected_segment": "ثليم",
            }
        )
        payload = MarketComparisonPayload.from_mapping(state)
        restored = MarketComparisonPayload.from_mapping(payload.as_dict())
        apply_market_comparison_payload(state, payload)

        self.assertEqual(restored, payload)
        self.assertEqual(state["comparison.primary_segment"], payload.as_dict())
        self.assertIsNone(state["comparison.secondary_segment"])

    def test_deal_input_submit_result_edit_and_invalidation(self) -> None:
        state: dict[str, object] = dict(CORE_STATE_DEFAULTS)
        self.assertFalse(deal_result_is_visible(state))

        inputs = {"purchase_price": 900_000, "annual_rent": 60_000}
        submit_deal(state, inputs)
        inputs["purchase_price"] = 1
        self.assertTrue(deal_result_is_visible(state))
        self.assertEqual(state["deal.submitted"]["purchase_price"], 900_000)

        edit_deal(state)
        self.assertFalse(deal_result_is_visible(state))
        self.assertEqual(state["deal.input.purchase_price"], 900_000)

        submit_deal(state, {"purchase_price": 900_000, "annual_rent": 60_000})
        update_deal_input(state, "purchase_price", 950_000)
        self.assertFalse(deal_result_is_visible(state))
        self.assertIsNone(state["deal.submitted"])


class ChartMapAndPresentationContractTests(unittest.TestCase):
    def test_chart_states_preserve_missing_period_as_null_without_connecting_gap(self) -> None:
        chart = build_chart_data_contract(
            {"2025 Q2": 10_000, "2025 Q4": 11_000},
            ["2025 Q2", "2025 Q3", "2025 Q4"],
        )
        self.assertIsInstance(chart, ChartDataContract)
        self.assertEqual(chart.status, "default")
        self.assertEqual(chart.points[1].period, "2025 Q3")
        self.assertIsNone(chart.points[1].value)
        self.assertFalse(chart.connectgaps)

        self.assertEqual(build_chart_data_contract({}, [], status="loading").status, "loading")
        self.assertEqual(build_chart_data_contract({}, [], status="insufficient").status, "insufficient")

    def test_current_map_contract_blocks_unverified_coordinates_with_list_fallback(self) -> None:
        safety = map_safety_contract()
        self.assertFalse(safety.verified_geography)
        self.assertFalse(safety.production_map_allowed)
        self.assertEqual(safety.fallback, "list")
        self.assertIn("غير متاحة", safety.message_ar)

    def test_arabic_terms_are_presentation_only_and_unambiguous(self) -> None:
        self.assertEqual(
            PRESENTATION_TERMS_AR,
            {
                "Inference": "استنتاج تحليلي",
                "Calculated": "مؤشر محسوب",
                "Data Sufficiency": "كفاية البيانات",
            },
        )
        self.assertEqual(presentation_term_ar("Inference"), "استنتاج تحليلي")
        self.assertNotEqual(presentation_term_ar("Data Sufficiency"), "الثقة")


if __name__ == "__main__":
    unittest.main()
