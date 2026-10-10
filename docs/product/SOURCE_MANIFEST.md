# Source manifest and baseline artifact status

**Repository:** `birko21/R-AI-cing_Nexus`  
**Imported:** 10 October 2026, UTC  
**Purpose:** record the exact source documents used to establish the repository baseline and identify referenced artifacts that are not yet present.

## Imported source documents

| Repository path | Supplied source | Source date | SHA-256 | Status |
|---|---|---|---|---|
| `docs/product/MASTER_SPEC_V1_1.md` | `1-MASTER_SPEC_V1_1.md` attachment | Effective 10 October 2026 | `F011DB74F4D1A7A04F7A98E2F30B6E556613D341ABE208FAE9CA93C3220CD325` | Imported verbatim |
| `docs/product/CODEX_EXECUTION_PROMPT_V1_1.md` | `2-CODEX_EXECUTION_PROMPT_V1_1.md` attachment | No standalone date stated | `FBBCF93F843B6DE91395B1BFA0159E3CFAC3318267F26C8A65B271B059A08614` | Imported verbatim |

The source attachments were supplied from the Codex workspace attachment directory. Hashes are recorded to detect accidental changes; the repository copies are the tracked project references.

## Referenced but missing at baseline

These files are named by the v1.1 documents but were not supplied or present in the repository when RIL-001 ran:

- `docs/OFFLINE_MVP_SCOPE.md`
- `docs/STATISTICAL_CONTRACT.md`
- `docs/STATUS_AND_GATES.md`
- `docs/DECISION_REGISTER.md`
- `contracts/openapi_mvp.yaml`
- `migrations/001_offline_mvp.sql`
- `MASTER_SPEC_V1_0_REFERENCE.md`
- `DATA_PROVIDER_DUE_DILIGENCE.md`

Their absence is an explicit G0 baseline condition. RIL-002 and later foundation tickets must create the active MVP artifacts before claiming contract compatibility or migration validation. The missing V1.0 reference and provider due-diligence document remain context/deferred artifacts until their contents are supplied or recreated with recorded provenance.

## Interpretation note

The execution prompt permits controlled public-web scraping under safeguards, while the v1.1 master specification defines G0–G3 as offline with no external connectivity. The master specification controls the active MVP: scraping is therefore deferred from G0–G3 and must be introduced only as a separately labelled, rights-aware later capability.

## Status

- Repository baseline: **IMPORTED**
- Runtime implementation: **NOT_STARTED**
- Data rights: **NO PROVIDER APPROVED**
- Model evidence: **NO VALIDATION CLAIM**
- Next action: implement RIL-002 decision register and traceability.

