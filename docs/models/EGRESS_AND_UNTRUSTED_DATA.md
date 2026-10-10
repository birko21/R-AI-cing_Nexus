# Untrusted data, redaction and egress controls

RIL-048 treats ingested text as data, never as instructions. The injection assessment records matched markers such as instruction overrides, role spoofing, secret requests and unauthorized tool-call requests; it does not execute or promote the text.

Before an external transmission decision, the redactor removes bearer tokens, secret assignments, AWS access keys, email addresses and Australian mobile numbers. The audit stores a checksum and categories, not the original payload. Egress is denied for `UNASSESSED`, `RESTRICTED` and `REJECTED` rights states, and for `LICENSED` data unless an explicit transmission permission is present. Synthetic data may pass this policy only after redaction.

Research-tool calls and responses are appended to an in-memory audit log containing user, tool, `as_of`, limit, argument-key metadata, status and row count. Raw arguments, secrets and result rows are excluded. The checked-in fixture is synthetic and offline; no external provider or live source is contacted.
