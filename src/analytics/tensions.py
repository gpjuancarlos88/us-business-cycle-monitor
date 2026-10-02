"""Conditional policy-transmission readings, not a policy forecast."""
from __future__ import annotations
import numpy as np
import pandas as pd


def _series(frame, name):
    if frame.empty or name not in frame:
        return pd.Series(dtype=float)
    return frame[name].replace([np.inf, -np.inf], np.nan).dropna().sort_index()


def economic_tensions(growth, inflation, financial):
    series = {
        "growth": _series(growth, "score"),
        "inflation": _series(inflation, "signal"),
        "inflation_rate": _series(inflation, "signal_input"),
        "financial": _series(financial, "signal"),
        "nfci": _series(financial, "level"),
    }
    shared = None
    for values in series.values():
        shared = values.index if shared is None else shared.intersection(values.index)
    empty = {"date": None, "headline": "Shared evidence unavailable", "summary": "Growth, services inflation and financial conditions need valid readings in the same month.", "policy": "A joint policy-transmission reading cannot be made until the three channels can be aligned.", "evidence": [], "details": [], "history": {}}
    if shared is None or shared.empty:
        return empty
    date = pd.Timestamp(shared.sort_values()[-1])
    prior = date - pd.offsets.MonthEnd(3)
    value = {key: float(values.loc[date]) for key, values in series.items()}
    changes = {key: float(values.loc[date] - values.loc[prior]) if prior in values.index else None
               for key, values in series.items()}
    # Persistence is explicitly repeated above-norm services inflation, not an
    # inflation-target test and not a statement about inflation expectations.
    persistence_dates = pd.date_range(end=date, periods=3, freq="ME")
    inflation_window = series["inflation"].reindex(persistence_dates)
    inflation_rates = series["inflation_rate"].reindex(persistence_dates)
    persistence_known = inflation_window.notna().all() and inflation_rates.notna().all()
    persistent = bool(persistence_known and (inflation_window > .25).all()
                      and (inflation_rates > 0).all())
    elevated = value["inflation"] > .25 and value["inflation_rate"] > 0
    weakening = changes["growth"] is not None and changes["growth"] < -1e-10
    strengthening = changes["growth"] is not None and changes["growth"] > 1e-10
    disinflating = changes["inflation_rate"] is not None and changes["inflation_rate"] < -1e-10 and value["inflation_rate"] > 0
    tightening = changes["nfci"] is not None and changes["nfci"] > 1e-10
    easing = changes["nfci"] is not None and changes["nfci"] < -1e-10
    incomplete = any(changes[key] is None for key in ["growth", "inflation_rate", "nfci"])
    if incomplete:
        headline = "Three-month direction incomplete"
        summary = "The current channels are aligned, but at least one exact three-month comparison is missing. A full tension reading is withheld."
        policy = "Review the current positions separately until all three directional comparisons are available."
    elif weakening and elevated:
        headline = "Activity softening · services pressure persists" if persistent else "Activity softening · services pressure elevated"
        summary = "The coincident activity signal has weakened while services inflation remains above its own rolling norm. The growth and price-pressure channels pull in different directions."
        policy = "Easier financing could support demand, while sustained services price pressure could complicate the inflation response. Tighter financing could restrain demand further. These are conditional transmission effects, not a recommendation or prediction of policy."
    elif weakening and disinflating:
        headline = "Activity softening · services disinflation"
        summary = "The activity signal and the services inflation rate have both declined over three months. Weaker demand is one possible common explanation; this comparison does not establish causation."
        policy = "Easier financing could cushion demand weakness; tighter conditions could amplify it. Services disinflation is relevant evidence, but it does not establish that broader inflation has reached the policy target."
    elif strengthening and elevated:
        headline = "Activity strengthening · services pressure elevated"
        summary = "The activity signal has strengthened while services inflation remains above its historical norm. Stronger activity does not by itself demonstrate overheating."
        policy = "Supportive financing can reinforce demand and make the persistence of price pressure relevant to policy transmission. Tighter financing can temper demand, with timing and magnitude depending on borrower exposure and credit availability."
    elif strengthening and disinflating:
        headline = "Activity strengthening · services disinflation"
        summary = "The activity signal has strengthened while the services inflation rate has fallen. Current activity and services disinflation are compatible in this snapshot."
        policy = "This combination reduces the apparent conflict between activity and services disinflation, but productivity, supply conditions and policy lags still matter. It is insufficient to establish a soft landing or a future policy path."
    else:
        headline = "No clear growth–services tension"
        summary = "The current rules do not identify a clear opposition between recent activity direction and services price pressure. That does not imply that all economic risks are resolved."
        policy = "Read financial conditions as the channel through which borrowing costs, credit access and asset prices can influence demand. Broader inflation, employment and expectations are needed to assess an actual policy decision."
    if not incomplete and elevated and disinflating:
        summary += " The services inflation rate is falling, so above-normal pressure coexists with disinflation."
    if not incomplete and tightening:
        policy += " In this snapshot, tightening conditions add a potential restraint on demand, even if their level remains historically loose."
    elif not incomplete and easing:
        policy += " In this snapshot, easing conditions could support demand, even if their level remains historically tight."
    finance_text = "NFCI has tightened over three months." if tightening else "NFCI has eased over three months." if easing else "NFCI is unchanged over three months." if changes["nfci"] is not None else "NFCI's three-month change is unavailable."
    if not incomplete:
        summary += " " + finance_text
    def change_label(change, units=""):
        return "Unavailable" if change is None else f"{change:+.3f}{units}"
    evidence = [
        {"Channel": "Growth", "Measure": "Coincident composite", "Shared reading": f"{value['growth']:+.2f}σ", "3M change": change_label(changes["growth"], "σ"), "Interpretation": "Change in a standardized activity score, not GDP growth"},
        {"Channel": "Price pressure", "Measure": "Services CPI · YoY", "Shared reading": f"{value['inflation_rate']:+.2f}%", "3M change": change_label(changes["inflation_rate"], " pp"), "Interpretation": f"{value['inflation']:+.2f}σ relative to its rolling norm"},
        {"Channel": "Financial conditions", "Measure": "NFCI · monthly mean", "Shared reading": f"{value['nfci']:+.3f}", "3M change": change_label(changes["nfci"]), "Interpretation": finance_text},
    ]
    details = [
        "Services pressure is called persistent here only when services YoY inflation is positive and its standardized signal exceeds +0.25σ in each of the latest three consecutive months." if persistent else "The latest services reading does not meet the defined three-month persistence rule." if persistence_known else "The three consecutive monthly readings needed to assess services persistence are incomplete.",
        "A falling positive inflation rate is disinflation, not a falling price level. Above-normal inflation refers to the series' own history, not the Fed's target.",
        "The NFCI level is tighter than its source's historical average when positive and looser when negative. Its three-month change is distinct from that level and from the dashboard's inverted rolling signal.",
        "The growth composite depends on the available coincident components at each date; changes can partly reflect changing coverage. None of these relationships establishes causation.",
        "Services CPI is a limited inflation lens. PCE inflation, broad labor-market slack, inflation expectations and the actual policy stance are not inputs to this section.",
    ]
    if any(values.index.max() > date for values in series.values()):
        details.append("Newer individual observations exist, but the joint reading uses the latest shared valid month.")
    return {"date": date, "headline": headline, "summary": summary, "policy": policy, "evidence": evidence,
            "details": details, "history": {"growth": series["growth"], "inflation": series["inflation"], "financial": series["financial"]},
            "persistent": persistent, "incomplete": incomplete}
