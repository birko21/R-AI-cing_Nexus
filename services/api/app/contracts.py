from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class SystemStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: Literal["racing-intelligence-lab"]
    environment: str
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
    external_connectivity: Literal[False]
    model_status: Literal["NOT_TRAINED", "ILLUSTRATIVE_ONLY", "MODEL_VALIDATED"]
    wagering_enabled: Literal[False]
