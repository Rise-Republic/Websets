from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
import asyncio
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class EmbeddingGenerator:
    """Generate embeddings for text content using OpenAI or other providers."""
    
    def __init__(self, model: str = "text-embedding-ada-002", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            if self.provider == "openai":
                self._client = OpenAI(api_key=settings.openai_api_key)
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Truncate text if too long (OpenAI has token limits)
            if len(text) > 8000:  # Conservative limit
                text = text[:8000]
            
            if self.provider == "openai":
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = np.array(response.data[0].embedding)
                return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[np.ndarray]:
        """Generate embeddings for multiple texts in batches."""
        if not texts:
            return []
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._process_batch(batch)
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(1)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    async def _process_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Process a batch of texts."""
        embeddings = []
        
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding for text: {e}")
                # Add zero vector as placeholder
                embeddings.append(np.zeros(1536))  # Default OpenAI embedding dimension
        
        return embeddings
    
    def embed_data_record(self, record: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for a data record by combining its fields."""
        
        # Extract textual content from record
        text_parts = []
        
        for key, value in record.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                # Handle list fields
                list_text = ", ".join(str(item) for item in value if item)
                if list_text:
                    text_parts.append(f"{key}: {list_text}")
        
        # Combine all text
        combined_text = " | ".join(text_parts)
        
        if not combined_text.strip():
            raise ValueError("No textual content found in record")
        
        return self.generate_embedding(combined_text)
    
    def embed_page_content(self, 
                          title: str, 
                          content: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Generate embedding for web page content."""
        
        text_parts = []
        
        # Add title (weighted more heavily)
        if title and title.strip():
            text_parts.append(f"Title: {title}")
            text_parts.append(title)  # Add twice for emphasis
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str) and value.strip():
                    text_parts.append(f"{key}: {value}")
        
        # Add main content (truncated)
        if content and content.strip():
            # Take first and last parts of content
            content_length = len(content)
            if content_length > 4000:
                start_content = content[:2000]
                end_content = content[-2000:]
                text_parts.append(f"Content: {start_content} ... {end_content}")
            else:
                text_parts.append(f"Content: {content}")
        
        combined_text = " | ".join(text_parts)
        
        if not combined_text.strip():
            raise ValueError("No content available for embedding")
        
        return self.generate_embedding(combined_text)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model."""
        if self.provider == "openai":
            if "ada-002" in self.model:
                return 1536
            elif "text-embedding-3-small" in self.model:
                return 1536
            elif "text-embedding-3-large" in self.model:
                return 3072
        
        # Default fallback
        return 1536