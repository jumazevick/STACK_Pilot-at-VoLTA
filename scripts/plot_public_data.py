"""Recreate aggregate-only figures without access to student-level data."""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public_data"
FIGURE_DATA = PUBLIC / "figure_source_data"


def save_activity(output: Path) -> None:
    data = pd.read_csv(PUBLIC / "activity_summary.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x="Quiz", y="Mean Grade", color="#4472C4", ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("Mean grade")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(output / "activity_mean_grade.png", dpi=200)
    plt.close(fig)


def save_activity_participation_performance(output: Path) -> None:
    """Recreate the combined participation and mean-performance chart."""
    data = pd.read_csv(PUBLIC / "activity_summary.csv")
    order = ["Intro to STACK", "Algebraic Operations", "Modulus & Argument", "Powers & Roots", "Expressions"]
    data["order"] = data["Quiz"].map({quiz: index for index, quiz in enumerate(order)})
    data = data.sort_values("order")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    positions = range(len(data))
    width = 0.24
    bars = [
        ax.bar([position - width for position in positions], data["Total Attempts"], width, label="Total Attempts", color="#1f77b4"),
        ax.bar(positions, data["Finished Attempts"], width, label="Finished Attempts", color="#ff7f0e"),
        ax.bar([position + width for position in positions], data["No. of Students"], width, label="No. of Students", color="#2ca02c"),
    ]
    for group in bars:
        for bar in group:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=8)
    line_ax = ax.twinx()
    line_ax.plot(list(positions), data["Mean Grade"], color="#1f77b4", marker="o", linewidth=2, label="Mean Grade")
    for position, value in zip(positions, data["Mean Grade"]):
        line_ax.text(position, value + 0.25, f"{value:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_title("STACK Quiz Participation and Mean Performance")
    ax.set_ylabel("Count")
    line_ax.set_ylabel("Mean Grade /10")
    line_ax.set_ylim(0, 10)
    ax.set_xticks(list(positions), data["Quiz"], rotation=20, ha="right")
    handles, labels = [], []
    for axis in (ax, line_ax):
        axis_handles, axis_labels = axis.get_legend_handles_labels()
        handles.extend(axis_handles)
        labels.extend(axis_labels)
    ax.legend(handles, labels, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "activity_participation_performance.png", dpi=200)
    plt.close(fig)


def save_facility(output: Path) -> None:
    data = pd.read_csv(FIGURE_DATA / "facility_index_by_question.csv")
    matrix = data.pivot(index="Quiz", columns="Question", values="Facility Index (%)")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.heatmap(matrix, annot=True, fmt=".1f", cmap="YlGnBu", vmin=0, vmax=100, ax=ax)
    ax.set_title("Question-level facility index (%)")
    fig.tight_layout()
    fig.savefig(output / "question_level_facility_index.png", dpi=200)
    plt.close(fig)


def save_status(output: Path) -> None:
    data = pd.read_csv(FIGURE_DATA / "response_status_by_quiz_and_question_long.csv")
    matrix = data.pivot_table(index="quiz_name", columns="response_status_viz", values="count", aggfunc="sum", fill_value=0)
    order = ["Correct", "Incorrect", "Invalid input", "No response / not evaluated"]
    matrix = matrix.reindex(columns=[column for column in order if column in matrix], fill_value=0)
    ax = matrix.plot(kind="bar", stacked=True, figsize=(10, 5), colormap="viridis")
    ax.set_xlabel("")
    ax.set_ylabel("Aggregate response count")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Response status", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.figure.tight_layout()
    ax.figure.savefig(output / "response_status_summary.png", dpi=200)
    plt.close(ax.figure)


def save_response_status_by_question(output: Path) -> None:
    """Recreate the paper's question-level response-status figure."""
    data = pd.read_csv(FIGURE_DATA / "response_status_by_quiz_and_question_long.csv")
    quiz_order = ["Intro to STACK", "Algebraic Operations", "Powers & Roots", "Modulus & Argument", "Expressions"]
    quiz_order = [quiz for quiz in quiz_order if quiz in set(data["quiz_name"])]
    fig = plt.figure(figsize=(12, 9), constrained_layout=True)
    grid = fig.add_gridspec(3, 2, height_ratios=[1.1, 1, 1], hspace=0.48, wspace=0.28)
    axes = [
        fig.add_subplot(grid[0, :]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[2, 0]),
        fig.add_subplot(grid[2, 1]),
    ]
    # The paper layout gives the introductory quiz a full-width panel.
    remaining = [quiz for quiz in quiz_order if quiz != "Intro to STACK"]
    panel_data = [("Intro to STACK", axes[0])] + list(zip(remaining, axes[1:]))
    colors = {"Incorrect": "#1f77b4", "Invalid input": "#ff7f0e", "No response / not evaluated": "#d62728", "Correct": "#9467bd"}
    order = ["Incorrect", "Invalid input", "No response / not evaluated", "Correct"]
    for quiz, ax in panel_data:
        subset = data[data["quiz_name"] == quiz].copy()
        matrix = subset.pivot_table(index="question_number", columns="response_status_viz", values="count", aggfunc="sum", fill_value=0)
        matrix = matrix.reindex(columns=order, fill_value=0)
        matrix["total"] = matrix.sum(axis=1)
        percentages = matrix[order].div(matrix["total"], axis=0).mul(100)
        questions = list(percentages.index)
        left = pd.Series(0.0, index=questions)
        for status in order[:-1]:
            values = -percentages[status]
            ax.barh(questions, values, left=left, color=colors[status], label=status)
            left += values
        right = pd.Series(0.0, index=questions)
        values = percentages["Correct"]
        ax.barh(questions, values, left=right, color=colors["Correct"], label="Correct")
        for question in questions:
            row = percentages.loc[question]
            negative = 0.0
            for status in order[:-1]:
                value = row[status]
                if value >= 4:
                    ax.text(negative - value / 2, question, f"{value:.0f}%", ha="center", va="center", fontsize=7)
                negative -= value
            if row["Correct"] >= 4:
                ax.text(row["Correct"] / 2, question, f"{row['Correct']:.0f}%", ha="center", va="center", fontsize=7)
        ax.axvline(0, color="black", linewidth=0.7)
        ax.set_title(quiz)
        ax.set_xlabel("Percentage")
        ax.set_xlim(-100, 100)
        ax.set_xticks([-100, -50, 0, 50, 100])
        ax.set_xticklabels(["100%", "50%", "0%", "50%", "100%"])
        ax.set_ylabel("Question")
        ax.grid(axis="x", alpha=0.25)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.01))
    fig.savefig(output / "response_status_by_question.png", dpi=200)
    plt.close(fig)


