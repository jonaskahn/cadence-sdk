"""Embedding service for multiple LLM providers.

This module provides dense embedding generation supporting:
- OpenAI (text-embedding-3-large)
- Azure OpenAI

Embeddings are used for semantic similarity search in recommendation resources.
"""

from typing import Any, Dict, List, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from cadence_sdk import Loggable


class EmbeddingService(Loggable):
    """Provides dense embedding generation for semantic search.

    Supports multiple embedding providers with automatic provider selection
    based on configuration. Embeddings enable semantic similarity matching
    for natural language queries.
    """

    PROVIDER_OPENAI = ["openai"]
    PROVIDER_AZURE = ["azure", "azure-openai"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.embedding_provider, self.model = self._create_embedding_provider(config)

    @staticmethod
    def _resolve_api_key(config: Dict[str, Any], provider: str) -> str | None:
        """Resolve API key for the given provider from config."""
        key_map = {
            "openai": "embedding_provider_openai_api_key",
            "azure-openai": "embedding_provider_azure_openai_api_key",
            "azure": "embedding_provider_azure_openai_api_key",
        }
        key_name = key_map.get(provider)
        return config.get(key_name) if key_name else None

    def _resolve_model(self, config: Dict[str, Any], provider: str) -> str:
        """Resolve model name for the given provider from config."""
        model_map = {
            "openai": "embedding_provider_openai_model",
            "azure": "embedding_provider_azure_openai_deployment",
            "azure-openai": "embedding_provider_azure_openai_deployment",
        }
        key_name = model_map.get(provider)
        default = (
            "text-embedding-3-large"
            if provider in self.PROVIDER_OPENAI + self.PROVIDER_AZURE
            else "text-embedding-3-large"
        )
        return config.get(key_name, default) if key_name else default

    def _create_embedding_provider(
        self, config: Dict[str, Any]
    ) -> tuple[Union[AsyncOpenAI, AsyncAzureOpenAI], str]:
        """Create embedding provider instance based on configuration."""
        provider = (config.get("embedding_provider") or "azure").lower()
        api_key = self._resolve_api_key(config, provider)
        if not api_key:
            raise ValueError(f"No API key found for embedding provider: {provider}")

        model = self._resolve_model(config, provider)

        if provider in self.PROVIDER_OPENAI:
            client = self._create_openai_client(api_key)
            return client, model
        elif provider in self.PROVIDER_AZURE:
            client = self._create_azure_client(api_key, model, config)
            return client, model
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")

    @staticmethod
    def _create_openai_client(api_key: str) -> AsyncOpenAI:
        """Create OpenAI async client."""
        return AsyncOpenAI(api_key=api_key)

    @staticmethod
    def _create_azure_client(
        api_key: str, _model: str, config: Dict[str, Any]
    ) -> AsyncAzureOpenAI:
        """Create Azure OpenAI async client."""
        return AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=config.get("embedding_provider_azure_openai_endpoint"),
            api_version=config.get(
                "embedding_provider_azure_openai_api_version", "2025-04-01-preview"
            ),
        )

    async def get_embedding_query(self, query: str) -> List[float]:
        """Generate embedding vector for search query."""
        collection = self.config.get("qdrant_collection_name", "")
        url = self.config.get("qdrant_url", "")
        self.logger.info(
            f"Generating embedding for query in collection {collection} on server {url}"
        )
        response = await self.embedding_provider.embeddings.create(
            model=self.model, input=query
        )
        return response.data[0].embedding
