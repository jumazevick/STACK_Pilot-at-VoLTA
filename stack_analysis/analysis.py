"""Higher-level quiz analysis helpers."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .cleaning import (
    identify_grade_col,
    keep_finished_attempts,
    remove_moodle_summary_rows,
)
from .config import QUIZ_ORDER, QUIZ_TITLES, PROBLEMATIC_RESPONSE_STATUSES, STARTED_COL, STUDENT_COL


def _quiz_categories(extra_values: list[str] | None = None) -> list[str]:
    """Return the canonical quiz title order plus any extra titles."""

    categories = [QUIZ_TITLES.get(key, key) for key in QUIZ_ORDER]
    for value in extra_values or []:
        if pd.notna(value) and value not in categories:
            categories.append(value)
    return categories


def extract_max_mark(col: Any) -> float | None:
    """Extract the maximum mark from a Moodle question column header."""

    match = re.search(r"/\s*([\d.]+)", str(col))
    return float(match.group(1)) if match else None


def question_analysis_table(df: pd.DataFrame, quiz_name: str | None = None) -> pd.DataFrame:
    """Summarize question scores for a single quiz grade export."""

    df = keep_finished_attempts(df)

    question_cols = [col for col in df.columns if str(col).startswith("Q.")]
    rows: list[dict[str, Any]] = []

    for col in question_cols:
        scores = pd.to_numeric(df[col], errors="coerce")
        max_mark = extract_max_mark(col)
        mean_score = scores.mean()

        row = {
            "Question": str(col).split("/")[0].strip(),
            "Max Mark": max_mark,
            "N": scores.count(),
            "Mean": mean_score,
            "SD": scores.std(),
            "Min": scores.min(),
            "Max": scores.max(),
            "Facility Index (%)": (mean_score / max_mark * 100) if max_mark else None,
        }
        if quiz_name is not None:
            row["Quiz"] = quiz_name
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    if "Quiz" in result.columns:
        order = _quiz_categories(result["Quiz"].astype(str).tolist())
        result["Quiz"] = pd.Categorical(result["Quiz"], categories=order, ordered=True)
        result["_question_sort"] = result["Question"].astype(str).str.extract(r"(\d+)")[0]
        result["_question_sort"] = pd.to_numeric(result["_question_sort"], errors="coerce")
        sort_cols = ["Quiz", "_question_sort", "Question"]
    else:
        result["_question_sort"] = result["Question"].astype(str).str.extract(r"(\d+)")[0]
        result["_question_sort"] = pd.to_numeric(result["_question_sort"], errors="coerce")
        sort_cols = ["_question_sort", "Question"]

    return (
        result.round(2)
        .sort_values(sort_cols)
        .drop(columns=["_question_sort"])
        .reset_index(drop=True)
    )


def build_quiz_overview(
    quiz_key: str,
    grade_df: pd.DataFrame,
    quiz_title: str | None = None,
) -> pd.DataFrame:
    """Create a one-row grade overview for a quiz."""

    quiz_title = quiz_title or QUIZ_TITLES.get(quiz_key, quiz_key)

    cleaned = remove_moodle_summary_rows(grade_df)
    total_attempts = len(cleaned)
    finished_df = keep_finished_attempts(cleaned)
    finished_attempts = len(finished_df)

    students_df = finished_df[[STUDENT_COL]].dropna().copy() if STUDENT_COL in finished_df.columns else pd.DataFrame(columns=[STUDENT_COL])
    if not students_df.empty:
        students_df[STUDENT_COL] = students_df[STUDENT_COL].astype(str).str.strip()
        students_df = students_df[students_df[STUDENT_COL].ne("")]
    n_students = students_df[STUDENT_COL].nunique() if not students_df.empty else 0

    grade_col = identify_grade_col(finished_df)
    grades = pd.to_numeric(finished_df[grade_col], errors="coerce") if grade_col else pd.Series(dtype=float)

    return pd.DataFrame(
        [
            {
                "Quiz Key": quiz_key,
                "Quiz": quiz_title,
                "Total Attempts": total_attempts,
                "Finished Attempts": finished_attempts,
                "No. of Students": n_students,
                "Mean Grade": grades.mean(),
                "SD Grade": grades.std(),
            }
        ]
    )


def build_student_count_summary(
    quiz_grade_tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build the combined student/attempt summary across all quizzes."""

    rows = []
    for quiz_key in QUIZ_ORDER:
        grade_df = quiz_grade_tables.get(quiz_key)
        if grade_df is None:
            continue
        rows.append(build_quiz_overview(quiz_key, grade_df))

    # Include any extra quizzes at the end.
    for quiz_key, grade_df in quiz_grade_tables.items():
        if quiz_key in QUIZ_ORDER:
            continue
        rows.append(build_quiz_overview(quiz_key, grade_df))

    if not rows:
        return pd.DataFrame(columns=["Quiz Key", "Quiz", "Total Attempts", "Finished Attempts", "No. of Students", "Mean Grade", "SD Grade"])

    result = pd.concat(rows, ignore_index=True)
    ordered_titles = _quiz_categories(result["Quiz"].astype(str).tolist())
    result["Quiz"] = pd.Categorical(result["Quiz"], categories=ordered_titles, ordered=True)
    return result.sort_values("Quiz").reset_index(drop=True).round(2)


