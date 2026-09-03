"""Cleaning helpers for Moodle quiz exports."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import FINISHED_STATE, STATE_COL, STUDENT_COL


def remove_moodle_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove Moodle summary rows such as 'Overall average'."""

    if df.empty or df.shape[1] == 0:
        return df.copy()

    summary_mask = df.astype(str).apply(
        lambda row: row.str.contains("Overall", case=False, na=False).any(),
        axis=1,
    )
    return df.loc[~summary_mask].copy()


def keep_finished_attempts(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only finished Moodle attempts."""

    if STATE_COL not in df.columns:
        return df.copy()

    return df[
        df[STATE_COL]
        .astype(str)
        .str.lower()
        .eq(FINISHED_STATE)
    ].copy()


def identify_response_cols(df: pd.DataFrame) -> list[str]:
    """Return the quiz response columns from a cleaned export."""

    return [c for c in df.columns if str(c).startswith("Response")]


def identify_grade_cols(df: pd.DataFrame) -> list[str]:
    """Return grade columns from a cleaned export."""

    return [c for c in df.columns if str(c).startswith("Grade/")]


def identify_grade_col(df: pd.DataFrame) -> str | None:
    """Return the first grade column, if any."""

    grade_cols = identify_grade_cols(df)
    return grade_cols[0] if grade_cols else None


def clean_quiz_responses(
    quiz_df: pd.DataFrame,
    quiz_name: str | None = None,
) -> dict[str, Any]:
    """
    Clean a Moodle quiz export and expose the key columns used downstream.

    Returns a dictionary so the notebook can inspect the intermediate data
    without needing a custom class.
    """

    original_df = quiz_df.copy()
    cleaned_df = remove_moodle_summary_rows(original_df)
    finished_df = keep_finished_attempts(cleaned_df)

    response_cols = identify_response_cols(finished_df)
    grade_col = identify_grade_col(finished_df)

    cols_to_show: list[str] = []
    for candidate in [STUDENT_COL, STATE_COL, grade_col]:
        if candidate and candidate not in cols_to_show and candidate in finished_df.columns:
            cols_to_show.append(candidate)
    cols_to_show.extend([c for c in response_cols if c not in cols_to_show])

    return {
        "quiz_name": quiz_name,
        "original_df": original_df,
        "cleaned_df": cleaned_df,
        "finished_df": finished_df,
        "original_shape": original_df.shape,
        "clean_shape": cleaned_df.shape,
        "finished_shape": finished_df.shape,
        "response_cols": response_cols,
        "grade_col": grade_col,
        "cols_to_show": cols_to_show,
    }
