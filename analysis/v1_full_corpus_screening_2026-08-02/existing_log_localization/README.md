# Existing-Log Candidate Localization

## What was done

No model calls were made. This audit reuses the saved title/abstract text, five-run outputs, and evidence spans from the 2026-08-02 Terra run. Raw provider responses remain unchanged.

## Deterministic routing correction

The protocol requires five identical first-failed criterion paths for an automatic exclusion. The historic runner additionally required agreement on unrelated fields, retaining records whose decisive exclusion path was already unanimous. Applying the criterion-path rule changed 330 routes: the technical `seek_full_text` count falls from 1972 to 1642. Metadata-protection routes were preserved.

## Manual triage, not a new eligibility rule

There are 700 original positive-causal routes. The first manual title/abstract queue has 135 records: five-of-five stable fields, an aging-process anchor in the title, and an explicit current-report multi-omics label. The remaining queues are retained for later review and are not excluded: priority 2=169, priority 3=128, priority 4=192, and unstable-positive=76.

`candidate_triage.csv` contains the abstract and exact audit fields for manual title/abstract review. `criterion_path_route_changes.csv` contains the 330 routing corrections. The priority labels organize workload only; they neither validate accuracy nor justify automatic exclusion.
