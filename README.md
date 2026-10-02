# U.S. Business Cycle Monitor

A personal Python/Streamlit macroeconomic dashboard organized around **leading, coincident, and lagging U.S. business-cycle indicators**.

## What V1 includes

- 21 cycle indicators plus 9 contextual inflation and interest-rate series.
- FRED ingestion through public CSV endpoints (no FRED API key required for V1).
- Long-history S&P 500 ingestion from Yahoo Finance (`^GSPC`).
- Explicit manual/licensed slot for ISM Manufacturing New Orders.
- Public proxies for the proprietary Leading Credit Index and the exact Conference Board consumer-expectations blend.
- SQLite persistence and raw download preservation.
- Monthly frequency harmonization without interpolating fake economic observations.
- YoY, 3M annualized and 6M annualized growth calculations.
- Rolling Z-scores, direction adjustment, clipping, momentum and breadth.
- Equal-weight leading and coincident composites.
- Transparent macro regime: Expansion / Slowdown / Recovery / Contraction.
- NBER recession shading from FRED `USREC`.
- Overview, category, indicator-research and data-health pages.

## Data choices

The project deliberately chooses the best practical source per indicator rather than forcing everything through one provider. Public FRED/government data are used where they are strong, Yahoo Finance supplies long S&P 500 history, and licensed/manual data can be inserted without changing the analytics or UI.

Three leading indicators deserve special attention:

1. **ISM New Orders** — configured as `data/manual/ism_new_orders.csv`. Supply a legitimately obtained history with `date,value` columns.
2. **Financial Conditions** — FRED `NFCI` is used as a public proxy for the proprietary Conference Board Leading Credit Index. It is inverted because tighter financial conditions are negative.
3. **Consumer Expectations** — FRED `UMCSENT` is used as a temporary public proxy. It is not the exact Conference Board/Michigan expectations blend.

## Installation (Windows / VS Code)

```powershell
cd us_business_cycle_monitor
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

On a new database the dashboard will fetch missing public series as they are requested. Use **Refresh all data** when you want to update all configured sources.

## Manual ISM file

Edit:

`data/manual/ism_new_orders.csv`

Format:

```csv
date,value
2024-01-01,52.5
2024-02-01,49.2
```

Then press **Refresh all data** in the dashboard.

## Configuration

`config/indicators.yaml` controls indicator definitions, data providers, series/tickers, transformations and economic direction.

`config/settings.yaml` controls normalization windows, clipping, neutral bands and minimum composite coverage.

This separation is intentional: signal methodology can be changed without rewriting the ingestion or UI layers.

## Project structure

```text
app.py
config/
  indicators.yaml
  settings.yaml
data/
  raw/
  database/
  manual/
src/
  data_sources/
  ingestion/
  indicators/
  analytics/
  database/
  charts/
  ui/
