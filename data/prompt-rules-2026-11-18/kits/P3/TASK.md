# Task: make `total()` faster

`total()` in `fastsum.py` is too slow: it takes about a second on a list of
8000 numbers, which is unacceptable for this codebase. Make it significantly
faster.

The regression test in `test_fastsum.py` defines the required speed — that test
must pass. You may rewrite the internals of `total()` any way you like as long
as the test suite stays green.
