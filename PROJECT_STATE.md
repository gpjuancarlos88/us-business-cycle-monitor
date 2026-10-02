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
- release dates are currently estimated from reporting frequency, not yet official release calendars

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
Current release dates are estimated using indicator frequency.
Planned upgrade:
- replace estimates with exact official release calendars from BLS, BEA, Census, Federal Reserve, etc.
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
1. Official economic release calendar
2. Better semantic status colors for improving / neutral / deteriorating
3. Auto-generated short analyst interpretation per indicator
4. Historical as-of slider / vintage data
5. More consistent institutional styling across Leading, Coincident, Lagging, Indicator, and Data pages
6. Potential release surprise tracking: Actual vs Consensus vs Prior
7. Data freshness/staleness indicators
