# RIL-057–060 operational-control evidence

The `contracts-security-and-synthetic-evaluation` CI job now validates the
deterministic operational controls on every pull request:

- `generate_sbom.py` checks the CycloneDX inventory against the pinned Python
  and pnpm lockfiles.
- `generate_operations_fixture.py` checks budget warning/cap thresholds and
  provider kill-switch behavior.
- `generate_backup_fixture.py` checks permitted-file hashing, isolated restore
  planning, migration rollback steps, and non-destructive retention planning.
- `generate_assistant_eval_fixture.py` checks the offline assistant budget
  ceiling and default disabled-provider policy.
- `generate_egress_fixture.py` checks redaction and external-egress denial.

These are synthetic/offline controls. They do not assert production billing,
cloud backup recovery, OIDC configuration, provider rights, or activation.
Those remain explicit release gates.
