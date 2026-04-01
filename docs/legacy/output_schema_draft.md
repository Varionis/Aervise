# Legacy Output Draft

This document is a legacy draft and is no longer the canonical output contract.

It predates the current split between:

- deterministic structured output
- rendered user-facing messaging

Use these documents instead:

1. [09_decision_output_schema.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/docs/09_decision_output_schema.md#L1)
2. [05_interaction_flow_contract.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/docs/05_interaction_flow_contract.md#L1)

Current implemented reality:

- `/decision/evaluate` returns the structured deterministic `DecisionOutput`
- `/decision/render` returns stable rendered messaging from structured output
- `/decision/evaluate-rendered` returns both together
