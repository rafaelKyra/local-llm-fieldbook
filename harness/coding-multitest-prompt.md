# Local LLM Coding Multitest — Tool Execution & Agentic Capabilities

**Purpose:** Evaluate local LLMs (3B-35B) on coding-relevant tasks that test tool execution, agentic reasoning, and structured output. Designed for RTX 3090 24GB + 256GB RAM rigs running LM Studio / OpenCode / rafa.ai.

**Scoring:** Each task is pass/fail. Median of 3 runs per model. Wall-clock time recorded. Total: 14 tasks.

---

## TASK 1 — Structured Tool-Call Generation

```
SYSTEM: You are a tool-calling agent. Reply ONLY with valid JSON tool calls.

TOOLS AVAILABLE:
- read_file(path: str) -> str
- write_file(path: str, content: str) -> bool
- search_code(pattern: str, glob: str) -> list[str]
- run_command(cmd: str) -> str

TASK: The user wants to find all Python files importing `requests` and replace `requests.get` with `httpx.get`. Generate the exact tool-call sequence to accomplish this. Output each step as a separate JSON object with "tool" and "args" keys.

CONSTRAINTS: No prose. No explanation. Only tool-call JSON objects, one per line.
```

**Pass criteria:** Correct tool sequence (search → read → write), valid JSON, no hallucinated tools, respects constraints.

---

## TASK 2 — Multi-Step Agentic Planning

```
SYSTEM: You are an agentic coding assistant. Think step-by-step, then execute.

CONTEXT: A Django project has a broken migration. The error is:
  django.db.utils.OperationalError: relation "orders_order" already exists

The migration 0015_add_index.py tries to CreateModel("Order") but the table exists from 0002_initial.py.

TASK: Generate a plan to fix this. Include:
1. Diagnosis steps (what to check)
2. Fix options (at least 2 approaches)
3. Verification steps
4. Rollback plan

Output as structured markdown with numbered steps.
```

**Pass criteria:** Identifies root cause (duplicate CreateModel), proposes valid fixes (fake migration / squash), includes rollback, no hallucinated commands.

---

## TASK 3 — Code Repair with Context

```
SYSTEM: Fix the bug. Output ONLY the corrected function. No explanation.

BROKEN CODE:
```python
def merge_sorted(a: list[int], b: list[int]) -> list[int]:
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    return result
```

TEST THAT FAILS:
```python
assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
```

TASK: Fix the function so the test passes.
```

**Pass criteria:** Appends remaining elements (`result.extend(a[i:])` or equivalent), test passes, no extra output.

---

## TASK 4 — API Contract Extraction

```
SYSTEM: Extract the API contract from the code. Output valid JSON Schema.

CODE:
```python
from pydantic import BaseModel
from typing import Optional

class CreateUserRequest(BaseModel):
    username: str
    email: str
    age: int = 0
    role: str = "viewer"
    mfa_enabled: bool = False

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str

@app.post("/users", response_model=UserResponse)
async def create_user(req: CreateUserRequest):
    ...

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    ...

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    ...
```

TASK: Generate a complete OpenAPI 3.0 spec (JSON) for these endpoints. Include request/response schemas, required fields, and HTTP methods.
```

**Pass criteria:** Valid OpenAPI JSON, correct methods/paths, schemas match Pydantic models, required fields marked.

---

## TASK 5 — Dependency Analysis

```
SYSTEM: Analyze the dependency graph. Output as adjacency list.

MODULES:
- main.py imports: api, db, auth, config
- api.py imports: db, auth, models, utils
- db.py imports: config, models
- auth.py imports: db, config, utils
- models.py imports: config
- utils.py imports: (none)
- config.py imports: (none)

TASK: 
1. List all modules in topological order (dependencies first)
2. Identify the module with the most dependents
3. Identify any circular dependencies
4. If config.py interface changes, list all affected modules (transitive)
```

**Pass criteria:** Correct topological order, accurate dependent count, detects zero cycles (correct), lists transitive affected set.

---

## TASK 6 — Refactoring with Safety

```
SYSTEM: Refactor the code. Output ONLY the refactored code. No explanation.

CODE:
```python
def process_data(data):
    results = []
    for item in data:
        if item.get("type") == "A":
            value = item["value"] * 2
            if value > 100:
                results.append({"id": item["id"], "value": value, "category": "high"})
            else:
                results.append({"id": item["id"], "value": value, "category": "low"})
        elif item.get("type") == "B":
            value = item["value"] + 50
            results.append({"id": item["id"], "value": value, "category": "adjusted"})
        elif item.get("type") == "C":
            if item["value"] < 0:
                results.append({"id": item["id"], "value": 0, "category": "clamped"})
            else:
                results.append({"id": item["id"], "value": item["value"], "category": "passthrough"})
    return results
