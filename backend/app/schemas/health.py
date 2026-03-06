from typing import Literal

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
    environment: str
    version: str