def save_invalid_inputs(output: Path) -> None:
    data = pd.read_csv(FIGURE_DATA / "invalid_inputs_by_quiz_and_question.csv")
    top = data.groupby("invalid_input", as_index=False)["frequency"].sum().nlargest(15, "frequency").sort_values("frequency")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top["invalid_input"].astype(str), top["frequency"], color="#ED7D31")
    ax.set_xlabel("Aggregate frequency")
    ax.set_ylabel("Invalid input")
    fig.tight_layout()
    fig.savefig(output / "invalid_input_frequency.png", dpi=200)
    plt.close(fig)


def save_invalid_input_heatmap(output: Path) -> None:
    """Recreate the paper's invalid-input frequency heatmap."""
    data = pd.read_csv(FIGURE_DATA / "invalid_inputs_by_quiz_and_question.csv")
    matrix = data.pivot_table(index="quiz_name", columns="question_number", values="frequency", aggfunc="sum", fill_value=0)
    quiz_order = ["Intro to STACK", "Algebraic Operations", "Modulus & Argument", "Powers & Roots", "Expressions"]
    matrix = matrix.reindex([quiz for quiz in quiz_order if quiz in matrix.index])
    matrix = matrix.reindex(sorted(matrix.columns, key=lambda value: int(str(value).lstrip("Q") or 0)), axis=1)
    labels = matrix.map(lambda value: str(int(value)) if value else "")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(matrix, annot=labels, fmt="", cmap="viridis", linewidths=0.5, cbar_kws={"label": "Invalid input count"}, ax=ax)
    ax.set_title("Invalid Input Frequency by Quiz and Question")
    ax.set_xlabel("Question")
    ax.set_ylabel("STACK activity")
    fig.tight_layout()
    fig.savefig(output / "invalid_input_heatmap.png", dpi=200)
    plt.close(fig)


