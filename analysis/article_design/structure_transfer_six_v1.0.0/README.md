# Biological-table structure transfer check v1.0.0

This transfer check repeats the procedure used for the first six-report
biological findings table on a disjoint subset of six reports. The reports were
selected from the unused portion of the frozen independent-inventory sample to
cover intervention, perturbation, prediction, Mendelian randomization,
mediation, animal aging, plant senescence, fruit senescence, and disease-proxy
boundaries.

For each report, an existing independent GPT-5.6 Terra Medium inventory and a
new independent Claude Opus 4.8 inventory were reconciled against the frozen
canonical sections and evidence-atom index. Opus received the exact frozen
prompt used in the historical attempt; that attempt had produced no scientific
output because of an external session-limit error. All six new Opus calls were
valid on their first attempt. Model inventories served as orientation drafts.
The table uses source-checked evidence rather than selecting a preferred model.

The five-question Results architecture transferred to all six reports. The
three provisional biological themes from the first subset did not transfer
unchanged: the second subset adds plant and postharvest senescence, formal
mediation, prediction-only boundaries, and a molecular-omics eligibility
boundary. The reader-facing five-question structure remains accepted; its
subthemes must be learned from the complete corpus.

Terra and Opus agreed for all six reports on source sufficiency, presence or
absence of a qualifying causal analysis, the set of design families, and the
set of causal-basis classes. They agreed on the exact number of analysis units
for two of six reports. This supports the broad structure while confirming that
analysis-unit enumeration remains unsuitable as an unadjudicated count.

Two reports require eligibility re-adjudication before synthesis:

- `10.21037/tcr-2026-1-0264`: both reviewers found prediction and association
  only, with no qualifying causal design.
- `10.1186/s13040-025-00432-1`: the directed mediation analysis combines
  genomics with accelerometry and neuroimaging; the latter are not molecular
  omics layers under the frozen review boundary.

These are transfer-check findings. This package does not silently modify the
eligibility ledger, PRISMA counts, or causal evidence levels.
