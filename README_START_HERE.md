# Racing Intelligence Lab

Racing Intelligence Lab is an independent, single-user, local-first research application for Australian thoroughbred, harness and greyhound racing.

## Current repository state

- **Active delivery scope:** offline MVP gates G0–G3.
- **Data mode:** synthetic-only for the active MVP; fictional fixtures must remain visibly labelled.
- **Model status:** illustrative B0/B1 baselines only; no validated predictive claim.
- **Wagering:** permanently out of scope; no bookmaker credentials, order endpoints or automatic staking.
- **Current checkpoint:** RIL-029 probability/evidence separation, support, missingness, disagreement and OOD abstention diagnostics are implemented.
- **Next ticket:** RIL-030, after the RIL-029 evidence is accepted.

## Normative reading order

1. `docs/product/MASTER_SPEC_V1_1.md` — binding v1.1 product, technical and safety requirements.
2. `docs/product/CODEX_EXECUTION_PROMPT_V1_1.md` — bounded execution and evidence instructions.
3. The v1.1 supporting artifacts listed in `docs/product/SOURCE_MANIFEST.md` as they are created.
4. `docs/backlog/EPICS.md` and `docs/backlog/TICKETS.md` — implementation decomposition.

When documents conflict, the v1.1 master specification controls the active MVP; later-vision material is backlog context only. Any material interpretation change requires a recorded ADR or decision-register entry.

## Expected local architecture

The active MVP is a modular local application:

`React/Vite browser (localhost) ↔ FastAPI (loopback, scoped auth) ↔ PostgreSQL (local)`

G0–G3 does not require cloud deployment, OIDC, licensed feeds, live odds, external LLMs, or external connectivity. Controlled public scraping is a later, separately labelled capability and cannot silently change the active synthetic-only evidence status.

## Evidence rule

A gate is complete only when the code runs, the relevant tests actually execute, and the checkpoint records observed commands, exit codes, artifacts, data mode, rights status, model status, costs and unresolved risks. Documentation alone is not implementation evidence.

## Backlog

- [Epic register](docs/backlog/EPICS.md)
- [Ticket register](docs/backlog/TICKETS.md)
- [Source manifest and missing baseline artifacts](docs/product/SOURCE_MANIFEST.md)
- [Local development and validation](docs/LOCAL_DEVELOPMENT.md)