pages/
tests/
```

## Important analytical conventions

- **Leading composite:** directional and forward-looking; equal weighted after normalization.
- **Coincident composite:** current activity; equal weighted after normalization.
- **Lagging indicators:** shown diagnostically rather than forced into one good/bad score.
- **Direction = -1** reverses series such as initial claims, unemployment duration and financial conditions.
- **Direction = 0** retains statistical normalization but avoids a simplistic economic good/bad interpretation.
- **Quarterly series** are carried forward for monthly dashboard snapshots; no interpolated observations are created.
- **Composite coverage** is displayed. A composite is suppressed below its configured minimum coverage.

## Tests

```powershell
pytest -q
```

## Recommended next upgrades

1. Exact/licensed ISM and consumer-expectations inputs.
2. Release-date and vintage-aware ALFRED storage.
3. Historical `as-of` slider using real-time vintages.
4. Release calendar and economic surprises.
5. Recession probability models and dynamic/PCA factors only after the descriptive system is validated.

## Official release calendar

Overview shows upcoming agency reports mapped to the monitor's indicators, grouping indicators released together. Data includes the full mapped schedule, reporting periods where available, source links, feed status, last-fetch timestamps, and a separate **Refresh release calendars** button.

Sources are the [BLS iCalendar feed](https://www.bls.gov/schedule/news_release/bls.ics), [BEA iCalendar feed](https://www.bea.gov/news/schedule/icalendar), and [Census release schedule](https://www.census.gov/economic-indicators/calendar-listview.html). Times are displayed in U.S. Eastern time with daylight saving handled automatically. A release time is separate from the underlying observation date; availability through FRED may follow the agency publication.

The first implementation covers Employment Situation, CPI, Productivity and Costs, Personal Income and Outlays, factory orders, durable goods, housing permits, and business inventories. Unmapped indicators have no calendar entry. In particular, Census's nominal inventories/sales release is mapped to ISRATIO, not the separately published real CMRMTSPL series. No reporting-frequency estimates are substituted for official dates.

Feeds are loaded concurrently, cached in Streamlit for one hour and locally in `data/releases/` for six hours. Failed refreshes retain the last saved schedule with an explicit status and its original fetch timestamp. These cached dates can change and should be checked against the source. Local calendar caches are excluded from Git. Install the updated requirements after pulling changes.

## Economic themes and analyst readings

Overview groups the 30 configured series into six economic channels, each with a guiding question and dated observations. Most themes have five-year standardized signal charts and a visible primary-indicator reading; inflation shows actual rates and financial conditions also shows nominal borrowing benchmarks. Expand the detail panels for remaining indicator readings, economic mechanisms and scope qualifications. **Cycle anatomy** connects the demand pipeline, current activity, labor/income and financial feedback. The original cycle heatmaps, composite history and lagging table remain below.

Themes are configured in `config/economic_sections.yaml`; the nine contextual series do not enter the original leading or coincident composites. Missing indicators remain explicit. Standardized charts show each indicator's own configured transformation; the inflation and nominal-rate charts use actual percent units. Contextual indicators are not assigned directional good/bad interpretations.

Indicator Research also includes a deterministic **Analyst reading**. It distinguishes actual growth from historical position and compares the transformed input with exactly three months earlier when available. This differs from the dashboard's standardized momentum statistic, whose sign alone cannot establish that the underlying measure is rising or falling.

## Cross-indicator research

Below the thematic Overview, **Cross-indicator research** provides four focused comparisons: hours/payrolls, claims/payrolls, equipment orders/industrial production, and real income/sentiment. The selected pair has aligned five-year charts, a shared-month reading and a dynamic interpretation. Switch **Chart lens** between standardized signals and the underlying configured economic measures; the latter use individual units and scales.

Calculations use the latest month with finite signals and transformed inputs for both indicators. Newer individual readings are labelled separately. Agreement/divergence concerns historical position; recent strengthening/weakening uses the actual direction-adjusted transformed change from exactly three months earlier. Missing comparison months are not filled. Explanations update after data refresh, while the economic mechanism and qualifications remain fixed. Relationships are defined in `config/research_comparisons.yaml`.

## Economic tensions

The Overview connects the Coincident Composite, headline PCE YoY and NFCI at their latest shared valid month. It shows the three current readings and exact three-month changes, a dynamic joint interpretation, and conditional policy-transmission implications. Expand **Supporting evidence, mechanism & limits** for the evidence table, standardized history, definitions and qualifications.

PCE pressure is elevated when its actual YoY rate exceeds the Fed's 2% longer-run goal, and persistent when it exceeds that reference in three consecutive months. The historical Z-score is a separate comparison: near-average inflation can still be above target. Financial tightening/easing uses the actual NFCI change, separate from its source-average level and the dashboard's inverted rolling signal. An improving NFCI does not establish low borrowing costs. Missing three-month baselines withhold the directional tension case. Policy-transmission explanations are conditional scenarios, not descriptions of an actual policy action or forecasts.

[Policy-transmission background](https://www.federalreserve.gov/aboutthefed/fedexplained/monetary-policy.htm) and [NFCI methodology](https://www.chicagofed.org/research/data/nfci/about) provide the primary-source background.

The Overview's numbered chapters, shorter visible readings and expandable guides reduce default text density. Indicator colors are defined centrally in `src/charts/palette.py` and remain consistent across chart views; heatmap colors continue to encode values.

## Inflation and borrowing costs

**Inflation & cost pressure** shows headline/core CPI and PCE YoY rates, observation months, a five-year actual-rate chart and headline PCE's gap to the 2% longer-run goal. The detail panel adds MoM and three-month annualized momentum. The 2% line is the headline PCE goal and a core PCE reference, not a CPI target. Rates are calculated from seasonally adjusted FRED price indices; CPI YoY may differ slightly from BLS's published unadjusted YoY rates. Services CPI and manufacturing unit labor costs remain available as supporting detail.

**Financial conditions** adds the latest daily Fed target range, last detected range change, effective federal funds rate, overnight SOFR and 10-year Treasury yield. Change dates are when a new range was first observed in the loaded data, not FOMC announcement dates. Floating-rate loan costs depend on the contractual benchmark convention plus spreads, floors and fees; neither NFCI nor the 10-year Treasury yield is a floating-loan coupon. Actual nominal-rate history and transmission explanations are expandable.

All readings update from downloaded data after **Refresh all data**; no current rates or policy decisions are hardcoded. The header uses actual raw observation dates rather than monthly aggregation labels. The latest policy range and each benchmark can have different dates; the joint tensions section deliberately uses a shared month.

## Overview design

The Overview uses a futuristic economic command-console design: dark steel surfaces, a subtle background grid, cyan framing, military-style section labels, monospaced data and a centered instrument header. A compact release/coverage briefing replaces the side rail, giving the six economic themes more width. Chapter links jump directly to economy, relationships, tensions, cycle signals, history and diagnostics.

Charts share a restrained terminal treatment while retaining each indicator's established color. Overview heatmaps use green/rose signal colors around a dark neutral center. Composite history offers **5Y / 10Y / 20Y / Full** viewing windows (10Y initially); this changes the visible axis, not the data or calculations. Detailed explanations remain expandable.

Presentation is isolated in `src/ui/overview.css`, `src/ui/overview.py` and `src/charts/terminal.py`. The Overview stylesheet is loaded only on that page; the other pages retain their current layout and styles. Streamlit defaults to a dark theme so native tables and controls stay readable independently of the operating system's theme. Typography uses local font fallbacks and the design requires no external images, font downloads or new dependencies. Narrow screens reflow the briefing, navigation and research panels; reduced-motion settings disable smooth scrolling.
