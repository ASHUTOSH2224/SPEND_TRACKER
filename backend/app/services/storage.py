import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.core.config import Settings

_STORAGE_SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class UploadTarget:
    upload_url: str
    file_storage_key: str


class UploadStorage(ABC):
    @abstractmethod
    def create_upload_target(
        self,
        *,
        user_id: UUID,
        file_name: str,
        content_type: str,
    ) -> UploadTarget:
        raise NotImplementedError

    @abstractmethod
    def is_owned_key(self, *, user_id: UUID, file_storage_key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_object(self, *, file_storage_key: str) -> bool:
        raise NotImplementedError


class LocalFakeUploadStorage(UploadStorage):
    def create_upload_target(
        self,
        *,
        user_id: UUID,
        file_name: str,
        content_type: str,
    ) -> UploadTarget:
        del content_type

        normalized_file_name = _sanitize_file_name(file_name)
        file_storage_key = f"statements/{user_id}/{uuid.uuid4()}-{normalized_file_name}"
        return UploadTarget(
            upload_url=f"local-fake://{file_storage_key}",
            file_storage_key=file_storage_key,
        )

    def is_owned_key(self, *, user_id: UUID, file_storage_key: str) -> bool:
        return file_storage_key.startswith(f"statements/{user_id}/")

    def delete_object(self, *, file_storage_key: str) -> bool:
        del file_storage_key
        return False


def _sanitize_file_name(file_name: str) -> str:
    normalized = file_name.strip().split("/")[-1].split("\\")[-1]
    normalized = _STORAGE_SAFE_NAME_PATTERN.sub("_", normalized)
    return normalized or "statement"


def build_upload_storage(settings: Settings) -> UploadStorage:
    if settings.storage_backend == "local_fake":
        return LocalFakeUploadStorage()
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
