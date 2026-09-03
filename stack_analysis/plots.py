"""Reusable plotting helpers for quiz analysis."""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns


def plot_response_status_distribution(response_level_df, ax=None, title="Response Status Distribution", palette="viridis"):
    """Plot counts of response statuses."""

    if response_level_df.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 4))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No response data available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    order = response_level_df["Response Status"].value_counts().index
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
        created_fig = True
    else:
        fig = ax.figure

    sns.countplot(
        data=response_level_df,
        y="Response Status",
        hue="Response Status",
        order=order,
        palette=palette,
        ax=ax,
        legend=False,
    )
    ax.set_title(title)
    ax.set_xlabel("Count")
    ax.set_ylabel("")
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax


def plot_problematic_responses_by_type(responses_of_interest, ax=None, title="Problematic Responses by Type", palette="magma"):
    """Plot the distribution of problematic response classes."""

    if responses_of_interest.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 4))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No problematic responses available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    order = responses_of_interest["Response Status"].value_counts().index
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
        created_fig = True
    else:
        fig = ax.figure

    sns.countplot(
        data=responses_of_interest,
        y="Response Status",
        hue="Response Status",
        order=order,
        palette=palette,
        ax=ax,
        legend=False,
    )
    ax.set_title(title)
    ax.set_xlabel("Count")
    ax.set_ylabel("")
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax


def plot_problematic_responses_by_question(analysis_df, ax=None, title="Problematic Responses by Question", color="tomato"):
    """Plot problematic responses by question."""

    if analysis_df.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 5))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No analysis data available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    issue_by_question = analysis_df["Question"].value_counts().sort_index()
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        created_fig = True
    else:
        fig = ax.figure

    sns.barplot(x=issue_by_question.index, y=issue_by_question.values, color=color, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Question")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax


def plot_grades_boxplot(grades_long, ax=None, title="Grades Across the Quizzes"):
    """Plot a boxplot with jittered points and mean/SD annotations."""

    if grades_long.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 5))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No grade data available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        created_fig = True
    else:
        fig = ax.figure

    summary = grades_long.groupby("Quiz", observed=True)["Grade"].agg(["mean", "std"])

    sns.boxplot(data=grades_long, x="Quiz", y="Grade", ax=ax)
    sns.stripplot(data=grades_long, x="Quiz", y="Grade", color="black", alpha=0.4, jitter=0.15, ax=ax)

    for i, (quiz, row) in enumerate(summary.iterrows()):
        ax.text(
            i,
            row["mean"] - 0.4,
            f"M={row['mean']:.2f}\nSD={row['std']:.2f}",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="lightgrey"),
        )

    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("Grade (/10)")
    ax.set_ylim(0, 10.5)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax


def plot_question_facility_heatmap(question_fi_summary, quiz_order, ax=None, title="Question Difficulty Heatmap (Moodle Facility Index %)"):
    """Plot a facility-index heatmap."""

    if question_fi_summary.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 5))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No facility-index data available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    heatmap_data = (
        question_fi_summary.pivot(index="Quiz", columns="Question", values="Facility Index (%)")
    )

    ordered_index = [quiz for quiz in quiz_order if quiz in heatmap_data.index]
    extras = [quiz for quiz in heatmap_data.index if quiz not in ordered_index]
    heatmap_data = heatmap_data.reindex(ordered_index + extras)

    if heatmap_data.empty:
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 5))
            created_fig = True
        else:
            fig = ax.figure
        ax.set_title(title)
        ax.text(0.5, 0.5, "No facility-index data available.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    question_order = sorted(
        heatmap_data.columns,
        key=lambda q: int("".join(ch for ch in str(q) if ch.isdigit()) or "0"),
    )
    heatmap_data = heatmap_data[question_order]

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        created_fig = True
    else:
        fig = ax.figure

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        linewidths=0.5,
        cbar_kws={"label": "Facility Index (%)"},
        ax=ax,
    )

    ax.set_title(title)
    ax.set_ylabel("Quiz")
    ax.set_xlabel("Question")
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax


def plot_quiz_start_density(quiz_starts_long, ax=None, title="Density of Quiz Start Times"):
    """Plot quiz start times as density curves."""

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 6))
        created_fig = True
    else:
        fig = ax.figure

    if quiz_starts_long.empty:
        ax.set_title(title)
        ax.text(0.5, 0.5, "No start timestamps found.", ha="center", va="center", transform=ax.transAxes)
        fig.tight_layout()
        return fig if created_fig else ax.figure, ax

    quiz_starts_long = quiz_starts_long.copy()
    quiz_starts_long["Started_num"] = mdates.date2num(quiz_starts_long["Started on"])
    x_min = quiz_starts_long["Started_num"].min()
    x_max = quiz_starts_long["Started_num"].max()
    pad = (x_max - x_min) * 0.08 if x_max != x_min else 1
    colors = sns.color_palette("tab10", n_colors=quiz_starts_long["Quiz"].nunique())

    for i, quiz_name in enumerate(quiz_starts_long["Quiz"].dropna().unique()):
        data = quiz_starts_long.loc[quiz_starts_long["Quiz"] == quiz_name, "Started_num"]
        if data.empty:
            continue
        sns.kdeplot(
            x=data,
            fill=True,
            alpha=0.18,
            linewidth=2,
            color=colors[i % len(colors)],
            label=quiz_name,
            bw_adjust=2.0,
            cut=3,
            ax=ax,
        )

    ax.set_title(title)
    ax.set_xlabel("Started on")
    ax.set_ylabel("Density")
    ax.set_xlim(x_min - pad, x_max + pad)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Quiz")
    fig.tight_layout()
    return fig if created_fig else ax.figure, ax
