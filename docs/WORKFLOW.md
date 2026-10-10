# Repository workflow

## Branches

- `main` is the protected release branch.
- Feature branches use `codex/<ticket-id>-<short-name>`.
- One ticket should be the primary purpose of a branch and commit series.
- Do not rewrite shared history or use destructive reset/checkout operations on `main`.

## Commits

Use concise conventional subjects:

```text
feat: implement RIL-021 uniform baseline
fix: reject future-known feature in RIL-027
docs: record RIL-002 decision register
test: cover RIL-025 scratching invalidation
```

Include the ticket ID in the commit body or subject. Keep generated artifacts and evidence linked to the ticket.

## Ticket states

- **Open:** planned or ready to work.
- **In progress:** active implementation branch exists.
- **Blocked:** an external approval, missing source, environment dependency or unresolved owner decision prevents progress; record the exact blocker.
- **Review:** implementation and observed tests are complete and evidence is attached.
- **Closed:** acceptance criteria are met, evidence is recorded and the change is merged/pushed.

Do not close a ticket because documentation describes future work. A `BLOCKED` gate is not a `PASS`.

## Review and merge rules

- Run the relevant local validation and test commands before review.
- Review source rights, authentication, temporal integrity, probability invariants and no-wagering impact for every material change.
- Keep commits small enough to audit and include migration/rollback notes where applicable.
- Merge to `main` only after acceptance evidence is present. Protected-branch settings remain an owner/repository-admin responsibility.

## External blockers

Use `blocked-external` when work depends on provider terms, credentials, paid services, OIDC, cloud deployment, external LLM transfer or another owner approval. Continue safe independent work; never invent access or silently accept terms.

