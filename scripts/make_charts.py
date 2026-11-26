"""Draw the README charts from the results files."""
from pathlib import Path
import pandas as pd
import brand_style as bs

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results", ROOT / "charts"
C = bs.PROJECT["trial-activation-milestone"]
SRC = "Brightwork synthetic trial data, 12,000 free trials, January to June 2026"


def main():
    OUT.mkdir(exist_ok=True)

    # 1. Which action matters most, after adjustment
    e = pd.read_csv(RES / "action_effects.csv")
    fig, ax = bs.chart(height=4.8, label_in=2.1)
    bs.titles(fig, "Sending a first invoice is the action most tied to paying",
              "Change in conversion when a trial takes the action, other actions and sign-up profile held constant")
    bs.hbar(ax, list(e.action), list(e.adjusted_effect_points), {0}, lambda v: f"+{v:.0f} pts", C, xmax=25,
            sublabels=[f"done by {r:.0%} of teams of 2+" if a == "Invite a team member" else f"done by {r:.0%} of trials"
                       for a, r in zip(e.action, e.share_reaching)])
    bs.credit(fig, SRC)
    bs.save(fig, OUT / "01_action_effects.png")

    # 2. Timing of the first invoice
    t = pd.read_csv(RES / "invoice_timing.csv")
    fig, ax = bs.chart(height=4.3, label_in=0.0, xaxis="ticks")
    first = t.iloc[:2]
    early = (first.conversion_rate * first.trials).sum() / first.trials.sum() * 100
    bs.titles(fig, f"Trials that invoice by day 3 convert at about {early:.0f}%; those that never do, "
                   f"{t.conversion_rate.iloc[-1] * 100:.0f}%",
              "Conversion to paid by the day of the first invoice (day 0 is the sign-up day)")
    bs.vbar(ax, list(t.first_invoice), list(t.conversion_rate * 100), {0, 1}, lambda v: f"{v:.0f}%", C, ymax=45)
    bs.credit(fig, SRC)
    bs.save(fig, OUT / "02_invoice_timing.png")

    # 3. Who gets there by day 3
    s = pd.read_csv(RES / "invoice_by_day3_segments.csv")
    d = s[s.cut == "Device"].set_index("segment").loc[["Mobile", "Desktop"]]
    fig, ax = bs.chart(height=3.4, label_in=1.6)
    bs.titles(fig, "Mobile sign-ups are less likely to send an invoice by day 3",
              "Share of trials that send a first invoice by day 3, by sign-up device")
    bs.hbar(ax, ["Mobile", "Desktop"], list(d.share_invoice_by_day3 * 100), {0}, lambda v: f"{v:.0f}%", C,
            xmax=40, sublabels=[f"{n:,} trials" for n in d.trials])
    bs.credit(fig, SRC)
    bs.save(fig, OUT / "03_mobile_gap.png")
    print("charts saved")


if __name__ == "__main__":
    main()
