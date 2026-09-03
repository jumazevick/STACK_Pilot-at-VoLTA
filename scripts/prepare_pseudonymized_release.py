"""Create a linked, pseudonymised release from a private historical checkout.

The lookup between source identifiers and student IDs is deliberately kept out
of the repository. This release is pseudonymised, not anonymous.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path


DIRECT_HEADERS = {
    "last name",
    "first name",
    "email address",
    "user full name",
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def norm(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_lookup(source_root: Path) -> dict[str, str]:
    people: dict[str, set[str]] = {}
    for path in sorted(source_root.rglob("*.csv")):
        fields, rows = read_csv(path)
        lower = {field.casefold(): field for field in fields}
        email_field = lower.get("email address")
        name_fields = [
            lower.get("user full name"),
            lower.get("last name"),
            lower.get("first name"),
        ]
        for row in rows:
            email = norm(row.get(email_field, "")) if email_field else ""
            name = norm(row.get(name_fields[0], "")) if name_fields[0] else ""
            if not name and name_fields[1] and name_fields[2]:
                name = norm(f"{row.get(name_fields[2], '')} {row.get(name_fields[1], '')}")
            key = email or name
            if key:
                people.setdefault(key, set()).update(x for x in (email, name) if x)

    ordered = sorted(people, key=lambda value: ("@" not in value, value))
    lookup: dict[str, str] = {}
    for index, key in enumerate(ordered, start=1):
        student_id = f"student{index:02d}"
        for alias in people[key]:
            lookup[alias] = student_id
    return lookup


def row_student_id(row: dict[str, str], lookup: dict[str, str]) -> str:
    for value in row.values():
        key = norm(value)
        if key in lookup:
            return lookup[key]
    for field, value in row.items():
        if "student" in field.casefold() or "email" in field.casefold():
            key = norm(value)
            if key in lookup:
                return lookup[key]
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("private_checkout", type=Path)
    parser.add_argument("--output", type=Path, default=Path("pseudonymized_data"))
    args = parser.parse_args()

    source_root = args.private_checkout / "data" / "raw"
    output_root = args.output
    if output_root.exists():
        shutil.rmtree(output_root)
    lookup = build_lookup(source_root)
    aliases = sorted(lookup, key=len, reverse=True)

    source_files = list(source_root.rglob("*.csv"))
    source_files += list((args.private_checkout / "outputs").rglob("*.csv"))
    source_files += [args.private_checkout / "coded_open_responses_manual_review.csv"]

    for source in sorted(path for path in source_files if path.exists()):
        fields, rows = read_csv(source)
        direct = {field for field in fields if field.casefold() in DIRECT_HEADERS}
        clean_fields = [field for field in fields if field not in direct]
        has_person = any(
            "student" in field.casefold()
            or "email" in field.casefold()
            or field.casefold() in DIRECT_HEADERS
            for field in fields
        )
        if has_person and "student_id" not in {field.casefold() for field in clean_fields}:
            clean_fields.insert(0, "student_id")

        clean_rows: list[dict[str, str]] = []
        for row in rows:
            student_id = row_student_id(row, lookup)
            clean = {field: row.get(field, "") for field in clean_fields if field != "student_id"}
            if has_person:
                clean["student_id"] = student_id
            for field, value in list(clean.items()):
                masked = value
                for alias in aliases:
                    if alias and ("@" in alias or len(alias) > 4):
                        masked = re.sub(re.escape(alias), student_id or "participant", masked, flags=re.IGNORECASE)
                clean[field] = masked
            clean_rows.append(clean)

        if source.is_relative_to(source_root):
            relative = Path("source") / source.relative_to(source_root)
        elif source.is_relative_to(args.private_checkout / "outputs"):
            relative = Path("outputs") / source.relative_to(args.private_checkout / "outputs")
        else:
            relative = Path("coded_open_responses_manual_review.csv")
        write_csv(output_root / relative, clean_fields, clean_rows)

    (output_root / "README.md").write_text(
        "# Linked pseudonymised data\n\n"
        "These files use stable student IDs (student01, student02, ...), allowing "
        "responses to be linked across survey and Moodle/STACK files. Direct names "
        "and email addresses have been removed. This is pseudonymised personal data, "
        "not anonymous data; the lookup key is not included. Public release assumes "
        "appropriate ethics and institutional approval.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
