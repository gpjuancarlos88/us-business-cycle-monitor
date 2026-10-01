# U.S. Business Cycle Monitor

A personal Python/Streamlit macroeconomic dashboard organized around **leading, coincident, and lagging U.S. business-cycle indicators**.

## What V1 includes

- 21 configured macro indicators.
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
