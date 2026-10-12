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
- provider rights gap analysis; and
- model-assurance workflow.

The packet deliberately leaves visual-owner, accessibility, racing-domain,
model-assurance, security-owner, OIDC, and provider-rights gates pending or
blocked external dependencies. It has no activation or promotion authority,
and it records external connectivity and wagering as disabled.

Generate and verify it with:

```text
python scripts/generate_s4_assurance_packet.py
```
