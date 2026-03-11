"""Product Recommendation Agent Services.

This module provides services for:
- Vector search using Qdrant
- Embedding generation for multiple providers
- Sparse embedding using BM25
"""

from .embedding_service import EmbeddingService
from .search_service import SearchService
from .sparse_embedding_service import SparseEmbeddingService

__all__ = [
    "EmbeddingService",
    "SearchService",
    "SparseEmbeddingService",
]