def _questionnaire_counts(questionnaire: pd.DataFrame, marker: str) -> pd.DataFrame:
    """Return counts for the first questionnaire item matching ``marker``."""
    matches = questionnaire[questionnaire["question"].astype(str).str.startswith(marker)].copy()
    return matches.sort_values("count")


def _save_questionnaire_background(output: Path, language: str) -> None:
    """Create the two-panel questionnaire background figure in one language."""
    questionnaire = pd.read_csv(PUBLIC / "questionnaire_summary_counts_percentages.csv")
    experience = _questionnaire_counts(questionnaire, "(1)")
    device = _questionnaire_counts(questionnaire, "(2)")
    if language == "it":
        experience_labels = {"No": "No"}
        yes_label = "Sì, una o due volte"
        titles = ("Esperienza precedente con la valutazione online", "Dispositivo usato per completare le attività")
        ylabels = "Numero di studenti"
        filename = "questionnaire_background_it.png"
    else:
        experience_labels = {"No": "No"}
        yes_label = "Yes, once or twice"
        titles = ("Previous experience with online assessment", "Device used to complete the activities")
        ylabels = "Number of students"
        filename = "questionnaire_background_en.png"
    experience = experience.copy()
    experience["response"] = experience["response"].apply(lambda value: experience_labels.get(str(value).strip(), yes_label))
    experience["order"] = experience["response"].map({"No": 0, yes_label: 1})
    experience = experience.sort_values("order")
    device_order = ["Laptop/PC", "Smartphone", "Tablet"]
    device = device.copy()
    device["order"] = device["response"].map({value: index for index, value in enumerate(device_order)})
    device = device.sort_values("order")
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 7.2))
    for ax, data, title in zip(axes, (experience, device), titles):
        ax.bar(data["response"], data["count"], color="#2C7FB8")
        for index, value in enumerate(data["count"]):
            ax.text(index, value + 0.25, str(int(value)), ha="center", va="bottom", fontsize=9)
        ax.set_title(title)
        ax.set_ylabel(ylabels)
        ax.set_xlabel("")
        ax.set_ylim(0, max(data["count"]) + 3)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / filename, dpi=200)
    plt.close(fig)


def save_questionnaire_background(output: Path) -> None:
    """Recreate the combined paper Figure 7 from aggregate counts."""
    _save_questionnaire_background(output, "en")


def save_questionnaire_background_en(output: Path) -> None:
    """Create the English questionnaire background figure."""
    _save_questionnaire_background(output, "en")


def save_questionnaire_background_it(output: Path) -> None:
    """Create the Italian questionnaire background figure."""
    _save_questionnaire_background(output, "it")


