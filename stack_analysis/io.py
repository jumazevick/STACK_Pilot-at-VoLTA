"""Input loading helpers for quiz response and grade exports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .config import QUIZ_KEY_ALIASES


def quiz_key_from_path(path: str | Path) -> str:
    """Map a file path to a canonical quiz key."""

    stem = Path(path).stem.lower()

    for quiz_key, aliases in QUIZ_KEY_ALIASES.items():
        if any(alias in stem for alias in aliases):
            return quiz_key

    return re.sub(r"[^a-z0-9]+", "_", stem).strip("_")


def load_quiz_tables(directory: str | Path) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Path]]:
    """Load CSV or Excel exports from a directory into keyed dataframes.

    Moodle exports are commonly downloaded as CSV files, while older copies
    of this project used XLSX files.  Supporting both formats keeps the
    pipeline usable with either export without changing the analysis code.
    """

    directory = Path(directory)
    tables: Dict[str, pd.DataFrame] = {}
    paths: Dict[str, Path] = {}

    paths_to_load = sorted(
        [*directory.glob("*.csv"), *directory.glob("*.xlsx"), *directory.glob("*.xls")]
    )

    for path in paths_to_load:
        quiz_key = quiz_key_from_path(path)

        if quiz_key in tables:
            raise ValueError(
                f"Duplicate quiz key '{quiz_key}' while loading {path}. "
                f"Existing file: {paths[quiz_key]}"
            )

        if path.suffix.lower() == ".csv":
            tables[quiz_key] = pd.read_csv(path)
        else:
            tables[quiz_key] = pd.read_excel(path)
        paths[quiz_key] = path

    return tables, paths


def load_quiz_exports(
    responses_dir: str | Path,
    grades_dir: str | Path,
) -> tuple[
    Dict[str, pd.DataFrame],
    Dict[str, pd.DataFrame],
    Dict[str, Path],
    Dict[str, Path],
]:
    """Load response and grade exports for every quiz."""

    quiz_responses, response_paths = load_quiz_tables(responses_dir)
    quiz_grades, grade_paths = load_quiz_tables(grades_dir)
    return quiz_responses, quiz_grades, response_paths, grade_paths
