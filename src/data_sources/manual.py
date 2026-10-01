from __future__ import annotations
from pathlib import Path
import pandas as pd
from .base import DataSource

class ManualCSVSource(DataSource):
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)

    def fetch(self, spec: dict) -> pd.DataFrame:
        path = self.project_root / spec["path"]
        if not path.exists():
            return pd.DataFrame(columns=["observation_date", "value"])
        df = pd.read_csv(path)
        if not {"date", "value"}.issubset(df.columns):
            raise ValueError(f"{path} must contain date,value columns")
        out = df.rename(columns={"date": "observation_date"})[["observation_date", "value"]]
        out["observation_date"] = pd.to_datetime(out["observation_date"], errors="coerce")
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        return out.dropna().sort_values("observation_date").reset_index(drop=True)
