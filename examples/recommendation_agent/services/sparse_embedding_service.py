"""Sparse Embedding Service Implementation.

This module provides sparse embedding functionality using FastEmbed BM25
for the product recommendation agent.
"""

from __future__ import annotations

import asyncio

from fastembed import SparseTextEmbedding
from qdrant_client.http import models

from cadence_sdk import Loggable


class SparseEmbeddingService(Loggable):

    def __init__(self):
        super().__init__()
        self.sparse_embedding_provider = SparseTextEmbedding("Qdrant/bm25")

    async def get_sparse_embedding_query(self, query: str) -> models.SparseVector:
        def _embed_query(query_text: str):
            return next(self.sparse_embedding_provider.embed([query_text]))

        sparse_embedding = await asyncio.to_thread(_embed_query, query)
        return models.SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist(),
        )
