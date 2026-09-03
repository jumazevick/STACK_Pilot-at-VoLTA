"""Create the paper's Table 3 from restricted invalid-response analysis data.

The output deliberately excludes student identifiers, grades, timestamps, and raw
STACK records. It is intended for local manuscript preparation, not public release.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "private_data" / "pseudonymized_data" / "outputs" / "visualisations" / "invalid_inputs_long.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "summary" / "table3_invalid_input_examples.csv"


def build_table(input_path: Path) -> list[dict[str, str]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("has_invalid_input", "").casefold() != "true":
                continue
            invalid = row.get("invalid_input", "").strip()
            expected_default = row.get("expected_answer_clean", "").strip()
            if not invalid:
                continue
            try:
                answer_fields = json.loads(row.get("invalid_answers_json", "{}"))
            except json.JSONDecodeError:
                answer_fields = {}
            expected_fields = {}
            right_answer_raw = row.get("right_answer_raw", "")
            for match in re.finditer(r"ans(\d+):\s*(.*?)(?=\s+\[score\];|\s+\[invalid\];|$)", right_answer_raw):
                expected_fields[f"ans{match.group(1)}"] = match.group(2).strip()
            for answer_field, value in answer_fields.items():
                expected = str(expected_fields.get(answer_field, expected_default)).strip()
                if not expected:
                    continue
                key = (
                    row.get("quiz_name", "").strip(),
                    row.get("question_number", "").strip(),
                    answer_field,
                    str(value).strip(),
                    expected,
                )
                counts[key] += 1

    rows = [
        {
            "Quiz": quiz,
            "Question": f"Q{question}" if question and not question.startswith("Q") else question,
            "Answer field": answer_field,
            "Invalid input": invalid,
            "Expected answer": expected,
            "Count": str(count),
        }
        for (quiz, question, answer_field, invalid, expected), count in counts.items()
    ]
    return sorted(rows, key=lambda row: (row["Quiz"], row["Question"], row["Answer field"], row["Invalid input"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Restricted input not found: {args.input}")
    rows = build_table(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["Quiz", "Question", "Answer field", "Invalid input", "Expected answer", "Count"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} rows in {args.output}")


if __name__ == "__main__":
    main()
