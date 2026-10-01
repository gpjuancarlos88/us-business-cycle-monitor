import pandas as pd
from src.analytics.composites import composite, classify_regime

def frame(values):
    idx=pd.date_range("2024-01-31",periods=len(values),freq="ME")
    return pd.DataFrame({"signal":values},index=idx)

def test_composite_mean_and_coverage():
    c=composite({"a":frame([1,1]),"b":frame([-1,1])},min_coverage=2)
    assert c["coverage"].iloc[-1] == 2
    assert c["score"].iloc[-1] == 1

def test_minimum_coverage_suppresses_score():
    c=composite({"a":frame([1,1])},min_coverage=2)
    assert pd.isna(c["score"].iloc[-1])

def test_regime_matrix():
    assert classify_regime(0.5,0.5,0.2)[0] == "Expansion"
    assert classify_regime(0.5,-0.5,-0.2)[0] == "Slowdown"
    assert classify_regime(-0.5,0.5,0.2)[0] == "Recovery"
    assert classify_regime(-0.5,-0.5,-0.2)[0] == "Contraction"
