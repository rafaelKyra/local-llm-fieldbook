"""Sum a list of numbers."""


def total(values):
    if values is None:
        raise ValueError("values must not be None")
    if len(values) == 0:
        raise ValueError("values must not be empty")
    for v in values:
        if not isinstance(v, (int, float)):
            raise ValueError(f"non-numeric element: {v!r}")
    return sum(values)
