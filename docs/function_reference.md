# Function Reference

This is a short reference for the public quiz-analysis helpers.

## `stack_analysis.config`

- `ensure_output_dirs()` - create the output folders used by the workflow.

## `stack_analysis.io`

- `quiz_key_from_path(path)` - convert a file name into a canonical quiz key.
- `load_quiz_tables(directory)` - load all Excel files from one folder into a keyed dictionary.
- `load_quiz_exports(responses_dir, grades_dir)` - load both response and grade exports.

## `stack_analysis.cleaning`

- `remove_moodle_summary_rows(df)` - remove Moodle rows such as `Overall average`.
- `keep_finished_attempts(df)` - keep only finished attempts.
- `identify_response_cols(df)` - find quiz response columns.
- `identify_grade_cols(df)` - find grade columns.
- `identify_grade_col(df)` - return the first grade column, if present.
- `clean_quiz_responses(quiz_df, quiz_name=None)` - clean a quiz export and return the useful subsets.

## `stack_analysis.response_parsing`

- `parse_extracted_answers(v)` - parse the stored `Extracted Answers` column.
- `get_student_answer(v)` - return the first answer text from the extracted answers list.
- `normalize_answer(ans)` - normalize a student answer for matching and grouping.
- `extract_answers(text)` - extract `ansN` tokens from a STACK response.
- `extract_prts(text)` - extract `prtN` tokens from a STACK response.
- `classify_response(raw)` - classify a STACK response by Moodle/STACK outcome.

## `stack_analysis.xml_context`

- `clean_question_name(name)` - remove STACK naming noise from a question name.
- `load_stack_question_names(xml_path)` - read the ordered STACK question names from XML.
- `choose_best_xml(question_count, xml_dir)` - pick the XML file that best matches a quiz.
- `make_question_title_map(question_count, question_names)` - build the `Q1 -> title` map.

## `stack_analysis.analysis`

- `extract_max_mark(col)` - read the maximum mark from a Moodle question column header.
- `question_analysis_table(df, quiz_name=None)` - summarize question scores for one quiz.
- `build_quiz_overview(quiz_key, grade_df, quiz_title=None)` - one-row quiz summary.
- `build_student_count_summary(quiz_grade_tables)` - combined summary across all quizzes.
- `build_grades_long(quiz_grade_tables)` - long-form grade table for all quizzes.
- `build_question_fi_summary(quiz_grade_tables)` - combined facility-index table.
- `build_quiz_starts_long(quiz_response_tables)` - long-form quiz start timestamps.
- `build_common_wrong_answers(analysis_df)` - count repeated wrong answers.
- `build_top_wrong_answers_per_question(common_wrong_answers, limit=10)` - keep the top wrong answers per question.
- `build_error_summary_by_question(analysis_df)` - summarize error types by question.
- `classify_error(row)` - assign a question-aware error code.

## `stack_analysis.pipeline`

- `build_response_level_table(...)` - create one row per student per question.
- `build_analysis_df(...)` - add student-answer normalization, XML titles, and error types.
- `run_quiz_pipeline(...)` - run the complete workflow for one quiz.
- `run_all_quizzes(...)` - run the complete workflow for every quiz.

## `stack_analysis.plots`

- `plot_response_status_distribution(...)`
- `plot_problematic_responses_by_type(...)`
- `plot_problematic_responses_by_question(...)`
- `plot_grades_boxplot(...)`
- `plot_question_facility_heatmap(...)`
- `plot_quiz_start_density(...)`
- `save_activity(output)` - recreate the activity mean-grade figure from aggregate data.
- `save_activity_participation_performance(output)` - recreate the combined activity participation and mean-performance chart.
- `save_facility(output)` - recreate the question-level facility-index heatmap.
- `save_status(output)` - recreate the response-status summary figure.
- `save_response_status_by_question(output)` - recreate the paper-style question-level response-status figure.
- `save_invalid_inputs(output)` - recreate the invalid-input frequency figure.
- `save_invalid_input_heatmap(output)` - recreate the quiz-by-question invalid-input heatmap.
- `save_questionnaire_background(output)` - recreate the questionnaire background figure (paper Figure 7).
- `save_questionnaire_background_en(output)` - create the English questionnaire background figure.
- `save_questionnaire_background_it(output)` - create the Italian questionnaire background figure.
- `save_reported_difficulties(output)` - recreate the reported-difficulties figure (paper Figure 8).
- `save_most_difficult_topic(output)` - recreate the topic-only Figure 8 chart.
- `save_appendix_d_survey_results(output)` - recreate the three-panel Appendix D coded-survey-results figure.

## Notebook usage

The notebooks can now import these helpers instead of redefining the analysis logic in multiple cells.