```

TASK: Refactor into:
1. A strategy pattern with separate handler functions per type
2. A dispatcher function
3. Keep the same external interface (process_data(data) -> list[dict])
4. Make it testable (pure functions, no side effects)
```

**Pass criteria:** Clean strategy pattern, dispatcher dispatches correctly, same output for same input, no logic changes.

---

## TASK 7 — Error Recovery Simulation

```
SYSTEM: You are an agent executing a plan. Something fails. Recover.

PLAN:
1. Clone repo: git clone https://github.com/example/app.git
2. Install deps: pip install -r requirements.txt
3. Run tests: pytest tests/
4. Deploy: docker build -t app .

STEP 2 FAILED:
ERROR: Could not install packages because of permission error: [Errno 13] Permission denied: '/usr/lib/python3/dist-packages/certifi'

TASK: 
1. Explain why step 2 failed
2. Generate the exact recovery command(s)
3. Show the revised plan from step 2 onward
4. Identify if this failure affects step 3 or 4
```

**Pass criteria:** Correct diagnosis (permission), valid recovery (--user or venv), revised plan correct, no cascading error false positives.

---

## TASK 8 — Test Generation

```
SYSTEM: Generate comprehensive tests. Output ONLY test code.

CODE:
```python
def parse_log_line(line: str) -> dict | None:
    """Parse a log line like '2024-01-15 10:30:45 ERROR [auth] Login failed for user admin'"""
    parts = line.split(" ", 5)
    if len(parts) < 6:
        return None
    date, time, level, module_raw, message = parts[0], parts[1], parts[2], parts[3], parts[5]
    module = module_raw.strip("[]")
    if level not in ("INFO", "WARN", "ERROR", "DEBUG"):
        return None
    return {"date": date, "time": time, "level": level, "module": module, "message": message}
```

TASK: Generate pytest tests covering:
1. Happy path (valid log line)
2. Edge cases (empty string, malformed, missing fields)
3. Invalid log level
4. Module name extraction with brackets
5. Multiple spaces in message
```

**Pass criteria:** ≥8 test cases, covers all edge cases listed, tests are runnable, assertions correct.

---

## TASK 9 — Concurrency Reasoning

```
SYSTEM: Analyze the race condition. Output the fix.

CODE:
```python
import threading

counter = 0
lock = threading.Lock()

def increment(n):
    global counter
    for _ in range(n):
        # BUG: lock is acquired but not held during increment
        with lock:
            pass
        counter += 1

threads = [threading.Thread(target=increment, args=(1000,)) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)  # Expected: 10000, Actual: varies
```

TASK:
1. Identify the exact bug
2. Show the corrected code
3. Explain why the original code fails
4. What would happen if you used `threading.RLock` instead?
```

**Pass criteria:** Identifies counter increment outside lock, correct fix shown, accurate explanation, correct RLock analysis.

---

## TASK 10 — Schema Inference

```
SYSTEM: Infer the data schema from usage. Output as TypeScript types.

USAGE:
```python
user = {
    "id": 12345,
    "name": "Alice",
    "email": "alice@example.com",
    "preferences": {
        "theme": "dark",
        "notifications": True,
        "language": "en"
    },
    "tags": ["admin", "beta-tester"],
    "last_login": "2024-01-15T10:30:00Z",
    "metadata": None
}

# Validation observed:
assert isinstance(user["id"], int)
assert isinstance(user["name"], str) and len(user["name"]) > 0
assert "@" in user["email"]
assert isinstance(user["preferences"]["theme"], str)
assert isinstance(user["preferences"]["notifications"], bool)
assert isinstance(user["tags"], list) and all(isinstance(t, str) for t in user["tags"])
```

TASK: Generate TypeScript interfaces for this schema. Include:
1. User interface
2. Preferences sub-interface
3. Proper optional/nullable handling for metadata
4. A validateUser() function with runtime type checks
```

**Pass criteria:** Correct TypeScript types, nullable metadata, validate function covers all observed constraints.

---

## TASK 11 — Prompt-to-Code (Agentic)

