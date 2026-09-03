"""Scan the staged/tracked tree for common public-release privacy risks."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
STUDENT_ID = re.compile(r"\bstudent\d{2,}\b", re.I)
TIMESTAMP = re.compile(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}")
RISKY_HEADERS = {
    "student_id",
    "email address",
    "started on",
    "completed",
    "time taken",
    "date",
    "moodle id",
    "user id",
}


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [ROOT / item for item in raw.decode().split("\0") if item]


def csv_headers(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [str(value).strip().casefold() for value in next(csv.reader(handle), [])]
    except (OSError, UnicodeDecodeError, StopIteration):
        return []


def main() -> int:
    risky: dict[str, set[str]] = {}
    safe_public: list[str] = []
    excluded: list[str] = []

    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if not path.exists():
            continue
        lower = relative.casefold()
        if any(token in Path(relative).name.casefold() for token in ("survey", "questionnaire", "responses")) and not lower.startswith("public_data/"):
            risky.setdefault(relative, set()).add("survey/response-looking filename outside public_data")
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        reasons: set[str] = set()
        if EMAIL.search(text):
            reasons.add("email address pattern")
        if STUDENT_ID.search(text) and lower.endswith((".csv", ".tsv")):
            reasons.add("student ID value")
        if TIMESTAMP.search(text) and lower.startswith("public_data/"):
            reasons.add("raw timestamp pattern")
        if lower.endswith((".csv", ".tsv")):
            headers = csv_headers(path)
            for header in headers:
                if header in RISKY_HEADERS:
                    reasons.add(f"risky column: {header}")
                if header in {"first name", "last name", "full name", "user full name"}:
                    reasons.add(f"name column: {header}")
        if reasons:
            risky[relative] = risky.get(relative, set()) | reasons
        elif lower.startswith("public_data/"):
            safe_public.append(relative)

    for folder in ("private_data", "restricted_data", "pseudonymized_data", "data/raw"):
        if (ROOT / folder).exists():
            excluded.append(folder + "/ (local restricted material; ignored)")

    print("SAFE PUBLIC FILES")
    for item in sorted(safe_public):
        print(f"  {item}")
    print("\nFILES EXCLUDED FROM PUBLIC RELEASE")
    for item in excluded:
        print(f"  {item}")
    print("\nREMAINING RISKY TRACKED FILES")
    if risky:
        for item, reasons in sorted(risky.items()):
            print(f"  {item}: {', '.join(sorted(reasons))}")
    else:
        print("  none")
    return 1 if risky else 0


if __name__ == "__main__":
    raise SystemExit(main())
