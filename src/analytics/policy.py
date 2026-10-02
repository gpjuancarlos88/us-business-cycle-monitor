"""Absolute inflation and nominal policy/benchmark rates, distinct from Z-scores."""
from __future__ import annotations
import math
import pandas as pd

INFLATION_IDS = ['headline_pce', 'core_pce', 'headline_cpi', 'core_cpi']
RATE_IDS = ['fed_target_lower', 'fed_target_upper', 'effective_fed_funds', 'sofr', 'treasury_10y']


def inflation_snapshot(specs, frames):
    rows = []
    for key in INFLATION_IDS:
        frame = frames[key]
        valid = frame.dropna(subset=['level']).sort_index() if not frame.empty and 'level' in frame else pd.DataFrame()
        if valid.empty:
            rows.append({'id': key, 'name': specs[key]['short_name'], 'date': None, 'yoy': None, 'mom': None, 'annualized_3m': None, 'gap': None})
            continue
        row = valid.iloc[-1]
        def number(column):
            value = row.get(column)
            return float(value) if value is not None and math.isfinite(float(value)) else None
        yoy = number('yoy_pct')
        reference = 2.0 if key in ['headline_pce', 'core_pce'] else None
        rows.append({'id': key, 'name': specs[key]['short_name'], 'date': pd.Timestamp(valid.index[-1]),
                     'yoy': yoy, 'mom': number('mom_pct'), 'annualized_3m': number('growth_3m_ann'),
                     'gap': yoy-reference if yoy is not None and reference is not None else None})
    return rows


def raw_rate_series(frame):
    if frame.empty or not {'observation_date', 'value'} <= set(frame):
        return pd.Series(dtype=float)
    valid = frame.dropna(subset=['observation_date', 'value']).copy()
    valid['observation_date'] = pd.to_datetime(valid['observation_date'])
    valid['value'] = pd.to_numeric(valid['value'], errors='coerce')
    valid = valid.loc[valid['value'].map(lambda x: math.isfinite(x))]
    return valid.groupby('observation_date')['value'].last().sort_index()


def policy_snapshot(raw_frames):
    series = {key: raw_rate_series(raw_frames.get(key, pd.DataFrame())) for key in RATE_IDS}
    rates = {key: {'date': values.index[-1], 'value': float(values.iloc[-1])} if not values.empty else None for key, values in series.items()}
    joint = pd.concat([series['fed_target_lower'].rename('lower'), series['fed_target_upper'].rename('upper')], axis=1).dropna()
    result = {'range': None, 'change': None, 'rates': rates, 'history': series}
    if joint.empty or joint.iloc[-1]['lower'] > joint.iloc[-1]['upper']:
        return result
    result['range'] = {'date': pd.Timestamp(joint.index[-1]), 'lower': float(joint.iloc[-1]['lower']), 'upper': float(joint.iloc[-1]['upper'])}
    changes = joint.diff()
    changed = changes.notna().all(axis=1) & (changes.abs() > 1e-10).any(axis=1)
    if changed.any():
        date = changes.loc[changed].index[-1]
        lower_delta, upper_delta = float(changes.loc[date, 'lower']), float(changes.loc[date, 'upper'])
        equal = abs(lower_delta-upper_delta) < 1e-10
        result['change'] = {'date': pd.Timestamp(date), 'lower_bps': lower_delta*100, 'upper_bps': upper_delta*100,
                            'action': 'Hike' if equal and lower_delta > 0 else 'Cut' if equal and lower_delta < 0 else 'Range reshaped'}
    return result
