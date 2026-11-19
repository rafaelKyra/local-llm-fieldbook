# Round 5 plan, written 2026-11-19 BEFORE the main series (the 4-run smoke test of repetition 1 was already done and is kept as data)

Question: does the closing-line rule in the `finish` tool description (arm `p3f`) change the closing line on a population of other models, and what does it cost?
Model id: exactly `openrouter/free` (owner's instruction). This is a ROUTER: each request may be answered by a different free model. The smoke test showed at least ten different models answering (1.7B to 550B parameters), sometimes several inside one run. The result therefore describes the router as a mixture, not any single model, and it may change as the free pool changes.
Cost: free models, 0 USD (key spend checked before and after). Free-tier limit 20 requests per minute; 429 answers are retried by the agent core.

Design: kits P3b and P3c; arms control and p3f; 30 repetitions per arm per kit (120 runs); arms interleaved inside each repetition with alternating order so router drift hits both equally; window 64,000; seed = repetition; 40 tool calls max. A logging proxy (`or-proxy.mjs`) records the model that answered each request (never the key or the prompt): `served-models.jsonl`.
Primary comparison (fixed now): closing-line rate of p3f against control, pooled over both kits, Fisher exact two-sided at 0.05, plus each kit on its own. Crashed or aborted runs count as not solved and not behaving; no run is excluded.
Secondary: tasks solved (the rule must not lower it), output tokens per run (ratio of means with bootstrap interval over runs), model calls.
Exploratory, not decisive: stratifying by served model (only models with at least 20 requests per arm).
Reading rule: a pooled behaviour gain with no loss in solved is "consistent with the earlier models"; a null result is reported as null. The 10 % cost rule is applied as written and reported next to the behaviour result.
