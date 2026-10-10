# ADR-0001: Modular local monolith for the offline MVP

- **Status:** Accepted for G0–G3
- **Date:** 10 October 2026
- **Scope:** Offline synthetic MVP

## Context

The MVP needs a browser UI, typed API, local relational persistence and deterministic forecast code, but it has no approved cloud, provider or production deployment dependency. Distributed services would add operational and security cost before the domain contracts are proven.

## Decision

Use a modular monolith with explicit boundaries:

`React/Vite browser (localhost) ↔ FastAPI (loopback) ↔ PostgreSQL (local)`

Keep domain, provenance, feature, model, evaluation and API contracts separated in code even when they run in one application. A background queue is not required for G0–G3; deterministic commands and database transactions are preferred.

## Consequences

- Local development and replay remain simple and reproducible.
- Shared process boundaries must not become hidden coupling; contracts and tests remain explicit.
- Deployment, worker scaling and cloud services are deferred until a later gate demonstrates need.

## Rejected alternatives

- Microservices: premature operational complexity.
- Hosted database: not approved for the offline MVP.
- Unbounded notebook-only implementation: cannot provide the required API, auth or UX evidence.

