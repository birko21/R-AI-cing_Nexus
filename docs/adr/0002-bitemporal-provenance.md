# ADR-0002: Bitemporal, receipt-backed provenance

- **Status:** Accepted for G0–G3
- **Date:** 10 October 2026
- **Scope:** All source facts, features, forecasts and results

## Context

Historical racing research is invalid if later-known fields, results, corrections or market information leak into an earlier forecast. A business-effective timestamp alone cannot prove when this application knew a fact.

## Decision

Every imported fact is associated with an immutable source receipt containing source identity, payload checksum, data mode, first observation time, publication time when available, effective time, rights state and parser/schema version. Canonical revisions are append-only. As-of queries require verifiable availability by cutoff; missing publication/receipt proof is excluded or marked unavailable.

Forecasts and selections reference exact field revisions and frozen feature/model manifests. Corrections append new revisions and never mutate archived decisions.

## Consequences

- Replay and leakage tests are first-class acceptance evidence.
- Synthetic fixtures must declare simulated times and cannot be treated as real event history.
- Storage and query code is more deliberate, but historical claims become auditable.

