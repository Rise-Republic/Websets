import pytest
from unittest.mock import MagicMock

from app.storage.object_storage import (
    LocalObjectStorage,
    S3ObjectStorage,
    GCSObjectStorage,
    ObjectStorageFactory,
    ObjectStorageProvider,
    get_object_storage,
)


class DummyLoop:
    async def run_in_executor(self, executor, func, *args, **kwargs):
        return func(*args, **kwargs)


@pytest.fixture
def immediate_loop(monkeypatch):
    loop = DummyLoop()
    monkeypatch.setattr("app.storage.object_storage.asyncio.get_event_loop", lambda: loop)
    return loop


@pytest.fixture
def mock_storage_settings(mocker, tmp_path):
    settings = mocker.patch("app.storage.object_storage.settings", autospec=True)
    settings.data_dir = str(tmp_path)
    settings.s3_bucket_name = "bucket"
    settings.aws_region = "us-east-1"
    settings.aws_access_key_id = "id"
    settings.aws_secret_access_key = "secret"
    settings.gcs_bucket_name = "gcs-bucket"
    settings.gcs_credentials_path = None
    settings.object_storage_provider = "local"
    return settings


@pytest.fixture(autouse=True)
def reset_singleton():
    from app.storage import object_storage

    object_storage._storage_instance = None
    yield
    object_storage._storage_instance = None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_local_storage_operations(mock_storage_settings, tmp_path):
    storage = LocalObjectStorage()
    key = "file.txt"
    data = b"hello"
    url = await storage.upload_bytes(data, key)
    assert url.endswith(key)
    download_path = tmp_path / "dl.txt"
    success = await storage.download_file(key, str(download_path))
    assert success is True
    assert download_path.read_bytes() == data
    files = await storage.list_files()
    assert any(f["key"] == key for f in files)
    deleted = await storage.delete_file(key)
    assert deleted is True
    assert not (tmp_path / key).exists()
    assert await storage.download_file("missing", str(download_path)) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_local_upload_file_error(mock_storage_settings, mocker, tmp_path):
    storage = LocalObjectStorage()
    src = tmp_path / "src.txt"
    src.write_text("data")
    mocker.patch("shutil.copy2", side_effect=Exception("err"))
    with pytest.raises(Exception):
        await storage.upload_file(str(src), "dest.txt")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s3_storage_success(monkeypatch, mocker, mock_storage_settings, immediate_loop):
    client = MagicMock()
    mocker.patch("boto3.client", return_value=client)
    storage = S3ObjectStorage()

    await storage.upload_file("path", "key", content_type="text/plain")
    client.upload_file.assert_called_with("path", "bucket", "key", {"ContentType": "text/plain"})

    await storage.upload_bytes(b"d", "key2")
    client.put_object.assert_called_with("bucket", "key2", b"d")

    client.generate_presigned_url.return_value = "url"
    url = await storage.get_file_url("key")
    assert url == "url"

    await storage.download_file("key", "dest")
    client.download_file.assert_called_with("bucket", "key", "dest")

    await storage.delete_file("key")
    client.delete_object.assert_called_with("bucket", "key")

    client.list_objects_v2.return_value = {"Contents": [{"Key": "k", "Size": 1, "LastModified": __import__('datetime').datetime(2020,1,1), "ETag": "e"}]}
    files = await storage.list_files()
    assert files[0]["key"] == "k"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s3_storage_errors(monkeypatch, mocker, mock_storage_settings, immediate_loop):
    client = MagicMock()
    mocker.patch("boto3.client", return_value=client)
    storage = S3ObjectStorage()
    client.upload_file.side_effect = Exception("boom")
    with pytest.raises(Exception):
        await storage.upload_file("p", "k")
    client.download_file.side_effect = Exception("fail")
    assert await storage.download_file("k", "dest") is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gcs_storage_success(monkeypatch, mocker, mock_storage_settings, immediate_loop):
    blob = MagicMock()
    bucket = MagicMock()
    bucket.blob.return_value = blob
    client = MagicMock()
    client.bucket.return_value = bucket
    mocker.patch("google.cloud.storage.Client", return_value=client)
    storage = GCSObjectStorage()

    await storage.upload_file("p", "key", content_type="text/plain")
    blob.upload_from_filename.assert_called_with("p")
    assert blob.content_type == "text/plain"

    await storage.upload_bytes(b"d", "k2")
    blob.upload_from_string.assert_called_with(b"d", None)

    blob.generate_signed_url.return_value = "signed"
    assert await storage.get_file_url("k") == "signed"

    await storage.download_file("k", "dest")
    blob.download_to_filename.assert_called_with("dest")

    await storage.delete_file("k")
    blob.delete.assert_called()

    bucket.list_blobs.return_value = [MagicMock(name="n", size=1, time_created=None, etag="e")]
    files = await storage.list_files()
    assert files[0]["etag"] == "e"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gcs_storage_errors(monkeypatch, mocker, mock_storage_settings, immediate_loop):
    blob = MagicMock()
    bucket = MagicMock()
    bucket.blob.return_value = blob
    client = MagicMock()
    client.bucket.return_value = bucket
    mocker.patch("google.cloud.storage.Client", return_value=client)
    storage = GCSObjectStorage()
    blob.upload_from_filename.side_effect = Exception("boom")
    with pytest.raises(Exception):
        await storage.upload_file("p", "k")
    blob.download_to_filename.side_effect = Exception("fail")
    assert await storage.download_file("k", "dest") is False


@pytest.mark.unit
def test_object_storage_factory(mocker, mock_storage_settings):
    mocker.patch("boto3.client", return_value=MagicMock())
    mocker.patch("google.cloud.storage.Client", return_value=MagicMock())
    assert isinstance(ObjectStorageFactory.create_storage(ObjectStorageProvider.LOCAL), LocalObjectStorage)
    assert isinstance(ObjectStorageFactory.create_storage(ObjectStorageProvider.S3), S3ObjectStorage)
    assert isinstance(ObjectStorageFactory.create_storage(ObjectStorageProvider.GCS), GCSObjectStorage)


@pytest.mark.unit
def test_get_object_storage_singleton(mocker, mock_storage_settings):
    mock_storage_settings.object_storage_provider = "local"
    inst1 = get_object_storage()
    inst2 = get_object_storage()
    assert inst1 is inst2
    assert isinstance(inst1, LocalObjectStorage)

