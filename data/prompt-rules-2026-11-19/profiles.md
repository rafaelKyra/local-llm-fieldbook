# Behavioural profile of every model with kit rows (kits P3b + P3c, control arm = the model as it is, p3f arm = with the closing-line sentence)

Same definition for all models (see the script header). Statistics are Fisher exact two-sided without correction; hosts, quantisations and sample sizes differ, so the table describes, it does not rank.

## Table 1: what the model does by itself (control arm)

| model | host | runs (control / p3f) | work right (hidden check) | verifies itself (status completed) | right but delivered unverified | mean model calls | mean output tokens | writes the closing line unprompted |
|---|---|---|---|---|---|---|---|---|
| Mistral-Small-3.2 24B (BF16) | Berget | 32 / 32 | 29/32 (91 %) | 7/32 (22 %) | 23/25 | 19.7 | 1075 | 1/32 (3 %) |
| Gemma-4-31B-it (BF16) | Berget | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 9.9 | 533 | 0/32 (0 %) |
| GLM-5.3-Flash (FP8) | Berget | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 9.1 | 3205 | 17/32 (53 %) |
| GLM-5.3-Flash | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 8.9 | 2323 | 17/32 (53 %) |
| deepseek-v4.1-flash | OpenRouter | 32 / 32 | 32/32 (100 %) | 31/32 (97 %) | 1/1 | 15.1 | 5766 | 18/32 (56 %) |
| Qwen3.8-Flash | OpenRouter | 32 / 32 | 32/32 (100 %) | 31/32 (97 %) | 1/1 | 15.8 | 7372 | 24/32 (75 %) |
| Qwen3.8-27B | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 7.8 | 2612 | 16/32 (50 %) |
| Qwen3.7-Flash | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 7.4 | 958 | 0/32 (0 %) |
| Qwen3-Coder-Next | OpenRouter | 32 / 32 | 29/32 (91 %) | 23/32 (72 %) | 6/9 | 20.4 | 1383 | 1/32 (3 %) |
| gpt-oss-120b | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 7.8 | 947 | 0/32 (0 %) |
| GLM-4.7-Flash | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 7.9 | 1170 | 0/32 (0 %) |
| Claude Haiku 5.5 | OpenRouter | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 6.4 | 1820 | 30/32 (94 %) |
| Nemotron-3-Ultra 550B | OpenRouter free | 32 / 32 | 32/32 (100 %) | 32/32 (100 %) | 0/0 | 8.4 | 908 | 1/32 (3 %) |
| Mercury 3 | Inception | 64 / 64 | 64/64 (100 %) | 64/64 (100 %) | 0/0 | 7.5 | 1204 | 23/64 (36 %) |
| Strata (Qwen3.8-Flash-Next IQ3_S) | local | 40 / 40 | 40/40 (100 %) | 40/40 (100 %) | 0/0 | 12.3 | 3655 | 27/40 (68 %) |
| Qwen3.8-27B distil (local) | local | 10 / 10 | 10/10 (100 %) | 10/10 (100 %) | 0/0 | 6.1 | 1058 | 0/10 (0 %) |
| OxCoder 9B Q4_K_S | local | 40 / 40 | 40/40 (100 %) | 34/40 (85 %) | 6/6 | 10.6 | 1494 | 0/40 (0 %) |

## Table 2: what the rule changes (p3f against control)

