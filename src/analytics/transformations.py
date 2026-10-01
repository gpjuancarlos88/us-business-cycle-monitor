from __future__ import annotations
import numpy as np
import pandas as pd

def to_monthly(df: pd.DataFrame, aggregation: str) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    s = df.set_index("observation_date")["value"].sort_index().astype(float)
    if aggregation == "mean":
        return s.resample("ME").mean().dropna()
    if aggregation == "claims_4wk_last":
        return s.rolling(4, min_periods=2).mean().resample("ME").last().dropna()
    if aggregation == "carry_forward":
        return s.resample("ME").last().ffill().dropna()
    return s.resample("ME").last().dropna()

def yoy_pct(s: pd.Series) -> pd.Series:
    return s.pct_change(12, fill_method=None) * 100.0

def annualized_growth(s: pd.Series, months: int) -> pd.Series:
    power = 12.0 / months
    ratio = s / s.shift(months)
    return (np.power(ratio, power) - 1.0) * 100.0

def transform_signal(s: pd.Series, method: str) -> pd.Series:
    if method == "level":
        return s
    if method == "yoy_pct":
        return yoy_pct(s)
    if method == "return_6m":
        return s.pct_change(6, fill_method=None) * 100.0
    if method == "ism_distance_50":
        return s - 50.0
    if method == "growth_3m_ann":
        return annualized_growth(s, 3)
    raise ValueError(f"Unknown signal transform: {method}")

def rolling_zscore(s: pd.Series, window: int = 120, min_periods: int = 36) -> pd.Series:
    mean = s.rolling(window, min_periods=min_periods).mean()
    std = s.rolling(window, min_periods=min_periods).std(ddof=0).replace(0, np.nan)
    return (s - mean) / std

def build_metrics(monthly: pd.Series, signal_transform: str, direction: int, zwindow: int, min_periods: int, clip: float) -> pd.DataFrame:
    out = pd.DataFrame(index=monthly.index)
    out["level"] = monthly
    out["mom_pct"] = monthly.pct_change(fill_method=None) * 100
    out["yoy_pct"] = yoy_pct(monthly)
    out["growth_3m_ann"] = annualized_growth(monthly, 3)
    out["growth_6m_ann"] = annualized_growth(monthly, 6)
    out["signal_input"] = transform_signal(monthly, signal_transform)
    out["signal_z_raw"] = rolling_zscore(out["signal_input"], zwindow, min_periods)
    if direction == 0:
        out["signal"] = out["signal_z_raw"].clip(-clip, clip)
    else:
        out["signal"] = (out["signal_z_raw"] * direction).clip(-clip, clip)
    out["momentum"] = rolling_zscore(out["signal_input"].diff(3), zwindow, min_periods).clip(-clip, clip)
    if direction != 0:
        out["momentum"] = out["momentum"] * direction
    return out
