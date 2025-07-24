from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class VectorStoreSettings(BaseSettings):
    """Settings for vector storage providers."""

    provider: str = Field("chromadb", validation_alias="VECTOR_STORE_PROVIDER")
    path: str = Field("./data/vector_store", validation_alias="VECTOR_STORE_PATH")

    # Pinecone
    pinecone_api_key: Optional[str] = Field(None, validation_alias="PINECONE_API_KEY")
    pinecone_environment: str = Field("us-east1-gcp", validation_alias="PINECONE_ENVIRONMENT")

    # Weaviate
    weaviate_url: str = Field("http://localhost:8080", validation_alias="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(None, validation_alias="WEAVIATE_API_KEY")

    # Qdrant
    qdrant_url: Optional[str] = Field(None, validation_alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, validation_alias="QDRANT_API_KEY")
