"""Score saved answers offline.

Three states, not two. A task is PASS or FAIL only when the answer finished
(finish_reason "stop"). An answer cut off by the token cap, or one that errored, is
INCOMPLETE: its visible text may satisfy a rule, but that proves nothing about the
answer the model would have given. Incomplete is never counted as pass.
`lenient_pass` keeps the older convention (visible text counts) so a result can be
compared with the published September 20 table.

Repeats are supported: every file is one run, files are grouped by model, and rates
are pooled over completed tasks. Scored by the same rules as the September 18 grid.

Offline on purpose: a rule can be argued with and the whole table re-scored without
touching a GPU. The first version of that grid was wrong on four tasks and failed
every model equally — which is only discoverable if the text is still there.

A truncated answer is reported separately and never silently counted as wrong.
"""
import argparse, json, math, re, sys
from collections import defaultdict
from pathlib import Path



def strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)


def t1(a: str) -> bool:
    # JSON tool calls only, from the four declared tools, starting with search_code
    # and containing a write_file.
    objects = re.findall(r'\{[^{}]*"tool"\s*:\s*"(\w+)"[^{}]*\}', a, re.S)
    if not objects:
        objects = re.findall(r'"(?:tool|name)"\s*:\s*"(\w+)"', a)
    declared = {"read_file", "write_file", "search_code", "run_command"}
    if not objects or any(o not in declared for o in objects):
        return False
    return objects[0] == "search_code" and "write_file" in objects


def t2(a: str) -> bool:
    """Cause named, a valid repair proposed, a rollback included.

    RULE WIDENED, and the reason is in the answers: two models proposed removing the
    duplicate CreateModel from 0015 and replacing it with AddIndex. That fixes the
    stated problem and is arguably better than a fake migration, but the rule as
    written ("proposes a fake migration") failed it. The criterion is a valid repair,
    not one particular repair — so editing out the duplicate operation now counts
    alongside --fake and squash. Widened 2026-09-20, before the table was published.
    """
    named = re.search(r"createmodel", a, re.I) is not None
    repair = re.search(
        r"--fake|fake\s+migration|squash|"
        r"(remove|delete|drop|strip)\w*\s+the\s+(duplicate\s+)?[`']?CreateModel|"
        r"replace\s+`?CreateModel`?\s+with|AddIndex", a, re.I) is not None
    rollback = re.search(r"rollback|revert|migrate\s+\w+\s+0", a, re.I) is not None
    return named and repair and rollback


def t3(a: str) -> bool:
    return re.search(r"(extend|\+=)\s*\(?\s*a?\[?\s*i\s*:|result\.extend|\+\s*a\[i:\]|\+\s*b\[j:\]", a) is not None


def t4(a: str) -> bool:
    if not re.search(r"/users", a):
        return False
    methods = sum(bool(re.search(rf'"?{m}"?\s*:', a, re.I)) for m in ("post", "get", "delete"))
    return methods >= 3 and re.search(r"\{[\w_]+\}|parameters", a) is not None and "required" in a.lower()


def t5(a: str) -> bool:
    order = re.search(r"config.*utils|utils.*config", a, re.I | re.S) is not None
    # The rule is "states that there is no cycle", not "uses the phrase 'no cycles'".
    # A model that wrote "Circular dependencies: None." was scored wrong by the first
    # version of this pattern (measured 2026-09-20).
    no_cycle = re.search(
        r"no (circular|cycle|cycles)|zero cycles|acyclic|0 cycles|"
        r"circular dependenc\w*\s*[:\-]?\s*\**\s*(none|no)\b|"
        r"(none|no) circular", a, re.I) is not None
    return order and no_cycle


