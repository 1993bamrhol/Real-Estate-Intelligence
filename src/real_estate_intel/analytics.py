from __future__ import annotations

import pandas as pd

DEFAULT_ENTITY_COLUMNS = ["region_ar", "city_ar", "location_ar", "property_type"]


def weighted_average(frame: pd.DataFrame, value: str, weight: str) -> float:
    clean = frame[[value, weight]].dropna()
    clean = clean[clean[weight] > 0]
    if clean.empty:
        return float("nan")
    return float((clean[value] * clean[weight]).sum() / clean[weight].sum())


def aggregate_market(frame: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=dimensions + ["total_deals", "average_rent", "records"])

    work = frame[[*dimensions, "total_deals", "average_rent"]].copy()
    valid_average = work["average_rent"].notna() & work["total_deals"].gt(0)
    work["_average_weight"] = work["total_deals"].where(valid_average, 0)
    work["_weighted_rent"] = (work["average_rent"] * work["total_deals"]).where(valid_average, 0)

    grouped = (
        work.groupby(dimensions, dropna=False, sort=False)
        .agg(
            total_deals=("total_deals", "sum"),
            records=("average_rent", "size"),
            _average_weight=("_average_weight", "sum"),
            _weighted_rent=("_weighted_rent", "sum"),
        )
        .reset_index()
    )
    grouped["average_rent"] = grouped["_weighted_rent"] / grouped["_average_weight"]
    grouped.loc[grouped["_average_weight"].eq(0), "average_rent"] = pd.NA
    return grouped[[*dimensions, "total_deals", "average_rent", "records"]]


def period_label(frame: pd.DataFrame, period_index: int | None = None) -> str:
    if frame.empty:
        return ""
    if period_index is None:
        period_index = int(frame["period_index"].max())
    match = frame[frame["period_index"] == period_index]
    if match.empty:
        return ""
    return str(match["period"].iloc[0])


def latest_slice(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    latest_period = frame["period_index"].max()
    return frame[frame["period_index"] == latest_period].copy()


def comparable_panel(
    frame: pd.DataFrame,
    key_columns: list[str] | None = None,
    anchor_period: int | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    key_columns = key_columns or DEFAULT_ENTITY_COLUMNS
    anchor_period = int(anchor_period or frame["period_index"].max())
    anchor_keys = frame.loc[frame["period_index"] == anchor_period, key_columns].drop_duplicates()
    if anchor_keys.empty:
        return frame.iloc[0:0].copy()
    return frame.merge(anchor_keys, on=key_columns, how="inner")


def comparable_anchor_period(
    frame: pd.DataFrame,
    key_columns: list[str] | None = None,
    min_periods: int = 2,
) -> int | None:
    if frame.empty:
        return None

    for period in sorted(frame["period_index"].dropna().unique(), reverse=True):
        panel = comparable_panel(frame, key_columns=key_columns, anchor_period=int(period))
        if panel["period_index"].nunique() >= min_periods:
            return int(period)
    return int(frame["period_index"].max())


def quarterly_trend(
    frame: pd.DataFrame,
    comparable: bool = True,
    key_columns: list[str] | None = None,
) -> pd.DataFrame:
    anchor_period = comparable_anchor_period(frame, key_columns=key_columns) if comparable else None
    work = (
        comparable_panel(frame, key_columns=key_columns, anchor_period=anchor_period)
        if comparable
        else frame
    )
    trend = aggregate_market(work, ["year", "quarter", "period_index", "period"])
    if trend.empty:
        return trend
    return trend.sort_values("period_index")


def period_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for period_index, group in frame.groupby("period_index"):
        rows.append(
            {
                "period_index": period_index,
                "period": group["period"].iloc[0],
                "regions": group["region_ar"].nunique(),
                "cities": group["city_ar"].nunique(),
                "locations": group["location_ar"].nunique() if "location_ar" in group else group["city_ar"].nunique(),
                "property_types": group["property_type"].nunique(),
                "records": len(group),
                "total_deals": group["total_deals"].sum(),
            }
        )
    return pd.DataFrame(rows).sort_values("period_index")


def entity_period_market(frame: pd.DataFrame) -> pd.DataFrame:
    market = aggregate_market(frame, ["period_index", "period", *DEFAULT_ENTITY_COLUMNS])
    if market.empty:
        return market
    market = market.sort_values([*DEFAULT_ENTITY_COLUMNS, "period_index"]).copy()
    grouped = market.groupby(DEFAULT_ENTITY_COLUMNS, dropna=False)
    market["previous_period"] = grouped["period"].shift(1)
    market["previous_average_rent"] = grouped["average_rent"].shift(1)
    market["previous_total_deals"] = grouped["total_deals"].shift(1)
    market["growth_pct"] = (
        (market["average_rent"] - market["previous_average_rent"])
        / market["previous_average_rent"]
        * 100
    )
    market.loc[market["previous_average_rent"].le(0), "growth_pct"] = pd.NA
    return market


def _latest_growth_period(market: pd.DataFrame, min_deals: int) -> int | None:
    stable = market[
        market["growth_pct"].notna()
        & (market["total_deals"] >= min_deals)
        & (market["previous_total_deals"] >= min_deals)
    ]
    if stable.empty:
        return None
    return int(stable["period_index"].max())


def opportunity_scores(frame: pd.DataFrame, min_deals: int = 10) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    market = entity_period_market(frame)
    if market.empty:
        return market

    latest_period = _latest_growth_period(market, min_deals) or int(market["period_index"].max())
    latest = market[market["period_index"] == latest_period].copy()
    latest = latest.dropna(subset=["average_rent", "total_deals"]).copy()
    latest = latest[latest["total_deals"] >= min_deals]
    if latest.empty:
        return latest

    # 1. Liquidity Score (based on deal volume) - How active is this segment?
    latest["liquidity_rank"] = latest["total_deals"].rank(pct=True)
    latest["liquidity_score"] = latest["liquidity_rank"] * 100

    # 2. Growth Score (based on rent growth) - Is this segment moving up?
    latest["growth_pct"] = latest["growth_pct"].fillna(0)
    latest["growth_rank"] = latest["growth_pct"].clip(lower=-50, upper=50).rank(pct=True)

    # 3. Affordability Score (based on relative rent) - Is it priced attractively?
    latest["affordability_rank"] = 1 - latest["average_rent"].rank(pct=True)

    # 4. Final Property Score (weighted decision metric)
    # This is the core decision engine. It balances finding a liquid, growing, and affordable market.
    latest["score"] = (
        latest["liquidity_rank"] * 40  # Weight for market activity
        + latest["growth_rank"] * 35  # Weight for upward momentum
        + latest["affordability_rank"] * 25  # Weight for entry price attractiveness
    )
    return latest.sort_values("score", ascending=False)


def top_growth_markets(frame: pd.DataFrame, min_deals: int = 10) -> pd.DataFrame:
    market = entity_period_market(frame)
    if market.empty:
        return market
    latest_period = _latest_growth_period(market, min_deals)
    if latest_period is None:
        return market.iloc[0:0].copy()
    latest = market[
        (market["period_index"] == latest_period)
        & (market["total_deals"] >= min_deals)
        & (market["previous_total_deals"] >= min_deals)
    ].copy()
    return latest.dropna(subset=["growth_pct"]).sort_values("growth_pct", ascending=False)
