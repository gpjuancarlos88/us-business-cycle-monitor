# U.S. Business Cycle Monitor — Project State

## Source of truth
- Repository: `gpjuancarlos88/us-business-cycle-monitor`
- Active development branch: `dev`
- Stable branch: `main`
- Local workflow: VS Code + Streamlit + GitHub
- Normal update workflow: make changes on `dev`, then local `git pull`
- Streamlit entrypoint: `streamlit run app.py`

## Project goal
A personal U.S. macroeconomic research terminal that monitors leading, coincident, and lagging business-cycle indicators with historical trends, standardized signals, composites, regime classification, recession shading, release information, and educational indicator pages.

## Core stack
- Python
- Streamlit
- Plotly
- pandas / numpy
- SQLite
- FRED public CSV
- Yahoo Finance for S&P 500
- Manual CSV support for proprietary/licensed data

## Indicator universe
### Leading (10)
1. Manufacturing Weekly Hours — AWHMAN
2. Initial Jobless Claims — ICSA
3. Consumer Goods Orders — ACOGNO
4. ISM Manufacturing New Orders — manual/licensed CSV
5. Nondefense Capital Goods ex Aircraft — NEWORDER
6. Building Permits — PERMIT
7. S&P 500 — Yahoo `^GSPC`
8. Financial Conditions proxy — NFCI
9. 10Y Treasury minus Fed Funds — T10YFF
10. Consumer Expectations proxy — UMCSENT

### Coincident (4)
1. Payrolls — PAYEMS
2. Industrial Production — INDPRO
3. Real Personal Income ex Transfers — W875RX1
4. Real Manufacturing & Trade Sales — CMRMTSPL

### Lagging (7)
1. Average Duration Unemployment — UEMPMEAN
2. Inventory/Sales — ISRATIO
3. Services Inflation — CUSR0000SAS
4. Manufacturing Unit Labor Costs — ULCMFG
5. Real C&I Loans — BUSLOANS deflated by PCEPI
6. Consumer Credit / Personal Income — TOTALSL / PI
7. Prime Rate — DPRIME

## Signal methodology
- Raw Data → Economic Transformation → Standardized Signal
- Rolling Z-score: 120 months
- Minimum observations: 36
- Composite signal clipping: ±3σ
- Direction multiplier:
  - +1 = higher is stronger
  - -1 = higher is weaker
  - 0 = contextual
- Positive breadth: share of available signals > +0.25σ
- Leading composite minimum coverage: 7/10
- Coincident composite minimum coverage: 3/4
- Equal-weight composites
- Macro regime:
  - Growth = latest Coincident Composite
  - Momentum = 70% Leading Composite + 30% 3-month change in Coincident Composite
  - Expansion / Slowdown / Recovery / Contraction / Transition

## Important implementation fixes already made
- Coverage, breadth, and composite now use the same latest valid composite date.
- Individual indicator charts start at their first available non-missing datapoint.
- Indicator charts include Robust vs Full y-axis scaling for extreme outliers such as COVID.
- Robust scale changes only the visible y-axis, never the underlying data.
- Indicator pages contain:
  - Leading / Coincident / Lagging classification
  - What it is
  - Why it matters
  - metrics
  - chart
  - source/frequency/quality
- Heatmaps label indicators with:
  - (LEI)
  - (C)
  - (Lag)
- Heatmap guide explains Z-scores, Signal, Momentum, and interpretation.
- Composite History includes an interpretation guide.
- Recession shading uses visible Dim Grey bands behind the lines.

## Current UI direction
Design target: professional institutional macro/research terminal, with inspiration from the SpaceX website's use of:
- full-width sections
- strong typography
- restrained borders
- large spacing
- subtle background shifts
- minimal card-like UI

### Palette
- Onyx: `#0C120C`
- Brick Ember: `#C20114`
- Dim Grey: `#6D7275`
- Ash Grey: `#C7D6D5`
- Ghost White: `#ECEBF3`

### Typography
Institutional sans-serif stack:
`Inter, Segoe UI, Helvetica Neue, Arial, sans-serif`

### Navigation
- Streamlit sidebar hidden
- Horizontal navigation across top:
  - Overview
  - Leading
  - Coincident
  - Lagging
  - Indicator
  - Data
