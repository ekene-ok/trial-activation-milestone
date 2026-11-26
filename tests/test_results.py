"""Checks that the results reproduce and that the README quotes them correctly."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ["add_client", "create_quote", "schedule_job", "send_invoice", "connect_payments", "invite_team"]


def run(script):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=ROOT, capture_output=True)


def summary():
    return pd.read_csv(ROOT / "results" / "summary.csv").set_index("metric")["value"]


def test_data_is_reproducible():
    run("generate_data.py")
    first = hashlib.md5((ROOT / "data" / "trial_events.csv").read_bytes()).hexdigest()
    run("generate_data.py")
    assert hashlib.md5((ROOT / "data" / "trial_events.csv").read_bytes()).hexdigest() == first


def test_invoice_ranks_first_and_early_beats_late():
    run("run_analysis.py")
    e = pd.read_csv(ROOT / "results" / "action_effects.csv")
    assert e.iloc[0].action == "Send an invoice"
    s = summary()
    assert s["invoice_day3_effect_points"] > s["invoice_later_effect_points"]
    assert s["mobile_invoice_by_day3"] < s["desktop_invoice_by_day3"]


def test_adjustment_moves_toward_truth():
    """Raw gaps overstate; adjusted effects sit closer to estimates that also control for hidden motivation."""
    os.chdir(ROOT)
    con = duckdb.connect()
    for f in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(f.read_text())
    df = con.execute("SELECT * FROM trial_view").df().merge(pd.read_csv(ROOT / "data" / "_truth.csv"))
    X = pd.concat([df[[f"day_{a}" for a in ACTIONS]].notna().astype(int).set_axis(ACTIONS, axis=1),
                   df[["motivation"]]], axis=1)
    m = LogisticRegression(C=1e6, max_iter=2000).fit(X, df.converted_to_paid.astype(int))
    on, off = X.copy(), X.copy()
    on["add_client"], off["add_client"] = 1, 0
    truthish = (m.predict_proba(on)[:, 1] - m.predict_proba(off)[:, 1]).mean() * 100
    e = pd.read_csv(ROOT / "results" / "action_effects.csv").set_index("action")
    assert abs(truthish) < e.loc["Add a client", "adjusted_effect_points"] < e.loc["Add a client", "raw_gap_points"]


def test_readme_numbers_match_results():
    s = summary()
    e = pd.read_csv(ROOT / "results" / "action_effects.csv").set_index("action")
    readme = (ROOT / "README.md").read_text()
    inv = e.loc["Send an invoice"]
    quoted = [
        f"{s['conversion_rate'] * 100:.1f}% convert",
        f"adds {inv.adjusted_effect_points:.1f} points",
        f"{inv.ci_low_points:.1f} to {inv.ci_high_points:.1f}",
        f"at {e.loc['Connect payments', 'adjusted_effect_points']:.1f}",
        f"adds only {s['add_client_adjusted_points']:.1f}",
        f"adds {s['invoice_day3_effect_points']:.1f} points",
        f"invoicing later adds {s['invoice_later_effect_points']:.1f}",
        f"Only {s['share_invoice_by_day3'] * 100:.1f}% of trials",
        f"({s['mobile_invoice_by_day3'] * 100:.0f}% against {s['desktop_invoice_by_day3'] * 100:.0f}%)",
        f"{s['milestone_test_trials_per_arm']:,.0f} | {s['milestone_test_weeks']:.0f} weeks",
        f"{s['conversion_test_trials_per_arm']:,.0f} | {s['conversion_test_weeks']:.0f} weeks",
        f"{s['extra_paid_accounts_low']:.0f} to {s['extra_paid_accounts_high']:.0f} extra paying accounts",
        f"${s['annual_value_low_thousands']:.0f}K to ${s['annual_value_high_thousands']:.0f}K",
    ]
    for q in quoted:
        assert q in readme, q
