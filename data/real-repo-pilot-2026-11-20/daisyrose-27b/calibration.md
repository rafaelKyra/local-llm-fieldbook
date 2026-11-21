# DaisyRose-27B Q4_K_M calibration 2026-11-20T10:25:06+0200 (llama.cpp runtime 2.76.0 started directly, context 75008, parallel 1, flash attention on, all layers requested on GPU)

The first attempt through LM Studio (runtime 2.74.0) failed to load the file at all ('tensor blk.0.ssm_beta.weight not found'); the earlier line 'no configuration fits' was wrong: it was a load error, not a memory result.

| KV | layers on GPU | VRAM loaded MiB | free after ~20k prompt MiB | gen tok/s | prefill tok/s | note |
|---|---|---|---|---|---|---|
| f16 | all (-ngl 99; offload count not logged) | 22108 | 2455 | 29.5 | 924.3 |  |
| q8_0 | all (-ngl 99; offload count not logged) | 20161 | 4314 | 29.3 | 914.6 |  |
| q4_0 | all (-ngl 99; offload count not logged) | 19067 | 5465 | 29.2 | 912.4 |  |

chosen KV type: f16
