from __future__ import annotations

from collections.abc import Callable, Mapping

from real_estate_intel.ui.contracts import ROUTE_IDS, normalize_route


RouteRenderer = Callable[[], None]


def dispatch_route(route_id: object, renderers: Mapping[str, RouteRenderer]) -> str:
    """Render exactly one route after validating the six-route shell contract."""
    missing = set(ROUTE_IDS).difference(renderers)
    if missing:
        raise ValueError(f"Missing route renderers: {sorted(missing)}")
    active_route = normalize_route(route_id)
    renderers[active_route]()
    return active_route
