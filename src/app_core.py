from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd
from src.indicators.registry import IndicatorRegistry
from src.database.repository import Repository
from src.ingestion.manager import DataManager
from src.analytics.transformations import to_monthly, build_metrics
from src.analytics.composites import composite, classify_regime

class MacroMonitor:
    def __init__(self, project_root: str | Path):
        self.root = Path(project_root)
        self.registry = IndicatorRegistry(self.root / "config" / "indicators.yaml")
        self.settings = yaml.safe_load((self.root / "config" / "settings.yaml").read_text())
        self.repo = Repository(self.root / "data" / "database" / "macro_monitor.db")
        self.manager = DataManager(self.root, self.registry, self.repo)

    def refresh_all(self):
        return self.manager.refresh_all()

    def metrics(self, indicator_id: str, refresh_if_empty: bool = True) -> pd.DataFrame:
        spec = self.registry.get(indicator_id)
        raw = self.repo.load(indicator_id)
        if raw.empty and refresh_if_empty:
            raw = self.manager.refresh(indicator_id)
        monthly = to_monthly(raw, spec.get("monthly_aggregation", "last"))
        cfg = self.settings["signals"]
        return build_metrics(monthly, spec["signal_transform"], int(spec.get("direction",1)), int(cfg["zscore_window_months"]), int(cfg["zscore_min_periods"]), float(cfg["winsor_limit"]))

    def category_metrics(self, category: str) -> dict[str, pd.DataFrame]:
        return {spec["id"]: self.metrics(spec["id"]) for spec in self.registry.by_category(category)}

    def category_composite(self, category: str) -> pd.DataFrame:
        cfg = self.settings["signals"]
        minimum = int(cfg["leading_min_coverage"] if category == "leading" else cfg["coincident_min_coverage"] if category == "coincident" else 1)
        return composite(self.category_metrics(category), minimum)

    def snapshot(self) -> dict:
        lead = self.category_composite("leading")
        coinc = self.category_composite("coincident")
        lead_last = lead["score"].dropna().iloc[-1] if not lead.empty and lead["score"].notna().any() else float("nan")
        coinc_last = coinc["score"].dropna().iloc[-1] if not coinc.empty and coinc["score"].notna().any() else float("nan")
        coinc_change = coinc["score"].diff(3).dropna().iloc[-1] if not coinc.empty and coinc["score"].diff(3).notna().any() else float("nan")
        regime, growth, momentum = classify_regime(coinc_last, lead_last, coinc_change)
        return {"regime": regime, "growth": growth, "momentum": momentum, "leading": lead, "coincident": coinc}
