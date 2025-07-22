import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_store", collection_name: str = "default"):
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection(collection_name)

    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        ids = [f"vec_{i}_{hash(str(meta))}" for i, meta in enumerate(metadata)]
        self.collection.add(
            embeddings=vectors.tolist(),
            metadatas=metadata,
            ids=ids
        )
        logger.info(f"Added {len(vectors)} vectors to ChromaDB")
        return ids

    def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=k,
            include=['metadatas', 'distances', 'ids']
        )
        output = []
        for i, distance in enumerate(results['distances'][0]):
            if distance <= threshold:
                meta = results['metadatas'][0][i]
                output.append({
                    **meta,
                    "vector_id": results['ids'][0][i],
                    "distance": distance
                })
        return output

    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        results = self.collection.get(ids=[vector_id], include=['metadatas'])
        if results['metadatas'] and results['metadatas'][0]:
            return results['metadatas'][0]
        return None

    def delete_by_id(self, vector_id: str) -> bool:
        self.collection.delete(ids=[vector_id])
        logger.info(f"Deleted vector {vector_id} from ChromaDB")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        count = self.collection.count()
        return {
            "total_vectors": count,
            "provider": "chromadb"
        }

    def clear(self):
        self.collection.delete()
        logger.info("Cleared ChromaDB collection")
