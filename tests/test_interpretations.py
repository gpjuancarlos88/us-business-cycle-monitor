import pandas as pd
from pathlib import Path

from src.analytics.interpretations import indicator_reading
from src.indicators.registry import IndicatorRegistry
from src.ui.research import load_sections


def frame(signal=.8, actual=-1, prior=2, momentum=1):
    dates = pd.date_range('2026-04-30', periods=4, freq='ME')
    return pd.DataFrame({'level': [100]*4, 'signal': [signal]*4,
                         'signal_input': [prior, 1, 0, actual], 'momentum':[momentum]*4}, index=dates)


def spec(direction=1, transform='yoy_pct', key='payrolls'):
    return {'id':key, 'direction':direction, 'signal_transform':transform}


def test_positive_norm_is_not_positive_growth_or_increasing():
    reading=indicator_reading(spec(),frame())
    assert '-1.00%' in reading['text']
    assert 'above its rolling historical norm' in reading['text']
    assert 'weakened' in reading['text']
    assert 'different stories' in reading['text']


def test_inverted_signal_describes_underlying_norm_correctly():
    reading=indicator_reading(spec(direction=-1,key='initial_claims'),frame(actual=-1,prior=2))
    assert 'below its rolling historical norm' in reading['text']
    assert 'strengthened' in reading['text']


def test_contextual_inflation_is_not_labeled_good_or_bad():
    reading=indicator_reading(spec(direction=0,key='services_inflation'),frame())
    assert reading['state']=='Contextual'
    assert 'fallen' in reading['text']
    assert 'strengthened' not in reading['text']
    assert 'price level' in reading['qualification']


def test_missing_latest_signal_does_not_use_older_reading():
    metrics=frame()
    metrics.iloc[-1,metrics.columns.get_loc('signal')]=float('nan')
    reading=indicator_reading(spec(),metrics)
    assert reading['signal'] is None
    assert reading['state']=='Building history'
    assert '-1.00%' in reading['text']


def test_missing_exact_three_month_date():
    reading=indicator_reading(spec(),frame().iloc[1:])
    assert 'comparison is not available' in reading['text']


def test_empty_data():
    assert indicator_reading(spec(),pd.DataFrame())['state']=='No data'


def test_ism_raw_threshold_distinct_from_standardized_norm():
    metrics=frame(signal=-1,actual=2,prior=1)
    metrics['level']=52
    reading=indicator_reading(spec(transform='ism_distance_50',key='ism_new_orders'),metrics)
    assert 'above the 50 threshold' in reading['text']
    assert 'below its rolling historical norm' in reading['text']


def test_theme_configuration_covers_registry():
    root=Path(__file__).resolve().parents[1]
    sections=load_sections(root)
    registry=IndicatorRegistry(root/'config/indicators.yaml').all()
    ids={s['id'] for s in registry}
    assert len(sections)==6
    assert {key for s in sections for key in s['indicators']}==ids
    assert len({s['id'] for s in sections})==6
