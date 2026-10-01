"""Run the 14-task coding grid against one model and save every answer.

Same method as the September 18 table, so the rows are comparable: one request per
task, T0.3 / P0.95, an 8,192-token cap, thinking on for tasks 2/4/5/9/13. Scoring is
NOT done here — the answers are saved and scored offline, so a rule can be disputed
and the whole table re-scored without touching a GPU.

`finish_reason` is recorded for every answer. At a 4,096 cap the same model scored
7/14 and 13/14 on identical text; a truncated answer is not a wrong one.
"""
import json, os, re, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = HERE / "coding-multitest-prompt.md"
OUT = Path(os.environ.get("FIELDBOOK_OUT", HERE.parent / "data" / "runs"))
THINKING_TASKS = {2, 4, 5, 9, 13}
TOKEN = os.environ.get("LM_API_TOKEN", "lm-studio")


def tasks() -> list[dict]:
    text = PROMPT.read_text(encoding="utf-8")
    blocks = re.split(r"^## TASK (\d+) — (.+)$", text, flags=re.M)[1:]
    out = []
    for i in range(0, len(blocks), 3):
        number, title, body = int(blocks[i]), blocks[i + 1].strip(), blocks[i + 2]
        # The WHOLE task body up to its pass criteria, not the first fenced block.
        # Several tasks carry the instruction in one fence and the code to work on in
        # another; taking only the first sent the model a task with no code, and it
        # answered "blocked: no code provided" — which scored as a model failure and
        # was a harness failure (measured 2026-09-20).
        body = re.split(r"^\*\*Pass criteria", body, flags=re.M)[0]
        prompt = re.sub(r"^```\w*$", "", body, flags=re.M).strip()
        out.append({"n": number, "title": title, "prompt": prompt})
    return out


def ask(model: str, prompt: str, thinking: bool) -> dict:
    messages = [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages, "max_tokens": 8192,
            "temperature": 0.3, "top_p": 0.95}
    if thinking:
        # LM Studio passes this through to models that support a reasoning budget.
        body["reasoning_effort"] = "medium"
    request = urllib.request.Request(
        os.environ.get("LM_BASE_URL", "http://localhost:1234/v1") + "/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
    started = time.time()
    with urllib.request.urlopen(request, timeout=1800) as response:
        payload = json.load(response)
    choice = payload["choices"][0]
    usage = payload.get("usage", {})
    seconds = time.time() - started
    return {
        "text": choice["message"].get("content") or "",
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "seconds": round(seconds, 1),
        "tokens_per_second": round((usage.get("completion_tokens") or 0) / seconds, 1) if seconds else None,
    }


def main() -> None:
    model = sys.argv[1]
    run = sys.argv[2] if len(sys.argv) > 2 else ""   # label for repeated runs: 1, 2, 3
    OUT.mkdir(parents=True, exist_ok=True)
    stem = model.replace('/', '_').replace('@', '_') + (f"__run{run}" if run else "")
    target = OUT / f"{stem}.json"
    saved = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"model": model, "answers": {}}

    for task in tasks():
        key = str(task["n"])
        if key in saved["answers"]:
            continue
        try:
            answer = ask(model, task["prompt"], task["n"] in THINKING_TASKS)
        except Exception as error:  # noqa: BLE001
            answer = {"text": "", "error": str(error)[:300], "finish_reason": "error"}
        answer["title"] = task["title"]
        saved["answers"][key] = answer
        target.write_text(json.dumps(saved, indent=1), encoding="utf-8")
        print(f"  task {task['n']:2d} {task['title'][:34]:34s} {answer.get('finish_reason')}"
              f" {answer.get('seconds')}s {answer.get('tokens_per_second')} t/s", flush=True)

    total = sum(a.get("seconds") or 0 for a in saved["answers"].values())
    tokens = sum(a.get("completion_tokens") or 0 for a in saved["answers"].values())
    saved["wall_seconds"] = round(total)
    saved["total_completion_tokens"] = tokens
    saved["median_tps"] = round(tokens / total, 1) if total else None
    target.write_text(json.dumps(saved, indent=1), encoding="utf-8")
    print(f"{model}: {round(total)}s, {tokens} tokens, {saved['median_tps']} t/s")


if __name__ == "__main__":
    main()
