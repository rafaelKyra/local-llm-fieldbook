Date: 2026-11-18
Model(s) and build: the 28 entries of an outside collection (Luke's Dev Lab, <https://lukesdevlab.com/>), listed below with his own labels.
Setup (runtime, quant, context, settings): not ours. His runs, his hardware, his harness. Fetched on 2026-11-18 from the public result files the site loads (`lukesdevlab.s3.us-east-1.amazonaws.com/models/*.json`).
The work: read his published numbers to help choose which models to test next; nothing here was re-run by us.
What happened: his data has three kinds of figure per model: decode speed (tokens/s), HumanEval (164 questions, correct), and a short list of agent tests (small build tasks such as a kanban board, sand physics, a dungeon crawler, a 3D lantern, a Godot platformer) marked pass or fail. The method differs from every ruler in this repository (single run per model, one-shot builds, his hardware), so the two are not merged and this note is not a measurement of ours. It is a reference for selection.

| Model (his label) | Quant | MTP | Type | Decode tok/s | HumanEval | Agent tests passed |
|---|---|---|---|---|---|---|
| unsloth/Qwen3.8-27B-GGUF | Q4_K_XL | True | Dense | 3.9 | 139/164 | 5/5 |
| ornith-ai/Ornith-1.5-35B-A3B-GGUF | Q4_K_M | True | MoE | 36.3 | 117/164 | 3/5 |
| ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF | IQ3_S | True | Dense | 4.6 | 142/164 | 5/5 |
| peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP | Q4_K_XL | True | MoE | 39.8 | 130/164 | 4/5 |
| peculiar-ragdoll/Nail-Qwen3.6-35B-A3B-GGUF-MTP | Q4_K_XL | True | MoE | 48.4 | 155/164 | 4/5 |
| unsloth/Qwen3.8-Flash-Next-GGUF | Q4_K_XL | – | MoE | 88.5 | – | 6/6 |
| Qwen/Qwen3.8-Max | – | – | MoE | 260.8 | 138/164 | 5/5 |
| moonshotai/Kimi-K3 | – | True | MoE | 43.1 | – | 6/6 |
| DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF | Q4_K_M | True | Dense | 7.2 | 101/164 | 4/5 |
| prism-ml/Ternary-Bonsai-2-27B-Q2_0-gguf | Q2_0 | – | Dense | 25.3 | – | 5/5 |
| prism-ml/Ternary-Bonsai-2-27B-TQ1_0-gguf | TQ1_0 | – | Dense | 24.2 | – | 3/5 |
| ukisai/Swift-Qwen3.8-27B-GGUF | Q4_K_M | True | Dense | 8.7 | – | 5/5 |
| unsloth/Qwen3.8-27B-GGUF | Q4_K_M | True | Dense | 9.7 | – | 5/5 |
| NANI-Nithin/K2-Horizon-MoVA-36B-A4B-GGUF | Q5_K_M | – | moVA | 14 | – | 3/5 |
| Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF | IQ_3_S | True | Dense | 30 | – | 5/5 |
| aj9o9/Qwen3.8-27B-Escha-W2-GGUF | Q8_0 | False | Dense | 11.4 | – | 5/5 |
| abenzerps/Nex-N2.5-mini-GGUF | Q4_K_M | True | MoE | 55.5 | 143/164 | 2/5 |
| bottlecapai/ThinkingCap-Qwen3.8-27B-GGUF | Q4_K_M | True | Dense | 9.4 | – | 5/5 |
| strata/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF | – | – | – | 42.8 | – | 5/5 |
| ConwayResearch/Underdog-Saluki-27B-1.0 | IQ2 | False | Dense | 18.4 | – | 3/5 |
| DavidAU/Qwen3.8-27B-Turbo-Brilliance-50X-Reasoning-Instruct-NEO-MAX-MTP-GGUF | Q4_K_M | True | Dense | 10.9 | – | 5/5 |
| unsloth/flint-GGUF | Q4_K_XL | False | MoE | 39.8 | – | 4/5 |
| LiquidAI/LFM2.5-24B-A2B-GGUF | Q4_K_M | False | MoE | 107.3 | – | 0/5 |
| InternScience/Sage-A1.5-Q4_K_M-GGUF | Q4_K_M | – | MoE | 39.8 | – | 3/5 |
| KRAFTON/Raon-1-mini-preview-gguf | Q4_K_M | – | – | 31.0 | – | 3/5 |
| byteshape/Qwen3.8-27B-GGUF | IQ3_XS | True | Dense | 31.0 | – | 4/5 |
| agentionai/Qwen3.8-Flash-Next-Gyro-GGUF | – | – | – | 57.3 | – | 7/7 |
| agentionai/Qwen3.8-Flash-Next-Gyro-M-GGUF | TQ2_0 | – | – | 57.8 | – | 6/6 |

Read with care:
- Decode speeds are on his rig. The slowest dense entries (3.9 to 11 tok/s) show a machine that is not ours; do not compare them with this repository's speeds. Compare models within his table only.
- "–" means the file has no value for that field, not zero.
- One pair worth cross-reading with this repository: `ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF` (IQ3_S) has 142/164 on HumanEval and 5/5 agent tests against 139/164 and 5/5 for `unsloth/Qwen3.8-27B-GGUF` at Q4_K_XL, i.e. no visible loss at the lower bit-width. In this repository's 14-task grid the same family (`qwen3.8-27b-gsq-rco`) scored 3 of 14. The two do not agree and the reason is not established: that grid has four incomplete answers (cut off at the token cap) and seven failures, one run each, a different task set, and the build may differ. Until it is re-run with repeats, neither figure is used to rank it.
- `unsloth/Qwen3.8-Flash-Next-GGUF` at Q4_K_XL passes 6/6 of his agent tests at 88.5 tok/s, and his Strata-labelled `Flash-Next-GSQ-RCO-Coder` passes 5/5; this repository's own use of a Flash-Next IQ3_S build is in [the prompt-rule screening](../data/prompt-rules-2026-11-18/README.md).

What I did not check: whether his agent tests are comparable between entries (the number of tests differs from 5 to 7), whether the labels on his site match the exact files, and his scoring rules.
