"""STACK response parsing helpers."""

from __future__ import annotations

import ast
import re
from typing import Any

import pandas as pd


def parse_extracted_answers(v: Any) -> list:
    """Parse the stringified Extracted Answers column into a Python list."""

    if isinstance(v, list):
        return v

    if v is None or (not isinstance(v, (list, tuple, dict)) and pd.isna(v)) or str(v).strip() == "":
        return []

    try:
        parsed = ast.literal_eval(v)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def get_student_answer(v: Any) -> str | None:
    """Return the first extracted student answer, if present."""

    parsed = parse_extracted_answers(v)

    if not parsed:
        return None

    first = parsed[0]
    if isinstance(first, (tuple, list)) and len(first) >= 2:
        return first[1]
    return None


def normalize_answer(ans: Any) -> str | None:
    """Normalize a student answer for grouping and matching."""

    if ans is None or (not isinstance(ans, (list, tuple, dict)) and pd.isna(ans)):
        return None

    s = str(ans).strip().lower()

    replacements = [
        ("π", "pi"),
        ("Π", "pi"),
        ("pigreco", "pi"),
        ("\\pi", "pi"),
        ("Ã—", "*"),
        ("×", "*"),
        ("÷", "/"),
        ("âˆ’", "-"),
        ("−", "-"),
        ("â€“", "-"),
        ("%e", "e"),
        ("%pi", "pi"),
    ]

    for old, new in replacements:
        s = s.replace(old, new)

    s = re.sub(r"\s+", "", s)
    return s


def extract_answers(text: Any) -> list[tuple[str, str, str]]:
    """Extract ansN records from a STACK response string."""

    return re.findall(
        r"(ans\d+):\s*(.*?)\s*\[(score|valid|invalid)\]",
        str(text),
    )


def extract_prts(text: Any) -> list[tuple[str, str]]:
    """Extract prtN records from a STACK response string."""

    return re.findall(
        r"(prt\d+):\s*(?:#\s*=\s*([01])|!)",
        str(text),
    )


def classify_response(raw: Any) -> str:
    """Classify the STACK response by Moodle/STACK outcome."""

    raw = str(raw)

    if "prt1: !" in raw or re.search(r"prt\d+:\s*!", raw):
        return "No response / not evaluated"
    if "[invalid]" in raw:
        return "Invalid syntax"
    if re.search(r"prt\d+:\s*#\s*=\s*0", raw):
        return "Incorrect"
    if re.search(r"prt\d+:\s*#\s*=\s*1", raw):
        return "Correct"
    return "Manual review"
