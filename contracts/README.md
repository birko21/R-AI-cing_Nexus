# MVP API contract

`openapi_mvp.yaml` is the versioned G1 contract for the offline MVP. It defines the public shape, authentication scopes, bounded paging metadata, provenance fields and stable error envelope for the health, code, meeting, race, entry, forecast and selection surfaces.

The contract is intentionally broader than the RIL-006 foundation runtime. RIL-007 establishes the schemas and shared client types; RIL-009 implements the typed routes and error handling. Until those routes are implemented, only `/health/live` and `/v1/system/status` are served by the foundation API.

The contract does not grant data rights, imply licensed/current data, enable wagering, or permit external connectivity in G0–G3.
