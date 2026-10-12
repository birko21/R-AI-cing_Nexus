# S4 assurance packet

The checked-in `s4_assurance_packet_v1.json` is the review handoff for the
next project stage. It verifies that the local synthetic evidence exists and
then records the remaining decisions without inferring them.

Machine evidence currently mapped:

- repository traceability and governance;
- responsive 14-workspace atlas;
- disposable PostgreSQL smoke;
- operational, backup, retention, budget, and egress controls;
- the hashed release gate;
- the synthetic ingestion-to-forecast vertical proof;
- the PostgreSQL worker-to-canonical backend acceptance;
- provider rights gap analysis; and
- model-assurance workflow.

The packet deliberately leaves the visual-owner gate until last. Automated
browser/axe, three-code contract, synthetic forecast/archive, security, and
Render-isolation checks may pass, but accessibility, racing-domain,
model-assurance, security-owner, OIDC, and provider-rights gates remain pending
or blocked external dependencies. It has no activation or promotion authority,
and it records external connectivity and wagering as disabled.

Generate and verify it with:

```text
python scripts/generate_s4_assurance_packet.py
```
