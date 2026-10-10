from fastapi import FastAPI

app = FastAPI(
    title="Racing Intelligence Lab API",
    version="0.1.0",
    description="Local-only offline MVP API foundation.",
)


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/system/status", tags=["system"])
def system_status() -> dict[str, str | bool]:
    return {
        "app": "racing-intelligence-lab",
        "environment": "development",
        "data_mode": "SYNTHETIC_ONLY",
        "external_connectivity": False,
        "model_status": "NOT_TRAINED",
        "wagering_enabled": False,
    }
