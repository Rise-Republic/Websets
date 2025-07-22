from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json
from loguru import logger
from enum import Enum

from app.config import settings


class VectorStoreProvider(str, Enum):
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    CHROMA = "chromadb"


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""
    
    @abstractmethod
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors with metadata to the store."""
        pass
    
    @abstractmethod
    async def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    async def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata by vector ID."""
        pass
    
    @abstractmethod
    async def delete_by_id(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        pass


class PineconeVectorStore(BaseVectorStore):
    """Pinecone vector store implementation."""
    
    def __init__(self, index_name: str = "websets-vectors", dimension: int = 1536):
        self.index_name = index_name
        self.dimension = dimension
        self.index = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone client and index."""
        try:
            import pinecone
            
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            self.index = pinecone.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to Pinecone index."""
        try:
            # Generate IDs
            ids = [f"vec_{i}_{hash(str(meta))}" for i, meta in enumerate(metadata)]
            
            # Prepare vectors for upsert
            vectors_list = []
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                vectors_list.append({
                    "id": ids[i],
                    "values": vector.tolist(),
                    "metadata": meta
                })
            
            # Upsert vectors
            self.index.upsert(vectors=vectors_list)
            logger.info(f"Added {len(vectors)} vectors to Pinecone")
            
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors to Pinecone: {e}")
            raise
    
    async def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search Pinecone index."""
        try:
            response = self.index.query(
                vector=query_vector.tolist(),
                top_k=k,
                include_metadata=True
            )
            
            results = []
            for match in response["matches"]:
                if match["score"] >= threshold:
                    result = {
                        **match["metadata"],
                        "vector_id": match["id"],
                        "similarity_score": match["score"]
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            raise
    
    async def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector metadata by ID from Pinecone."""
        try:
            response = self.index.fetch(ids=[vector_id])
            if vector_id in response["vectors"]:
                return response["vectors"][vector_id]["metadata"]
            return None
        except Exception as e:
            logger.error(f"Failed to get vector by ID from Pinecone: {e}")
            return None
    
    async def delete_by_id(self, vector_id: str) -> bool:
        """Delete vector by ID from Pinecone."""
        try:
            self.index.delete(ids=[vector_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector from Pinecone: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats["total_vector_count"],
                "dimension": stats["dimension"],
                "index_fullness": stats.get("index_fullness", 0),
                "provider": "pinecone"
            }
        except Exception as e:
            logger.error(f"Failed to get Pinecone statistics: {e}")
            return {"provider": "pinecone", "error": str(e)}


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store implementation."""
    
    def __init__(self, collection_name: str = "websets_vectors", dimension: int = 1536):
        self.collection_name = collection_name
        self.dimension = dimension
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            # Connect to Qdrant
            if hasattr(settings, 'qdrant_url') and settings.qdrant_url:
                self.client = QdrantClient(url=settings.qdrant_url)
            else:
                # Local instance
                self.client = QdrantClient(host="localhost", port=6333)
            
            # Create collection if it doesn't exist
            try:
                self.client.get_collection(self.collection_name)
            except Exception:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            
            logger.info(f"Connected to Qdrant collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to Qdrant collection."""
        try:
            from qdrant_client.http import models
            import uuid
            
            # Generate IDs
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            
            # Prepare points
            points = []
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                points.append(models.PointStruct(
                    id=ids[i],
                    vector=vector.tolist(),
                    payload=meta
                ))
            
            # Upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(vectors)} vectors to Qdrant")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors to Qdrant: {e}")
            raise
    
    async def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search Qdrant collection."""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=k,
                score_threshold=threshold
            )
            
            formatted_results = []
            for result in results:
                formatted_result = {
                    **result.payload,
                    "vector_id": result.id,
                    "similarity_score": result.score
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            raise
    
    async def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector metadata by ID from Qdrant."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id]
            )
            if result:
                return result[0].payload
            return None
        except Exception as e:
            logger.error(f"Failed to get vector by ID from Qdrant: {e}")
            return None
    
    async def delete_by_id(self, vector_id: str) -> bool:
        """Delete vector by ID from Qdrant."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[vector_id])
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector from Qdrant: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Qdrant collection statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_vectors": info.points_count,
                "dimension": info.config.params.vectors.size,
                "provider": "qdrant"
            }
        except Exception as e:
            logger.error(f"Failed to get Qdrant statistics: {e}")
            return {"provider": "qdrant", "error": str(e)}


class WeaviateVectorStore(BaseVectorStore):
    """Weaviate vector store implementation."""
    
    def __init__(self, class_name: str = "WebsetsVector", dimension: int = 1536):
        self.class_name = class_name
        self.dimension = dimension
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Weaviate client."""
        try:
            import weaviate
            
            # Connect to Weaviate
            self.client = weaviate.Client(
                url=settings.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(settings.weaviate_api_key) if hasattr(settings, 'weaviate_api_key') else None
            )
            
            # Create schema if it doesn't exist
            if not self.client.schema.exists(self.class_name):
                schema = {
                    "class": self.class_name,
                    "vectorizer": "none",  # We'll provide vectors manually
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"]
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"]
                        }
                    ]
                }
                self.client.schema.create_class(schema)
                logger.info(f"Created Weaviate class: {self.class_name}")
            
            logger.info(f"Connected to Weaviate class: {self.class_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            raise
    
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to Weaviate."""
        try:
            ids = []
            
            # Add vectors one by one (can be batched for better performance)
            for vector, meta in zip(vectors, metadata):
                result = self.client.data_object.create(
                    data_object={
                        "content": meta.get("content", ""),
                        "metadata": meta
                    },
                    class_name=self.class_name,
                    vector=vector.tolist()
                )
                ids.append(result)
            
            logger.info(f"Added {len(vectors)} vectors to Weaviate")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors to Weaviate: {e}")
            raise
    
    async def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search Weaviate."""
        try:
            result = (
                self.client.query
                .get(self.class_name, ["content", "metadata"])
                .with_near_vector({"vector": query_vector.tolist()})
                .with_limit(k)
                .with_additional(["certainty", "id"])
                .do()
            )
            
            results = []
            for item in result["data"]["Get"][self.class_name]:
                certainty = item["_additional"]["certainty"]
                if certainty >= threshold:
                    formatted_result = {
                        **item["metadata"],
                        "vector_id": item["_additional"]["id"],
                        "similarity_score": certainty,
                        "content": item["content"]
                    }
                    results.append(formatted_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search Weaviate: {e}")
            raise
    
    async def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector metadata by ID from Weaviate."""
        try:
            result = self.client.data_object.get_by_id(vector_id, class_name=self.class_name)
            if result:
                return result["properties"]["metadata"]
            return None
        except Exception as e:
            logger.error(f"Failed to get vector by ID from Weaviate: {e}")
            return None
    
    async def delete_by_id(self, vector_id: str) -> bool:
        """Delete vector by ID from Weaviate."""
        try:
            self.client.data_object.delete(vector_id, class_name=self.class_name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector from Weaviate: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Weaviate statistics."""
        try:
            result = (
                self.client.query
                .aggregate(self.class_name)
                .with_meta_count()
                .do()
            )
            
            count = result["data"]["Aggregate"][self.class_name][0]["meta"]["count"]
            return {
                "total_vectors": count,
                "dimension": self.dimension,
                "provider": "weaviate"
            }
        except Exception as e:
            logger.error(f"Failed to get Weaviate statistics: {e}")
            return {"provider": "weaviate", "error": str(e)}


class VectorStoreFactory:
    """Factory for creating vector store instances."""
    
    @staticmethod
    def create_vector_store(provider: VectorStoreProvider, **kwargs) -> BaseVectorStore:
        """Create a vector store instance based on provider."""
        if provider == VectorStoreProvider.PINECONE:
            return PineconeVectorStore(**kwargs)
        elif provider == VectorStoreProvider.QDRANT:
            return QdrantVectorStore(**kwargs)
        elif provider == VectorStoreProvider.WEAVIATE:
            return WeaviateVectorStore(**kwargs)
        elif provider == VectorStoreProvider.CHROMA:
            from .chroma_vector_store import ChromaVectorStore
            return ChromaVectorStore(**kwargs)
        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")


# Singleton instance
_vector_store_instance = None

def get_vector_store() -> BaseVectorStore:
    """Get the configured vector store instance."""
    global _vector_store_instance
    
    if _vector_store_instance is None:
        provider = VectorStoreProvider(getattr(settings, 'vector_store_provider', 'chromadb'))
        _vector_store_instance = VectorStoreFactory.create_vector_store(provider)
    
    return _vector_store_instance