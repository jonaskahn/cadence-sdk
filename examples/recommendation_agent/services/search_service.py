"""Search service for product recommendations using Qdrant vector database.

This module provides search and retrieval functionality combining dense (semantic)
and sparse (BM25) search. Implements multi-query fusion for comprehensive product discovery.
"""

import asyncio
import hashlib
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import FieldCondition, Filter, MatchValue, SparseVector

from cadence_sdk import Loggable
from .embedding_service import EmbeddingService
from .sparse_embedding_service import SparseEmbeddingService
from ..schemas import SearchTerm


class SearchService(Loggable):
    """Provides semantic and keyword-based product search.

    Combines dense embeddings (semantic understanding) and sparse embeddings (BM25)
    using Reciprocal Rank Fusion. Supports multi-query search for result diversity.
    """

    INITIAL_FETCH_LIMIT = 20
    MAX_FETCH_LIMIT = 150
    MAX_FETCH_ITERATIONS = 10
    ERROR_MESSAGE = "Could not fetch data right now"

    def __init__(
        self,
        embedding_service: EmbeddingService,
        sparse_embedding_service: SparseEmbeddingService,
        config: Dict[str, Any],
    ):
        super().__init__()
        self.embedding_service = embedding_service
        self.sparse_embedding_service = sparse_embedding_service
        self.config = config
        self.qdrant_client = self._create_qdrant_client(config)

    @staticmethod
    def _create_qdrant_client(config: Dict[str, Any]) -> QdrantClient:
        """Create and configure Qdrant client."""
        return QdrantClient(
            url=config.get("qdrant_url", "http://127.0.0.1:6333"),
            timeout=config.get("qdrant_timeout", 60),
            prefer_grpc=config.get("qdrant_prefer_grpc", False),
        )

    def _get_collection_name(self, collection: Optional[str] = None) -> str:
        """Resolve collection name from config or override."""
        return collection or self.config.get(
            "qdrant_collection_name", "shopapi_12112025"
        )

    def _get_retry_count(self) -> int:
        return self.config.get("qdrant_retry_count", 3)

    def _get_retry_delay(self) -> float:
        return self.config.get("qdrant_retry_delay", 1.0)

    def _get_dense_vector_name(self) -> str:
        return self.config.get("qdrant_dense_vector_name", "text-embedding-3-large")

    async def get_similar_items(
        self,
        search_terms: List[SearchTerm],
        collection: Optional[str] = None,
        score_threshold: float = 0.3,
        excluded_ids: Optional[str] = None,
        max_results: int = 15,
    ) -> list[Any] | str | list[dict] | dict[str, str] | None:
        """Find similar items using multiple search terms with fusion.

        Executes searches for each term (both semantic and keyword-based), deduplicates
        results, then ranks by semantic score.

        Args:
            search_terms: List of SearchTerm objects with queries and keywords
            collection: Qdrant collection name (uses default if None)
            score_threshold: Minimum similarity score to include
            excluded_ids: Comma-separated IDs to exclude from results
            max_results: Maximum number of results to return

        Returns:
            List of product dictionaries or error message
        """
        try:
            if not search_terms:
                self.logger.warning("Empty search_terms provided")
                return []

            excluded_ids_list = self._parse_excluded_ids(excluded_ids)
            all_documents = await self._collect_documents_from_all_terms(
                search_terms, collection, score_threshold, excluded_ids_list
            )

            if not all_documents:
                return None

            return self._rank_results(all_documents, max_results)
        except Exception as error:
            self.logger.warning(f"Failed to retrieve similar items: {error}")
            return None

    def _rank_results(self, all_documents: List[dict], max_results: int) -> List[dict]:
        """Rank documents by semantic score (fallback ranking)."""
        return self._fallback_to_semantic_ranking(all_documents, max_results)

    async def get_resource_by_id(
        self, resource_id: str, collection: Optional[str] = None
    ) -> Optional[dict]:
        """Retrieve single product by Qdrant ID."""
        if not self._is_valid_string(resource_id):
            self.logger.warning("Empty resource_id provided")
            return None

        try:
            point = self._retrieve_point_by_id(resource_id, collection)
            if not point:
                return None
            return self._format_response(point.id, point.payload or {})
        except Exception as error:
            self.logger.error(f"Error retrieving resource_id {resource_id}: {error}")
            return {"error": self.ERROR_MESSAGE}

    async def get_resource_by_url(
        self, url: str, collection: Optional[str] = None
    ) -> Optional[dict]:
        """Retrieve single product by URL."""
        if not self._is_valid_string(url):
            self.logger.warning("Empty url provided")
            return None

        try:
            url_filter = self._create_url_filter(url)
            point = self._query_single_point(collection, url_filter)
            if not point:
                return None
            return self._format_response(point.id, point.payload or {})
        except Exception as error:
            self.logger.error(f"Error retrieving url {url}: {error}")
            return None

    async def _collect_documents_from_all_terms(
        self,
        search_terms: List[SearchTerm],
        collection: Optional[str],
        score_threshold: float,
        excluded_ids_list: List[str],
    ) -> List[dict]:
        """Execute searches for all terms and collect deduplicated results."""
        all_documents = []
        seen_hashes = set()
        search_tasks = []

        for term in search_terms:
            query_text, keywords_text = self._extract_term_texts(term)
            if not self._is_valid_string(query_text) or not self._is_valid_string(
                keywords_text
            ):
                continue

            search_tasks.append(
                self._search_qdrant(
                    keywords_text,
                    query_text,
                    collection,
                    score_threshold,
                    excluded_ids_list,
                )
            )
            search_tasks.append(
                self._search_qdrant(
                    query_text,
                    keywords_text,
                    collection,
                    score_threshold,
                    excluded_ids_list,
                )
            )

        if not search_tasks:
            return []

        results = await asyncio.gather(*search_tasks)
        for result in results:
            self._add_search_results(result, all_documents, seen_hashes)

        return all_documents

    def _add_search_results(
        self, documents: List[dict], all_documents: List[dict], seen_hashes: set
    ) -> None:
        """Add documents to collection if not already seen."""
        for doc in documents:
            url = doc.get("url", "")
            url_hash = self._hash_payload(url)
            if url_hash in seen_hashes:
                continue
            seen_hashes.add(url_hash)
            all_documents.append(doc)

    async def _search_qdrant(
        self,
        query: str,
        sparse_query: str,
        collection: Optional[str],
        score_threshold: float,
        excluded_ids_list: List[str],
    ) -> List[dict]:
        """Execute iterative search with dense and sparse embeddings."""
        query_embeddings = await self.embedding_service.get_embedding_query(query)
        sparse_embeddings = (
            await self.sparse_embedding_service.get_sparse_embedding_query(sparse_query)
        )

        return await self._fetch_documents_iteratively(
            query_embeddings,
            sparse_embeddings,
            collection,
            score_threshold,
            excluded_ids_list,
        )

    async def _fetch_documents_iteratively(
        self,
        dense_embeddings: List[float],
        sparse_embeddings: SparseVector,
        collection: Optional[str],
        score_threshold: float,
        excluded_ids_list: List[str],
    ) -> List[dict]:
        """Fetch documents in batches with exponential limit increase."""
        retrieved_documents = []
        seen_hashes = set()
        current_limit = self.INITIAL_FETCH_LIMIT

        for _ in range(self.MAX_FETCH_ITERATIONS):
            hits = await self._fetch_batch_from_qdrant(
                dense_embeddings, sparse_embeddings, collection, current_limit
            )

            if not hits:
                break

            should_continue = self._process_and_deduplicate_batch(
                hits,
                seen_hashes,
                retrieved_documents,
                score_threshold,
                excluded_ids_list,
            )

            if not should_continue or len(hits) < current_limit:
                break

            current_limit = min(current_limit * 2, self.MAX_FETCH_LIMIT)

        return retrieved_documents

    async def _fetch_batch_from_qdrant(
        self,
        dense_embeddings: List[float],
        sparse_embeddings: SparseVector,
        collection: Optional[str],
        limit: int,
    ) -> List:
        """Fetch batch of results using RRF fusion of dense and sparse vectors."""
        prefetch_limit = limit // 2
        retry_count = self._get_retry_count()

        for attempt in range(retry_count):
            try:
                return self._execute_fusion_query(
                    dense_embeddings,
                    sparse_embeddings,
                    collection,
                    limit,
                    prefetch_limit,
                )
            except Exception as error:
                if not self._should_retry(attempt, retry_count):
                    self.logger.error(f"All retry attempts failed: {error}")
                    return []
                self._wait_before_retry(attempt)

        return []

    def _execute_fusion_query(
        self,
        dense_embeddings: List[float],
        sparse_embeddings: SparseVector,
        collection: Optional[str],
        limit: int,
        prefetch_limit: int,
    ) -> List:
        """Execute Qdrant fusion query combining dense and sparse searches."""
        coll = self._get_collection_name(collection)
        return self.qdrant_client.query_points(
            collection_name=coll,
            prefetch=[
                models.Prefetch(
                    query=dense_embeddings,
                    using=self._get_dense_vector_name(),
                    limit=prefetch_limit,
                ),
                models.Prefetch(
                    query=sparse_embeddings,
                    using="bm25",
                    limit=prefetch_limit,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            with_payload=True,
            limit=limit,
        ).points

    def _process_and_deduplicate_batch(
        self,
        hits: List,
        seen_hashes: set,
        retrieved_documents: List[dict],
        score_threshold: float,
        excluded_ids_list: List[str],
    ) -> bool:
        """Process batch of hits with deduplication and threshold filtering."""
        all_scores_above_threshold = True

        for hit in hits:
            if self._should_skip_hit(hit, score_threshold, excluded_ids_list):
                if self._is_score_below_threshold(hit.score, score_threshold):
                    all_scores_above_threshold = False
                continue

            if self._is_duplicate(hit, seen_hashes):
                continue

            self._add_document_to_results(hit, seen_hashes, retrieved_documents)

            if self._is_score_below_threshold(hit.score, score_threshold):
                all_scores_above_threshold = False

        return all_scores_above_threshold

    def _should_skip_hit(
        self, hit, score_threshold: float, excluded_ids_list: List[str]
    ) -> bool:
        """Check if hit should be filtered out."""
        return self._is_score_below_threshold(
            hit.score, score_threshold
        ) or self._is_excluded_id(hit, excluded_ids_list)

    def _is_duplicate(self, hit, seen_hashes: set) -> bool:
        """Check if document is duplicate based on URL hash."""
        payload = hit.payload or {}
        payload_hash = self._hash_payload(payload.get("url", ""))
        return payload_hash in seen_hashes

    def _add_document_to_results(
        self, hit, seen_hashes: set, retrieved_documents: List[dict]
    ) -> None:
        """Add hit to results and mark as seen."""
        payload = hit.payload or {}
        payload_hash = self._hash_payload(payload.get("url", ""))
        seen_hashes.add(payload_hash)
        retrieved_documents.append(self._format_response(hit.id, payload, hit.score))

    @staticmethod
    def _fallback_to_semantic_ranking(
        documents: List[dict], max_results: int
    ) -> List[dict]:
        """Rank documents by original semantic scores."""
        sorted_docs = sorted(
            documents, key=lambda x: x.get("score", 0.0) or 0.0, reverse=True
        )
        return sorted_docs[:max_results]

    def _retrieve_point_by_id(
        self, point_id: str, collection: Optional[str]
    ) -> Optional[dict]:
        """Retrieve single point by ID with retry logic."""
        coll = self._get_collection_name(collection)
        retry_count = self._get_retry_count()

        for attempt in range(retry_count):
            try:
                points = self.qdrant_client.retrieve(
                    collection_name=coll,
                    ids=[point_id],
                    with_payload=True,
                )
                return points[0] if points else None
            except Exception as error:
                if not self._handle_retry_error(
                    attempt, error, f"retrieving point {point_id}"
                ):
                    return None

        return None

    def _query_single_point(
        self, collection: Optional[str], query_filter: Optional[Filter]
    ) -> Optional[dict]:
        """Query for single point matching filter with retry logic."""
        coll = self._get_collection_name(collection)
        retry_count = self._get_retry_count()

        for attempt in range(retry_count):
            try:
                points = self.qdrant_client.query_points(
                    collection_name=coll,
                    query_filter=query_filter,
                    with_payload=True,
                ).points
                return points[0] if points else None
            except Exception as error:
                if not self._handle_retry_error(
                    attempt, error, "querying single point"
                ):
                    return None

        return None

    def _handle_retry_error(
        self, attempt: int, error: Exception, operation: str
    ) -> bool:
        """Handle retry logic for failed operations."""
        retry_count = self._get_retry_count()
        self.logger.warning(
            f"Attempt {attempt + 1}/{retry_count} failed for {operation}: {error}"
        )

        if self._should_retry(attempt, retry_count):
            self._wait_before_retry(attempt)
            return True

        self.logger.error(f"All retry attempts failed for {operation}: {error}")
        return False

    def _should_retry(self, attempt: int, retry_count: int) -> bool:
        """Check if should retry based on attempt number."""
        return attempt < retry_count - 1

    def _wait_before_retry(self, attempt: int) -> None:
        """Wait before retrying with exponential backoff."""
        delay = self._get_retry_delay()
        time.sleep(delay * (attempt + 1))

    @staticmethod
    def _format_response(
        point_id: str, payload: dict, score: Optional[float] = None
    ) -> dict:
        """Format Qdrant point into product response dictionary."""
        return {
            "qdrant_id": point_id,
            "product_id": payload.get("card_id"),
            "score": score,
            "url": payload.get("url"),
            "title": payload.get("name"),
            "spec": payload.get("spec"),
            "description": payload.get("description"),
        }

    @staticmethod
    def _parse_excluded_ids(excluded_ids: Optional[str]) -> List[str]:
        """Parse comma or semicolon separated string into list of IDs."""
        if not excluded_ids:
            return []
        return [x.strip() for x in re.split(r"[,;]", excluded_ids) if x.strip()]

    @staticmethod
    def _hash_payload(payload: str | dict) -> str:
        """Generate deterministic MD5 hash for payload deduplication."""
        if isinstance(payload, str):
            payload_str = payload
        else:
            payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(payload_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_term_texts(term: SearchTerm) -> Tuple[str, str]:
        """Extract query and keywords text from SearchTerm object or dict."""
        query_text = term.query if hasattr(term, "query") else term.get("query", "")
        keywords_text = (
            term.keywords if hasattr(term, "keywords") else term.get("keywords", "")
        )
        return query_text, keywords_text

    @staticmethod
    def _extract_query_text(term: SearchTerm) -> str:
        """Extract query text from SearchTerm object or dict."""
        keywords = (
            term.keywords if hasattr(term, "keywords") else term.get("keywords", "")
        )
        query = term.query if hasattr(term, "query") else term.get("query", "")
        return keywords if keywords else query

    @staticmethod
    def _is_valid_string(value: Optional[str]) -> bool:
        """Check if string value is non-empty."""
        return bool(value and value.strip())

    @staticmethod
    def _is_score_below_threshold(score: Optional[float], threshold: float) -> bool:
        """Check if score is below threshold."""
        return score is not None and score <= threshold

    @staticmethod
    def _is_excluded_id(hit, excluded_ids_list: List[str]) -> bool:
        """Check if hit ID is in excluded list."""
        hit_id = getattr(hit, "id", None) or (
            hit.payload.get("id") if hit.payload else None
        )
        if hit_id is None:
            return False
        return str(hit_id) in excluded_ids_list

    @staticmethod
    def _create_url_filter(url: str) -> Filter:
        """Create Qdrant filter for URL matching."""
        return Filter(must=[FieldCondition(key="url", match=MatchValue(value=url))])
