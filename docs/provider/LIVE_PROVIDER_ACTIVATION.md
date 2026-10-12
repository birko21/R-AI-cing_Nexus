# Live provider activation

The repository now contains an explicit operator path for owner-configured,
read-only provider access. It does not activate a provider during API startup,
does not expose credentials to the browser, and does not contain order,
staking, wagering or trading operations.

## What is required

Set the selected provider's credentials in the local process environment or a
secret manager. Do not paste them into chat, source files, approval JSON, or
issue comments. The supported variables are:

| Provider | Required credentials |
|---|---|
| PuntersEdge | `NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY` |
| FormFav | `NEXUS_PROVIDER_FORMFAV_API_KEY` |
| Krok Odds | `NEXUS_PROVIDER_KROK_ODDS_API_KEY` |
| Betfair Exchange | `NEXUS_PROVIDER_BETFAIR_APP_KEY` and `NEXUS_PROVIDER_BETFAIR_SESSION_TOKEN` |

Set only the selected `NEXUS_PROVIDER_<PROVIDER>_ENABLED=true` flag. The
provider approval record is separate and contains references, not secrets. It
can be supplied as a local JSON file using the corresponding
`NEXUS_PROVIDER_<PROVIDER>_APPROVAL_FILE` variable. Its fields are:

```json
{
  "approval_tier": "HISTORICAL_RETENTION_AND_MODEL_TRAINING",
  "approved_operations": ["GET_RESULTS", "GET_ENTRIES"],
  "approved_codes": ["THOROUGHBRED"],
  "written_rights": "owner-record:rights-reference",
  "credential_policy": "owner-record:credential-policy-reference",
  "retention_terms": "owner-record:retention-reference",
  "model_training_permission": "owner-record:model-use-reference",
  "display_permission": "owner-record:display-reference",
  "reconciliation_report": "owner-record:identity-reference",
  "account_entitlement_evidence": "owner-record:account-reference",
  "credential_custodian": "owner",
  "quota_ceiling": "bounded requests per run",
  "kill_switch_reference": "owner-record:kill-switch"
}
```

The approval file must not contain `api_key`, `app_key`, `session_token`,
`token`, `secret` or `password` fields. A successful account login alone does
not authorize historical retention, model training or forecast display; the
record must name those rights for this application.

## First connectivity check without retention

For PuntersEdge, the safest first check uses two separate approval files: one
for `ACCOUNT_METADATA_READ` and one for
`EPHEMERAL_READ_ONLY_DIAGNOSTIC`. Set their paths in
`NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_APPROVAL_FILE` and
`NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_APPROVAL_FILE`, then run:

```powershell
$env:NEXUS_DIAGNOSTICS_ENABLED = 'true'
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --diagnostic --provider punters-edge --operation GET_RESULTS --code THOROUGHBRED --date 2026-10-12 --venue Randwick
```

This makes the account/quota request first and then one bounded read. It
returns no runner names, prices, timestamps, raw provider errors or payload.
It is a connectivity/schema check, not yet a recommendation feed.

## First live request

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --status
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --provider punters-edge --operation GET_RESULTS --code THOROUGHBRED --date 2026-10-12 --venue Randwick
```

The first command prints non-secret configuration status only. The second
performs one bounded read-only request and prints a shape/checksum summary;
the provider payload is discarded. Add `--persist` only after the named
approval record allows raw retention, which writes an append-only envelope
under the ignored `data/live/raw/` directory.

For Betfair, capture a catalogue first. A book request must use explicit
market IDs from that catalogue capture:

```powershell
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --provider betfair-exchange --operation GET_MARKETS --view catalogue --date 2026-10-12
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --provider betfair-exchange --operation GET_MARKETS --view book --market-id <catalogue-market-id>
```

The Betfair path uses read-only `listMarketCatalogue` and `listMarketBook`
JSON-RPC calls. `listMarketBook` is deliberately a second step because it
requires market IDs returned by the catalogue. Neither path can place an
order.

Once PostgreSQL is migrated and the catalogue rights record explicitly allows
retention, the catalogue can also be projected into the canonical read model:

```powershell
$env:NEXUS_PROVIDER_BETFAIR_ENABLED = 'true'
.\.venv\Scripts\python.exe scripts\run_live_provider_capture.py --provider betfair-exchange --operation GET_MARKETS --view catalogue --date 2026-10-12 --persist-postgres --project-betfair
```

The projection is intentionally limited to meeting/race/runner identity and
field status. It creates no forecast. Invalid race numbers, missing market
identity, duplicate selections or missing timestamps abort the transaction.

## Current boundary

This first activation milestone proves real connectivity and preserves raw
licensed envelopes. It does not yet claim that provider responses have been
mapped into the canonical meetings/races/entries tables or that live forecasts
are validated. That next step requires provider-specific parsers, identity
reconciliation, chronological evaluation and a real-data model gate. Until
those checks pass, the existing API remains synthetic and forecasts remain
non-production/illustrative.
