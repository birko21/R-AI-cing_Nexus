# Chronological walk-forward splits

`walk-forward-v1` uses half-open UTC windows `[start, end)` and partitions race IDs into training, calibration and final-test sets without overlap. Expanding mode keeps the initial training start fixed as the cutoff advances. Rolling mode uses a fixed training duration and advances the window by the configured step.

Race IDs must be unique and timestamps must be timezone-aware. Every fold records its boundaries and race IDs; no row is silently reused between partitions. The current six-race fixture spans one fictional demo date, so its committed manifest records the honest limitation that no pre-demo training races are fabricated. The implementation and synthetic manifest are ready for later multi-date replay data.

