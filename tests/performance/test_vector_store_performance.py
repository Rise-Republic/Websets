import time
import numpy as np
import pytest
import chromadb
from app.storage.chroma_vector_store import ChromaVectorStore


@pytest.mark.slow
def test_add_vector_performance(tmp_path, monkeypatch):
    monkeypatch.setattr(chromadb, "Client", lambda settings: chromadb.PersistentClient(path=str(tmp_path)))
    store = ChromaVectorStore(persist_directory=str(tmp_path))
    vectors = np.random.random((100, 8)).astype(float)
    metadata = [{"i": i} for i in range(100)]

    start = time.time()
    ids = store.add_vectors(vectors, metadata)
    duration = time.time() - start

    assert len(ids) == 100
    assert duration < 5
