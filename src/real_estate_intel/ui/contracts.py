from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Final, Literal, Mapping, MutableMapping, Sequence


HOME_ROUTE_ID: Final = "home"


@dataclass(frozen=True)
class RouteDefinition:
    route_id: str
    label_ar: str


CORE_ROUTES: Final = (
    RouteDefinition(HOME_ROUTE_ID, "الرئيسية"),
    RouteDefinition("deal_analysis", "تحليل صفقة"),
    RouteDefinition("market_exploration", "استكشاف السوق"),
    RouteDefinition("comparison", "المقارنة"),
    RouteDefinition("reports", "التقارير"),
    RouteDefinition("data_methodology", "البيانات والمنهجية"),
)
ROUTE_IDS: Final = tuple(route.route_id for route in CORE_ROUTES)
ROUTE_LABELS_AR: Final = {route.route_id: route.label_ar for route in CORE_ROUTES}


def normalize_route(route_id: object) -> str:
    candidate = str(route_id or "").strip()
    return candidate if candidate in ROUTE_IDS else HOME_ROUTE_ID


DEAL_INPUT_PREFIX: Final = "deal.input."
CORE_STATE_DEFAULTS: Final = {
    "core.route": HOME_ROUTE_ID,
    "market.city": "الرياض",
    "market.property_type": None,
    "market.period": None,
    "market.geographic_level": "district",
    "market.selected_segment": None,
    "market.view_mode": "list",
    "comparison.primary_segment": None,
    "comparison.secondary_segment": None,
    "deal.mode": "input",
    "deal.submitted": None,
}
_STATE_ENUMS: Final = {
    "core.route": frozenset(ROUTE_IDS),
    "market.geographic_level": frozenset({"city", "district"}),
    "market.view_mode": frozenset({"list", "map"}),
    "deal.mode": frozenset({"input", "result"}),
}
_CORE_PREFIXES: Final = ("core.", "market.", "comparison.", "deal.")


def initialize_core_state(state: MutableMapping[str, object]) -> MutableMapping[str, object]:
    for key, default in CORE_STATE_DEFAULTS.items():
        state.setdefault(key, deepcopy(default))
    return state


def validate_core_state(state: Mapping[str, object]) -> tuple[str, ...]:
    errors: list[str] = []
    for key in state:
        if key.startswith(_CORE_PREFIXES) and key not in CORE_STATE_DEFAULTS and not key.startswith(DEAL_INPUT_PREFIX):
            errors.append(f"unknown_core_state_key:{key}")

    for key, allowed in _STATE_ENUMS.items():
        if key in state and state[key] not in allowed:
            errors.append(f"invalid_state_value:{key}")

    submitted = state.get("deal.submitted")
    if submitted is not None and not isinstance(submitted, Mapping):
        errors.append("invalid_state_value:deal.submitted")

    for key in ("comparison.primary_segment", "comparison.secondary_segment"):
        value = state.get(key)
        if value is not None and not isinstance(value, Mapping):
            errors.append(f"invalid_state_value:{key}")
    return tuple(errors)


@dataclass(frozen=True)
class ComparisonCandidate:
    city: str
    property_type: str
    period: str
    geographic_level: str
    segment: str

    @property
    def opportunity_cohort(self) -> tuple[str, str, str, str]:
        return (self.city, self.property_type, self.period, self.geographic_level)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> ComparisonCandidate:
        return cls(
            city=str(value.get("city") or "").strip(),
            property_type=str(value.get("property_type") or "").strip(),
            period=str(value.get("period") or "").strip(),
            geographic_level=str(value.get("geographic_level") or "").strip(),
            segment=str(value.get("selected_segment") or value.get("segment") or "").strip(),
        )


@dataclass(frozen=True)
class ComparisonEligibility:
    eligible: bool
    reasons: tuple[str, ...]


