"""Nightly report writer."""
import os


def save_report(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
