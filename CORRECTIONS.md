# Corrections

What was retracted or changed, when, and why. Newest first.

## 2026-10-01 — before first publication

Found while turning the hand-written report into this repository. Each item is checked
against the saved answers in `data/grid-2026-09-20/`.

1. **Task 1 was read as "obeying a declared tool contract". It does not measure that.**
   The runner cuts the task at "Pass criteria", so the model never sees the required
   search → read → write sequence. Re-checked: of 14 failing answers, 13 never emit
   `write_file` and 7 contain `sed`; the most common failing answer is a single
   `grep | xargs sed -i` command that does what the request says. The earlier statements that
   models "violate an explicit instruction" and "route around a tool contract", and the
   conclusion that "only three models respect a declared tool contract", are withdrawn.
   Task 1 needs rewriting, ideally as an executable check against a fixture repository.
2. **Truncated answers were counted as passes.** Four points depended on answers cut off by
   the token cap. Scoring now has three states: pass, fail, incomplete.
3. **A "KING" tier was built on an unmeasured figure.** One model was ranked first on a
   "14/14, owner-confirmed" figure. On the reproducible grid it scores 12/14 (11/14 strict),
   one point *below* its smaller quantisation (13/14, 12/14 strict). On the 18 September runs
   the two were level (13, 13, 13 each), but those answers were lost and cannot be re-checked.
   The same model carried three different scores on one page (14/14, 13/14, 12/14) from
   three different rulers. There is no king; the grid cannot separate these builds.
   Production impressions remain as field notes, labelled as such.
4. **Measured and asserted figures shared a column.** Owner-confirmed numbers appeared next
   to measured pass rates in one score column. They are now kept in separate places.
5. **Machine-specific paths and a storage description were removed** from the published text.
6. **The arm-version table counted passes by a looser rule than the analysis script** (2026-10-07). The page counted an abandoned plan as a pass and counted every recorded report field, so the v10 row read 7 passes while the analysis and the text said 6. The page now uses the analysis script's rule (the four original facts, an abandoned plan fails) and the row reads 6; the other rows are unchanged.
