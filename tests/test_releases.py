from datetime import date
import json

import pandas as pd
import pytest
import requests

from src.data_sources.releases import FEEDS, ReleaseCalendar, parse_census, parse_ics, upcoming_releases

ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:jobs
SEQUENCE:0
SUMMARY:Employment Situation
DTSTART;TZID=America/New_York:20261002T083000
END:VEVENT
BEGIN:VEVENT
UID:jobs
SEQUENCE:1
SUMMARY:Employment Situation
DTSTART;TZID=America/New_York:20261003T083000
END:VEVENT
BEGIN:VEVENT
UID:cpi
SUMMARY:Consumer Price Index
DTSTART;TZID=America/New_York:20261113T083000
END:VEVENT
BEGIN:VEVENT
UID:cancelled
SUMMARY:Productivity and Costs
DTSTART:20261006T123000Z
STATUS:CANCELLED
END:VEVENT
BEGIN:VEVENT
UID:income
SUMMARY:Personal Income and Outlays\\, September
 2026
DTSTART;VALUE=DATE:20261030
END:VEVENT
END:VCALENDAR
"""
SPECS = [
    {"id": "manufacturing_hours", "short_name": "Hours", "category": "leading"},
    {"id": "payrolls", "short_name": "Payrolls", "category": "coincident"},
    {"id": "services_inflation", "short_name": "Services CPI", "category": "lagging"},
    {"id": "real_income_ex_transfers", "short_name": "Income", "category": "coincident"},
]


def test_revision_cancellation_and_dst():
    events = parse_ics(ICS, "BLS", FEEDS["BLS"])
    assert len(events) == 3
    jobs = next(x for x in events if x["title"] == "Employment Situation")
    assert jobs["release_at"] == "2026-10-03T12:30:00+00:00"
    cpi = next(x for x in events if x["title"] == "Consumer Price Index")
    assert cpi["release_at"] == "2026-11-13T13:30:00+00:00"
    schedule = upcoming_releases(events, SPECS, now="2026-10-03T13:00:00Z")
    assert schedule["Indicators"].tolist() == ["Services CPI"]


def test_shared_report_grouped_and_all_day_retained():
    events = parse_ics(ICS, "BLS", FEEDS["BLS"])
    schedule = upcoming_releases(events, SPECS, now="2026-10-03T12:00:00Z")
    assert schedule.iloc[0]["Indicators"] == "Hours, Payrolls"
    bea = parse_ics(ICS, "BEA", FEEDS["BEA"])
    schedule = upcoming_releases(bea, SPECS, now="2026-10-30T18:00:00Z")
    assert len(schedule) == 1
    assert not schedule.iloc[0]["Time known"]
    assert schedule.iloc[0]["Release time (ET)"].date() == date(2026, 10, 30)


def test_census_period_and_bad_rows():
    html = """<table id='calendar'>
    <tr><th>Title</th><th>Date</th></tr>
    <tr><td><a href='/construction/nrc'>New Residential Construction (Building Permits)</a></td>
    <td>November 18, 2026</td><td>8:30 AM</td><td>October 2026</td></tr>
    <tr><td>New Residential Construction</td><td>TBD</td><td>TBD</td><td>Unknown</td></tr>
    </table>"""
    events = parse_census(html, FEEDS["Census"])
    assert len(events) == 1
    assert events[0]["period"] == "October 2026"
    assert events[0]["release_at"] == "2026-11-18T13:30:00+00:00"
    assert events[0]["indicator_ids"] == ["building_permits"]
    assert events[0]["url"] == "https://www.census.gov/construction/nrc"


@pytest.mark.parametrize("parser,args", [(parse_ics, ("BLS", FEEDS["BLS"])), (parse_census, (FEEDS["Census"],))])
def test_block_page_rejected(parser, args):
    with pytest.raises(ValueError):
        parser("<html>Access denied</html>", *args)


def test_offline_fallback_keeps_fetch_timestamp(tmp_path, monkeypatch):
    calendar = ReleaseCalendar(tmp_path)
    calendar.cache_dir.mkdir(parents=True)
    events = parse_ics(ICS, "BLS", FEEDS["BLS"])
    saved = {"fetched_at": "2026-10-01T00:00:00+00:00", "events": events}
    (calendar.cache_dir / "bls.json").write_text(json.dumps(saved))
    def offline(*args, **kwargs):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(requests, "get", offline)
    rows, status = calendar.load(now="2026-10-02T00:00:00Z")
    assert rows == events
    assert status.iloc[0]["Status"] == "Cached · refresh failed"
    assert status.iloc[0]["Last fetched (UTC)"] == saved["fetched_at"]
    assert status.iloc[1]["Status"] == "Unavailable"


def test_recent_cache_and_force_refresh(tmp_path, monkeypatch):
    calendar = ReleaseCalendar(tmp_path)
    calendar.cache_dir.mkdir(parents=True)
    saved = {"fetched_at": "2026-10-02T00:00:00+00:00", "events": parse_ics(ICS, "BLS", FEEDS["BLS"])}
    (calendar.cache_dir / "bls.json").write_text(json.dumps(saved))
    calls = []
    class Response:
        text = ICS
        def raise_for_status(self):
            pass
    def get(*args, **kwargs):
        calls.append(args[0])
        return Response()
    monkeypatch.setattr(requests, "get", get)
    now = pd.Timestamp("2026-10-02T01:00:00Z")
    _, status = calendar._load_agency("BLS", FEEDS["BLS"], now, False)
    assert status["Status"] == "Cached"
    assert not calls
    _, status = calendar._load_agency("BLS", FEEDS["BLS"], now, True)
    assert status["Status"] == "Live"
    assert len(calls) == 1
    assert json.loads((calendar.cache_dir / "bls.json").read_text())["fetched_at"] == now.isoformat()