```
SYSTEM: You are a coding agent. Execute the task step-by-step.

TASK: Create a Python CLI tool that:
1. Reads a directory of .log files
2. Counts occurrences of each log level (INFO, WARN, ERROR, DEBUG) per file
3. Outputs a summary table (file | INFO | WARN | ERROR | DEBUG)
4. Supports --min-errors N flag to only show files with ≥N errors
5. Uses only stdlib (no pip install)

OUTPUT: Complete, runnable Python script with argparse. No placeholders.
```

**Pass criteria:** Complete runnable script, argparse with --min-errors, correct counting logic, table output, stdlib only.

---

## TASK 12 — Debugging with Evidence

```
SYSTEM: Debug using the provided evidence. Output the root cause and fix.

EVIDENCE:
- Symptom: API returns 500 intermittently under load
- Logs: "ConnectionResetError: [Errno 104] Connection reset by peer"
- Timing: Happens after ~500 concurrent requests
- Config: pool_size=10, max_overflow=20, pool_timeout=30
- Database: PostgreSQL 15
- Framework: SQLAlchemy 2.0 + asyncpg

TASK:
1. What is the root cause?
2. Why does it happen at ~500 concurrent requests specifically?
3. Provide the exact config fix (SQLAlchemy engine creation code)
4. Provide the monitoring query to verify the fix
```

**Pass criteria:** Identifies connection pool exhaustion, explains math (10+20=30 < 500), correct engine recreation code, valid monitoring query.

---

## TASK 13 — Architecture Decision

```
SYSTEM: Make an architecture decision. Output a structured ADR.

CONTEXT:
- Building a real-time notification system
- 10M users, 100K concurrent
- Notifications: email, push, in-app, SMS
- Latency requirement: <500ms for in-app
- Budget: must run on existing AWS infrastructure
- Team: 3 backend engineers, 1 DevOps

CURRENT: Monolithic Django app with Celery workers

TASK: Write an Architecture Decision Record (ADR) comparing:
1. Keep monolith + add Redis Pub/Sub
2. Migrate to microservices + Kafka
3. Hybrid: monolith + dedicated notification service

Include: context, decision, rationale, consequences, and a final recommendation.
```

**Pass criteria:** Structured ADR format, realistic trade-offs, considers team size and budget, justified recommendation.

---

## TASK 14 — Security Audit

```
SYSTEM: Audit the code for security vulnerabilities. Output as a structured list.

CODE:
```python
from flask import Flask, request, jsonify
import sqlite3
import os
import subprocess

app = Flask(__name__)

@app.route("/search")
def search():
    q = request.args.get("q", "")
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{q}%'")
    results = cursor.fetchall()
    return jsonify(results)

@app.route("/export")
def export():
    fmt = request.args.get("format", "csv")
    cmd = f"python3 scripts/export.py --format {fmt}"
    output = subprocess.check_output(cmd, shell=True)
    return output

@app.route("/config")
def config():
    return jsonify({
        "db_password": os.environ.get("DB_PASS", "admin123"),
        "secret_key": app.secret_key
    })
```

TASK: List every security vulnerability with:
1. CWE ID (if applicable)
2. Severity (Critical/High/Medium/Low)
3. Exact line(s) affected
4. Remediation with code fix
```

**Pass criteria:** Identifies SQL injection (CWE-89), command injection (CWE-78), information disclosure (CWE-200), hardcoded credentials (CWE-798), correct fixes.

---

## Running the Multitest

```bash
# For each model, run all 14 tasks and record:
# - Pass/Fail per task
# - Wall-clock time per task
# - Token count (output)
# - Memory usage during run

# Suggested harness setup (LM Studio):
# - Thinking ON for tasks 2, 4, 5, 9, 13 (planning/reasoning)
# - Thinking OFF for tasks 1, 3, 6, 8, 11, 14 (execution/code gen)
# - T0.6 P0.95 K20 default sampling
# - max_tokens 4096 per task
# - timeout 120s per task

# Scoring:
# - Total pass count (0-14)
# - Median wall-clock time
# - Tokens per correct task
# - Memory peak
# 
# Compare across: Qwen3.8-27B Q5_K_M, Q4_K_S, Nemotron Lightning, 
# KAT-Coder, Nex-N2.5-mini, MiniCPM5-2B, Phi-4-mini, Nemotron Nano 9B V2,
# LFM2.5-8B-A1B, Qwen3.5 9B
```
