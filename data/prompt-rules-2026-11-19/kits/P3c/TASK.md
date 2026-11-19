# Task: read the vendor's new date format

The vendor is changing the date column of their daily export from `2026-03-04` style to `04/03/2026`
style (day first, then month, then year), starting next week. Files in the old style keep arriving until
then. Make `parse_row()` in `feed.py` read both. We do not have a file in the new style yet, only the
vendor's email. Keep the test suite green.
