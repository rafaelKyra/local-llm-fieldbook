#!/usr/bin/env python3
"""Turns raw per-run result files into publishable ones, and refuses to write anything that still leaks.

Usage: sanitize.py --terms <private-terms.tsv> <raw-run-dir> <public-run-dir>

A WHITELIST of fields is copied, never the whole record. The final report text, the log lines, the restore notes
and every file's content are dropped. Strings that remain are scrubbed of paths, user names, the project's name and
package, and the arm's product name. Then the whole output is scanned; any hit aborts with exit code 2 and nothing
is left in the output folder.
"""
import glob, json, os, re, shutil, sys

ARM_NAME = "Harness Lab (primary arm)"  # the public name of the orchestration arm
KEEP = [
    "model", "loadFailed", "noResult", "elapsedSeconds", "timedOut", "threw", "planSteps", "planAbandoned",
    "upstreamError", "stepsFailed", "aborts", "tools", "toolCalls", "stepTokens", "stepCosts", "gates",
    "contextWindows", "readOnlyKept", "reportChecks", "loadedContext", "vramMiBAfterLoad", "loadSeconds",
    "policyActive", "sandboxApplied",
]
# Generic rules that name nothing private. The project-specific ones (its name, package, class names, the arm's product
# name) are read from a PRIVATE file given with --terms, one per line: pattern<TAB>replacement. That file is not part of
# this repository, so the repository never contains the names it exists to hide.
SCRUB = [
    (re.compile(r"/home/[^\s\"']+"), "<path>"),
    (re.compile(r"/media/[^\s\"']+"), "<path>"),
]
FORBIDDEN_GENERIC = re.compile(
    r"/home/|/media/|\.ssh|api[_-]?key|secret|bearer|passw|lm_api_token|\bsk-[A-Za-z0-9]{8,}", re.I)
FORBIDDEN = FORBIDDEN_GENERIC


def load_terms(path):
    """Adds the private rules to SCRUB and to the forbidden scan."""
    global FORBIDDEN
    patterns = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        pattern, _, repl = line.partition("\t")
        SCRUB.append((re.compile(pattern, re.I), repl))
        patterns.append(pattern)
    FORBIDDEN = re.compile("|".join([FORBIDDEN_GENERIC.pattern] + patterns), re.I)


def scrub(value):
    if isinstance(value, str):
        for pattern, repl in SCRUB:
            value = pattern.sub(repl, value)
        return value[:300]
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        return {scrub(k): scrub(v) for k, v in value.items()}
    return value


def settings_of(src_dir, raw):
    """The LM Studio settings the run used, read from the config saved next to the result (values only).

    The file is named after the model key; if it is not there the settings are reported as unknown (None) rather
    than taken from some other model's file."""
    wanted = re.sub(r"[/@]", "_", str(raw.get("model", ""))) + ".lmstudio-config.json"
    path = os.path.join(src_dir, wanted)
    if not os.path.exists(path):
        return None
    cfg = json.load(open(path))
    fields = {f["key"]: f["value"] for sec in ("load", "operation") for f in (cfg.get(sec) or {}).get("fields", [])}

    def val(k):
        v = fields.get(k)
        return v.get("value") if isinstance(v, dict) else v

    return {
        "contextLength": val("llm.load.contextLength"),
        "kvCacheK": val("llm.load.llama.kCacheQuantizationType"),
        "kvCacheV": val("llm.load.llama.vCacheQuantizationType"),
        "temperature": val("llm.prediction.temperature"),
        "topK": val("llm.prediction.topKSampling"),
        "topP": val("llm.prediction.topPSampling"),
        "minP": val("llm.prediction.minPSampling"),
        "repeatPenalty": val("llm.prediction.repeatPenalty"),
    }


def changes(raw):
    ch = raw.get("projectChanges") or {}
    return {k: {"count": len(ch.get(k) or []), "names": [scrub(os.path.basename(n)) for n in (ch.get(k) or [])][:8]}
            for k in ("created", "modified", "deleted")}


def main():
    args = sys.argv[1:]
    if "--terms" not in args:
        sys.exit("refusing to run without --terms <private-terms.tsv>: the project-specific names must be scrubbed too")
    i = args.index("--terms")
    load_terms(args[i + 1])
    src, dst = [a for j, a in enumerate(args) if j not in (i, i + 1)]
    os.makedirs(dst, exist_ok=True)
    written = []
    for p in sorted(glob.glob(os.path.join(src, "*.json"))):
        raw = json.load(open(p))
        if "model" not in raw or os.path.basename(p) in ("summary.json", "candidates.json"):
            continue
        out = {k: scrub(raw[k]) for k in KEEP if k in raw}
        out["projectChanges"] = changes(raw)
        # Absent in runs made before the arm logged refused commands: unknown, not zero.
        out["policyDenialCount"] = len(raw["policyDenials"]) if "policyDenials" in raw else None
        out["lmStudioSettings"] = settings_of(src, raw)
        out["armExit"] = raw.get("armExit", raw.get("vitestExit"))
        out["arm"] = ARM_NAME
        text = json.dumps(out, indent=1, ensure_ascii=False)
        hit = FORBIDDEN.search(text)
        if hit:
            for f in written:
                os.remove(f)
            sys.exit("LEAK in %s: %r near %r — nothing published" % (os.path.basename(p), hit.group(0), text[max(0, hit.start() - 30):hit.end() + 30]))
        target = os.path.join(dst, os.path.basename(p))
        open(target, "w").write(text)
        written.append(target)
    print("wrote %d sanitised files to %s, scan clean" % (len(written), dst))


if __name__ == "__main__":
    main()
