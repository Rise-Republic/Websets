from typing import Optional
from pydantic_settings import BaseSettings


class VectorStoreSettings(BaseSettings):
    """Settings for vector storage providers."""

    provider: str = "chromadb"  # chromadb, pinecone, weaviate, qdrant
    path: str = "./data/vector_store"
    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east1-gcp"
    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    # Qdrant
    qdrant_url: Optional[str] = None  # e.g., "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

