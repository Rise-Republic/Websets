import time
import pytest
from app.storage.object_storage import LocalObjectStorage


@pytest.mark.slow
@pytest.mark.asyncio
async def test_bulk_upload_performance(tmp_path):
    storage = LocalObjectStorage(base_path=str(tmp_path))
    data = b"x" * 1024
    start = time.time()
    for i in range(50):
        await storage.upload_bytes(data, f"file_{i}.bin")
    duration = time.time() - start
    files = await storage.list_files()
    assert len(files) == 50
    assert duration < 5
