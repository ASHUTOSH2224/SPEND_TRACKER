import calendar
import re
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

StatementFileType = Literal["pdf", "csv", "xls", "xlsx"]
StatementUploadStatus = Literal["uploaded", "processing", "completed", "failed"]
StatementProcessingStatus = Literal["pending", "running", "completed", "failed"]

_SAFE_STORAGE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
_MONTH_FILTER_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _normalize_required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Value is required")
    return normalized


def _normalize_lower_text(value: str) -> str:
    return _normalize_required_text(value).lower()


class StatementRead(BaseModel):
    id: UUID
    card_id: UUID
    file_name: str
    file_storage_key: str
    file_type: StatementFileType
    statement_period_start: date
    statement_period_end: date
    upload_status: StatementUploadStatus
    extraction_status: StatementProcessingStatus
    categorization_status: StatementProcessingStatus
    transaction_count: int
    processing_error: str | None = None
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatementCreate(BaseModel):
    card_id: UUID
    file_name: Annotated[str, Field(min_length=1, max_length=255)]
    file_storage_key: Annotated[str, Field(min_length=1, max_length=1024)]
    file_password: Annotated[str | None, Field(default=None, max_length=256)] = None
    file_type: StatementFileType
    statement_period_start: date
    statement_period_end: date

    @field_validator("file_name", mode="before")
    @classmethod
    def normalize_file_name(cls, value: str) -> str:
        return _normalize_required_text(value)

    @field_validator("file_storage_key", mode="before")
    @classmethod
    def normalize_file_storage_key(cls, value: str) -> str:
        normalized = _normalize_required_text(value).lstrip("/")
        if not _SAFE_STORAGE_KEY_PATTERN.fullmatch(normalized):
            raise ValueError("file_storage_key contains unsupported characters")
        return normalized

    @field_validator("file_password", mode="before")
    @classmethod
    def normalize_file_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("file_password must be a string")
        return value if value != "" else None

    @field_validator("file_type", mode="before")
    @classmethod
    def normalize_file_type(cls, value: str) -> str:
        return _normalize_lower_text(value)

    @model_validator(mode="after")
    def validate_period(self) -> "StatementCreate":
        if self.file_type == "pdf" and self.file_password is None:
            raise ValueError("file_password is required for pdf statements")
        if self.statement_period_end < self.statement_period_start:
            raise ValueError("statement_period_end must be on or after statement_period_start")
        return self


class StatementListQuery(BaseModel):
    card_id: UUID | None = None
    status: StatementUploadStatus | None = None
    month: str | None = None
    page: Annotated[int, Field(default=1, ge=1)]
    page_size: Annotated[int, Field(default=20, ge=1, le=100)]

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not _MONTH_FILTER_PATTERN.fullmatch(normalized):
            raise ValueError("month must be in YYYY-MM format")

        year, month = normalized.split("-", 1)
        if not 1 <= int(month) <= 12:
            raise ValueError("month must be in YYYY-MM format")
        return normalized

    def month_bounds(self) -> tuple[date, date] | None:
        if self.month is None:
            return None

        year, month = self.month.split("-", 1)
        first_day = date(int(year), int(month), 1)
        last_day = date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])
        return first_day, last_day


class StatementDeleteResult(BaseModel):
    id: UUID
    deleted: bool
    transactions_deleted: int
    storage_object_deleted: bool
    delete_policy: str
