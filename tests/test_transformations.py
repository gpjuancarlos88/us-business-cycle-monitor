import numpy as np
import pandas as pd
from src.analytics.transformations import annualized_growth, rolling_zscore, build_metrics

def monthly(values):
    idx=pd.date_range("2020-01-31", periods=len(values), freq="ME")
    return pd.Series(values,index=idx,dtype=float)

def test_annualized_growth_three_months():
    s=monthly([100,100,100,101])
    expected=(1.01**4-1)*100
    assert np.isclose(annualized_growth(s,3).iloc[-1],expected)

def test_inverse_direction_flips_signal():
    s=monthly(np.linspace(100,200,60))
    pos=build_metrics(s,"level",1,36,12,3)
    inv=build_metrics(s,"level",-1,36,12,3)
    assert np.isclose(pos["signal"].dropna().iloc[-1],-inv["signal"].dropna().iloc[-1])

def test_rolling_zscore_constant_is_nan():
    s=monthly([5]*50)
    assert rolling_zscore(s,36,12).dropna().empty
