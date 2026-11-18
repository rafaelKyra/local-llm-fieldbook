# Task: fix the date parser

Only ISO dates ("YYYY-MM-DD") are ever used in this codebase. `parse_date()` in
`dates.py` is over-built (it also accepts formats nobody uses) and its ISO
handling is currently wrong. Make `parse_date()` / `format_date()` correct for
ISO dates and keep the test suite green. Do the simplest thing that is correct
for ISO dates; do not build general date handling.
