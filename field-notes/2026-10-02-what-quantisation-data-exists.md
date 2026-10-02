Date: 2026-10-02
Model(s) and build: all models in the local lab runs of September 2026.
Setup (runtime, quant, context, settings): quantisation is recorded only as a label on the model file (for example Q8_0, Q8, Q5_K_M), one label per model.
The work: checking whether the lab results can say anything about quantisation.
What happened: they cannot. Each model was run at one quantisation only, so quantisation is mixed up with the model itself. There is no pair "same model, two quantisations, same tasks" in the data. A single-pass exploratory battery of 10 defective repositories (patch valid / resolved, one run each) shows large spread between models (for example 0/10, 4/10, 7/10 and 10/10 resolved), but that spread is explained at least as well by model size and tool-call behaviour as by quantisation.
What I did not check: a controlled test. To get a statistic on quantisation the next step is the same model at 3 quantisations (for example Q4_K_M, Q5_K_M, Q8_0), the same task set, at least 5 repeats each, three-state scoring as in the grid, reporting intervals not a single number.
