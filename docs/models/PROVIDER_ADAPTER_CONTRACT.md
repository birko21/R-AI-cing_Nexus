# Provider capability and adapter contract

RIL-032 defines the boundary between a source-specific adapter and the Racing Intelligence Lab domain. An adapter must describe what it can provide before it can be registered, and every returned record must use the common immutable `RawEnvelope`.

## Capability matrix

Each provider declaration reports:

- supported racing codes and fields;
- supported timestamp fields, including the required retrieval and first-observed timestamps;
- explicit `data_mode` and `rights_state`;
- pagination support, style, and maximum page size;
- request, daily, and concurrency quotas, or an explicit unknown state;
- supported operations and a disjoint list of unsupported operations;
- whether the provider is enabled.

The matrix is deterministic and reviewable. The checked-in matrix is a synthetic fixture only; it does not represent a live provider, entitlement, licence, or external connection.

## Adapter contract

`ContractedProviderAdapter` rejects unsupported codes and operations before calling an implementation. It also rejects invalid page sizes, cursors returned without declared pagination, pages exceeding the declared limit, disabled providers, and records whose data mode or rights state differs from the provider declaration.

The adapter protocol returns `AdapterPage`, whose records are typed `RawEnvelope` instances. This keeps source-specific retrieval separate from canonical ingestion and preserves payload checksums, timestamps, rights, data mode, and retrieval metadata. Provider-specific parsers must not return loosely typed domain records directly.

No operation in this contract places wagers, accesses bookmaker credentials, bypasses access controls, or enables outbound retrieval by itself. A future real provider remains subject to the capability guard, approved rights, retention policy, and the controlled scraping boundary.