- Navigation is fixed below Streamlit's own top toolbar
- Dark Onyx background
- Brick Ember active/hover state

## Overview layout
### Hero
Centered:
- U.S. Business Cycle Monitor
- subtitle
- DATA THROUGH
- SESSION REFRESH
- centered Refresh all data button

### Left analyst rail
A separate, subtle vertical section containing:
- Upcoming releases
- What to watch
- sticky behavior intended while scrolling
- release rows show date, indicator, category
- release dates now come from official BLS, BEA and Census schedules for mapped indicators
- report rows group all affected indicators and display U.S. Eastern release times

### Main section
- Hero summary metrics:
  - Macro Regime
  - Growth
  - Momentum
  - Latest Common Signal
- Compact signal strip:
  - Leading
  - Coincident
  - Leading breadth
  - Coincident breadth
  - Coverage
- Leading heatmap
- Coincident heatmap
- Composite History
- Lagging Conditions

## Metric help text
Overview hover explanations exist for:
- Growth
- Momentum
- Composite
- Positive breadth
- Coverage

These explain both economic meaning and exact dashboard calculation.

## Chart styling
- Transparent Plotly paper/plot backgrounds
- Institutional font
- subdued grid lines
- unified hover mode
- minimal chart chrome
- Plotly mode bar hidden
- recession bands rendered behind lines

## Data / release roadmap
Official release calendar implemented for BLS, BEA and Census:
- modular source adapter: `src/data_sources/releases.py`
- BLS / BEA iCalendar feeds and Census calendar table
- 10 mapped indicators across 8 report families; shared reports are grouped
- UTC storage and U.S. Eastern display, including daylight saving
- calendar feed status, original fetch timestamps and manual refresh on Data
- one-hour Streamlit cache and six-hour disk cache; failed refreshes retain a clearly labelled saved schedule
- cache directory `data/releases/` is ignored by Git
- no inferred dates for unmapped indicators; official report dates do not imply immediate FRED availability

Remaining upgrades:
- add Federal Reserve, DOL, Chicago Fed, Michigan and ISM release schedules
- add publication calendar for real manufacturing/trade sales separately from nominal Census sales
- eventually track observation date separately from release date
- later add historical as-of/vintage mode

## Streamlit / Windows workflow
Typical local commands:

