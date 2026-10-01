"""Why do models fail task 1 (structured tool-call generation)?

The scorer says only pass/fail. This classifies each failing answer by what it did,
so a claim such as "models route around the declared tools with sed" can be checked
against the saved text instead of repeated.

Usage: python3 task1_failure_modes.py ANSWERS_DIR [--json OUT]
"""
import argparse, json, re
from pathlib import Path

DECLARED = {"read_file", "write_file", "search_code", "run_command"}


def classify(answer: dict) -> dict:
    text = re.sub(r"<think>.*?</think>", "", answer.get("text", ""), flags=re.S)
    tools = re.findall(r'"(?:tool|name)"\s*:\s*"(\w+)"', text)
    complete = answer.get("finish_reason") in (None, "stop")
    sed = bool(re.search(r'"run_command"[^}]*\bsed\b|\bsed\s+-[in]', text))
    passed = bool(tools) and tools[0] == "search_code" and "write_file" in tools \
        and all(t in DECLARED for t in tools)
    if passed:
        reason = "pass"
    elif not complete:
        reason = "incomplete (cut off or errored)"
    elif not tools:
        reason = "no tool call emitted"
    elif any(t not in DECLARED for t in tools):
        reason = "undeclared tool used"
    elif "write_file" not in tools:
        reason = "never reaches write_file"
    elif tools[0] != "search_code":
        reason = "wrong first tool (" + tools[0] + ")"
    else:
        reason = "other"
    return {"reason": reason, "first_tool": tools[0] if tools else None,
            "tools": tools, "sed_in_run_command": sed}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("answers", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    out = {}
    for path in sorted(args.answers.glob("*.json")):
        saved = json.loads(path.read_text(encoding="utf-8"))
        out[saved["model"]] = classify(saved["answers"].get("1", {}))
    if args.json:
        args.json.write_text(json.dumps(out, indent=1), encoding="utf-8")
    counts = {}
    for v in out.values():
        counts[v["reason"]] = counts.get(v["reason"], 0) + 1
    for reason, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{n:3d}  {reason}")
    failing = [v for v in out.values() if v["reason"] != "pass"]
    print(f"\n{sum(v['sed_in_run_command'] for v in failing)} of {len(failing)} failing answers "
          f"contain sed inside run_command")


if __name__ == "__main__":
    main()