def t6(a: str) -> bool:
    """Three or more handlers, a dispatcher, and process_data still taking `data`.

    The handler pattern missed `_handle_a`, `_handle_b`, `_handle_c` — a private
    naming convention, not a different design. Counting only `handle_` and `Handler`
    failed six models for a leading underscore (measured 2026-09-20).
    """
    handlers = len(re.findall(r"class\s+\w*Handler\b|def\s+_?handle\w*\s*\(", a))
    return handlers >= 3 and re.search(r"def\s+process_data\s*\(\s*data", a) is not None


def t7(a: str) -> bool:
    # Same correction: the diagnosis is "a permission problem", however it is worded.
    # "owned by the system and is not writable by the current user" is that diagnosis.
    diagnosed = re.search(r"permission|not writable|read-?only|EACCES|owned by (the )?(system|root)",
                          a, re.I) is not None
    return diagnosed and re.search(r"--user|venv|virtualenv", a, re.I) is not None


def t8(a: str) -> bool:
    tests = len(re.findall(r"def\s+test_\w+", a))
    return tests >= 8 and "assert" in a and re.search(r"\bNone\b", a) is not None


def t9(a: str) -> bool:
    """The increment inside the lock, and the race named however it is worded.

    Two corrections here. The lock in this task is a module-level `lock`, not
    `self._lock` — the first pattern was written for code that does not appear in the
    task, and failed every correct answer. And "the race named" is not the literal
    phrase "race condition": "lost updates", "unprotected", "not atomic" all name it.
    """
    inside = re.search(r"with\s+[\w.]*lock\s*:\s*\n\s+counter\s*\+=", a) is not None
    named = re.search(r"race condition|data race|lost update|unprotected|not atomic|"
                      r"without synchroni|concurrent(ly)? (update|modif)", a, re.I) is not None
    return inside and named


def t10(a: str) -> bool:
    return (re.search(r"interface\s+\w+|type\s+\w+\s*=", a) is not None
            and re.search(r"\|\s*null|\?\s*:", a) is not None
            and re.search(r"function\s+validate|const\s+validate", a, re.I) is not None)


def t11(a: str) -> bool:
    if "argparse" not in a or "--min-errors" not in a:
        return False
    third_party = re.search(r"^\s*import\s+(pandas|numpy|requests|tabulate|rich)", a, re.M)
    return third_party is None


def t12(a: str) -> bool:
    return (re.search(r"pool", a, re.I) is not None
            and re.search(r"\b10\b.*\b20\b|\b30\b", a, re.S) is not None
            and re.search(r"create_engine|pool_size", a) is not None)


def t13(a: str) -> bool:
    return (re.search(r"context|decision|consequences|trade-?offs?", a, re.I) is not None
            and re.search(r"recommend", a, re.I) is not None)


def t14(a: str) -> bool:
    """Three of the four classes, named in prose OR by their CWE number.

    The task's own criteria give both forms — "information disclosure (CWE-200),
    hardcoded credentials (CWE-798)" — and an answer that labels each finding with
    its CWE is naming the class, not avoiding it. Four models were failed for using
    the canonical identifier instead of the English phrase (measured 2026-09-20).
    """
    classes = sum(bool(re.search(p, a, re.I)) for p in (
        r"sql injection|CWE-?89\b",
        r"command injection|CWE-?78\b",
        r"hard-?coded (credential|password|secret)|CWE-?798\b",
        r"information (disclosure|exposure)|sensitive data|stack trace|CWE-?200\b"))
    return classes >= 3


RULES = {1: t1, 2: t2, 3: t3, 4: t4, 5: t5, 6: t6, 7: t7,
         8: t8, 9: t9, 10: t10, 11: t11, 12: t12, 13: t13, 14: t14}


STATES = ("pass", "fail", "incomplete")


def classify(n: int, answer: dict | None) -> tuple[str, bool]:
    """Return (state, visible_text_satisfies_rule)."""
    if not answer:
        return "incomplete", False          # never run, or lost: unknown, not failed
    text = strip_thinking(answer.get("text", ""))
    visible_ok = RULES[n](text)
    if answer.get("finish_reason") in (None, "stop"):
        return ("pass" if visible_ok else "fail"), visible_ok
    return "incomplete", visible_ok


