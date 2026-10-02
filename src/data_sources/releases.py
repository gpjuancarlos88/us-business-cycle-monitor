"""Official release schedules, independent of observation/signal dates."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from icalendar import Calendar
import pandas as pd
import requests

EASTERN = "America/New_York"
FEEDS = {
    "BLS": "https://www.bls.gov/schedule/news_release/bls.ics",
    "BEA": "https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics",
    "Census": "https://www.census.gov/economic-indicators/calendar-listview.html",
}
# These are release-to-series mappings, not inferred reporting-frequency dates.
MAPPINGS = {
    "BLS": {
        "employment situation": ("manufacturing_hours", "payrolls", "unemployment_duration"),
        "consumer price index": ("services_inflation",),
        "productivity and costs": ("unit_labor_costs",),
    },
    "BEA": {"personal income and outlays": ("real_income_ex_transfers",)},
    "Census": {
        "full report - manufacturers": ("consumer_goods_orders",),
        "advance report on durable goods": ("cap_goods_ex_air",),
        "new residential construction": ("building_permits",),
        "manufacturing and trade: inventories and sales": ("inventory_sales_ratio",),
    },
}


def _event(agency, title, when, url, period="", time_known=True):
    title = " ".join(title.split())
    ids = next((ids for prefix, ids in MAPPINGS[agency].items()
                if title.casefold().startswith(prefix)), ())
    stamp = pd.Timestamp(when)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize(EASTERN)
    return {"agency": agency, "title": title, "release_at": stamp.tz_convert("UTC").isoformat(),
            "url": url, "period": period, "indicator_ids": list(ids), "time_known": time_known}


def parse_ics(payload: str, agency: str, url: str) -> list[dict]:
    if "BEGIN:VCALENDAR" not in payload:
        raise ValueError("Expected an iCalendar feed")
    calendar = Calendar.from_ical(payload)
    # Respect schedule revisions and cancellations when UIDs repeat.
    latest = {}
    for event in calendar.walk("VEVENT"):
        key = str(event.get("UID", str(event.get("SUMMARY")) + str(event.get("DTSTART"))))
        if key not in latest or int(event.get("SEQUENCE", 0)) >= int(latest[key].get("SEQUENCE", 0)):
            latest[key] = event
    rows = []
    for event in latest.values():
        if str(event.get("STATUS", "")).upper() == "CANCELLED" or "DTSTART" not in event:
            continue
        when = event.decoded("DTSTART")
        rows.append(_event(agency, str(event.get("SUMMARY", "")), when, url,
                           time_known=isinstance(when, datetime)))
    if not rows:
        raise ValueError("No release events found")
    return rows


def parse_census(payload: str, url: str) -> list[dict]:
    soup = BeautifulSoup(payload, "html.parser")
    table = soup.find("table", id="calendar")
    if table is None:
        raise ValueError("Census calendar table not found")
    rows = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        title, date, time, period = [" ".join(c.stripped_strings) for c in cells[:4]]
        try:
            when = datetime.strptime(f"{date} {time}", "%B %d, %Y %I:%M %p")
        except ValueError:
            continue  # Never invent a date/time for unscheduled or malformed rows.
        link = cells[0].find("a", href=True)
        rows.append(_event("Census", title, when, urljoin(url, link["href"]) if link else url, period))
    if not rows:
        raise ValueError("No dated Census releases found")
    return rows


class ReleaseCalendar:
    def __init__(self, project_root: str | Path):
        self.cache_dir = Path(project_root) / "data" / "releases"

    def _load_agency(self, agency, url, now, force):
        path = self.cache_dir / f"{agency.lower()}.json"
        cached = None
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            # Validate before accepting an old/local cache.
            pd.Timestamp(cached["fetched_at"])
            for event in cached["events"]:
                pd.Timestamp(event["release_at"])
                event["indicator_ids"]
        except (OSError, ValueError, KeyError, TypeError):
            cached = None
        if cached and not force and pd.Timedelta(0) <= now - pd.Timestamp(cached["fetched_at"]) < pd.Timedelta(hours=6):
            return cached["events"], {"Agency": agency, "Status": "Cached", "Last fetched (UTC)": cached["fetched_at"], "Detail": "", "Source": url}
        try:
            response = requests.get(url, timeout=(10, 20), headers={"User-Agent": "USBusinessCycleMonitor/1.0"})
            response.raise_for_status()
            events = parse_census(response.text, url) if agency == "Census" else parse_ics(response.text, agency, url)
            saved = {"fetched_at": now.isoformat(), "events": events}
            detail = ""
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(".tmp")
                temporary.write_text(json.dumps(saved), encoding="utf-8")
                temporary.replace(path)
            except OSError:
                detail = "Live schedule loaded; local cache could not be saved."
            return events, {"Agency": agency, "Status": "Live", "Last fetched (UTC)": saved["fetched_at"], "Detail": detail, "Source": url}
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            return (cached["events"] if cached else []), {
                "Agency": agency, "Status": "Cached · refresh failed" if cached else "Unavailable",
                "Last fetched (UTC)": cached["fetched_at"] if cached else "Never",
                "Detail": str(exc), "Source": url,
            }

    def load(self, force=False, now=None):
        now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        with ThreadPoolExecutor(max_workers=len(FEEDS)) as pool:
            results = list(pool.map(lambda item: self._load_agency(*item, now, force), FEEDS.items()))
        events = [event for rows, _ in results for event in rows]
        return events, pd.DataFrame([status for _, status in results])


def upcoming_releases(events, registry, now=None, limit=None):
    now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    if now.tzinfo is None:
        now = now.tz_localize(EASTERN)
    specs = {spec["id"]: spec for spec in registry}
    rows = []
    for event in events:
        when = pd.Timestamp(event["release_at"]).tz_convert(EASTERN)
        # Keep all-day releases visible throughout their date without inventing a time.
        if (when < now if event["time_known"] else when.date() < now.tz_convert(EASTERN).date()):
            continue
        matched = [specs[key] for key in event["indicator_ids"] if key in specs]
        if not matched:
            continue
        rows.append({"Release": event["title"], "Release time (ET)": when,
                     "Indicators": ", ".join(spec["short_name"] for spec in matched),
                     "Categories": ", ".join(dict.fromkeys(spec["category"].title() for spec in matched)),
                     "Agency": event["agency"], "Period": event["period"],
                     "Time known": event["time_known"], "Source": event["url"]})
    columns = ["Release", "Release time (ET)", "Indicators", "Categories", "Agency", "Period", "Time known", "Source"]
    result = pd.DataFrame(rows, columns=columns)
    if not result.empty:
        result = result.drop_duplicates(subset=["Release", "Release time (ET)", "Period"]).sort_values("Release time (ET)")
    return result.head(limit) if limit is not None else result
