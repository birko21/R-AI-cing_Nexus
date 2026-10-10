# First real source approval gate

RIL-034 remains `BLOCKED_EXTERNAL_DEPENDENCY` until the project has recorded all of the following for a named provider:

- written rights to access and use the source;
- a credential policy reference, without storing credentials in the repository;
- retention terms;
- model-training permission or an explicit prohibition;
- display permission; and
- a reconciliation report covering representative meetings, runners, and results.

`SourceApprovalRecord` stores references to evidence, not secrets. `evaluate_source_approval` returns an explicit checkpoint. An incomplete record cannot become an active adapter, and `UnavailableSourceStub` returns `NOT_AVAILABLE` without making a network request.

The checked-in checkpoint is deliberately blocked. This is not a failed integration and is not evidence that any source is approved, licensed, official, current, or connected. Once the owner supplies recorded evidence, a future change can populate the references and add a source-specific adapter and reconciliation evidence.
