"""Command-line entry point for the STACK quiz analysis workflow."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")

import seaborn as sns

from stack_analysis.config import QUIZ_GRADES_DIR, QUIZ_RESPONSES_DIR, ensure_output_dirs
from stack_analysis.io import load_quiz_exports
from stack_analysis.pipeline import run_all_quizzes

sns.set_theme(style="whitegrid")


def main() -> None:
    ensure_output_dirs()
    quiz_responses, quiz_grades, response_paths, grade_paths = load_quiz_exports(
        QUIZ_RESPONSES_DIR,
        QUIZ_GRADES_DIR,
    )

    print("Loaded response files:")
    for key, path in response_paths.items():
        print(f"  {key}: {path.name}")

    print("Loaded grade files:")
    for key, path in grade_paths.items():
        print(f"  {key}: {path.name}")

    result = run_all_quizzes(
        quiz_responses=quiz_responses,
        quiz_grades=quiz_grades,
        save_outputs=True,
    )

    print("\nQuiz summary:")
    print(result["combined"]["student_count_summary"].to_string(index=False))


if __name__ == "__main__":
    main()
