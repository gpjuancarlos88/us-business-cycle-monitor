from __future__ import annotations
from pathlib import Path
import yaml

class IndicatorRegistry:
    def __init__(self, path: str | Path):
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self._items = {item["id"]: item for item in payload["indicators"]}

    def get(self, indicator_id: str) -> dict:
        return self._items[indicator_id]

    def all(self) -> list[dict]:
        return list(self._items.values())

    def by_category(self, category: str) -> list[dict]:
        return [x for x in self._items.values() if x["category"] == category]
