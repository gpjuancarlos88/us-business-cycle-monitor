from __future__ import annotations
import math

def fmt(value, digits=2):
    try:
        if value is None or math.isnan(float(value)): return "N/A"
        return f"{float(value):.{digits}f}"
    except Exception:
        return "N/A"

def signal_label(x: float, neutral=0.25, strong=1.0):
    if x != x: return "Unavailable"
    if x >= strong: return "Strong"
    if x > neutral: return "Improving"
    if x <= -strong: return "Weak"
    if x < -neutral: return "Deteriorating"
    return "Neutral"
