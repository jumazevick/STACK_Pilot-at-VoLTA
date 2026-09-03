# Quiz Workflow

This repo now uses a small reusable pipeline for the STACK quiz analysis.

## Input files

- Quiz responses: `data/raw/quiz_responses/*.xlsx`
- Quiz grades: `data/raw/quiz_grades/*.xlsx`
- Survey export: `data/raw/survey/*.csv`
- STACK XML question files: `moodle_qsn_xml_files/*.xml`

## Canonical quiz keys

- `intro_stack`
- `algebraic_operations`
- `modulus_argument`
- `powers_roots`
- `expressions`

These keys are resolved from file names by `stack_analysis.io.quiz_key_from_path()`.

## Workflow

1. Load every quiz response and grade export.
2. Clean each Moodle export.
3. Build a response-level table with raw STACK output, extracted answers, and PRTs.
4. Keep only problematic responses for error analysis.
5. Attach question titles from the STACK XML.
6. Classify the wrong answers into reusable error codes.
7. Summarize quiz-level and question-level results.
8. Save outputs into `outputs/quizzes/<quiz_key>/` and `outputs/summary/`.

## Output folders

### Per quiz

- `finished_attempts.csv`
- `response_level.csv`
- `responses_of_interest.csv`
- `analysis_df.csv`
- `common_wrong_answers.csv`
- `top_10_wrong_answers_per_question.csv`
- `error_summary_by_question.csv`
- `question_fi_summary.csv`
- `overview.csv`
- `figures/`

### Combined summary

- `student_count_summary.csv`
- `grades_long.csv`
- `question_fi_summary.csv`
- `quiz_starts_long.csv`
- `response_level_all_quizzes.csv`
- `analysis_df_all_quizzes.csv`
- `grades_boxplot.png`
- `question_facility_heatmap.png`
- `quiz_start_density.png`

## Main entry point

Run the full pipeline with:

```bash
python scripts/run_quiz_pipeline.py
```
