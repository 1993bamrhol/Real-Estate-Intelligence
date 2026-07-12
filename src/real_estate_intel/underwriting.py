from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyAssumptions:
    purchase_price: float
    annual_rent: float
    occupancy_pct: float = 90.0
    operating_expense_pct: float = 15.0
    annual_maintenance: float = 0.0
    down_payment_pct: float = 100.0
    interest_rate_pct: float = 0.0
    loan_years: int = 20
    acquisition_cost_pct: float = 2.5
    target_net_yield_pct: float = 5.0
    market_fair_price: float | None = None
    market_demand_rank: float = 0.5


def annual_debt_service(principal: float, interest_rate_pct: float, years: int) -> float:
    if principal <= 0 or years <= 0:
        return 0.0
    rate = max(interest_rate_pct, 0.0) / 100 / 12
    payments = years * 12
    if rate == 0:
        return principal / years
    monthly = principal * rate * (1 + rate) ** payments / ((1 + rate) ** payments - 1)
    return monthly * 12


def analyze_property(assumptions: PropertyAssumptions) -> dict[str, float | str]:
    price = max(float(assumptions.purchase_price), 0.0)
    annual_rent = max(float(assumptions.annual_rent), 0.0)
    occupancy = _clamp(assumptions.occupancy_pct / 100, 0, 1)
    expense_ratio = _clamp(assumptions.operating_expense_pct / 100, 0, 0.95)
    down_payment_ratio = _clamp(assumptions.down_payment_pct / 100, 0, 1)

    effective_income = annual_rent * occupancy
    variable_expenses = effective_income * expense_ratio
    operating_expenses = variable_expenses + max(assumptions.annual_maintenance, 0.0)
    noi = effective_income - operating_expenses

    loan_amount = price * (1 - down_payment_ratio)
    debt_service = annual_debt_service(loan_amount, assumptions.interest_rate_pct, assumptions.loan_years)
    acquisition_cost = price * max(assumptions.acquisition_cost_pct, 0.0) / 100
    invested_cash = price * down_payment_ratio + acquisition_cost
    annual_cash_flow = noi - debt_service

    gross_yield = _pct(annual_rent, price)
    net_yield = _pct(noi, price)
    cash_on_cash = _pct(annual_cash_flow, invested_cash)
    dscr = noi / debt_service if debt_service > 0 else math.inf
    payback = invested_cash / annual_cash_flow if annual_cash_flow > 0 else math.inf

    target_yield = max(assumptions.target_net_yield_pct, 0.1) / 100
    income_fair_price = noi / target_yield if noi > 0 else 0.0
    market_fair_price = max(float(assumptions.market_fair_price or 0), 0.0)
    fair_candidates = [value for value in (income_fair_price, market_fair_price) if value > 0]
    blended_fair_price = sum(fair_candidates) / len(fair_candidates) if fair_candidates else 0.0
    price_gap_pct = _pct(price - blended_fair_price, blended_fair_price) if blended_fair_price else 0.0
    negotiation_amount = max(price - blended_fair_price, 0.0)

    debt_and_fixed_cost = debt_service + max(assumptions.annual_maintenance, 0.0)
    rentable_margin = annual_rent * (1 - expense_ratio)
    break_even_occupancy = (
        _clamp(debt_and_fixed_cost / rentable_margin, 0, 1.5) * 100 if rentable_margin > 0 else 100.0
    )

    score = _deal_score(
        net_yield_pct=net_yield,
        target_yield_pct=assumptions.target_net_yield_pct,
        cash_flow=annual_cash_flow,
        dscr=dscr,
        price_gap_pct=price_gap_pct,
        break_even_occupancy_pct=break_even_occupancy,
        demand_rank=assumptions.market_demand_rank,
    )
    decision = "buy" if score >= 72 else "negotiate" if score >= 52 else "reject"

    return {
        "effective_income": effective_income,
        "operating_expenses": operating_expenses,
        "noi": noi,
        "loan_amount": loan_amount,
        "annual_debt_service": debt_service,
        "invested_cash": invested_cash,
        "annual_cash_flow": annual_cash_flow,
        "gross_yield_pct": gross_yield,
        "net_yield_pct": net_yield,
        "cash_on_cash_pct": cash_on_cash,
        "dscr": dscr,
        "payback_years": payback,
        "income_fair_price": income_fair_price,
        "blended_fair_price": blended_fair_price,
        "price_gap_pct": price_gap_pct,
        "negotiation_amount": negotiation_amount,
        "break_even_occupancy_pct": break_even_occupancy,
        "deal_score": score,
        "decision": decision,
    }


def _deal_score(
    *,
    net_yield_pct: float,
    target_yield_pct: float,
    cash_flow: float,
    dscr: float,
    price_gap_pct: float,
    break_even_occupancy_pct: float,
    demand_rank: float,
) -> float:
    yield_score = _clamp(net_yield_pct / max(target_yield_pct, 0.1), 0, 1.25) / 1.25 * 30
    price_score = _clamp((15 - price_gap_pct) / 30, 0, 1) * 25
    cash_score = (15 if cash_flow > 0 else 0) + _clamp((dscr - 1) / 0.5, 0, 1) * 10
    risk_score = _clamp((100 - break_even_occupancy_pct) / 35, 0, 1) * 10
    demand_score = _clamp(demand_rank, 0, 1) * 10
    return round(_clamp(yield_score + price_score + cash_score + risk_score + demand_score, 0, 100), 1)


def _pct(numerator: float, denominator: float) -> float:
    return numerator / denominator * 100 if denominator > 0 else 0.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)
