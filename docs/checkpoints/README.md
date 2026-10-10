# Gate checkpoints

Every gate checkpoint has a machine-readable JSON record and a human-readable Markdown report. Checkpoints record observed evidence; they are not plans or predictions.

## Required fields

- Gate and title.
- `PASS`, `CONDITIONAL_PASS`, `BLOCKED` or `FAIL` status.
- Completed scope and actual commands with exit codes.
- Security findings and data-rights status.
- Data mode and model status.
- Evidence paths/URLs, costs, risks, owner decisions and next unblocked work.

Validate a checkpoint locally with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_checkpoint.ps1 -Path docs/checkpoints/examples/GATE_G0_BLOCKED.json
```

The first real G0 checkpoint should be created only after all G0 evidence is observed. The example in `examples/` intentionally demonstrates a blocked state and must not be copied as a passing result.

