"""Settings loader."""


# shortcut: no quoting, escapes, sections or multi-line values; upgrade when a settings file needs any of them
def load_settings(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out
