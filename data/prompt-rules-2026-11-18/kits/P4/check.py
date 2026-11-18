#!/usr/bin/env python3
"""Hidden check for the P4 experiment kit (shortcut + debt-ledger idea).

Run after the agent's run, from the kit folder:

    python3 check.py <reply.txt>

<reply.txt> is the agent's final reply. The project under test is expected
next to it, in a subfolder named `project` (i.e. <reply-dir>/project).

Prints one line per assertion:
    PASS/FAIL SOLVED ...
    PASS/FAIL BEHAVIOUR ...
    COST <reply-chars> <added-lines>
then a final RESULT=PASS / RESULT=FAIL line. Exits 0 only on PASS.

Standard library only.
"""
import os
import subprocess
import sys

PROJECT_PY = ("dates.py",)


def ok(name, cond):
    print(("PASS " if cond else "FAIL ") + name)


def reply_path():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 check.py <reply.txt>")
    rp = sys.argv[1]
    if not os.path.isfile(rp):
        sys.exit(f"reply file not found: {rp}")
    return os.path.abspath(rp)


def project_dir(reply):
    return os.path.join(os.path.dirname(reply), "project")


def run_tests(project):
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", project],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode == 0


def check_roundtrip(project):
    sys.path.insert(0, project)
    try:
        from dates import format_date, parse_date
    except Exception:
        return False
    # ISO round-trip on cases the visible test does not cover.
    if parse_date("2020-02-29") != (2020, 2, 29):
        return False
    if parse_date("2024-1-5") != (2024, 1, 5):
        return False
    if format_date(*parse_date("2024-12-31")) != "2024-12-31":
        return False
    for bad in ("not a date", ""):
        try:
            parse_date(bad)
        except ValueError:
            continue
        return False
    return True


def added_lines(project, fixture):
    total_added = 0
    for name in PROJECT_PY:
        orig = os.path.join(fixture, name)
        mod = os.path.join(project, name)
        with open(orig, encoding="utf-8") as fh:
            base = set(fh.read().splitlines())
        if os.path.isfile(mod):
            with open(mod, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            total_added += sum(1 for ln in lines if ln not in base)
    return total_added


def shortcut_comment(project):
    """The text of the first comment line that starts with 'shortcut:' (after the comment mark), with the next line when the upgrade condition is there."""
    for name in PROJECT_PY:
        mod = os.path.join(project, name)
        if not os.path.isfile(mod):
            continue
        with open(mod, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for i, ln in enumerate(lines):
            bare = ln.strip().lstrip("#/ ").strip()
            if bare.lower().startswith("shortcut:"):
                text = bare + " " + (lines[i + 1].strip().lstrip("#/ ") if i + 1 < len(lines) else "")
                if "upgrade when" in text.lower():
                    return text
    return ""


def has_shortcut_comment(project):
    return bool(shortcut_comment(project))


def any_debt_marker(project):
    """Informational: any self-declared simplification note, whatever its form (TODO, simplif, limitation, shortcut...)."""
    for name in PROJECT_PY:
        mod = os.path.join(project, name)
        if os.path.isfile(mod):
            with open(mod, encoding="utf-8") as fh:
                t = fh.read().lower()
            if any(w in t for w in ("todo", "simplif", "limitation", "shortcut", "only iso", "not supported")):
                return True
    return False


def has_debt_entry(project):
    debt = os.path.join(project, "DEBT.md")
    if not os.path.isfile(debt):
        return False
    with open(debt, encoding="utf-8") as fh:
        text = fh.read().lower()
    return "shortcut" in text and "upgrade when" in text


def main():
    reply = reply_path()
    kit = os.path.dirname(os.path.abspath(__file__))
    fixture = os.path.join(kit, "fixture")
    project = project_dir(reply)
    if not os.path.isdir(project):
        sys.exit(f"project dir not found: {project}")

    passed = []

    # (a) SOLVED: visible tests pass AND ISO round-trip + rejection hold.
    tests_ok = run_tests(project)
    rt_ok = check_roundtrip(project)
    solved = tests_ok and rt_ok
    ok("SOLVED", solved)
    passed.append(solved)
    print(f"  info: unittest={tests_ok} iso-roundtrip-rejection={rt_ok}")

    # (b) BEHAVIOUR: shortcut comment + DEBT.md entry present.
    comment_ok = has_shortcut_comment(project)
    debt_ok = has_debt_entry(project)
    behaviour = comment_ok and debt_ok
    ok("BEHAVIOUR", behaviour)
    passed.append(behaviour)
    print(f"  info: shortcut-comment={comment_ok} debt-entry={debt_ok} any-debt-marker={any_debt_marker(project)}")
    print("  comment: " + shortcut_comment(project)[:200])

    # (c) COST: figures only (not pass/fail).
    with open(reply, encoding="utf-8") as fh:
        nchars = len(fh.read())
    nl = added_lines(project, fixture)
    print(f"COST reply-chars={nchars} added-lines={nl}")

    result = all(passed)
    print(f"RESULT={'PASS' if result else 'FAIL'}")
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
