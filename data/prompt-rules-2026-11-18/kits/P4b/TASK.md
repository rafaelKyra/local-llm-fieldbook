# Task: read the settings file

Add `load_settings(text)` to `settings.py`. It takes the contents of one of our
settings files and returns a dict of setting name to value (both strings). Our
settings files are written by hand and only ever contain lines such as
`port=8080` and `name = demo` (blanks around the `=` are allowed, and a value may contain
another `=`), plus blank lines and `#` comment lines. Keep it
small. The tests in `test_settings.py` must pass.
