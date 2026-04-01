# Legacy Decision Engine Draft

This document is retained only as a historical design reference.

It is not the current source of truth for the implemented backend.

Use these documents instead:

1. [04_interaction_flow_contract.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/docs/04_interaction_flow_contract.md#L1)
2. [04_c_decision_input_schema.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/docs/04_c_decision_input_schema.md#L1)
3. [04_d_decision_output_schema.md](/d:/Users/arnav/Documents/Github_Repos/Aervise/docs/04_d_decision_output_schema.md#L1)

Current implemented reality:

- The deterministic core starts from the Stage 3 canonical `DecisionInput`.
- The core currently covers factor evaluation, policy mapping, and explanation output.
- Same-day timing guidance is weather-only.
- Future-day planning remains conservative because AQ forecast is not implemented.

If this file is expanded again later, it should be rewritten from the current implementation rather than treated as an active spec.
