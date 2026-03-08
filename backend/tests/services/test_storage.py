from pathlib import Path
from uuid import uuid4

from app.core.config import clear_settings_cache, get_settings
from app.services.storage import build_upload_storage


def test_local_storage_retrieves_and_deletes_uploaded_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "statement-files"))
    clear_settings_cache()

    storage = build_upload_storage(get_settings())
    user_id = uuid4()
    target = storage.create_upload_target(
        user_id=user_id,
        file_name="march_2026.pdf",
        content_type="application/pdf",
    )

    assert storage.is_owned_key(
        user_id=user_id,
        file_storage_key=target.file_storage_key,
    )

    storage.store_object(
        file_storage_key=target.file_storage_key,
        content=b"%PDF-1.7 stored locally",
    )
    assert (
        storage.get_object_bytes(file_storage_key=target.file_storage_key)
        == b"%PDF-1.7 stored locally"
    )
    assert storage.delete_object(file_storage_key=target.file_storage_key) is True
    assert storage.delete_object(file_storage_key=target.file_storage_key) is False

    clear_settings_cache()


def test_relative_storage_root_resolves_from_repo_root(
    monkeypatch,
) -> None:
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", ".local_storage")
    clear_settings_cache()

    settings = get_settings()

    assert settings.storage_local_root.is_absolute()
    assert settings.storage_local_root.name == ".local_storage"
    assert settings.storage_local_root.parent == settings.storage_local_root.parent.parent / "spend_tracker"

    clear_settings_cache()
