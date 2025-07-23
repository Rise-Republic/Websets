import os
import pytest

from app.storage.object_storage import LocalObjectStorage


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_download_delete_bytes(tmp_path):
    storage = LocalObjectStorage(base_path=str(tmp_path))
    data = b"hello world"
    key = "test/file.txt"

    url = await storage.upload_bytes(data, key, content_type="text/plain")
    assert os.path.exists(url)

    download_path = tmp_path / "download.txt"
    success = await storage.download_file(key, str(download_path))
    assert success is True
    assert download_path.read_bytes() == data

    files = await storage.list_files()
    assert any(f["key"] == key for f in files)

    deleted = await storage.delete_file(key)
    assert deleted is True
    assert not (tmp_path / key).exists()
