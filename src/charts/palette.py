"""Stable identities across research, comparison and indicator charts."""
INDICATOR_COLORS = {
    "headline_pce": "#C9AA78", "core_pce": "#B5A2C8", "headline_cpi": "#8FAABF", "core_cpi": "#80B8B3",
    "fed_target_lower": "#C7D6D5", "fed_target_upper": "#C9AA78", "effective_fed_funds": "#8FAABF", "sofr": "#B5A2C8", "treasury_10y": "#80B8B3",
    "manufacturing_hours": "#B5A2C8", "initial_claims": "#91B7A1",
    "consumer_goods_orders": "#C9AA78", "ism_new_orders": "#80B8B3",
    "cap_goods_ex_air": "#C9AA78", "building_permits": "#8FAABF",
    "sp500": "#8FAABF", "financial_conditions": "#91B7A1",
    "yield_spread": "#C9AA78", "consumer_expectations": "#B5A2C8",
    "payrolls": "#C7D6D5", "industrial_production": "#8FAABF",
    "real_income_ex_transfers": "#80B8B3", "real_manufacturing_trade_sales": "#C9AA78",
    "unemployment_duration": "#9EA5AD", "inventory_sales_ratio": "#9EA5AD",
    "services_inflation": "#C9AA78", "unit_labor_costs": "#B5A2C8",
    "real_ci_loans": "#C7D6D5", "consumer_credit_income": "#9EA5AD",
    "prime_rate": "#B5A2C8", "leading_composite": "#C7D6D5",
    "coincident_composite": "#8FAABF",
}


def indicator_color(indicator_id):
    return INDICATOR_COLORS.get(indicator_id, "#C7D6D5")
