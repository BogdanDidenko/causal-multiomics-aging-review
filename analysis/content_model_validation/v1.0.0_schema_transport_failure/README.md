# CMACM v1.0.0 schema transport failure

This run was interrupted after strict Codex transport rejected the dynamic
`axis_values` object in the response schema. The rejection occurred before any
model read a report or produced a scientific response. All 15 input reports,
their complete Markdown, the original schema, and failure logs remain preserved
for audit.

CMACM v1.0.1 replaces this dynamic JSON object with explicit axis/value-set
records. The scientific Foundation, sample membership, and validation plan are
unchanged. The v1.0.1 run is the first scientific execution of the model.