```powershell
git checkout dev
git pull
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Streamlit config:
```toml
[server]
runOnSave = true
fileWatcherType = "auto"
```

If Windows file watching becomes unreliable, switch to:
```toml
fileWatcherType = "poll"
```

## Important Git workflow rule
Do not edit `main` during active development.
All iterative changes go to `dev`.

Before pulling:
```powershell
git status
```

If clean:
```powershell
git pull
```

## Known design principle
Avoid heavy rounded cards and excessive shadows. Prefer:
- section spacing
- subtle separators
- restrained background changes
- semantic use of color
- strong hierarchy through typography

Brick Ember should remain scarce and meaningful rather than decorative.

## Next high-value upgrades
1. Extend official release-calendar coverage beyond BLS / BEA / Census
2. Better semantic status colors for improving / neutral / deteriorating
3. Refine theme and cross-indicator interpretations
4. Historical as-of slider / vintage data
5. More consistent institutional styling across Leading, Coincident, Lagging, Indicator, and Data pages
6. Potential release surprise tracking: Actual vs Consensus vs Prior
7. Data freshness/staleness indicators

## Latest continuation — 2026-10-02
- Implemented the first official release-calendar layer on `dev`.
- Preserved the centered hero/refresh control, established palette, charts and signal calculations.
- New dependencies: `icalendar`, `beautifulsoup4`, `tzdata` (important for Windows timezone support).
- Regression tests cover daylight saving, calendar revisions/cancellations, shared reports, all-day events, Census periods, blocked feed responses, offline fallback and forced refresh.
- Next priority: extend calendar coverage and add freshness indicators; vintage-aware storage is still future work.

## Economic research Overview — 2026-10-02
- User priority: deepen economic understanding and create an exceptional personal terminal; V1 freshness/vintage refinements are deferred.
- Overview now opens with six economic themes before the existing cycle heatmaps: Growth & activity, Labor market, Household demand, Investment & inventories, Inflation & cost pressure, Financial conditions.
- `config/economic_sections.yaml` groups all 21 configured indicators, with each theme's question, transmission mechanism and scope qualifications.
- `src/ui/research.py` renders restrained two-column sections, observation-month labels, five-year standardized histories, visible primary-indicator readings and expandable evidence for every indicator.
- Cycle anatomy explains the pipeline and financial feedback in an expandable section. Existing composites, charts, centered header and refresh button are retained.
- `src/analytics/interpretations.py` generates deterministic readings: actual growth/return where applicable, historical position, actual three-month transformed change and indicator-specific qualifications.
- Interpretations use the raw transformed change for direction, not the standardized momentum score. An above-average change can still be negative.
- Inverted indicators describe underlying historical position correctly; contextual indicators are not assigned good/bad interpretations.
- Indicator Research includes an Analyst reading; contextual metric labels now say Contextual.
- No theme composites, GDP estimates, forecasts, new data sources or model-generated economic claims are introduced.
- Verification: 21 tests pass; Streamlit component smoke checks cover the complete Overview and contextual indicator selection. Browser screenshot verification was blocked by the local-preview environment.
- Next design/content iteration: review the six-theme layout with the user's actual data, refine comparative readings across related indicators, and consider direct consumption/GDP/inflation measures if the user wants to broaden the universe.

## Cross-indicator research — 2026-10-02
- Added a focused research workspace after the six economic themes and before the original cycle evidence.
- Four selectable relationships: Hours vs payrolls, Claims vs payrolls, Orders vs production, Income vs sentiment.
- Configuration: `config/research_comparisons.yaml`; calculations: `src/analytics/comparisons.py`; rendering: `src/ui/research.py`.
- Interpretations and numeric readings use the latest exact shared month with finite signals, levels and transformed inputs. A newer valid individual month is labelled separately; missing months are not imputed.
- Agreement/divergence describes direction-adjusted historical position relative to ±0.25σ, separately from recent underlying direction over exactly three months.
- Actual transformed changes determine strengthening/weakening; standardized momentum is not used for that decision.
- Two aligned five-year charts support Standardized signal (shared ±3.2σ axes) or Economic measure (individual native units/scales). A vertical dashed line marks the shared reading month.
- Economic mechanism and relationship-specific interpretation limits are expandable. Claims inversion and sector/nominal-versus-real differences are explicit.
- No additional indicators, forecasts, theme composites or ingestion changes.
- Verification: 33 tests pass; complete Overview component smoke checks cover all four relationships and the economic-measure switch. The previously documented browser screenshot limitation still applies.

## Economic tensions and visual refinement — 2026-10-02
- User requested an Economic Tensions section and visual refinement, rather than a broader indicator universe.
- New section after Cross-indicator Research connects the Coincident Composite, services CPI YoY and NFCI at their latest shared valid month.
- `src/analytics/tensions.py` separates levels, three-month changes and three-month services persistence. Services pressure is persistent only with positive YoY inflation and standardized signals above +0.25σ for three consecutive months; this is not a policy-target comparison.
- Cases include weakening activity with elevated/persistent services inflation, weakening activity with disinflation, strengthening activity with elevated services pressure, strengthening activity with disinflation, mixed evidence and incomplete direction.
- Financial tightening/easing uses the actual NFCI level change, independently of its historically tight/loose level and the dashboard's inverted rolling signal.
- Visible summary and policy-transmission reading update after data refresh. Supporting evidence, standardized chart, exact definitions and qualifications are expandable. Explanations are conditional mechanisms rather than a Fed forecast.
- Methodology sources: Federal Reserve's Fed Explained monetary-policy chapter and Chicago Fed NFCI methodology (linked in the section).
- Central palette `src/charts/palette.py` gives stable colors across themes, comparisons, tensions, Indicator Research and composite charts. Colors identify series rather than good/bad outcomes; heatmap colors still encode signal values.
- Overview now has six numbered chapter breaks with subtle background shifts and stronger separators. Default theme, comparison and analyst readings are shorter; full interpretations, qualifications and chart guides remain expandable.
- No source, indicator-universe, signal-methodology or refresh-workflow changes.
- Verification: 46 tests pass, including tension cases, exact shared months, missing baselines/persistence observations, NFCI level/direction distinctions and chart-color consistency. Overview smoke checks show 12 charts and 13 expanders; comparison controls pass. Screenshot verification remains unavailable in this environment.
