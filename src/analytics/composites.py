from __future__ import annotations
import numpy as np
import pandas as pd

def align_signal_frames(frames: dict[str, pd.DataFrame], column: str = "signal") -> pd.DataFrame:
    parts = []
    for key, df in frames.items():
        if not df.empty and column in df:
            parts.append(df[column].rename(key))
    return pd.concat(parts, axis=1).sort_index() if parts else pd.DataFrame()

def composite(frames: dict[str, pd.DataFrame], min_coverage: int) -> pd.DataFrame:
    signals = align_signal_frames(frames, "signal")
    if signals.empty:
        return pd.DataFrame(columns=["score","coverage","positive_breadth","negative_breadth","net_breadth"])
    coverage = signals.notna().sum(axis=1)
    score = signals.mean(axis=1).where(coverage >= min_coverage)
    pos = (signals > 0.25).sum(axis=1) / coverage.replace(0, np.nan)
    neg = (signals < -0.25).sum(axis=1) / coverage.replace(0, np.nan)
    return pd.DataFrame({
        "score": score,
        "coverage": coverage,
        "positive_breadth": pos,
        "negative_breadth": neg,
        "net_breadth": pos-neg,
    })

def classify_regime(coincident_score: float, leading_score: float, coincident_change: float, neutral: float = 0.10) -> tuple[str, float, float]:
    growth = coincident_score
    momentum = 0.70 * leading_score + 0.30 * coincident_change
    if pd.isna(growth) or pd.isna(momentum):
        return "Insufficient data", growth, momentum
    g = 0 if abs(growth) < neutral else (1 if growth > 0 else -1)
    m = 0 if abs(momentum) < neutral else (1 if momentum > 0 else -1)
    if g >= 0 and m > 0:
        regime = "Expansion"
    elif g > 0 and m <= 0:
        regime = "Slowdown"
    elif g < 0 and m > 0:
        regime = "Recovery"
    elif g < 0 and m <= 0:
        regime = "Contraction"
    else:
        regime = "Transition"
    return regime, growth, momentum
