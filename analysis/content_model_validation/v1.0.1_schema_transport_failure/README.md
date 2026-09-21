# CMACM v1.0.1 schema transport failure

The first v1.0.1 preflight was rejected by Codex strict-schema transport before
the model read the report. The constrained `model_version` field lacked an
explicit JSON string type. CMACM v1.0.2 added explicit JSON types to constrained
string fields. No scientific model output was produced in this run.
