from typing import List, Dict, Any, Optional
import numpy as np
# from app.storage.chroma_vector_store import ChromaVectorStore  # Temporarily disabled due to dependency issue

class VectorStore:
    """ChromaDB-based vector storage for semantic search capabilities."""
    def __init__(self, dimension: int = 1536, persist_directory: str = "./data/chroma_store", collection_name: str = "default"):
        self.dimension = dimension
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chroma_store = ChromaVectorStore(persist_directory=persist_directory, collection_name=collection_name)

    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        return self.chroma_store.add_vectors(vectors, metadata)

    def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        return self.chroma_store.search(query_vector, k, threshold)

    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        return self.chroma_store.get_by_id(vector_id)

    def delete_by_id(self, vector_id: str) -> bool:
        return self.chroma_store.delete_by_id(vector_id)

    def get_statistics(self) -> Dict[str, Any]:
        return self.chroma_store.get_statistics()

    def clear(self):
        self.chroma_store.clear()
