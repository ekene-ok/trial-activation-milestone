"""Generate synthetic free-trial data for Brightwork, a fictional scheduling and invoicing app for small trades businesses.

Every new account gets a 14-day free trial. The data covers 12,000 trials started from January to June 2026:
who signed up, which setup actions they took and on which day, and whether they converted to paid.

Planted effects the analysis has to find from the data alone:
  1. Sending a first invoice to a real client has the largest effect on conversion
  2. Sending it by day 3 matters more than sending it later
  3. Inviting a team member helps, but only for businesses with more than one person
  4. Adding a client is common but adds almost nothing on its own
  5. Mobile sign-ups take longer to reach the first invoice
  6. Motivated trial users do more of everything, so raw comparisons overstate every action

A hidden file (data/_truth.csv) holds each trial's underlying motivation. Only the tests read it.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20261126
N = 12_000
OUT = Path(__file__).resolve().parents[1] / "data"
MILESTONES = ["add_client", "create_quote", "schedule_job", "send_invoice", "connect_payments", "invite_team"]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def main():
    rng = np.random.default_rng(SEED)
    OUT.mkdir(exist_ok=True)

    ids = [f"TR-{i:05d}" for i in range(1, N + 1)]
    signup = np.datetime64("2026-01-01") + rng.integers(0, 181, N).astype("timedelta64[D]")
    trade = rng.choice(["Landscaping", "Cleaning", "Plumbing and HVAC", "Painting"], N)
    team = rng.choice(["Solo", "2 to 5", "6 or more"], N, p=[0.50, 0.35, 0.15])
    source = rng.choice(["Paid search", "Organic search", "Referral", "Partner"], N, p=[0.35, 0.30, 0.20, 0.15])
    device = np.where(rng.random(N) < 0.45, "Mobile", "Desktop")

    motivation = rng.normal(0, 1, N) + 0.3 * np.isin(source, ["Referral", "Partner"])
    mobile = device == "Mobile"
    multi = team != "Solo"

    reach_logit = {
        "add_client": 1.8 + 0.8 * motivation,
        "create_quote": 0.4 + 0.9 * motivation,
        "schedule_job": 0.2 + 0.9 * motivation,
        "send_invoice": -0.4 + 1.0 * motivation,
        "connect_payments": -1.1 + 0.9 * motivation,
        "invite_team": np.where(multi, -0.3 + 0.8 * motivation, -9.0),
    }
    mean_day = {"add_client": 0.8, "create_quote": 1.8, "schedule_job": 2.2, "send_invoice": 3.2,
                "connect_payments": 4.0, "invite_team": 3.0}

    days = {}
    for m in MILESTONES:
        reached = rng.random(N) < sigmoid(reach_logit[m])
        scale = mean_day[m] * np.where(mobile & (m == "send_invoice"), 2.0, 1.0) * np.exp(-0.25 * motivation)
        day = np.floor(rng.exponential(scale)).astype(int)
        days[m] = np.where(reached & (day <= 13), day, -1)

    inv = days["send_invoice"]
    conv_logit = (-2.75 + 0.6 * motivation
                  + 1.4 * ((inv >= 0) & (inv <= 3)) + 0.6 * (inv > 3)
                  + 0.5 * (days["connect_payments"] >= 0)
                  + 0.45 * ((days["invite_team"] >= 0) & multi)
                  + 0.15 * (days["schedule_job"] >= 0)
                  + 0.10 * (days["create_quote"] >= 0)
                  + 0.0 * (days["add_client"] >= 0))
    converted = rng.random(N) < sigmoid(conv_logit)

    trials = pd.DataFrame({"trial_id": ids, "signup_date": signup, "trade": trade, "team_size": team,
                           "signup_source": source, "signup_device": device})
    events = []
    for m in MILESTONES:
        hit = days[m] >= 0
        events.append(pd.DataFrame({"trial_id": np.array(ids)[hit], "action": m,
                                    "event_date": signup[hit] + days[m][hit].astype("timedelta64[D]")}))
    events = pd.concat(events).sort_values(["trial_id", "event_date", "action"])
    outcomes = pd.DataFrame({"trial_id": ids, "converted_to_paid": converted})

    trials.to_csv(OUT / "trials.csv", index=False)
    events.to_csv(OUT / "trial_events.csv", index=False)
    outcomes.to_csv(OUT / "trial_outcomes.csv", index=False)
    pd.DataFrame({"trial_id": ids, "motivation": motivation.round(4)}).to_csv(OUT / "_truth.csv", index=False)
    print(f"Wrote {N} trials and {len(events)} events to {OUT}")


if __name__ == "__main__":
    main()
