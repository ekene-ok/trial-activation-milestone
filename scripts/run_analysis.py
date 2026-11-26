"""Find the trial action most tied to converting, check how fast it has to happen, and size the test that would prove it.

Raw gaps (convert rate with an action minus without) overstate every action, because motivated trial users
do more of everything. So each action's effect is also estimated with a logistic regression that holds the
other actions and the sign-up profile (trade, team size, source, device) constant, reported as the average
change in conversion probability (percentage points), with a 300-sample bootstrap interval.

This is still observational. The README recommends a randomized onboarding test, sized here.
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
ACTIONS = {"add_client": "Add a client", "create_quote": "Create a quote", "schedule_job": "Schedule a job",
           "send_invoice": "Send an invoice", "connect_payments": "Connect payments",
           "invite_team": "Invite a team member"}
CONTROLS = ["trade", "team_size", "signup_source", "signup_device"]
BOOT = 300
SEED = 11
TRIALS_PER_YEAR = 24_000          # assumption: the January to June volume, twice
ANNUAL_REVENUE_PER_ACCOUNT = 948  # assumption: $79 a month
SHIFT = (0.05, 0.10)              # assumption: onboarding moves 5 to 10 more trials in 100 to invoice by day 3
MILESTONE_LIFT = 0.05             # test stage 1: invoice-by-day-3 rate, smallest lift worth detecting
CONVERSION_LIFT = 0.025           # test stage 2: conversion, smallest lift worth detecting


def run_sql(con):
    for f in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(f.read_text())


def design(df, flags):
    X = pd.concat([df[flags].astype(int), pd.get_dummies(df[CONTROLS], drop_first=True).astype(int)], axis=1)
    return X


def fit(X, y):
    return LogisticRegression(C=1e6, max_iter=2000).fit(X, y)


def ame(model, X, col, rows=None):
    """Average change in predicted conversion when col is switched from 0 to 1."""
    Xs = X if rows is None else X[rows]
    on, off = Xs.copy(), Xs.copy()
    on[col], off[col] = 1, 0
    return model.predict_proba(on)[:, 1].mean() - model.predict_proba(off)[:, 1].mean()


def effects(df, flags, targets, rng):
    y = df.converted_to_paid.astype(int)
    X = design(df, flags)
    m = fit(X, y)
    multi = (df.team_size != "Solo").values
    rows_for = {c: (multi if c == "invite_team" else None) for c in targets}
    est = {c: ame(m, X, c, rows_for[c]) for c in targets}
    boots = {c: [] for c in targets}
    for _ in range(BOOT):
        idx = rng.integers(0, len(df), len(df))
        Xb, yb = X.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)
        mb = fit(Xb, yb)
        mult = multi[idx]
        for c in targets:
            boots[c].append(ame(mb, Xb, c, mult if c == "invite_team" else None))
    return {c: (est[c], *np.quantile(boots[c], [0.025, 0.975])) for c in targets}


def sample_per_arm(p0, lift, alpha=0.05, power=0.80):
    p1 = p0 + lift
    pbar = (p0 + p1) / 2
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    n = (za * np.sqrt(2 * pbar * (1 - pbar)) + zb * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2 / lift ** 2
    return int(np.ceil(n))


def main():
    RES.mkdir(exist_ok=True)
    os.chdir(ROOT)
    con = duckdb.connect()
    run_sql(con)
    for t in ["milestone_raw", "invoice_timing", "invoice_by_day3_segments"]:
        con.execute(f"SELECT * FROM {t}").df().to_csv(RES / f"{t}.csv", index=False)

    df = con.execute("SELECT * FROM trial_view").df()
    for a in ACTIONS:
        df[a] = df[f"day_{a}"].notna()
    df["invoice_by_day3"] = df.day_send_invoice.notna() & (df.day_send_invoice <= 3)
    df["invoice_after_day3"] = df.day_send_invoice.notna() & (df.day_send_invoice > 3)
    rng = np.random.default_rng(SEED)

    # Adjusted effect of each action, holding the others and the sign-up profile constant
    adj = effects(df, list(ACTIONS), list(ACTIONS), rng)
    raw = pd.read_csv(RES / "milestone_raw.csv").set_index("action")
    rows = []
    for a, label in ACTIONS.items():
        e, lo, hi = adj[a]
        rows.append({"action": label, "share_reaching": raw.loc[label, "share_reaching"],
                     "raw_gap_points": round(raw.loc[label, "raw_gap"] * 100, 1),
                     "adjusted_effect_points": round(e * 100, 1),
                     "ci_low_points": round(lo * 100, 1), "ci_high_points": round(hi * 100, 1)})
    eff = pd.DataFrame(rows).sort_values("adjusted_effect_points", ascending=False)
    eff.to_csv(RES / "action_effects.csv", index=False)

    # Timing: invoice by day 3 versus later, both against never
    timing_flags = ["add_client", "create_quote", "schedule_job", "invoice_by_day3", "invoice_after_day3",
                    "connect_payments", "invite_team"]
    tim = effects(df, timing_flags, ["invoice_by_day3", "invoice_after_day3"], rng)
    timing = pd.DataFrame([{"first_invoice": k, "adjusted_effect_points": round(v[0] * 100, 1),
                            "ci_low_points": round(v[1] * 100, 1), "ci_high_points": round(v[2] * 100, 1)}
                           for k, v in tim.items()])
    timing.to_csv(RES / "invoice_timing_effects.csv", index=False)

    # Test sizing and value
    p0 = df.converted_to_paid.mean()
    m0 = df.invoice_by_day3.mean()
    weekly = len(df) / 26
    n_milestone = sample_per_arm(m0, MILESTONE_LIFT)
    n_conversion = sample_per_arm(p0, CONVERSION_LIFT)
    weeks_milestone = int(np.ceil(2 * n_milestone / weekly))
    weeks_conversion = int(np.ceil(2 * n_conversion / weekly))
    day3_effect = tim["invoice_by_day3"][0]
    # The adjusted effect is an upper bound (leftover bias), so the low case uses half of it
    extra = [TRIALS_PER_YEAR * SHIFT[0] * day3_effect / 2, TRIALS_PER_YEAR * SHIFT[1] * day3_effect]
    value = [round(x * ANNUAL_REVENUE_PER_ACCOUNT / 1e3) for x in extra]

    seg = pd.read_csv(RES / "invoice_by_day3_segments.csv")
    dev = seg[seg.cut == "Device"].set_index("segment").share_invoice_by_day3
    summary = pd.DataFrame([
        ("trials", len(df)),
        ("conversion_rate", round(p0, 3)),
        ("share_invoice_by_day3", round(df.invoice_by_day3.mean(), 3)),
        ("invoice_day3_effect_points", round(day3_effect * 100, 1)),
        ("invoice_later_effect_points", round(tim["invoice_after_day3"][0] * 100, 1)),
        ("mobile_invoice_by_day3", dev["Mobile"]),
        ("desktop_invoice_by_day3", dev["Desktop"]),
        ("add_client_adjusted_points", float(eff.set_index("action").loc["Add a client", "adjusted_effect_points"])),
        ("milestone_test_lift_points", MILESTONE_LIFT * 100),
        ("milestone_test_trials_per_arm", n_milestone),
        ("milestone_test_weeks", weeks_milestone),
        ("conversion_test_lift_points", CONVERSION_LIFT * 100),
        ("conversion_test_trials_per_arm", n_conversion),
        ("conversion_test_weeks", weeks_conversion),
        ("weekly_trials", round(weekly)),
        ("extra_paid_accounts_low", round(extra[0])),
        ("extra_paid_accounts_high", round(extra[1])),
        ("annual_value_low_thousands", value[0]),
        ("annual_value_high_thousands", value[1]),
    ], columns=["metric", "value"])
    summary.to_csv(RES / "summary.csv", index=False)
    print(summary.to_string(index=False))
    print(eff.to_string(index=False))
    print(timing.to_string(index=False))


if __name__ == "__main__":
    main()
