"""Deterministic research readings grounded in the configured transformations."""
from __future__ import annotations

import math
import pandas as pd

TRANSFORM_NAMES = {
    "level": "level",
    "yoy_pct": "year-over-year growth rate",
    "return_6m": "six-month return",
    "ism_distance_50": "distance from the ISM 50 threshold",
    "growth_3m_ann": "three-month annualized growth rate",
}

CAVEATS = {
    "manufacturing_hours": "Hours can adjust before headcount, but manufacturing is only one part of the labor market.",
    "initial_claims": "The signal compares claims growth with its historical norm; it does not measure the unemployment rate.",
    "consumer_goods_orders": "Factory orders describe the demand pipeline rather than completed household consumption.",
    "ism_new_orders": "A standardized reading is distinct from the survey's expansion threshold of 50.",
    "cap_goods_ex_air": "Orders can be revised or cancelled and do not establish that equipment investment has occurred.",
    "building_permits": "Permits precede construction, but financing constraints can prevent authorized projects from starting.",
    "sp500": "Equity prices also reflect discount rates and risk premia, so strength is not a direct measure of economic output.",
    "financial_conditions": "NFCI is a public proxy; financial conditions can respond to policy and risk appetite as well as growth.",
    "yield_spread": "A wider spread can reflect lower short rates during weakness; its level and the reasons for steepening matter.",
    "consumer_expectations": "The input is headline Michigan sentiment, not a pure expectations index or a direct spending measure.",
    "payrolls": "Employment is coincident evidence and can remain resilient after forward-looking indicators weaken.",
    "industrial_production": "This covers manufacturing, mining and utilities rather than the entire services-heavy economy.",
    "real_income_ex_transfers": "Excluding transfers emphasizes market-generated income rather than all household resources.",
    "real_manufacturing_trade_sales": "Real goods-sector sales provide demand evidence but exclude much of services consumption.",
    "unemployment_duration": "Average duration can be affected by the composition of unemployment and may lag improvements in hiring.",
    "inventory_sales_ratio": "High inventories can reflect planned stocking or weak sales; production and orders help distinguish them.",
    "services_inflation": "Disinflation means prices rise more slowly, not necessarily that the price level is falling. Services CPI is not PCE inflation.",
    "unit_labor_costs": "Compensation and productivity jointly determine these costs. Quarterly observations are carried forward in monthly views.",
    "real_ci_loans": "Loan balances combine credit demand, bank supply and repayments; higher balances are not automatically stronger growth.",
    "consumer_credit_income": "Higher leverage can accompany spending or financial strain; this ratio alone cannot distinguish them.",
    "prime_rate": "The prime rate describes borrowing costs and policy transmission, not an independent growth signal.",
}


def _finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def indicator_reading(spec: dict, metrics: pd.DataFrame) -> dict:
    missing = {"date": None, "signal": None, "state": "No data", "text": "No observations are available for this indicator.", "qualification": CAVEATS.get(spec["id"], "")}
    if metrics.empty or "level" not in metrics or not metrics["level"].notna().any():
        return missing
    valid = metrics.dropna(subset=["level"]).sort_index()
    date = pd.Timestamp(valid.index[-1])
    row = valid.iloc[-1]
    signal = row.get("signal")
    transform = spec.get("signal_transform", "level")
    measure = TRANSFORM_NAMES.get(transform, transform.replace("_", " "))
    direction = spec.get("direction", 1)
    actual = row.get("signal_input")
    text = []
    if _finite(actual) and transform in {"yoy_pct", "return_6m", "growth_3m_ann"}:
        text.append(f"The {measure} is {actual:+.2f}%.")
    elif _finite(row.get("level")) and transform == "ism_distance_50":
        level = float(row["level"])
        text.append(f"The index is {level:.1f}, {'above' if level > 50 else 'below' if level < 50 else 'at'} the 50 threshold.")
    if _finite(signal):
        position = "above" if signal > .25 else "below" if signal < -.25 else "near"
        if direction == -1:
            position = "below" if signal > .25 else "above" if signal < -.25 else "near"
        text.append(f"Its {measure} is {position} its rolling historical norm.")
        state = "Contextual" if direction == 0 else "Stronger relative to norm" if signal > .25 else "Weaker relative to norm" if signal < -.25 else "Near norm"
        # Use the actual transformed change, not the Z-score of changes: a
        # positive momentum Z-score can coexist with a negative actual change.
        prior_date = date - pd.offsets.MonthEnd(3)
        if "signal_input" in valid and prior_date in valid.index and _finite(actual) and _finite(valid.loc[prior_date, "signal_input"]):
            change = float(actual) - float(valid.loc[prior_date, "signal_input"])
            if abs(change) < 1e-10:
                text.append("The transformed measure is unchanged from three months earlier.")
            elif direction == 0:
                text.append(f"It has {'risen' if change > 0 else 'fallen'} versus three months earlier; the economic meaning depends on context.")
            else:
                strengthening = change * direction > 0
                text.append(f"The directional measure has {'strengthened' if strengthening else 'weakened'} versus three months earlier.")
                if (signal > .25 and not strengthening) or (signal < -.25 and strengthening):
                    text.append("Its historical position and recent direction therefore tell different stories.")
        else:
            text.append("A three-month comparison is not available at this observation.")
    else:
        state = "Building history"
        text.append("There is not enough valid variation/history for a standardized reading at this observation.")
    return {"date": date, "signal": float(signal) if _finite(signal) else None,
            "state": state, "text": " ".join(text), "qualification": CAVEATS.get(spec["id"], "")}
