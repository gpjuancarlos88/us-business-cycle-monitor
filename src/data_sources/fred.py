from __future__ import annotations
import io
import requests
import pandas as pd
from .base import DataSource

class FredCSVSource(DataSource):
    BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def fetch(self, spec: dict) -> pd.DataFrame:
        series_id = spec["series_id"]
        r = requests.get(self.BASE, params={"id": series_id}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        date_col = df.columns[0]
        value_col = series_id if series_id in df.columns else df.columns[-1]
        out = df.rename(columns={date_col: "observation_date", value_col: "value"})[["observation_date", "value"]]
        out["observation_date"] = pd.to_datetime(out["observation_date"], errors="coerce")
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        return out.dropna().sort_values("observation_date").reset_index(drop=True)