| model | closing line control -> p3f | p | work right control -> p3f | verifies itself control -> p3f | output tokens p3f / control (95 % CI) | reading |
|---|---|---|---|---|---|---|
| Mistral-Small-3.2 24B (BF16) | 1/32 -> 22/32 | 0.0000 | 29/32 -> 28/32 | 7/32 -> 9/32 | 1.11 (0.77-1.59) | rule works |
| Gemma-4-31B-it (BF16) | 0/32 -> 0/32 | 1.0000 | 32/32 -> 32/32 | 32/32 -> 32/32 | 0.99 (0.84-1.20) | never writes it (nothing to change) |
| GLM-5.3-Flash (FP8) | 17/32 -> 24/32 | 0.1172 | 32/32 -> 32/32 | 32/32 -> 32/32 | 0.87 (0.67-1.13) | no clear effect |
| GLM-5.3-Flash | 17/32 -> 25/32 | 0.0643 | 32/32 -> 32/32 | 32/32 -> 32/32 | 0.86 (0.58-1.27) | no clear effect |
| deepseek-v4.1-flash | 18/32 -> 30/32 | 0.0010 | 32/32 -> 32/32 | 31/32 -> 32/32 | 0.88 (0.64-1.21) | rule works |
| Qwen3.8-Flash | 24/32 -> 31/32 | 0.0265 | 32/32 -> 32/32 | 31/32 -> 31/32 | 1.02 (0.69-1.46) | rule works (weaker) |
| Qwen3.8-27B | 16/32 -> 17/32 | 1.0000 | 32/32 -> 32/32 | 32/32 -> 32/32 | 1.18 (0.83-1.62) | no clear effect |
| Qwen3.7-Flash | 0/32 -> 2/32 | 0.4921 | 32/32 -> 32/32 | 32/32 -> 32/32 | 1.02 (0.96-1.10) | never writes it (nothing to change) |
| Qwen3-Coder-Next | 1/32 -> 2/32 | 1.0000 | 29/32 -> 30/32 | 23/32 -> 29/32 | 1.07 (0.78-1.47) | never writes it (nothing to change) |
| gpt-oss-120b | 0/32 -> 2/32 | 0.4921 | 32/32 -> 32/32 | 32/32 -> 32/32 | 0.97 (0.87-1.07) | never writes it (nothing to change) |
| GLM-4.7-Flash | 0/32 -> 2/32 | 0.4921 | 32/32 -> 32/32 | 32/32 -> 31/32 | 1.16 (0.94-1.47) | never writes it (nothing to change) |
| Claude Haiku 5.5 | 30/32 -> 32/32 | 0.4921 | 32/32 -> 32/32 | 32/32 -> 32/32 | 0.96 (0.90-1.03) | writes the line anyway (ceiling) |
| Nemotron-3-Ultra 550B | 1/32 -> 0/32 | 1.0000 | 32/32 -> 32/32 | 32/32 -> 32/32 | 1.02 (0.99-1.05) | never writes it (nothing to change) |
| Mercury 3 | 23/64 -> 27/64 | 0.5870 | 64/64 -> 64/64 | 64/64 -> 64/64 | 0.99 (0.86-1.16) | no clear effect |
| Strata (Qwen3.8-Flash-Next IQ3_S) | 27/40 -> 40/40 | 0.0001 | 40/40 -> 40/40 | 40/40 -> 40/40 | 0.84 (0.65-1.09) | rule works |
| Qwen3.8-27B distil (local) | 0/10 -> 10/10 | 0.0000 | 10/10 -> 10/10 | 10/10 -> 10/10 | 1.20 (1.16-1.24) | rule works |
| OxCoder 9B Q4_K_S | 0/40 -> 0/40 | 1.0000 | 40/40 -> 40/40 | 34/40 -> 40/40 | 0.77 (0.62-0.96) | never writes it (nothing to change) |

## Profile types (control arm: verifies itself? writes the line unprompted?)

- **mostly does not verify / silent:** Mistral-Small-3.2 24B (BF16)
- **verifies / silent:** Gemma-4-31B-it (BF16); Qwen3.7-Flash; Qwen3-Coder-Next; gpt-oss-120b; GLM-4.7-Flash; Nemotron-3-Ultra 550B; Qwen3.8-27B distil (local); OxCoder 9B Q4_K_S
- **verifies / speaks sometimes:** GLM-5.3-Flash (FP8); GLM-5.3-Flash; deepseek-v4.1-flash; Qwen3.8-27B; Mercury 3; Strata (Qwen3.8-Flash-Next IQ3_S)
- **verifies / speaks unprompted:** Qwen3.8-Flash; Claude Haiku 5.5

## Exploratory notes (not planned beforehand)

- Across 16 models (GLM-5.3-Flash counted once), Spearman correlation between mean output tokens per run and the share of runs that write the closing line unprompted: **0.78**; with mean model calls per run: 0.22. Models that write more per run tend to report what they skipped on their own. Output-token counts may not include hidden reasoning for every host, so this is a description of the kits, not a law.
- Verification habit with the rule: Qwen3-Coder-Next: 23/32 -> 29/32 (p = 0.107); one of many comparisons, not a finding.
- Verification habit with the rule: OxCoder 9B Q4_K_S: 34/40 -> 40/40 (p = 0.026); one of many comparisons, not a finding.
