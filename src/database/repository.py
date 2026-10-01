from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    indicator_id TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    value REAL NOT NULL,
    source TEXT,
    retrieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (indicator_id, observation_date)
);
CREATE INDEX IF NOT EXISTS idx_obs_indicator_date ON observations(indicator_id, observation_date);
CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT,
    status TEXT,
    message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

class Repository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript(SCHEMA)

    def connect(self):
        return sqlite3.connect(self.path)

    def upsert_observations(self, indicator_id: str, df: pd.DataFrame, source: str):
        if df.empty:
            return
        rows = [(indicator_id, d.strftime("%Y-%m-%d"), float(v), source) for d, v in zip(df.observation_date, df.value)]
        with self.connect() as con:
            con.executemany(
                "INSERT INTO observations(indicator_id, observation_date, value, source) VALUES(?,?,?,?) "
                "ON CONFLICT(indicator_id, observation_date) DO UPDATE SET value=excluded.value, source=excluded.source, retrieved_at=CURRENT_TIMESTAMP",
                rows,
            )

    def load(self, indicator_id: str) -> pd.DataFrame:
        with self.connect() as con:
            df = pd.read_sql_query(
                "SELECT observation_date, value FROM observations WHERE indicator_id=? ORDER BY observation_date",
                con, params=(indicator_id,)
            )
        if not df.empty:
            df["observation_date"] = pd.to_datetime(df["observation_date"])
        return df

    def log(self, indicator_id: str, status: str, message: str):
        with self.connect() as con:
            con.execute("INSERT INTO update_log(indicator_id,status,message) VALUES(?,?,?)", (indicator_id,status,message))

    def recent_logs(self, limit: int = 100) -> pd.DataFrame:
        with self.connect() as con:
            return pd.read_sql_query("SELECT * FROM update_log ORDER BY id DESC LIMIT ?", con, params=(limit,))
