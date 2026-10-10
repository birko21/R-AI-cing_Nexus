from fastapi import FastAPI

from app.contracts import HealthResponse, SystemStatusResponse

app = FastAPI(
    title="Racing Intelligence Lab API",
    version="0.1.0",
    description="Local-only offline MVP API foundation.",
)


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/system/status", response_model=SystemStatusResponse, tags=["system"])
def system_status() -> SystemStatusResponse:
    return SystemStatusResponse(
        app="racing-intelligence-lab",
        environment="development",
        data_mode="SYNTHETIC_ONLY",
        external_connectivity=False,
        model_status="NOT_TRAINED",
        wagering_enabled=False,
    )
