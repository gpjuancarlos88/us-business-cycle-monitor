"""Compare evidence at an actual shared month, without imputing observations."""
from __future__ import annotations
import math
import pandas as pd

from src.analytics.interpretations import TRANSFORM_NAMES


def _valid(frame):
    required = ["level", "signal", "signal_input"]
    if frame.empty or not all(key in frame for key in required):
        return pd.DataFrame(columns=required)
    valid = frame[required].dropna().sort_index()
    if valid.empty:
        return valid
    return valid.loc[valid.apply(lambda row: all(math.isfinite(float(v)) for v in row), axis=1)]


def compare_indicators(left_spec, left, right_spec, right):
    frames = [_valid(left), _valid(right)]
    shared = frames[0].index.intersection(frames[1].index).sort_values()
    if shared.empty:
        return {"date": None, "headline": "Insufficient shared evidence", "relationship": "unavailable",
                "text": "Both indicators need valid standardized signals and transformed inputs in the same month before a comparison can be made.", "evidence": []}
    date = pd.Timestamp(shared[-1])
    prior_date = date - pd.offsets.MonthEnd(3)
    evidence = []
    for spec, frame in zip([left_spec, right_spec], frames):
        row = frame.loc[date]
        score = float(row["signal"])
        position = "stronger" if score > .25 else "weaker" if score < -.25 else "near"
        direction = spec.get("direction", 1)
        change = None
        if prior_date in frame.index:
            change = (float(row["signal_input"]) - float(frame.loc[prior_date, "signal_input"])) * direction
        trend = "unavailable" if change is None else "unchanged" if abs(change) < 1e-10 else "strengthening" if change > 0 else "weakening"
        evidence.append({"name": spec["short_name"], "signal": score, "input": float(row["signal_input"]),
                         "measure": TRANSFORM_NAMES.get(spec.get("signal_transform"), "transformed measure"),
                         "position": position, "trend": trend, "latest": pd.Timestamp(frame.index[-1])})
    a, b = evidence
    if a["position"] == b["position"] and a["position"] != "near":
        relationship = "agreement"
        headline = "Agreement · stronger relative to norm" if a["position"] == "stronger" else "Agreement · weaker relative to norm"
        text = f"Both directional readings are {a['position']} than their own historical norms at the shared observation month. This adds confirmation across the two measures, rather than proving the economy is expanding or contracting."
    elif {a["position"], b["position"]} == {"stronger", "weaker"}:
        relationship = "divergence"
        headline = "Divergence · historical positions differ"
        text = f"{a['name']} is stronger relative to its own norm while {b['name']} is weaker." if a["position"] == "stronger" else f"{a['name']} is weaker relative to its own norm while {b['name']} is stronger."
    else:
        relationship = "mixed"
        headline = "Limited confirmation · near-normal evidence"
        text = "At least one reading is within the ±0.25σ neutral band. The pair does not provide clear confirmation of shared strength or shared weakness relative to historical norms."
    trends = [e["trend"] for e in evidence]
    if "unavailable" in trends:
        text += " An exact three-month directional comparison is unavailable for at least one indicator."
    elif trends[0] == trends[1]:
        text += " Both underlying directional measures are " + ("unchanged" if trends[0] == "unchanged" else trends[0]) + " versus three months earlier."
    else:
        text += f"Over three months, {a['name']} is {a['trend']} and {b['name']} is {b['trend']}. Their recent directions differ."
    if any(e["latest"] > date for e in evidence):
        text += " A newer individual reading is available, but this comparison uses the latest shared valid month."
    return {"date": date, "headline": headline, "relationship": relationship, "text": text, "evidence": evidence}
