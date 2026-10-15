# LIVE-017 authenticated hosted E2E checklist

This checklist is the operator-run acceptance record for the first real live
hosted journey. It uses the deployed staging site and does not capture tokens,
credentials, provider payloads, or screenshots containing sensitive data.

## Preconditions

- Render frontend is live from the staging branch and the API reports
  `LICENSED`, `postgres`, `punters-edge`, and `wagering_enabled=false`.
- The owner completes Auth0 sign-in in the browser. Credentials are entered by
  the owner only.
- The public API still returns `401` for `GET /v1/meetings` without a bearer
  token.

## Acceptance steps

1. Open `https://nexus-staging-frontend.onrender.com/` and choose **Sign in
   with Auth0**.
2. Confirm the page shows **Signed in as** the allowlisted owner identity.
3. Confirm the licensed dashboard shows **LICENSED INGESTION MONITOR** and a
   bounded `HEALTHY`, `STALE`, `FAILED`, or `NO DATA` status.
4. Confirm at least one meeting card shows **LIVE READ-ONLY** and **Open live
   meeting**.
5. Open the meeting and confirm **LIVE RESEARCH VIEW · READ-ONLY**, a
   `LICENSED` race panel, and a **Canonical entries** table.
6. Confirm the live view says provider payloads and forecasts are not
   displayed, and does not show synthetic meeting, race, forecast, market, or
   wagering values.
7. Sign out, reload, and confirm the public page returns to **Nexus owner
   sign-in required**.

## Evidence to record

Record only timestamps, URLs, HTTP status codes, bounded labels, aggregate
counts, deployment IDs, workflow run IDs, and commit IDs. Never record the
Auth0 token, password, email address, raw provider response, or full browser
storage state.

| Check | Result | Evidence |
|---|---|---|
| Auth0 owner session | PASS | Hosted browser owner session authenticated |
| Licensed status monitor | PASS | `HEALTHY`; 3 meetings, 3 races, 31 entries, 4 results |
| Live meeting list | PASS | Three licensed meeting cards; Northam opened |
| Race and entry detail | PASS | Race 8; 12 canonical entries; 9 active, 3 scratched |
| Synthetic fallback absent | PASS | Licensed view showed only canonical provider data and explicit no-payload state |
| Wagering disabled | PASS | UI showed `DISABLED`; safe API field was `false` |
| Logout returns to owner gate | PASS | Browser returned to `Nexus owner sign-in required`; unauthenticated meetings returned `401` |
