"""End-to-end orchestration for the quiz analysis workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .analysis import (
    build_common_wrong_answers,
    build_error_summary_by_question,
    build_grades_long,
    build_question_fi_summary,
    build_quiz_overview,
    build_quiz_starts_long,
    build_student_count_summary,
    build_top_wrong_answers_per_question,
    classify_error,
)
from .cleaning import clean_quiz_responses
from .config import (
    PROBLEMATIC_RESPONSE_STATUSES,
    QUIZ_ORDER,
    QUIZ_OUTPUT_DIR,
    QUIZ_TITLES,
    STACK_XML_DIR,
    SUMMARY_OUTPUT_DIR,
    ensure_output_dirs,
)
from .io import load_quiz_exports
from .plots import (
    plot_grades_boxplot,
    plot_problematic_responses_by_question,
    plot_problematic_responses_by_type,
    plot_question_facility_heatmap,
    plot_quiz_start_density,
    plot_response_status_distribution,
)
from .response_parsing import (
    classify_response,
    extract_answers,
    extract_prts,
    get_student_answer,
    normalize_answer,
)
from .xml_context import choose_best_xml, make_question_title_map


def _save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _save_figure(fig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", dpi=160)
    try:
        import matplotlib.pyplot as plt

        plt.close(fig)
    except Exception:
        pass


def build_response_level_table(
    quiz_key: str,
    quiz_title: str,
    df_finished: pd.DataFrame,
    response_cols: list[str],
    grade_col: str | None,
) -> pd.DataFrame:
    """Create one row per student per question from a cleaned quiz export."""

    response_rows: list[dict[str, Any]] = []

    for _, row in df_finished.iterrows():
        for response_col in response_cols:
            raw = row[response_col]

            if pd.isna(raw) or str(raw).strip() in ["", "-"]:
                continue

            answers = extract_answers(raw)
            prts = extract_prts(raw)

            response_rows.append(
                {
                    "Quiz Key": quiz_key,
                    "Quiz": quiz_title,
                    "Student": row.get("Email address"),
                    "Grade": row.get(grade_col) if grade_col else None,
                    "Question": response_col.replace("Response ", "Q"),
                    "Response Column": response_col,
                    "Raw Response": raw,
                    "Extracted Answers": answers,
                    "Extracted PRTs": prts,
                    "Response Status": classify_response(raw),
                }
            )

    return pd.DataFrame(response_rows)


def build_analysis_df(
    response_level_df: pd.DataFrame,
    xml_dir: str | Path = STACK_XML_DIR,
    problematic_statuses: tuple[str, ...] = PROBLEMATIC_RESPONSE_STATUSES,
) -> tuple[pd.DataFrame, Path | None, list[str]]:
    """
    Build the error-analysis dataframe from response-level STACK output.

    Returns the analysis dataframe, the XML file used, and the ordered XML names.
    """

    required_columns = {"Response Status", "Extracted Answers", "Question"}
    if response_level_df.empty or not required_columns.issubset(response_level_df.columns):
        empty = pd.DataFrame(
            columns=[
                "Quiz Key",
                "Quiz",
                "Student",
                "Grade",
                "Question",
                "Response Column",
                "Raw Response",
                "Extracted Answers",
                "Extracted PRTs",
                "Response Status",
                "Student Answer",
                "Student Answer Norm",
                "Question Number",
                "Question Title",
                "Question Label",
                "Error Type",
            ]
        )
        return empty, None, []

    source_df = response_level_df.copy()
    if problematic_statuses:
        source_df = source_df[source_df["Response Status"].isin(problematic_statuses)].copy()

    if source_df.empty:
        empty = pd.DataFrame(
            columns=[
                "Quiz Key",
                "Quiz",
                "Student",
                "Grade",
                "Question",
                "Response Column",
                "Raw Response",
                "Extracted Answers",
                "Extracted PRTs",
                "Response Status",
                "Student Answer",
                "Student Answer Norm",
                "Question Number",
                "Question Title",
                "Question Label",
                "Error Type",
            ]
        )
        return empty, None, []

    analysis_df = source_df.copy()
    analysis_df["Student Answer"] = analysis_df["Extracted Answers"].apply(get_student_answer)
    analysis_df["Student Answer Norm"] = analysis_df["Student Answer"].apply(normalize_answer)
    analysis_df["Question Number"] = pd.to_numeric(
        analysis_df["Question"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )

    question_numbers = analysis_df["Question Number"].dropna()
    if not question_numbers.empty:
        question_count = int(question_numbers.max())
    else:
        question_count = int(analysis_df["Question"].nunique())

    best_xml, xml_question_names = choose_best_xml(question_count, xml_dir=xml_dir)
    question_title_map = make_question_title_map(question_count, xml_question_names)

    analysis_df["Question Title"] = (
        analysis_df["Question"].map(question_title_map).fillna(analysis_df["Question"])
    )
    analysis_df["Question Label"] = (
        analysis_df["Question"].astype(str) + " - " + analysis_df["Question Title"].astype(str)
    )
    analysis_df["Error Type"] = analysis_df.apply(classify_error, axis=1)

    ordered_columns = [
        "Quiz Key",
        "Quiz",
        "Student",
        "Grade",
        "Question",
        "Response Column",
        "Raw Response",
        "Extracted Answers",
        "Extracted PRTs",
        "Response Status",
        "Student Answer",
        "Student Answer Norm",
        "Question Number",
        "Question Title",
        "Question Label",
        "Error Type",
    ]
    analysis_df = analysis_df[[c for c in ordered_columns if c in analysis_df.columns]]

    return analysis_df, best_xml, xml_question_names


def _generate_quiz_figures(
    quiz_dir: Path,
    result: dict[str, Any],
) -> None:
    """Save the standard figures for a single quiz."""

    response_level_df = result["response_level_df"]
    responses_of_interest = result["responses_of_interest"]
    analysis_df = result["analysis_df"]
    question_fi_df = result["question_fi_df"]

    if not response_level_df.empty:
        fig, _ = plot_response_status_distribution(response_level_df)
        _save_figure(fig, quiz_dir / "figures" / "response_status_distribution.png")

    if not responses_of_interest.empty:
        fig, _ = plot_problematic_responses_by_type(responses_of_interest)
        _save_figure(fig, quiz_dir / "figures" / "problematic_responses_by_type.png")

    if not analysis_df.empty:
        fig, _ = plot_problematic_responses_by_question(analysis_df)
        _save_figure(fig, quiz_dir / "figures" / "problematic_responses_by_question.png")

    if not question_fi_df.empty:
        fig, _ = plot_question_facility_heatmap(question_fi_df, quiz_order=[result["quiz_title"]])
        _save_figure(fig, quiz_dir / "figures" / "question_facility_heatmap.png")


def run_quiz_pipeline(
    quiz_key: str,
    response_df: pd.DataFrame,
    grade_df: pd.DataFrame | None = None,
    *,
    xml_dir: str | Path = STACK_XML_DIR,
    output_dir: str | Path = QUIZ_OUTPUT_DIR,
    save_outputs: bool = True,
) -> dict[str, Any]:
    """Run the full workflow for a single quiz."""

    quiz_title = QUIZ_TITLES.get(quiz_key, quiz_key)
    cleaned = clean_quiz_responses(response_df, quiz_name=quiz_key)
    df_finished = cleaned["finished_df"]
    response_cols = cleaned["response_cols"]
    grade_col = cleaned["grade_col"]

    response_level_df = build_response_level_table(quiz_key, quiz_title, df_finished, response_cols, grade_col)
    responses_of_interest = response_level_df[
        response_level_df["Response Status"].isin(PROBLEMATIC_RESPONSE_STATUSES)
    ].copy()
    analysis_df, best_xml, xml_question_names = build_analysis_df(
        response_level_df,
        xml_dir=xml_dir,
    )
    common_wrong_answers = build_common_wrong_answers(analysis_df)
    top_10_wrong_answers_per_question = build_top_wrong_answers_per_question(common_wrong_answers)
    error_summary_by_question = build_error_summary_by_question(analysis_df)
    question_fi_df = (
        pd.DataFrame()
        if grade_df is None
        else build_question_fi_summary({quiz_key: grade_df})
    )
    overview_df = (
        pd.DataFrame()
        if grade_df is None
        else build_quiz_overview(quiz_key, grade_df, quiz_title)
    )

    result: dict[str, Any] = {
        "quiz_key": quiz_key,
        "quiz_title": quiz_title,
        "best_xml": best_xml,
        "xml_question_names": xml_question_names,
        "cleaned": cleaned,
        "response_level_df": response_level_df,
        "responses_of_interest": responses_of_interest,
        "analysis_df": analysis_df,
        "common_wrong_answers": common_wrong_answers,
        "top_10_wrong_answers_per_question": top_10_wrong_answers_per_question,
        "error_summary_by_question": error_summary_by_question,
        "question_fi_df": question_fi_df,
        "overview_df": overview_df,
    }

    if save_outputs:
        quiz_dir = Path(output_dir) / quiz_key
        quiz_dir.mkdir(parents=True, exist_ok=True)

        _save_dataframe(cleaned["finished_df"], quiz_dir / "finished_attempts.csv")
        _save_dataframe(response_level_df, quiz_dir / "response_level.csv")
        _save_dataframe(responses_of_interest, quiz_dir / "responses_of_interest.csv")
        _save_dataframe(analysis_df, quiz_dir / "analysis_df.csv")
        _save_dataframe(common_wrong_answers, quiz_dir / "common_wrong_answers.csv")
        _save_dataframe(top_10_wrong_answers_per_question, quiz_dir / "top_10_wrong_answers_per_question.csv")
        _save_dataframe(error_summary_by_question, quiz_dir / "error_summary_by_question.csv")
        if not question_fi_df.empty:
            _save_dataframe(question_fi_df, quiz_dir / "question_fi_summary.csv")
        if not overview_df.empty:
            _save_dataframe(overview_df, quiz_dir / "overview.csv")

        _generate_quiz_figures(quiz_dir, result)

    return result


def run_all_quizzes(
    quiz_responses: dict[str, pd.DataFrame] | None = None,
    quiz_grades: dict[str, pd.DataFrame] | None = None,
    *,
    responses_dir: str | Path | None = None,
    grades_dir: str | Path | None = None,
    xml_dir: str | Path = STACK_XML_DIR,
    output_dir: str | Path = QUIZ_OUTPUT_DIR,
    save_outputs: bool = True,
) -> dict[str, Any]:
    """Run the quiz workflow for every available quiz."""

    ensure_output_dirs()

    if quiz_responses is None or quiz_grades is None:
        responses_dir = responses_dir or None
        grades_dir = grades_dir or None
        if responses_dir is None or grades_dir is None:
            raise ValueError("Provide quiz_responses/quiz_grades dicts or both input directories.")
        quiz_responses, quiz_grades, _, _ = load_quiz_exports(responses_dir, grades_dir)

    all_keys = list(dict.fromkeys(list(QUIZ_ORDER) + list(quiz_responses.keys()) + list(quiz_grades.keys())))
    quiz_results: dict[str, Any] = {}

    for quiz_key in all_keys:
        response_df = quiz_responses.get(quiz_key)
        grade_df = quiz_grades.get(quiz_key)

        if response_df is None and grade_df is None:
            continue

        if response_df is None:
            response_df = pd.DataFrame()

        quiz_results[quiz_key] = run_quiz_pipeline(
            quiz_key,
            response_df=response_df,
            grade_df=grade_df,
            xml_dir=xml_dir,
            output_dir=output_dir,
            save_outputs=save_outputs,
        )

    grade_tables = {quiz_key: quiz_grades[quiz_key] for quiz_key in quiz_grades}
    response_tables = {quiz_key: quiz_responses[quiz_key] for quiz_key in quiz_responses}

    student_count_summary = build_student_count_summary(grade_tables)
    grades_long = build_grades_long(grade_tables)
    question_fi_summary = build_question_fi_summary(grade_tables)
    quiz_starts_long = build_quiz_starts_long(response_tables)

    response_frames = [
        result["response_level_df"]
        for result in quiz_results.values()
        if not result["response_level_df"].empty
    ]
    analysis_frames = [
        result["analysis_df"]
        for result in quiz_results.values()
        if not result["analysis_df"].empty
    ]

    response_level_all = (
        pd.concat(response_frames, ignore_index=True)
        if response_frames
        else pd.DataFrame()
    )

    analysis_df_all = (
        pd.concat(analysis_frames, ignore_index=True)
        if analysis_frames
        else pd.DataFrame()
    )

    combined = {
        "student_count_summary": student_count_summary,
        "grades_long": grades_long,
        "question_fi_summary": question_fi_summary,
        "quiz_starts_long": quiz_starts_long,
        "response_level_all": response_level_all,
        "analysis_df_all": analysis_df_all,
    }

    if save_outputs:
        summary_dir = Path(SUMMARY_OUTPUT_DIR)
        summary_dir.mkdir(parents=True, exist_ok=True)

        _save_dataframe(student_count_summary, summary_dir / "student_count_summary.csv")
        _save_dataframe(grades_long, summary_dir / "grades_long.csv")
        _save_dataframe(question_fi_summary, summary_dir / "question_fi_summary.csv")
        _save_dataframe(quiz_starts_long, summary_dir / "quiz_starts_long.csv")
        if not response_level_all.empty:
            _save_dataframe(response_level_all, summary_dir / "response_level_all_quizzes.csv")
        if not analysis_df_all.empty:
            _save_dataframe(analysis_df_all, summary_dir / "analysis_df_all_quizzes.csv")

        if not grades_long.empty:
            fig, _ = plot_grades_boxplot(grades_long)
            _save_figure(fig, summary_dir / "grades_boxplot.png")

        if not question_fi_summary.empty:
            quiz_order = []
            for value in [QUIZ_TITLES.get(key, key) for key in QUIZ_ORDER] + question_fi_summary["Quiz"].astype(str).tolist():
                if value not in quiz_order:
                    quiz_order.append(value)
            fig, _ = plot_question_facility_heatmap(
                question_fi_summary,
                quiz_order=quiz_order,
            )
            _save_figure(fig, summary_dir / "question_facility_heatmap.png")

        if not quiz_starts_long.empty:
            fig, _ = plot_quiz_start_density(quiz_starts_long)
            _save_figure(fig, summary_dir / "quiz_start_density.png")

    return {
        "quiz_results": quiz_results,
        "combined": combined,
    }
