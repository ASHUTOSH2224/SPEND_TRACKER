import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
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
    def store_object(self, *, file_storage_key: str, content: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_object_bytes(self, *, file_storage_key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete_object(self, *, file_storage_key: str) -> bool:
        raise NotImplementedError


class LocalFileUploadStorage(UploadStorage):
    def __init__(self, *, root: Path, api_v1_prefix: str) -> None:
        self._root = root
        self._api_v1_prefix = api_v1_prefix.rstrip("/")

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
            upload_url=(
                f"{self._api_v1_prefix}/uploads/content"
                f"?file_storage_key={quote(file_storage_key, safe='')}"
            ),
            file_storage_key=file_storage_key,
        )

    def is_owned_key(self, *, user_id: UUID, file_storage_key: str) -> bool:
        return file_storage_key.startswith(f"statements/{user_id}/")

    def store_object(self, *, file_storage_key: str, content: bytes) -> None:
        file_path = self._resolve_path(file_storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    def get_object_bytes(self, *, file_storage_key: str) -> bytes:
        file_path = self._resolve_path(file_storage_key)
        if not file_path.exists():
            raise FileNotFoundError("Stored statement file not found")
        return file_path.read_bytes()

    def delete_object(self, *, file_storage_key: str) -> bool:
        file_path = self._resolve_path(file_storage_key)
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def _resolve_path(self, file_storage_key: str) -> Path:
        candidate = (self._root / file_storage_key).resolve()
        root = self._root.resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("Unsupported file_storage_key path")
        return candidate


def _sanitize_file_name(file_name: str) -> str:
    normalized = file_name.strip().split("/")[-1].split("\\")[-1]
    normalized = _STORAGE_SAFE_NAME_PATTERN.sub("_", normalized)
    return normalized or "statement"


def build_upload_storage(settings: Settings) -> UploadStorage:
    if settings.storage_backend == "local_fake":
        return LocalFileUploadStorage(
            root=settings.storage_local_root,
            api_v1_prefix=settings.api_v1_prefix,
        )
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
