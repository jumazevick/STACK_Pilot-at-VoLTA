from __future__ import annotations

from collections import Counter, OrderedDict
from pathlib import Path
import csv

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
CODED_RESPONSES = ROOT / "outputs" / "summary" / "coded_open_responses_manual_review.csv"
OUTPUT = ROOT / "outputs" / "summary" / "reported_difficulties.png"


BUCKET_ORDER = [
    "Feedback interpretation",
    "Syntax / representation",
    "Mathematical difficulty",
    "Instructions / question clarity",
]

BUCKET_PREFERRED_THEMES = {
    "Feedback interpretation": [
        "Used feedback to understand error",
        "Rechecked calculations",
        "Reviewed notes/materials",
        "Sought external help",
    ],
    "Syntax / representation": [
        "Syntax / answer formatting",
        "System rigidity / correct answer rejected",
        "Syntax / formatting difficulty",
    ],
    "Mathematical difficulty": [
        "Mathematical difficulty",
        "Mathematical understanding",
        "Calculations / algebraic manipulation",
        "Powers and roots difficulty",
        "Modulus and argument difficulty",
    ],
    "Instructions / question clarity": [
        "Instruction / clarity issue",
        "Feedback / instruction clarity",
    ],
}

THEME_TO_BUCKET = {
    "Syntax / answer formatting": "Syntax / representation",
    "System rigidity / correct answer rejected": "Syntax / representation",
    "Syntax / formatting difficulty": "Syntax / representation",
    "Mathematical difficulty": "Mathematical difficulty",
    "Mathematical understanding": "Mathematical difficulty",
    "Calculations / algebraic manipulation": "Mathematical difficulty",
    "Powers and roots difficulty": "Mathematical difficulty",
    "Modulus and argument difficulty": "Mathematical difficulty",
    "Used feedback to understand error": "Feedback interpretation",
    "Reviewed notes/materials": "Feedback interpretation",
    "Sought external help": "Feedback interpretation",
    "Rechecked calculations": "Feedback interpretation",
    "Changed approach/method": "Feedback interpretation",
    "Changed answer format": "Feedback interpretation",
    "Tried again": "Feedback interpretation",
    "Instruction / clarity issue": "Instructions / question clarity",
    "Feedback / instruction clarity": "Instructions / question clarity",
}


def wrap_text(text: str, width: int = 52) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        extra = len(word) if not current else len(word) + 1
        if current and length + extra > width:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += extra
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def shorten_quote(text: str, limit: int = 185) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rsplit(" ", 1)[0] + "..."


def read_rows() -> list[dict[str, str]]:
    with CODED_RESPONSES.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def count_buckets(rows: list[dict[str, str]]) -> OrderedDict[str, int]:
    counts = Counter()
    for row in rows:
        themes = [t.strip() for t in row.get("Assigned Themes", "").split(";") if t.strip()]
        for theme in themes:
            bucket = THEME_TO_BUCKET.get(theme)
            if bucket:
                counts[bucket] += 1
    ordered = OrderedDict()
    for bucket in BUCKET_ORDER:
        ordered[bucket] = counts.get(bucket, 0)
    return ordered


def pick_quotes(rows: list[dict[str, str]]) -> dict[str, str]:
    examples: dict[str, str] = {}
    used_rows: set[str] = set()
    min_len = 50
    max_len = 220

    for bucket, preferred_themes in BUCKET_PREFERRED_THEMES.items():
        candidates: list[tuple[int, str, str]] = []
        for row in rows:
            row_id = row.get("Student_Index", "")
            if row_id in used_rows:
                continue
            themes = [t.strip() for t in row.get("Assigned Themes", "").split(";") if t.strip()]
            if not any(theme in themes for theme in preferred_themes):
                continue
            text = " ".join(row.get("Response", "").split())
            if not text:
                continue
            candidates.append((len(text), row_id, text))

        if candidates:
            in_range = [item for item in candidates if min_len <= item[0] <= max_len]
            pool = in_range if in_range else candidates
            _, row_id, text = min(pool, key=lambda item: item[0])
            examples[bucket] = shorten_quote(text)
            used_rows.add(row_id)

    return examples


def add_quote_card(ax, y_pos: float, bucket: str, quote: str) -> None:
    card = FancyBboxPatch(
        (0.02, y_pos - 0.28),
        0.96,
        0.26,
        boxstyle="round,pad=0.018,rounding_size=0.015",
        linewidth=1.0,
        edgecolor="#d1d5db",
        facecolor="#f9fafb",
        transform=ax.transAxes,
    )
    ax.add_patch(card)
    ax.text(
        0.05,
        y_pos - 0.06,
        bucket,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        color="#111827",
        va="top",
    )
    ax.text(
        0.05,
        y_pos - 0.12,
        wrap_text(quote, width=60),
        transform=ax.transAxes,
        fontsize=9.8,
        color="#374151",
        va="top",
    )


def make_figure() -> None:
    rows = read_rows()
    counts = count_buckets(rows)
    quotes = pick_quotes(rows)

    fig = plt.figure(figsize=(14, 10), facecolor="white")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.35], hspace=0.26, wspace=0.16)

    ax = fig.add_subplot(gs[0, :])
    colors = ["#325288", "#6B9080", "#C97C5D", "#8E7DBE"]
    y = list(counts.keys())
    values = list(counts.values())

    bars = ax.barh(y, values, color=colors, edgecolor="#1f2937", linewidth=0.8)
    ax.invert_yaxis()
    ax.set_title("Reported Difficulties in the Questionnaire", loc="left", fontsize=18, fontweight="bold")
    ax.set_xlabel("Theme mentions")
    ax.set_xlim(0, max(values) + 4)
    ax.grid(axis="x", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + 0.2,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
            color="#111827",
        )

    quote_axes = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    quote_pairs = [BUCKET_ORDER[:2], BUCKET_ORDER[2:]]
    y_positions = [0.92, 0.43]

    for axq, pair in zip(quote_axes, quote_pairs):
        axq.set_axis_off()
        for y_pos, bucket in zip(y_positions, pair):
            quote = quotes.get(bucket, "No representative quotation available.")
            add_quote_card(axq, y_pos, bucket, quote)

    fig.text(
        0.01,
        0.01,
        "Counts are theme mentions because some responses were coded with multiple difficulties.",
        fontsize=9.5,
        color="#6b7280",
    )
    fig.subplots_adjust(left=0.16, right=0.98, top=0.94, bottom=0.06, hspace=0.22, wspace=0.14)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    make_figure()
