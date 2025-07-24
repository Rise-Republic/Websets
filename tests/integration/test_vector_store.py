import numpy as np
import pytest
import chromadb
from app.storage.chroma_vector_store import ChromaVectorStore


@pytest.mark.integration
def test_add_search_vector(tmp_path, monkeypatch):
    monkeypatch.setattr(chromadb, "Client", lambda settings: chromadb.PersistentClient(path=str(tmp_path)))
    store = ChromaVectorStore(persist_directory=str(tmp_path))
    vectors = np.random.random((5, 4)).astype(float)
    metadata = [{"index": i} for i in range(5)]
    ids = store.add_vectors(vectors, metadata)
    assert len(ids) == 5

    def patched_search(self, query_vector, k=10, threshold=0.5):
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=k,
            include=["metadatas", "distances"],
        )
        output = []
        for i, distance in enumerate(results["distances"][0]):
            if distance <= threshold:
                meta = results["metadatas"][0][i]
                output.append({"vector_id": results["ids"][0][i], "distance": distance, **meta})
        return output

    monkeypatch.setattr(ChromaVectorStore, "search", patched_search)

    results = store.search(vectors[0], k=3, threshold=2)
    assert any(r["vector_id"] == ids[0] for r in results)


def test_get_and_delete_vector(tmp_path, monkeypatch):
    monkeypatch.setattr(chromadb, "Client", lambda settings: chromadb.PersistentClient(path=str(tmp_path)))
    store = ChromaVectorStore(persist_directory=str(tmp_path))
    vector = np.random.random((1, 4))
    metadata = [{"id": 1}]
    ids = store.add_vectors(vector, metadata)
    meta = store.get_by_id(ids[0])
    assert meta == metadata[0]

    deleted = store.delete_by_id(ids[0])
    assert deleted is True
    assert store.get_by_id(ids[0]) is None
