from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    error: ErrorDetail | None = None

    model_config = ConfigDict(from_attributes=True)


def success_response(data: T, *, meta: dict[str, Any] | None = None) -> ResponseEnvelope[T]:
    return ResponseEnvelope(data=data, meta=meta or {}, error=None)
