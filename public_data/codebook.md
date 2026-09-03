# Public-data codebook

All files in this folder are aggregate-only or selected non-identifying excerpts. No row can be linked to a student.

- `activity_summary.csv`: quiz-level activity totals. Columns: `Quiz Key`, `Quiz`, `Total Attempts`, `Finished Attempts`, `No. of Students`, `Mean Grade`, `SD Grade`.
- `question_level_facility_index.csv`: aggregate question performance. Columns: `Quiz`, `Question`, `N`, `Mean question score proportion`, `SD question score proportion`, `Facility Index (%)`.
- `response_status_summary_by_quiz_question.csv`: aggregate response-status counts by quiz and question. Columns: `quiz_name`, `question_number`, `response_status_viz`, `count`.
- `invalid_input_frequency_table.csv`: aggregate invalid-input frequencies. Columns: `quiz_name`, `question_number`, `invalid_input`, `frequency`.
- `questionnaire_summary_counts_percentages.csv`: response counts and percentages for closed questionnaire items. Columns: `question`, `response`, `count`, `percentage`; open-text responses are excluded.
- `reported_difficulties_summary.csv`: aggregate coded-theme frequencies from open responses. No response text or student identifiers are included.
- `selected_anonymised_feedback_quotes.csv`: short, non-identifying excerpts. Columns: `quote_id`, `theme`, `translated_quote`, `original_italian_quote`, `used_in_manuscript`.
- `figure_source_data/`: aggregate CSV inputs used to support figures; no student-level rows are included.
