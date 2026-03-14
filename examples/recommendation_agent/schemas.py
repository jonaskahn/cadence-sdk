"""Data models and schemas for recommendation agent.

This module contains all input/output data models used across
the recommendation agent tools and services.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchTerm(BaseModel):
    """A single search term with query, keywords, and intent."""

    query: str = Field(
        description=(
            "Specification-focused query (3-8 terms) optimized for semantic search. "
            "Primary entity anchors search, attributes refine it. Each term adds distinct semantic value."
        )
    )

    keywords: str = Field(
        description=(
            "Comma-separated keywords (typically 1-3 terms) for exact/sparse matching (BM25). "
            "Use specific names, identifiers, or key attributes. "
            "Example: 'Nike, Air Max' or 'iPhone 15, Apple'"
        )
    )

    intent: Optional[str] = Field(
        default=None,
        description=(
            "Brief explanation (1-2 sentences) for this specific search term: "
            "what user wants, why these specs/keywords chosen."
        ),
    )


class RecommendationSearchInput(BaseModel):
    """Input schema for recommendation search."""

    search_terms: List[SearchTerm] = Field(
        description=(
            "List of search term objects. Each contains query (semantic specs), "
            "keywords (exact matches), and optional intent. Multiple terms allow "
            "searching for different resource variations in one request. Provide 1-5 search terms."
        ),
        min_length=1,
        max_length=5,
    )

    excluded_qdrant_ids: Optional[str] = Field(
        default=None,
        description=(
            "A comma-delimited string of Qdrant vector IDs to explicitly exclude from search results, "
            "thereby preventing duplication of previously recommended items. ALWAYS send an explicit value: "
            "• If continuing a conversation with prior recommendations: populate with accumulated IDs "
            "  from previous results (e.g., '12345,67890,11223') "
            "• If this is the initial search: explicitly send None or empty string "
            "Extract IDs from prior results and accumulate them across multiple search iterations to "
            "ensure users receive diverse, non-repetitive recommendations."
        ),
    )

    score_threshold: Optional[float] = Field(
        default=0.2,
        description=(
            "Similarity score (0.1-1.0). Default 0.4. "
            "0.6-1.0: Precise | 0.3-0.6: Balanced | 0.1-0.3: Broad"
        ),
        le=1.0,
    )

    max_results: Optional[int] = Field(
        default=15,
        description=(
            "Max items (10-25). Default 15. Prioritize quality over literal user requests. "
            "10-12: Narrow | 15-18: Standard | 20-25: Broad"
        ),
        le=25,
    )


class ResourceByIdInput(BaseModel):
    """Input schema for retrieving a resource by Qdrant ID."""

    qdrant_id: str = Field(
        description="Exact qdrant_id from conversation history. Must exist in prior search results."
    )


class ResourceByUrlInput(BaseModel):
    """Input schema for retrieving a resource by URL."""

    url: str = Field(description="Resource URL")
