from typing import List, Dict, Any, Optional, Tuple
import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from loguru import logger

from app.config import settings


class VectorStore:
    """FAISS-based vector storage for semantic search capabilities."""
    
    def __init__(self, dimension: int = 1536, index_type: str = "flat"):
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self.id_to_index = {}  # Map record IDs to index positions
        self.next_id = 0
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index based on configuration."""
        if self.index_type == "flat":
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        elif self.index_type == "ivf":
            # Index with inverted file for faster search on large datasets
            nlist = 100  # Number of clusters
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info(f"Initialized FAISS index: {self.index_type}, dimension: {self.dimension}")
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """
        Add vectors to the index with associated metadata.
        
        Args:
            vectors: Array of embeddings to add
            metadata: List of metadata dicts for each vector
            
        Returns:
            List of assigned IDs for the vectors
        """
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors must match number of metadata items")
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)
        
        # Train index if needed (for IVF)
        if self.index_type == "ivf" and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(vectors)
        
        # Add vectors to index
        start_id = self.next_id
        self.index.add(vectors)
        
        # Store metadata and ID mapping
        assigned_ids = []
        for i, meta in enumerate(metadata):
            vector_id = f"vec_{start_id + i}"
            self.metadata.append({
                **meta,
                'vector_id': vector_id,
                'index_position': start_id + i
            })
            self.id_to_index[vector_id] = start_id + i
            assigned_ids.append(vector_id)
        
        self.next_id += len(vectors)
        
        logger.info(f"Added {len(vectors)} vectors to index")
        return assigned_ids
    
    def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results with metadata and scores
        """
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"Query vector dimension {query_vector.shape[0]} doesn't match index dimension {self.dimension}")
        
        if self.index.ntotal == 0:
            return []
        
        # Normalize query vector
        query_vector = query_vector.reshape(1, -1)
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # No more results
                break
            
            if score >= threshold:
                result = {
                    **self.metadata[idx],
                    'similarity_score': float(score)
                }
                results.append(result)
        
        return results
    
    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata by vector ID."""
        index_pos = self.id_to_index.get(vector_id)
        if index_pos is not None and index_pos < len(self.metadata):
            return self.metadata[index_pos]
        return None
    
    def save(self, path: Optional[str] = None) -> str:
        """Save index and metadata to disk."""
        if path is None:
            path = settings.vector_store_path
        
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = save_path / "index.faiss"
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata and mappings
        metadata_path = save_path / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'id_to_index': self.id_to_index,
                'next_id': self.next_id,
                'dimension': self.dimension,
                'index_type': self.index_type
            }, f)
        
        logger.info(f"Saved vector store to {save_path}")
        return str(save_path)
    
    def load(self, path: Optional[str] = None) -> bool:
        """Load index and metadata from disk."""
        if path is None:
            path = settings.vector_store_path
        
        load_path = Path(path)
        if not load_path.exists():
            logger.warning(f"Vector store path doesn't exist: {load_path}")
            return False
        
        try:
            # Load FAISS index
            index_path = load_path / "index.faiss"
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            metadata_path = load_path / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data['metadata']
                    self.id_to_index = data['id_to_index']
                    self.next_id = data['next_id']
                    self.dimension = data['dimension']
                    self.index_type = data['index_type']
            
            logger.info(f"Loaded vector store from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'metadata_count': len(self.metadata),
            'next_id': self.next_id
        }
    
    def delete_by_id(self, vector_id: str) -> bool:
        """Delete a vector by ID (not efficient with FAISS, requires rebuild)."""
        # Note: FAISS doesn't support efficient deletion
        # This is a limitation - for production use, consider other vector DBs
        logger.warning("Vector deletion requires index rebuild - not implemented for FAISS")
        return False
    
    def clear(self):
        """Clear all vectors and metadata."""
        self._initialize_index()
        self.metadata = []
        self.id_to_index = {}
        self.next_id = 0
        logger.info("Cleared vector store")