Date: 2026-09-30 (run), written 2026-10-02
Model(s) and build: one 27B model, same weights for all three runtimes. Quantisation not recorded in the run summary.
Setup (runtime, quant, context, settings): same model served locally, context 32,768, three agent runtimes tried one after another (own loop, "pi", "claude" client), one attempt each, no repeats.
The work: consolidate about twenty scattered test and debugging scripts in a project root into one test suite without changing assertions, record a baseline first, report pre-existing failures instead of fixing them. The gate (the external check) fails before the work, so it can detect whether the work was done.
What happened:
- Own loop: finished in 504 s, outcome "failed verification".
- "pi": finished in 8,402 s (about 2 h 20 min), outcome "failed verification". It found real baseline failures (a SHA-256 test set, a SQL test with the wrong number of bind values) and correctly left them failing.
- "claude" client: errored after 183 s.
What I did not check: repeats, why verification failed in each case, quantisation, whether the 17x time difference is the runtime or the run. One task, one run each: this is an observation, not a ranking of runtimes.
