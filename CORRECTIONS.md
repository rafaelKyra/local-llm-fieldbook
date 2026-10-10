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
7. **"One definition of a write" was overstated** (2026-10-07, found by a second review and reproduced). From v7 on the text said the read-only tool policy and the evidence gate share one definition of a write. They share a core (writer commands, `touch`, the scratch rule); the policy also refuses a `touch` inside a command substitution, a delete after a harmless pipe and an interpreter write, which the gate does not count. Two further defects of the v11 line were reproduced and corrected afterwards (a code-execution tool was classed as a mutation although it only inspects; a request to *explain* a fix switched read-only off). The text of v11 now says so; the v7 wording is left as published and corrected here.
8. **A batch was scored against a ground truth that had moved** (2026-10-07). A confirmation batch came out all PARTIAL because the project had gained a test: 75 instead of 74. The scorers looked for the literal 74 (v1) or four fixed class counts (v2); the reports were correct. The batch was not published as a result of the arm; it is kept as `v12-invalid-ground-truth-75-tests`. Scorer 3 reads the expected counts from the project at the start of each run and is applied only to runs that carry it. The earlier columns are unchanged.
9. **The per-version table recomputed a verdict that cannot see `finished`** (2026-10-10, found while adding head-to-head data). The published records
   leave out `finished`; `analyze.verdict` therefore scored a run that never finished, but whose report carried all four facts, as a PASS or PARTIAL,
   while the harness had scored it FAIL. In the published table one cell was affected: v12, holo4, run 2 showed `~` and should show `x`. No pass count
   changed. The scripts now use the verdict stored in the record whenever there is one (`run_verdict`), and the new comparisons were computed that way.
