"""Build the aggregate-only public_data release from local restricted files."""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private_data" / "pseudonymized_data"
SOURCE = PRIVATE / "source"
OLD_OUTPUTS = PRIVATE / "outputs"
PUBLIC = ROOT / "public_data"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def copy_csv(source: Path, target: Path) -> None:
    fields, rows = read_csv(source)
    write_csv(target, fields, rows)


def build_activity_summary() -> None:
    fields = [
        "Quiz Key",
        "Quiz",
        "Total Attempts",
        "Finished Attempts",
        "No. of Students",
        "Mean Grade",
        "SD Grade",
    ]
    rows: list[dict[str, str]] = []
    for source in sorted((OLD_OUTPUTS / "quizzes").glob("*/overview.csv")):
        source_fields, source_rows = read_csv(source)
        for row in source_rows:
            rows.append({field: row.get(field, "") for field in fields if field in source_fields})
    write_csv(PUBLIC / "activity_summary.csv", fields, rows)


def build_questionnaire_summary() -> None:
    survey = next((SOURCE / "survey").glob("*.csv"))
    fields, rows = read_csv(survey)
    summary: list[dict[str, str]] = []
    excluded = {"student_id", "groups", "date"}
    date_pattern = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),")
    for field in fields:
        if field.casefold() in excluded or "domanda aperta" in field.casefold():
            continue
        values = [row.get(field, "").strip() for row in rows if row.get(field, "").strip()]
        if not values or all(date_pattern.search(value) for value in values):
            continue
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        denominator = len(values)
        for value, count in sorted(counts.items()):
            summary.append(
                {
                    "question": field,
                    "response": value,
                    "count": str(count),
                    "percentage": f"{100 * count / denominator:.2f}",
                }
            )
    write_csv(
        PUBLIC / "questionnaire_summary_counts_percentages.csv",
        ["question", "response", "count", "percentage"],
        summary,
    )


def build_reported_difficulties_summary() -> None:
    """Copy aggregate coded-theme counts without exposing response text or IDs."""
    source = OLD_OUTPUTS / "summary" / "open_theme_summary.csv"
    fields, rows = read_csv(source)
    keep = [field for field in ("Question", "Theme", "Frequency") if field in fields]
    write_csv(
        PUBLIC / "reported_difficulties_summary.csv",
        keep,
        [{field: row.get(field, "") for field in keep} for row in rows],
    )


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Restricted source not found: {SOURCE}")
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    build_activity_summary()
    copy_csv(OLD_OUTPUTS / "facility_index" / "facility_index_by_question.csv", PUBLIC / "question_level_facility_index.csv")
    copy_csv(
        OLD_OUTPUTS / "visualisations" / "response_status_by_quiz_and_question_long.csv",
        PUBLIC / "response_status_summary_by_quiz_question.csv",
    )
    copy_csv(
        OLD_OUTPUTS / "visualisations" / "invalid_inputs_by_quiz_and_question.csv",
        PUBLIC / "invalid_input_frequency_table.csv",
    )
    build_questionnaire_summary()
    build_reported_difficulties_summary()

    write_csv(
        PUBLIC / "selected_anonymised_feedback_quotes.csv",
        ["quote_id", "theme", "translated_quote", "original_italian_quote", "used_in_manuscript"],
        [
            {
                "quote_id": "quote01",
                "theme": "Feedback use",
                "translated_quote": "I looked at the feedback provided by the system, understood it, and tried the exercise again.",
                "original_italian_quote": "Ogni volta che sbagliavo un esercizio, guardavo il feedback fornito dal sistema, lo capivo e riprovavo a fare l'esercizio.",
                "used_in_manuscript": "no",
            },
            {
                "quote_id": "quote02",
                "theme": "Mathematical difficulty",
                "translated_quote": "Mathematical understanding.",
                "original_italian_quote": "Comprensione matematica.",
                "used_in_manuscript": "no",
            },
            {
                "quote_id": "quote03",
                "theme": "Input difficulty",
                "translated_quote": "The main difficulty was entering the answers, even though it was fairly clear how to enter them.",
                "original_italian_quote": "Principalmente nelle risposte, perché nonostante fosse abbastanza chiaro come inserire le risposte comunque l'ho trovato abbastanza scomodo.",
                "used_in_manuscript": "no",
            },
        ],
    )

    figure_data = PUBLIC / "figure_source_data"
    figure_data.mkdir()
    for source in (
        OLD_OUTPUTS / "facility_index" / "facility_index_by_question.csv",
        OLD_OUTPUTS / "facility_index" / "facility_index_matrix.csv",
        OLD_OUTPUTS / "visualisations" / "response_status_by_quiz_and_question_long.csv",
        OLD_OUTPUTS / "visualisations" / "invalid_inputs_by_quiz_and_question.csv",
        PUBLIC / "questionnaire_summary_counts_percentages.csv",
        PUBLIC / "reported_difficulties_summary.csv",
    ):
        copy_csv(source, figure_data / source.name)

    (PUBLIC / "codebook.md").write_text(
        "# Public-data codebook\n\n"
        "All files in this folder are aggregate-only or selected non-identifying excerpts. "
        "No row can be linked to a student.\n\n"
        "- `activity_summary.csv`: quiz-level activity totals. Columns: `Quiz Key`, `Quiz`, `Total Attempts`, `Finished Attempts`, `No. of Students`, `Mean Grade`, `SD Grade`.\n"
        "- `question_level_facility_index.csv`: aggregate question performance. Columns: `Quiz`, `Question`, `N`, `Mean question score proportion`, `SD question score proportion`, `Facility Index (%)`.\n"
        "- `response_status_summary_by_quiz_question.csv`: aggregate response-status counts by quiz and question. Columns: `quiz_name`, `question_number`, `response_status_viz`, `count`.\n"
        "- `invalid_input_frequency_table.csv`: aggregate invalid-input frequencies. Columns: `quiz_name`, `question_number`, `invalid_input`, `frequency`.\n"
        "- `questionnaire_summary_counts_percentages.csv`: response counts and percentages for closed questionnaire items. Columns: `question`, `response`, `count`, `percentage`; open-text responses are excluded.\n"
        "- `reported_difficulties_summary.csv`: aggregate coded-theme frequencies from open responses. No response text or student identifiers are included.\n"
        "- `selected_anonymised_feedback_quotes.csv`: short, non-identifying excerpts. Columns: `quote_id`, `theme`, `translated_quote`, `original_italian_quote`, `used_in_manuscript`.\n"
        "- `figure_source_data/`: aggregate CSV inputs used to support figures; no student-level rows are included.\n",
        encoding="utf-8",
    )
    (PUBLIC / "README.md").write_text(
        "# Public data\n\n"
        "This folder contains only anonymised and aggregated data, figure source data, "
        "selected non-linkable feedback excerpts, and documentation. It contains no "
        "student IDs, names, email addresses, timestamps linked to individuals, raw "
        "Moodle/STACK logs, raw quiz scores, or raw questionnaire rows.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
