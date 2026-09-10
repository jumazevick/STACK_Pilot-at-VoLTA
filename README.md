# STACK Pilot at VoLTA

Reproducible aggregate-only data and analysis materials for the manuscript
?Evaluating Students? First-time Use of STACK in Complex-Analysis Exercises
in an Italian Upper-Secondary School?.

Public repository: <https://github.com/jumazevick/STACK_Pilot-at-VoLTA>

## Run the quiz pipeline

Create/activate a virtual environment and install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Then run:

```powershell
python scripts/run_quiz_pipeline.py
```

Quiz exports may be CSV or Excel files. Response exports belong in
`data/raw/quiz_responses`; grade exports belong in `data/raw/quiz_grades`.

## Data Availability

This repository contains the anonymised and aggregated public data supporting the manuscript. The public files include aggregated Moodle/STACK activity summaries, question-level facility-index data, response-status summaries, invalid-input frequency tables, questionnaire summary statistics, selected anonymised feedback excerpts, figure source data, and analysis scripts.

Raw student-level Moodle/STACK records, linked Moodle-questionnaire datasets, and full questionnaire responses are not publicly available because the study involved upper-secondary students and these records may allow participant re-identification, even after pseudonymisation. Access to restricted data may be considered by the corresponding author upon reasonable request, subject to ethical, privacy, institutional, and school-level approval.

For the wording used in the manuscript, see [`docs/data_availability_statement.md`](docs/data_availability_statement.md).

## Reproducing public figures

The public figures can be regenerated without restricted data:

```powershell
python -m pip install -r requirements.txt
python scripts/plot_public_data.py
```

The script reads only aggregate CSVs in `public_data/` and `public_data/figure_source_data/`. It writes thirteen PNG files to `reproduced_figures/`, including the paper-style participation/performance, response-status, invalid-input, questionnaire, topic, and Appendix D survey-results plots.

For the complete function-to-input-to-output mapping and individual Python code blocks, see [`docs/plot_reproduction.md`](docs/plot_reproduction.md).
