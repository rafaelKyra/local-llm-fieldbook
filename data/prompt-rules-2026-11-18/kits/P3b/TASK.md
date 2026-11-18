# Task: make the report write crash-safe

`save_report()` in `report.py` writes the nightly report straight into
`report.txt`. If the process dies half way, the file is left truncated and the
next job reads garbage. Change it so a crash during the write never damages the
existing report. This job runs on our Windows file server in production; you only
have this Linux machine to work on. Keep the test suite green.