def save_reported_difficulties(output: Path) -> None:
    """Recreate paper Figure 8 from topic and aggregate coded-theme counts."""
    questionnaire = pd.read_csv(PUBLIC / "questionnaire_summary_counts_percentages.csv")
    topics = questionnaire[questionnaire["question"].astype(str).str.contains("Quale argomento", na=False)].copy()
    themes = pd.read_csv(PUBLIC / "reported_difficulties_summary.csv")
    themes = themes[themes["Question"].astype(str).str.contains("Difficoltà|Difficolta|diffic", case=False, na=False)].copy()
    themes = themes.sort_values("Frequency").tail(10)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].barh(topics["response"], topics["count"], color="#70AD47")
    axes[0].set_title("Most difficult topic")
    axes[0].set_xlabel("Responses")
    axes[0].set_ylabel("")
    axes[1].barh(themes["Theme"], themes["Frequency"], color="#ED7D31")
    axes[1].set_title("Reported difficulties")
    axes[1].set_xlabel("Theme mentions")
    axes[1].set_ylabel("")
    fig.tight_layout()
    fig.savefig(output / "reported_difficulties.png", dpi=200)
    plt.close(fig)


def save_most_difficult_topic(output: Path) -> None:
    """Recreate the paper's topic-only Figure 8 from aggregate survey counts."""
    questionnaire = pd.read_csv(PUBLIC / "questionnaire_summary_counts_percentages.csv")
    topics = questionnaire[questionnaire["question"].astype(str).str.contains("Quale argomento", na=False)].copy()
    translations = {
        "Potenze e radici": "Powers and Roots",
        "Modulo e argomento": "Modulus and Argument",
        "Equazioni": "Equations",
    }
    topics["Topic"] = topics["response"].map(translations).fillna(topics["response"])
    topics["Topic"] = topics["Topic"].map(lambda value: textwrap.fill(str(value), width=48))
    topics = topics.sort_values(["count", "Topic"], ascending=[False, True])
    topics["percentage"] = pd.to_numeric(topics["percentage"], errors="coerce")
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(topics["Topic"], topics["count"], color="#2C7FB8")
    ax.invert_yaxis()
    for bar, count, percentage in zip(bars, topics["count"], topics["percentage"]):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2, f"{int(count)} ({percentage:.2f}%)", va="center", fontsize=8)
    ax.set_title("Most Difficult Topic")
    ax.set_xlabel("Number of Students")
    ax.set_ylabel("Topic")
    ax.set_xlim(0, max(topics["count"]) + 4)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "most_difficult_topic.png", dpi=200)
    plt.close(fig)


def save_appendix_d_survey_results(output: Path) -> None:
    """Create the three-panel Appendix D coded-survey-results figure."""
    data = pd.read_csv(PUBLIC / "reported_difficulties_summary.csv")
    panels = [
        ("PEOU: Difficulties using the system", "PEOU: Difficulties using the system"),
        ("PU: Reaction to feedback", "PU: Reaction to feedback"),
        ("ATU: Reason for most difficult topic", "ATU: Reason for most difficult topic"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(9, 12))
    for ax, (title, question) in zip(axes, panels):
        subset = data[data["Question"] == question].sort_values("Frequency")
        ax.barh(subset["Theme"], subset["Frequency"], color="#2C7FB8")
        for index, value in enumerate(subset["Frequency"]):
            ax.text(value + 0.12, index, str(int(value)), va="center", fontsize=8)
        ax.set_title(title)
        ax.set_xlabel("Number of coded responses")
        ax.set_ylabel("Theme")
        ax.set_xlim(0, max(subset["Frequency"]) + 1.5)
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle("Appendix D: Descriptive Survey Results", fontsize=14, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(output / "appendix_d_survey_results.png", dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced_figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    save_activity(args.output)
    save_activity_participation_performance(args.output)
    save_facility(args.output)
    save_status(args.output)
    save_response_status_by_question(args.output)
    save_invalid_inputs(args.output)
    save_invalid_input_heatmap(args.output)
    save_questionnaire_background(args.output)
    save_questionnaire_background_en(args.output)
    save_questionnaire_background_it(args.output)
    save_reported_difficulties(args.output)
    save_most_difficult_topic(args.output)
    save_appendix_d_survey_results(args.output)
    print(f"Created figures in {args.output}")


if __name__ == "__main__":
    main()
