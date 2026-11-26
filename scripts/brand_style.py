"""Shared chart style for Ekene Okafor's portfolio.

One message per chart, stated in a sentence-case headline (regular weight, not bold or all caps),
a short deck underneath, one highlight colour with grey for context, direct labels instead of legends,
no gridlines, horizontal text only, bars from zero, and a source line.
Colours are validated with the dataviz palette checks (lightness band, chroma, contrast, CVD).
"""
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.transforms

INK = "#14213d"        # navy: headlines, values, key labels
MUTED = "#5f6470"      # deck, axis labels, source line (5.9:1 on white)
CONTEXT = "#c4c1ba"    # grey for everything that is not the message (always direct-labelled)
HAIRLINE = "#dedbd4"   # baselines and reference lines
SURFACE = "#ffffff"
BRAND_ACCENT = "#e0612e"  # signature orange

# One highlight colour per project, so each repo is recognisable; never mixed in one chart
PROJECT = {
    "city-expansion-scorecard": "#2a78d6",
    "campaign-uplift-targeting": "#e0612e",
    "saas-cross-sell-playbook": "#14946a",
    "business-review-agent": "#6250d6",
    "marketplace-supply-simulation": "#2f8a2f",
    "market-entry-investment-case": "#c94f86",
    "funnel-attribution-audit": "#b35900",
    "gtm-launch-playbook": "#d1495b",
    "crm-data-hygiene-audit": "#00819e",
    "marketing-workflows": "#8a6a00",
    "customer-value-emails": "#3d5a98",
    "customer-health-score": "#7a5195",
    "trial-activation-milestone": "#1b998b",
}

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": HAIRLINE,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def figure(width=8.0, height=5.0):
    """Default 8 x 5 (a 5:8 height to width ratio)."""
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    return fig, ax


def clean(ax, keep="x"):
    """Remove chart junk. keep='x' keeps a bottom baseline (vertical bars, lines);
    keep='y' keeps a left baseline (horizontal bars); keep=None removes both."""
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    if keep == "x":
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(HAIRLINE)
    if keep == "y":
        ax.spines["left"].set_visible(True)
        ax.spines["left"].set_color(HAIRLINE)
    ax.grid(False)
    ax.tick_params(length=0, labelsize=10.5, colors=MUTED)
    return ax


def headline(fig, title, deck=None):
    """Takeaway headline in sentence case, regular weight, with an optional deck."""
    fig.text(0.03, 0.965, title, fontsize=15, color=INK, ha="left", va="top")
    if deck:
        fig.text(0.03, 0.905, deck, fontsize=10.5, color=MUTED, ha="left", va="top")


def source(fig, text):
    fig.text(0.03, 0.02, f"Source: {text}", fontsize=8.5, color=MUTED, ha="left", va="bottom")


def finish(fig, path, top=0.84, bottom=0.12, left=0.08, right=0.97):
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


# Standard chart layout, set in inches so every chart has the same margins whatever its height
WIDTH = 8.0
TITLE_IN, DECK_IN, PLOT_TOP_IN = 0.28, 0.62, 1.15   # distances from the top edge
SOURCE_IN = 0.2                                      # distance from the bottom edge
LEFT_IN = 0.25                                       # left edge for headline, deck and source
VALUE = 10.5                                         # value and category label size


def chart(height=4.5, label_in=1.6, xaxis=False, right_in=0.55):
    """A figure with fixed margins. label_in is the room for category labels on the left;
    xaxis reserves room under the plot: True for tick labels plus an axis title, "ticks" for tick labels only."""
    fig = plt.figure(figsize=(WIDTH, height), dpi=200)
    bottom_in = 0.8 if xaxis == "ticks" else 1.0 if xaxis else 0.55
    left = (LEFT_IN + label_in) / WIDTH
    ax = fig.add_axes([left, bottom_in / height, 1 - left - right_in / WIDTH,
                       1 - (PLOT_TOP_IN + bottom_in) / height])
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, labelsize=VALUE, colors=MUTED)
    fig._h = height
    return fig, ax


def titles(fig, title, deck=None):
    h = fig._h
    fig.text(LEFT_IN / WIDTH, 1 - TITLE_IN / h, title, fontsize=15, color=INK, ha="left", va="center")
    if deck:
        fig.text(LEFT_IN / WIDTH, 1 - DECK_IN / h, deck, fontsize=10.5, color=MUTED, ha="left", va="center")


def credit(fig, text):
    fig.text(LEFT_IN / WIDTH, SOURCE_IN / fig._h, f"Source: {text}", fontsize=8, color=MUTED, ha="left",
             va="bottom")


def save(fig, path):
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def _row_labels(ax, ys, labels, highlight, sublabels=None):
    """Category labels at the left of the plot, with an optional smaller second line that explains them."""
    ax.set_yticks(ys)
    if not sublabels:
        ax.set_yticklabels(labels)
        for i, t in enumerate(ax.get_yticklabels()):
            t.set_color(INK if i in highlight else MUTED)
        return
    ax.set_yticklabels([""] * len(ys))
    tr = matplotlib.transforms.blended_transform_factory(ax.transAxes, ax.transData)
    for i, (y, lab, sub) in enumerate(zip(ys, labels, sublabels)):
        ax.text(-0.02, y + 0.13, lab, transform=tr, ha="right", va="center", fontsize=VALUE,
                color=INK if i in highlight else MUTED)
        ax.text(-0.02, y - 0.2, sub, transform=tr, ha="right", va="center", fontsize=8.5, color=MUTED)


