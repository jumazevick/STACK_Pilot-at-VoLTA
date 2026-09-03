"""Prepare a privacy-safe, aggregate-only release of the analysis repository."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public_data"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_csv(source: Path, target: Path) -> None:
    rows = read_csv(source)
    if rows:
        write_csv(target, rows, list(rows[0]))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> None:
    # Build the public release from aggregate outputs before removing private material.
    overview_rows: list[dict[str, str]] = []
    for source in sorted((ROOT / "outputs" / "quizzes").glob("*/overview.csv")):
        overview_rows.extend(read_csv(source))
    write_csv(
        PUBLIC / "aggregated_activity_summary.csv",
        overview_rows,
        [
            "Quiz Key",
            "Quiz",
            "Total Attempts",
            "Finished Attempts",
            "No. of Students",
            "Mean Grade",
            "SD Grade",
        ],
    )

    copy_csv(
        ROOT / "outputs" / "facility_index" / "facility_index_by_question.csv",
        PUBLIC / "question_level_facility_index.csv",
    )
    copy_csv(
        ROOT / "outputs" / "visualisations" / "response_status_summary_by_quiz.csv",
        PUBLIC / "response_status_summary.csv",
    )
    copy_csv(
        ROOT / "outputs" / "visualisations" / "invalid_inputs_by_quiz_and_question.csv",
        PUBLIC / "invalid_input_frequency_table.csv",
    )
    copy_csv(
        ROOT / "outputs" / "summary" / "open_theme_summary.csv",
        PUBLIC / "questionnaire_summary.csv",
    )

    scripts_dir = PUBLIC / "analysis_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in (ROOT / "stack_analysis", ROOT / "scripts"):
        for source in sorted(source_dir.glob("*.py")):
            if source.name != Path(__file__).name:
                shutil.copyfile(source, scripts_dir / source.name)

    figures_dir = PUBLIC / "figures_data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "outputs").rglob("*.png"):
        relative = source.relative_to(ROOT / "outputs")
        target = figures_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    (PUBLIC / "README.md").write_text(
        "# Public analysis materials\n\n"
        "This directory contains aggregate, anonymised materials for reproducing "
        "the reported tables and figures. It contains no raw student-level Moodle/"
        "STACK records, names, email addresses, questionnaire responses, or student IDs.\n",
        encoding="utf-8",
    )

    private_paths = [
        ROOT / "data" / "raw",
        ROOT / "outputs",
        ROOT / "notebooks",
        ROOT / "Analysis_Survey.ipynb",
        ROOT / "coded_open_responses_manual_review.csv",
        ROOT / "docs" / "report",
    ]
    for path in private_paths:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
