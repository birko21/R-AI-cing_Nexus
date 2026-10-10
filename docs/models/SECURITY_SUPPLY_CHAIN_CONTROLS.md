# Secrets, dependencies and supply-chain controls

RIL-057 adds a deterministic tracked-source audit for high-confidence private-key, cloud-token, GitHub-token, live-key and password-assignment patterns. It also checks frontend source for provider-secret environment references. Findings contain only path and rule metadata; secret values are never printed.

The repository retains both the pnpm and Python lockfiles. A lockfile-derived CycloneDX-style SBOM is checked in at `docs/evidence/ril-057/sbom.json`. Provider keys remain server-side; log redaction uses the shared egress redactor and removes bearer tokens and PII before transmission. This local evidence does not replace a hosted dependency vulnerability service or owner-approved production secret manager.