def score_run(path: Path) -> dict:
    saved = json.loads(path.read_text(encoding="utf-8"))
    cells = {}
    for n in range(1, 15):
        state, visible = classify(n, saved["answers"].get(str(n)))
        cells[n] = {"state": state, "visible_ok": visible}
    return {"model": saved["model"], "file": path.name, "cells": cells,
            "wall_seconds": saved.get("wall_seconds"), "tps": saved.get("median_tps"),
            "tokens": saved.get("total_completion_tokens")}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials. Treats tasks as the sample:
    it says how much the 14 tasks could move the rate, NOT how much run-to-run
    noise there is - repeats are what measure that."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def aggregate(runs: list[dict]) -> list[dict]:
    by_model = defaultdict(list)
    for run in runs:
        by_model[run["model"]].append(run)
    rows = []
    for model, rs in by_model.items():
        counts = {s: 0 for s in STATES}
        lenient = 0
        per_task = {}
        for n in range(1, 15):
            cell = [r["cells"][n]["state"] for r in rs]
            per_task[n] = cell
            for st, r in zip(cell, rs):
                counts[st] += 1
                lenient += st == "pass" or (st == "incomplete" and r["cells"][n]["visible_ok"])
        done = counts["pass"] + counts["fail"]
        total = 14 * len(rs)
        # Headline = passes out of ALL tasks. An incomplete task is unknown, but a model
        # that cannot finish a task inside the cap has not delivered it; rating only the
        # tasks that finished would put a model that finished 8 of 14 at "100%".
        lo, hi = wilson(counts["pass"], total)
        rows.append({"model": model, "runs": len(rs), "tasks_scored": 14 * len(rs),
                     "pass": counts["pass"], "fail": counts["fail"],
                     "incomplete": counts["incomplete"], "completed": done,
                     "rate": round(counts["pass"] / total, 3),
                     "ceiling": round((counts["pass"] + counts["incomplete"]) / total, 3),
                     "completed_rate": round(counts["pass"] / done, 3) if done else None,
                     "ci95": [round(lo, 3), round(hi, 3)],
                     "lenient_pass": lenient, "per_task": per_task,
                     "tps": rs[0].get("tps"), "wall_seconds": rs[0].get("wall_seconds")})
    rows.sort(key=lambda r: (-r["rate"], r["incomplete"], r["model"]))
    return rows


def bands(rows: list[dict]) -> list[dict]:
    """Greedy bands: a model joins the current band while its interval overlaps the
    interval of the band's leader; otherwise it starts a new band. Rows in one band
    are NOT ranked against each other - that is the point."""
    band, leader = 0, None
    for r in rows:
        if leader is None or r["ci95"][1] < leader["ci95"][0]:
            band += 1
            leader = r
        r["band"] = band
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("answers", type=Path, help="directory of per-run answer JSON files")
    ap.add_argument("--json", type=Path, help="write the full result here")
    args = ap.parse_args()
    runs = [score_run(p) for p in sorted(args.answers.glob("*.json"))]
    rows = bands(aggregate(runs))
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("rate = pass / all tasks (incomplete counts against); ceiling = if every incomplete had passed;")
    print("old = visible-text convention of the published Sept 20 table\n")
    print(f"{'band':>4}  {'pass':>4} {'fail':>4} {'inc':>3}  {'rate':>5}  {'95% interval':>13}  {'ceil':>5}  {'old':>4}  model")
    for r in rows:
        ci = f"{r['ci95'][0]:.2f}-{r['ci95'][1]:.2f}"
        print(f"{r['band'] or '-':>4}  {r['pass']:>4} {r['fail']:>4} {r['incomplete']:>3}  "
              f"{r['rate']:>5.2f}  {ci:>13}  {r['ceiling']:>5.2f}  {r['lenient_pass']:>4}  {r['model']}")


if __name__ == "__main__":
    main()
