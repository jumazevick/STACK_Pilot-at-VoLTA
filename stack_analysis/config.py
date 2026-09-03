"""Central configuration for the quiz analysis workflow."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Public compatibility alias used by ``stack_analysis.__init__`` and older
# notebooks.
PROJECT_DIR = BASE_DIR
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

QUIZ_RESPONSES_DIR = RAW_DATA_DIR / "quiz_responses"
QUIZ_GRADES_DIR = RAW_DATA_DIR / "quiz_grades"
SURVEY_DATA_DIR = RAW_DATA_DIR / "survey"
STACK_XML_DIR = BASE_DIR / "moodle_qsn_xml_files"

OUTPUT_DIR = BASE_DIR / "outputs"
QUIZ_OUTPUT_DIR = OUTPUT_DIR / "quizzes"
SUMMARY_OUTPUT_DIR = OUTPUT_DIR / "summary"

STUDENT_COL = "Email address"
STATE_COL = "State"
STARTED_COL = "Started on"
FINISHED_STATE = "finished"

QUIZ_TITLES = {
    "intro_stack": "Intro to STACK",
    "algebraic_operations": "Algebraic Operations",
    "modulus_argument": "Modulus & Argument",
    "powers_roots": "Powers & Roots",
    "expressions": "Expressions",
}

QUIZ_ORDER = [
    "intro_stack",
    "algebraic_operations",
    "modulus_argument",
    "powers_roots",
    "expressions",
]

QUIZ_ORDER_TITLES = [QUIZ_TITLES[key] for key in QUIZ_ORDER]

QUIZ_KEY_ALIASES = {
    "intro_stack": [
        "guida introduttiva",
        "intro to stack",
        "intro_stack",
        "intro_to_stack",
    ],
    "algebraic_operations": [
        "operazioni di base",
        "algebraic operations",
        "algebraic_operations",
    ],
    "modulus_argument": [
        "modulo e argomento",
        "modulus & argument",
        "modulus_argument",
    ],
    "powers_roots": [
        "potenze e radici",
        "powers & roots",
        "powers_roots",
    ],
    "expressions": [
        "espressioni",
        "expressions",
    ],
}

PROBLEMATIC_RESPONSE_STATUSES = (
    "Incorrect",
    "Invalid syntax",
    "No response / not evaluated",
    "Manual review",
)


def ensure_output_dirs() -> dict[str, Path]:
    """Create the output folders used by the quiz workflow."""

    dirs = {
        "output": OUTPUT_DIR,
        "quiz_output": QUIZ_OUTPUT_DIR,
        "summary_output": SUMMARY_OUTPUT_DIR,
    }

    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    return dirs
