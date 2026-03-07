import re

from pydantic import BaseModel, Field, field_validator

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_SAFE_FILE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


def _normalize_file_name(value: str) -> str:
    normalized = value.strip().split("/")[-1].split("\\")[-1]
    normalized = _SAFE_FILE_NAME_PATTERN.sub("_", normalized)
    if not normalized or normalized in {".", ".."}:
        raise ValueError("file_name is required")
    return normalized


class UploadPresignRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)

    @field_validator("file_name", mode="before")
    @classmethod
    def normalize_file_name(cls, value: str) -> str:
        return _normalize_file_name(value)

    @field_validator("content_type", mode="before")
    @classmethod
    def normalize_content_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_CONTENT_TYPES:
            raise ValueError("Unsupported content_type")
        return normalized


class UploadPresignRead(BaseModel):
    upload_url: str
    file_storage_key: str


class UploadStoreRead(BaseModel):
    stored: bool
    file_storage_key: str
