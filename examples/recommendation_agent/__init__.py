"""Product Recommendation Plugin for resources from Qdrant.

Recommends resources from a Qdrant vector collection. The content can be
anything stored in the collection—products, documents, items, etc.
"""

from .plugin import ProductRecommendationPlugin
from .schemas import (
    RecommendationSearchInput,
    ResourceByIdInput,
    ResourceByUrlInput,
    SearchTerm,
)

__all__ = [
    "ProductRecommendationPlugin",
    "RecommendationSearchInput",
    "ResourceByIdInput",
    "ResourceByUrlInput",
    "SearchTerm",
]
