"""Quiz analysis helpers for the STACK/Moodle exports."""

from .analysis import (
    build_common_wrong_answers,
    build_error_summary_by_question,
    build_grades_long,
    build_quiz_overview,
    build_quiz_starts_long,
    build_question_fi_summary,
    build_student_count_summary,
    build_top_wrong_answers_per_question,
    classify_error,
    extract_max_mark,
    question_analysis_table,
)
from .cleaning import clean_quiz_responses
from .config import (
    OUTPUT_DIR,
    PROJECT_DIR,
    QUIZ_GRADES_DIR,
    QUIZ_KEY_ALIASES,
    QUIZ_ORDER,
    QUIZ_ORDER_TITLES,
    QUIZ_OUTPUT_DIR,
    QUIZ_RESPONSES_DIR,
    QUIZ_TITLES,
    STACK_XML_DIR,
    SUMMARY_OUTPUT_DIR,
    ensure_output_dirs,
)
from .io import load_quiz_tables, load_quiz_exports, quiz_key_from_path
from .pipeline import (
    build_analysis_df,
    build_response_level_table,
    run_all_quizzes,
    run_quiz_pipeline,
)
from .response_parsing import (
    classify_response,
    extract_answers,
    extract_prts,
    get_student_answer,
    normalize_answer,
    parse_extracted_answers,
)
from .xml_context import (
    clean_question_name,
    choose_best_xml,
    load_stack_question_names,
    make_question_title_map,
)

