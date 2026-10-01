from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.data_sources.fred import FredCSVSource
from src.data_sources.yahoo import YahooSource
from src.data_sources.manual import ManualCSVSource

class DataManager:
    def __init__(self, project_root: str | Path, registry, repository):
        self.root = Path(project_root)
        self.registry = registry
        self.repo = repository
        self.sources = {
            "fred": FredCSVSource(),
            "yahoo": YahooSource(),
            "manual": ManualCSVSource(self.root),
        }

    def _fetch_atomic(self, atom: dict) -> pd.DataFrame:
        return self.sources[atom["provider"]].fetch(atom)

    def fetch_indicator(self, spec: dict) -> pd.DataFrame:
        provider = spec["provider"]
        if provider != "derived":
            return self.sources[provider].fetch(spec)
        inputs = spec["inputs"]
        num = self._fetch_atomic(inputs["numerator"]).set_index("observation_date")["value"].resample("ME").last()
        den = self._fetch_atomic(inputs["denominator"]).set_index("observation_date")["value"].resample("ME").last()
        num = num * float(inputs["numerator"].get("unit_scale", 1))
        den = den * float(inputs["denominator"].get("unit_scale", 1))
        if spec["operation"] == "ratio":
            result = num / den
        elif spec["operation"] == "deflate_index":
            result = num / den * 100.0
        else:
            raise ValueError(f"Unknown derived operation {spec['operation']}")
        return result.dropna().rename("value").reset_index()

    def refresh(self, indicator_id: str) -> pd.DataFrame:
        spec = self.registry.get(indicator_id)
        try:
            df = self.fetch_indicator(spec)
            raw_dir = self.root / "data" / "raw" / spec["provider"]
            raw_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(raw_dir / f"{indicator_id}.csv", index=False)
            self.repo.upsert_observations(indicator_id, df, spec["provider"] )
            status = "OK" if not df.empty else "EMPTY"
            self.repo.log(indicator_id, status, f"{len(df)} observations fetched")
            return df
        except Exception as exc:
            self.repo.log(indicator_id, "ERROR", str(exc))
            return self.repo.load(indicator_id)

    def refresh_all(self):
        return {spec["id"]: self.refresh(spec["id"]) for spec in self.registry.all()}
