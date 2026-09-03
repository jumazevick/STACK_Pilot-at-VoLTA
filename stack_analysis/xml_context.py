"""Helpers for reading STACK question XML files."""

from __future__ import annotations

from pathlib import Path

import xml.etree.ElementTree as ET

from .config import STACK_XML_DIR


def clean_question_name(name: str) -> str:
    """Clean a STACK question name for display."""

    s = str(name).strip()
    return s.removeprefix("Q0_Syntax-")


def load_stack_question_names(xml_path: str | Path) -> list[str]:
    """Load the ordered list of question names from a STACK XML file."""

    root = ET.parse(xml_path).getroot()
    names: list[str] = []

    for q in root.findall(".//question[@type='stack']"):
        name_node = q.find("name")
        raw_name = "".join(name_node.itertext()).strip() if name_node is not None else ""
        if raw_name:
            names.append(clean_question_name(raw_name))

    return names


def choose_best_xml(
    question_count: int,
    xml_dir: str | Path = STACK_XML_DIR,
) -> tuple[Path | None, list[str]]:
    """Pick the XML file whose STACK question count best matches a quiz."""

    xml_dir = Path(xml_dir)
    xml_files = sorted(xml_dir.glob("*.xml"))
    candidates: list[tuple[int, int, Path, list[str]]] = []

    for path in xml_files:
        names = load_stack_question_names(path)
        candidates.append((abs(len(names) - question_count), len(names), path, names))

    if not candidates:
        return None, []

    candidates.sort(key=lambda item: (item[0], item[1]))
    _, _, best_path, best_names = candidates[0]
    return best_path, best_names


def make_question_title_map(question_count: int, question_names: list[str]) -> dict[str, str]:
    """Build a Q1/Q2/... -> question title mapping from ordered XML names."""

    upper = max(question_count, len(question_names))
    mapping: dict[str, str] = {}

    for i in range(1, upper + 1):
        if i - 1 < len(question_names):
            mapping[f"Q{i}"] = question_names[i - 1]
        else:
            mapping[f"Q{i}"] = f"Question {i}"

    return mapping

