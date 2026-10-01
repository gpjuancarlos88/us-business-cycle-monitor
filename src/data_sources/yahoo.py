from __future__ import annotations
import pandas as pd
from .base import DataSource

class YahooSource(DataSource):
    def fetch(self, spec: dict) -> pd.DataFrame:
        import yfinance as yf
        ticker = spec["ticker"]
        df = yf.download(ticker, period="max", auto_adjust=False, progress=False, threads=False)
        if df.empty:
            raise RuntimeError(f"Yahoo Finance returned no data for {ticker}")
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        out = close.rename("value").reset_index()
        out.columns = ["observation_date", "value"]
        out["observation_date"] = pd.to_datetime(out["observation_date"]).dt.tz_localize(None)
        return out.dropna().sort_values("observation_date").reset_index(drop=True)