def hbar(ax, labels, values, highlight, fmt, color, xmax=None, sublabels=None):
    """Horizontal bars, first item at the top. highlight: set of indexes drawn in the project colour."""
    n = len(values)
    ys = list(range(n))[::-1]
    lo = min(0, min(values))
    hi = xmax or max(values)
    span = hi - lo
    for y, v, i in zip(ys, values, range(n)):
        c = color if i in highlight else CONTEXT
        ax.barh(y, v, height=0.62, color=c, linewidth=0)
        small_neg = v < 0 and abs(v) < span * 0.05   # label a tiny negative on the right, like the rest
        ha, x = ("left", max(v, 0) + span * 0.015) if v >= 0 or small_neg else ("right", v - span * 0.015)
        ax.text(x, y, fmt[i] if isinstance(fmt, list) else fmt(v), va="center", ha=ha, fontsize=VALUE, color=INK if i in highlight else MUTED)
    _row_labels(ax, ys, labels, highlight, sublabels)
    ax.set_ylim(-0.6, n - 0.4)
    big_neg = lo < -span * 0.05
    ax.set_xlim(lo - span * 0.3 if big_neg else min(lo, 0), hi + span * 0.16)
    ax.set_xticks([])
    ax.axvline(0, color=HAIRLINE, linewidth=1)
    return ax


def vbar(ax, labels, values, highlight, fmt, color, ymax=None):
    """Vertical bars with values on top and categories underneath."""
    xs = range(len(values))
    hi = ymax or max(values)
    for x, v, i in zip(xs, values, range(len(values))):
        c = color if i in highlight else CONTEXT
        ax.bar(x, v, width=0.62, color=c, linewidth=0)
        ax.text(x, v + hi * 0.02, fmt[i] if isinstance(fmt, list) else fmt(v), ha="center", va="bottom", fontsize=VALUE,
                color=INK if i in highlight else MUTED)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels)
    for i, t in enumerate(ax.get_xticklabels()):
        t.set_color(INK if i in highlight else MUTED)
    ax.set_yticks([])
    ax.set_ylim(0, hi * 1.12)
    ax.axhline(0, color=HAIRLINE, linewidth=1)
    return ax


def dotrange(ax, labels, est, lo, hi, highlight, fmt, color, xlim=None, zero=True, sublabels=None):
    """Estimate with its interval: a dot on a range line, first item at the top."""
    n = len(est)
    ys = list(range(n))[::-1]
    for y, e, a, b_, i in zip(ys, est, lo, hi, range(n)):
        c = color if i in highlight else CONTEXT
        ax.plot([a, b_], [y, y], color=c, linewidth=2.4, solid_capstyle="round")
        ax.scatter([e], [y], s=80, color=c, zorder=3, linewidths=0)
        ax.text(e, y + 0.26, fmt(e), ha="center", va="bottom", fontsize=VALUE,
                color=INK if i in highlight else MUTED)
    _row_labels(ax, ys, labels, highlight, sublabels)
    ax.set_ylim(-0.6, n - 0.2)
    if xlim:
        ax.set_xlim(*xlim)
    ax.set_xticks([])
    if zero:
        ax.axvline(0, color=HAIRLINE, linewidth=1)
        ax.text(0, -0.55, "0", ha="center", va="top", fontsize=9, color=MUTED)
    return ax


def paired_hbar(ax, labels, before, after, highlight, fmt, color, names=("Before", "After")):
    """Two thin bars per row: before in grey, after in the project colour (grey too unless highlighted)."""
    n = len(labels)
    ys = list(range(n))[::-1]
    hi = max(max(before), max(after))
    for y, a, b_, i in zip(ys, before, after, range(n)):
        ca = color
        ax.barh(y + 0.17, a, height=0.3, color=CONTEXT, linewidth=0)
        ax.barh(y - 0.17, b_, height=0.3, color=ca, linewidth=0)
        ax.text(a + hi * 0.015, y + 0.17, fmt(a), va="center", fontsize=9.5, color=MUTED)
        ax.text(b_ + hi * 0.015, y - 0.17, fmt(b_), va="center", fontsize=VALUE,
                color=INK if i in highlight else MUTED)
    top = ys[0]
    ax.text(hi * 1.22, top + 0.17, names[0], va="center", fontsize=9, color=MUTED)
    ax.text(hi * 1.22, top - 0.17, names[1], va="center", fontsize=9, color=color)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    for i, t in enumerate(ax.get_yticklabels()):
        t.set_color(INK if i in highlight else MUTED)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(0, hi * 1.42)
    ax.set_xticks([])
    ax.axvline(0, color=HAIRLINE, linewidth=1)
    return ax


def line_axes(ax, xaxis=True, yfmt=None):
    """Line charts: keep a bottom baseline and light y tick labels, no gridlines."""
    if xaxis:
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(HAIRLINE)
    if yfmt:
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: yfmt(v)))
    return ax


STREAMLIT_THEME = """[theme]
base = "light"
primaryColor = "{accent}"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f7f6f2"
textColor = "#14213d"
font = "sans serif"
"""
