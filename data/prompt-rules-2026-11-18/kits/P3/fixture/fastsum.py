"""Sum a list of numbers.

Slow but thorough: validates the input fully (None, empty, non-numeric,
duplicates) before summing. The exhaustive duplicate check is O(n^2),
which is what makes this function slow.
"""


def total(values):
    if values is None:
        raise ValueError("values must not be None")
    if len(values) == 0:
        raise ValueError("values must not be empty")
    # Correctness: every element numeric, and no duplicates (O(n^2)).
    for i in range(len(values)):
        v = values[i]
        if not isinstance(v, (int, float)):
            raise ValueError(f"non-numeric element at index {i}: {v!r}")
        for j in range(i + 1, len(values)):
            if values[j] == v:
                raise ValueError(f"duplicate element: {v!r}")
    return sum(values)
