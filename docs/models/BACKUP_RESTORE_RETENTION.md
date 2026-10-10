# Backup, restore, retention and migration runbook

RIL-059 backs up only explicit permitted files, records SHA-256 and size in a manifest, restores only to a caller-provided isolated destination, and verifies hashes after restore. Retention planning returns expired `RESTRICTED`/`REJECTED` IDs but performs no deletion; an owner-approved operational action must execute any deletion.

Migration rollback is a documented sequence: record the current revision, migrate in an isolated database, run checksum/fixture checks, downgrade one revision, verify the previous revision and require owner review before promotion. The checked-in transcript is synthetic evidence and does not touch a production database.