def validate_comparison(
    primary: ComparisonCandidate,
    secondary: ComparisonCandidate,
    *,
    uses_opportunity: bool = False,
) -> ComparisonEligibility:
    reasons: list[str] = []
    for name, candidate in (("primary", primary), ("secondary", secondary)):
        if not candidate.period:
            reasons.append(f"missing_period:{name}")
        elif not _is_quarter(candidate.period):
            reasons.append(f"non_comparable_period:{name}")
        if not candidate.property_type:
            reasons.append(f"missing_property_type:{name}")
        if candidate.geographic_level not in {"city", "district"}:
            reasons.append(f"invalid_geographic_level:{name}")

    if primary.property_type and secondary.property_type and primary.property_type != secondary.property_type:
        reasons.append("property_type_mismatch")
    if primary.geographic_level and secondary.geographic_level and primary.geographic_level != secondary.geographic_level:
        reasons.append("geographic_level_mismatch")
    if primary.period and secondary.period and primary.period != secondary.period:
        reasons.append("period_mismatch")
    if uses_opportunity and primary.opportunity_cohort != secondary.opportunity_cohort:
        reasons.append("opportunity_cohort_mismatch")
    return ComparisonEligibility(not reasons, tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class MarketComparisonPayload:
    city: str
    property_type: str
    period: str
    geographic_level: str
    selected_segment: str

    def as_dict(self) -> dict[str, str]:
        return {
            "city": self.city,
            "property_type": self.property_type,
            "period": self.period,
            "geographic_level": self.geographic_level,
            "selected_segment": self.selected_segment,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> MarketComparisonPayload:
        payload = cls(
            city=str(value.get("city") or value.get("market.city") or "").strip(),
            property_type=str(value.get("property_type") or value.get("market.property_type") or "").strip(),
            period=str(value.get("period") or value.get("market.period") or "").strip(),
            geographic_level=str(value.get("geographic_level") or value.get("market.geographic_level") or "").strip(),
            selected_segment=str(value.get("selected_segment") or value.get("market.selected_segment") or "").strip(),
        )
        if not all(payload.as_dict().values()):
            raise ValueError("Market comparison payload requires a complete base scope.")
        return payload


def apply_market_comparison_payload(
    state: MutableMapping[str, object], payload: MarketComparisonPayload
) -> None:
    state["comparison.primary_segment"] = payload.as_dict()


def submit_deal(state: MutableMapping[str, object], inputs: Mapping[str, object]) -> None:
    snapshot = deepcopy(dict(inputs))
    if not snapshot:
        raise ValueError("Deal submission requires input values.")
    state["deal.submitted"] = snapshot
    state["deal.mode"] = "result"


def edit_deal(state: MutableMapping[str, object]) -> None:
    submitted = state.get("deal.submitted")
    if isinstance(submitted, Mapping):
        for key, value in submitted.items():
            state[f"{DEAL_INPUT_PREFIX}{key}"] = deepcopy(value)
    state["deal.mode"] = "input"


def update_deal_input(state: MutableMapping[str, object], key: str, value: object) -> None:
    input_key = f"{DEAL_INPUT_PREFIX}{key}"
    state[input_key] = value
    submitted = state.get("deal.submitted")
    if isinstance(submitted, Mapping) and submitted.get(key) != value:
        state["deal.submitted"] = None
        state["deal.mode"] = "input"


def deal_result_is_visible(state: Mapping[str, object]) -> bool:
    submitted = state.get("deal.submitted")
    return state.get("deal.mode") == "result" and isinstance(submitted, Mapping) and bool(submitted)


ChartStatus = Literal["default", "loading", "insufficient"]


@dataclass(frozen=True)
class ChartPoint:
    period: str
    value: float | None


@dataclass(frozen=True)
class ChartDataContract:
    status: ChartStatus
    points: tuple[ChartPoint, ...]
    connectgaps: bool = False


def build_chart_data_contract(
    values: Mapping[str, float | int | None],
    expected_periods: Sequence[str],
    *,
    status: ChartStatus = "default",
) -> ChartDataContract:
    if status not in {"default", "loading", "insufficient"}:
        raise ValueError(f"Unsupported chart status: {status}")
    if status != "default":
        return ChartDataContract(status=status, points=())
    points = tuple(
        ChartPoint(period=period, value=None if values.get(period) is None else float(values[period]))
        for period in expected_periods
    )
    return ChartDataContract(status=status, points=points, connectgaps=False)


@dataclass(frozen=True)
class MapSafetyContract:
    verified_geography: bool
    production_map_allowed: bool
    fallback: Literal["list"]
    message_ar: str


def map_safety_contract(*, verified_geography: bool = False) -> MapSafetyContract:
    return MapSafetyContract(
        verified_geography=verified_geography,
        production_map_allowed=verified_geography,
        fallback="list",
        message_ar=(
            "الخريطة غير متاحة حتى اعتماد مصدر جغرافي موثق؛ استخدم عرض القائمة."
            if not verified_geography
            else "المصدر الجغرافي موثق ويمكن تفعيل عرض الخريطة."
        ),
    )


PRESENTATION_TERMS_AR: Final = {
    "Inference": "استنتاج تحليلي",
    "Calculated": "مؤشر محسوب",
    "Data Sufficiency": "كفاية البيانات",
}


def presentation_term_ar(term: str) -> str:
    return PRESENTATION_TERMS_AR.get(term, term)


def _is_quarter(value: str) -> bool:
    parts = value.split()
    return (
        len(parts) == 2
        and len(parts[0]) == 4
        and parts[0].isdigit()
        and parts[1] in {"Q1", "Q2", "Q3", "Q4"}
    )