def build_grades_long(quiz_grade_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Flatten all finished quiz grades into a long dataframe."""

    frames = []

    for quiz_key in QUIZ_ORDER:
        grade_df = quiz_grade_tables.get(quiz_key)
        if grade_df is None:
            continue

        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        cleaned = keep_finished_attempts(remove_moodle_summary_rows(grade_df))
        grade_col = identify_grade_col(cleaned)
        if not grade_col:
            continue

        grades = pd.to_numeric(cleaned[grade_col], errors="coerce")
        frames.append(
            pd.DataFrame(
                {
                    "Quiz Key": quiz_key,
                    "Quiz": quiz_title,
                    "Grade": grades,
                }
            )
        )

    for quiz_key, grade_df in quiz_grade_tables.items():
        if quiz_key in QUIZ_ORDER:
            continue

        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        cleaned = keep_finished_attempts(remove_moodle_summary_rows(grade_df))
        grade_col = identify_grade_col(cleaned)
        if not grade_col:
            continue

        grades = pd.to_numeric(cleaned[grade_col], errors="coerce")
        frames.append(
            pd.DataFrame(
                {
                    "Quiz Key": quiz_key,
                    "Quiz": quiz_title,
                    "Grade": grades,
                }
            )
        )

    if not frames:
        return pd.DataFrame(columns=["Quiz Key", "Quiz", "Grade"])

    result = pd.concat(frames, ignore_index=True)
    ordered_titles = _quiz_categories(result["Quiz"].astype(str).tolist())
    result["Quiz"] = pd.Categorical(result["Quiz"], categories=ordered_titles, ordered=True)
    return result.sort_values(["Quiz"]).reset_index(drop=True)


def build_question_fi_summary(quiz_grade_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build the combined facility-index table for all quizzes."""

    frames = []

    for quiz_key in QUIZ_ORDER:
        grade_df = quiz_grade_tables.get(quiz_key)
        if grade_df is None:
            continue
        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        frames.append(question_analysis_table(grade_df, quiz_title))

    for quiz_key, grade_df in quiz_grade_tables.items():
        if quiz_key in QUIZ_ORDER:
            continue
        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        frames.append(question_analysis_table(grade_df, quiz_title))

    if not frames:
        return pd.DataFrame(
            columns=["Quiz", "Question", "Max Mark", "N", "Mean", "SD", "Min", "Max", "Facility Index (%)"]
        )

    result = pd.concat(frames, ignore_index=True)
    ordered_titles = _quiz_categories(result["Quiz"].astype(str).tolist())
    result["Quiz"] = pd.Categorical(result["Quiz"], categories=ordered_titles, ordered=True)
    result["_question_sort"] = result["Question"].astype(str).str.extract(r"(\d+)")[0]
    result["_question_sort"] = pd.to_numeric(result["_question_sort"], errors="coerce")
    return (
        result.sort_values(["Quiz", "_question_sort", "Question"])
        .drop(columns=["_question_sort"])
        .reset_index(drop=True)
        .round(2)
    )


def build_quiz_starts_long(quiz_response_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Extract finished attempt start times for all quizzes."""

    frames = []

    for quiz_key in QUIZ_ORDER:
        response_df = quiz_response_tables.get(quiz_key)
        if response_df is None or STARTED_COL not in response_df.columns:
            continue

        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        finished_df = keep_finished_attempts(remove_moodle_summary_rows(response_df))

        started = (
            finished_df[STARTED_COL]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        started = pd.to_datetime(started, format="%d %b %Y %I:%M %p", errors="coerce")
        started = started.dropna()

        if started.empty:
            continue

        frames.append(
            pd.DataFrame(
                {
                    "Quiz Key": quiz_key,
                    "Quiz": quiz_title,
                    "Started on": started,
                }
            )
        )

    for quiz_key, response_df in quiz_response_tables.items():
        if quiz_key in QUIZ_ORDER:
            continue
        if response_df is None or STARTED_COL not in response_df.columns:
            continue

        quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
        finished_df = keep_finished_attempts(remove_moodle_summary_rows(response_df))
        started = (
            finished_df[STARTED_COL]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        started = pd.to_datetime(started, format="%d %b %Y %I:%M %p", errors="coerce")
        started = started.dropna()

        if started.empty:
            continue

        frames.append(
            pd.DataFrame(
                {
                    "Quiz Key": quiz_key,
                    "Quiz": quiz_title,
                    "Started on": started,
                }
            )
        )

    if not frames:
        return pd.DataFrame(columns=["Quiz Key", "Quiz", "Started on"])

    result = pd.concat(frames, ignore_index=True)
    ordered_titles = _quiz_categories(result["Quiz"].astype(str).tolist())
    result["Quiz"] = pd.Categorical(result["Quiz"], categories=ordered_titles, ordered=True)
    return result.sort_values(["Quiz", "Started on"]).reset_index(drop=True)


def build_common_wrong_answers(analysis_df: pd.DataFrame) -> pd.DataFrame:
    """Count repeated wrong answers by question."""

    if analysis_df.empty:
        return pd.DataFrame(columns=["Question", "Question Title", "Student Answer Norm", "Frequency"])

    filtered = analysis_df[
        analysis_df["Student Answer Norm"].notna()
        & (analysis_df["Student Answer Norm"] != "")
    ]

    return (
        filtered.groupby(
            ["Question", "Question Title", "Student Answer Norm"],
            dropna=False,
        )
        .size()
        .reset_index(name="Frequency")
        .sort_values(["Question", "Frequency"], ascending=[True, False])
        .reset_index(drop=True)
    )


def build_top_wrong_answers_per_question(
    common_wrong_answers: pd.DataFrame,
    limit: int = 10,
) -> pd.DataFrame:
    """Take the top N wrong answers per question."""

    if common_wrong_answers.empty:
        return common_wrong_answers.copy()

    return (
        common_wrong_answers.sort_values(["Question", "Frequency"], ascending=[True, False])
        .groupby("Question", as_index=False, group_keys=False)
        .head(limit)
        .reset_index(drop=True)
    )


def build_error_summary_by_question(analysis_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize coded error types by question."""

    if analysis_df.empty:
        return pd.DataFrame(columns=["Question Label", "Error Type", "Count"])

    return (
        analysis_df.groupby(["Question Label", "Error Type"])
        .size()
        .reset_index(name="Count")
        .sort_values(["Question Label", "Count"], ascending=[True, False])
        .reset_index(drop=True)
    )


def classify_error(row: pd.Series) -> str:
    """Question-aware error classification for problematic responses."""

    status = str(row.get("Response Status", ""))
    ans = str(row.get("Student Answer Norm") or "")
    raw = str(row.get("Raw Response", "")).lower()
    qtitle = str(row.get("Question Title", "")).lower()
    q = str(row.get("Question", ""))

    if ans.strip() == "" or ans == "none":
        return "No response"

    if status == "No response / not evaluated" and "[invalid]" in raw:
        return "Syntax / parser"

    if status == "Invalid syntax":
        return "Syntax / parser"

    if status == "No response / not evaluated":
        return "No response"

    if "exponential" in qtitle or q == "Q4":
        if any(tok in ans for tok in ["epsilon", "pigreco"]):
            return "Symbol notation"
        if "pi" in ans:
            return "Symbol notation"
        if re.search(r"e\^p($|\*)", ans):
            return "Exponential structure"
        if re.search(r"e\^px", ans):
            return "Exponential structure"
        if re.search(r"e\^\(p\*x\)", ans):
            return "Exponential structure"
        if re.search(r"e\^\(x\)", ans):
            return "Exponential structure"
        if ans in ["epsilon", "e", "ex"]:
            return "Symbol notation"
        return "Exponential structure"

    if "rational" in qtitle or q == "Q7":
        if "/(x-5)*(x+1)" in ans:
            return "Rational grouping"
        if "/((x-5)*(x+1))" not in ans:
            return "Rational expression error"
        return "Rational expression error"

    if "polynomial" in qtitle or q == "Q6":
        if "6^2" in ans:
            return "Polynomial construction"
        if any(tok in ans for tok in ["a*x^n", "ax^n"]):
            return "Generic formula instead of expression"
        return "Polynomial error"

    if "floating" in qtitle or q == "Q5":
        if re.search(r"\d+[a-z]", ans):
            return "Missing operator"
        if re.search(r"\d+\.\d+", ans):
            return "Decimal / exact form"
        if "1/33" in ans:
            return "Fraction error"
        return "Expression form error"

    if "complex" in qtitle or q in ["Q1", "Q2"]:
        if "4*i-3" in ans:
            return "Complex sign error"
        if "4*i*3" in ans:
            return "Complex operation error"
        return "Complex number error"

    if any(tok in ans for tok in ["epsilon", "pigreco", "pi"]):
        return "Symbol notation"

    if re.search(r"\d+[a-z]", ans) or re.search(r"[a-z]\d+", ans):
        return "Missing operator"

    if "/" in ans and "*" in ans:
        return "Grouping / brackets"

    return "Mathematical error"
