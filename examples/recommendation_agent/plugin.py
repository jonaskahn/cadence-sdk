"""Product Recommendation Plugin for resources from Qdrant.

This plugin recommends resources from a Qdrant vector collection. The content
can be anything stored in the collection—products, documents, items, etc.
Utilizes vector search with dense and sparse embeddings for optimal discovery.
"""

from typing import Any, Dict, List, Optional

from cadence_sdk import (
    BasePlugin,
    BaseSpecializedAgent,
    PluginMetadata,
    UvTool,
    plugin_settings,
    uvtool,
)
from .schemas import (
    RecommendationSearchInput,
    ResourceByIdInput,
    ResourceByUrlInput,
    SearchTerm,
)
from .services.embedding_service import EmbeddingService
from .services.search_service import SearchService
from .services.sparse_embedding_service import SparseEmbeddingService


def _stream_recommendation_resources(result: dict) -> list[dict]:
    """Stream filter: expose only product_id and url to the client."""
    items = (result.get("result") or []) if isinstance(result, dict) else []
    return [
        {"product_id": r.get("product_id"), "url": r.get("url")}
        for r in items
        if r.get("product_id") or r.get("url")
    ]


class ProductRecommendationAgent(BaseSpecializedAgent):
    """Agent for routing recommendation queries to tools.

    Recommends resources from Qdrant. Analyzes user queries and routes to
    appropriate search or retrieval tools with optimized parameters based on
    conversation history and user intent.
    """

    SYSTEM_PROMPT = """You are the Routing Agent for recommendation resources from Qdrant. Analyze user queries and route to appropriate tools.

**Routing Protocol:**
- Carefully understand current user query to call right tool with meaningful parameters most suitable for query
- Route to optimal tool/function call
- Clarify only when routing is ambiguous
- No comprehensive answers - route only

**Context Awareness:**
- Analyze conversation history to identify previously recommended resources
"""

    def __init__(self) -> None:
        super().__init__()
        self._search_service: Optional[SearchService] = None
        self._system_prompt: Optional[str] = None

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize agent with configuration from plugin_settings (injected at runtime)."""
        embedding_svc = EmbeddingService(config)
        sparse_svc = SparseEmbeddingService()
        self._search_service = SearchService(embedding_svc, sparse_svc, config)
        self._system_prompt = config.get("system_prompt")

    def _get_search_service(self) -> SearchService:
        """Get search service (requires initialize to have been called)."""
        if self._search_service is None:
            raise RuntimeError(
                "ProductRecommendationAgent not initialized. "
                "initialize(config) must be called before get_tools()."
            )
        return self._search_service

    def _create_recommendation_tool(self) -> UvTool:
        """Create get_recommendation_resources tool."""

        @uvtool(
            args_schema=RecommendationSearchInput,
            stream=True,
            stream_filter=_stream_recommendation_resources,
            validate=True,
        )
        async def get_recommendation_resources(
            search_terms: List[SearchTerm],
            score_threshold: Optional[float] = 0.2,
            excluded_qdrant_ids: Optional[str] = None,
            max_results: int = 20,
        ) -> Optional[dict]:
            """Search resources in Qdrant using hybrid semantic and keyword matching across multiple search variations.

            Executes searches for each term using both dense (semantic) embeddings and
            sparse (BM25) embeddings, then fuses results with reranking.

            Args:
                score_threshold:
                search_terms: List of SearchTerm objects with queries and keywords
                excluded_qdrant_ids: Comma-separated IDs to exclude from results
                max_results: Maximum number of results to return

            Returns:
                Dictionary with query_validate and result fields, or error message
            """
            search_service = self._get_search_service()
            result = await search_service.get_similar_items(
                search_terms=search_terms,
                score_threshold=score_threshold,
                max_results=max_results,
                excluded_ids=excluded_qdrant_ids,
            )

            if isinstance(result, list):
                for item in result:
                    if not item.get("url") and item.get("product_id"):
                        item["url"] = f"card://{item['product_id']}"

            return result if result else None

        return get_recommendation_resources

    def _create_resource_by_id_tool(self) -> UvTool:
        """Create get_resource_by_qdrant_id tool."""

        @uvtool(args_schema=ResourceByIdInput)
        async def get_resource_by_qdrant_id(qdrant_id: str) -> Optional[dict]:
            """Retrieve detailed resource by Qdrant vector ID.

            Use ONLY when exact qdrant_id exists in chat history from previous searches.

            Args:
                qdrant_id: Exact Qdrant point ID from previous search results

            Returns:
                Dictionary with result field containing resource details, or not found message
            """
            search_service = self._get_search_service()
            item = await search_service.get_resource_by_id(resource_id=qdrant_id)
            return item

        return get_resource_by_qdrant_id

    def _create_resource_by_url_tool(self) -> UvTool:
        """Create get_resource_by_url tool."""

        @uvtool(args_schema=ResourceByUrlInput)
        async def get_resource_by_url(url: str) -> Optional[dict]:
            """Retrieve resource details by URL.

            Use when user provides or references a specific resource URL.

            Args:
                url: Resource URL

            Returns:
                Dictionary with result field containing resource details, or not found message
            """
            search_service = self._get_search_service()
            item = await search_service.get_resource_by_url(url=url)
            return [item] if item else None

        return get_resource_by_url

    def get_tools(self) -> List[UvTool]:
        """Provide list of available recommendation tools."""
        return [
            self._create_recommendation_tool(),
            self._create_resource_by_id_tool(),
            self._create_resource_by_url_tool(),
        ]

    def get_system_prompt(self) -> str:
        """Provide system prompt for agent behavior."""
        return self._system_prompt or self.SYSTEM_PROMPT

    async def prefetch_context(self, identifier: str) -> Dict[str, Any]:
        """Fetch the anchor product by URL or Qdrant ID."""
        service = self._get_search_service()
        if identifier.startswith(("http://", "https://")):
            item = await service.get_resource_by_url(url=identifier)
        else:
            item = await service.get_resource_by_id(resource_id=identifier)
        return item or {}

    def build_context_scope(self, context: Dict[str, Any]) -> str:
        """Generate scope from the fetched product name."""
        title = context.get("title") or context.get("name", "this item")
        return (
            f"Answer questions about {title} and similar or related items. "
            "Do not answer questions unrelated to this item or the product collection."
        )


@plugin_settings(
    [
        {
            "key": "qdrant_url",
            "name": "Qdrant URL",
            "type": "str",
            "required": True,
            "description": "Qdrant server URL",
        },
        {
            "key": "qdrant_api_key",
            "name": "Qdrant API key",
            "type": "str",
            "sensitive": True,
            "required": False,
            "description": "Qdrant API key",
        },
        {
            "key": "qdrant_collection_name",
            "name": "Qdrant Collection",
            "type": "str",
            "required": True,
            "description": "Qdrant collection name for product vectors",
        },
        {
            "key": "qdrant_timeout",
            "name": "Qdrant Timeout",
            "type": "int",
            "default": 60,
            "required": False,
            "description": "Qdrant client timeout in seconds",
        },
        {
            "key": "qdrant_prefer_grpc",
            "name": "Qdrant Prefer gRPC",
            "type": "bool",
            "default": False,
            "required": False,
            "description": "Use gRPC protocol for Qdrant",
        },
        {
            "key": "qdrant_retry_count",
            "name": "Qdrant Retry Count",
            "type": "int",
            "default": 3,
            "required": False,
            "description": "Number of retry attempts for Qdrant operations",
        },
        {
            "key": "qdrant_retry_delay",
            "name": "Qdrant Retry Delay",
            "type": "float",
            "default": 1.0,
            "required": False,
            "description": "Delay between retry attempts in seconds",
        },
        {
            "key": "qdrant_dense_vector_name",
            "name": "Qdrant Dense Vector Name",
            "type": "str",
            "default": "text-embedding-3-large",
            "required": False,
            "description": "Qdrant vector name for dense embeddings",
        },
        {
            "key": "embedding_provider",
            "name": "Embedding Provider",
            "type": "str",
            "default": "azure",
            "required": False,
            "description": "Embedding provider: openai, azure",
        },
        {
            "key": "embedding_provider_openai_model",
            "name": "OpenAI Embedding Model",
            "type": "str",
            "default": "text-embedding-3-large",
            "required": False,
            "description": "OpenAI embedding model name",
        },
        {
            "key": "embedding_provider_openai_api_key",
            "name": "OpenAI API Key",
            "type": "str",
            "required": False,
            "sensitive": True,
            "description": "OpenAI API key",
        },
        {
            "key": "embedding_provider_azure_openai_api_key",
            "name": "Azure OpenAI API Key",
            "type": "str",
            "required": False,
            "sensitive": True,
            "description": "Azure OpenAI API key",
        },
        {
            "key": "embedding_provider_azure_openai_endpoint",
            "name": "Azure OpenAI Endpoint",
            "type": "str",
            "required": False,
            "description": "Azure OpenAI endpoint URL",
        },
        {
            "key": "embedding_provider_azure_openai_api_version",
            "name": "Azure OpenAI API Version",
            "type": "str",
            "default": "2025-04-01-preview",
            "required": False,
            "description": "Azure OpenAI API version",
        },
        {
            "key": "embedding_provider_azure_openai_deployment",
            "name": "Azure OpenAI Deployment",
            "type": "str",
            "default": "text-embedding-3-large",
            "required": False,
            "description": "Azure OpenAI deployment name for embeddings",
        },
        {
            "key": "system_prompt",
            "name": "System Prompt Override",
            "type": "str",
            "required": False,
            "description": "Optional override for the agent system prompt. Leave empty to use default.",
        },
    ]
)
class ProductRecommendationPlugin(BasePlugin):
    """Plugin that recommends resources from Qdrant. Content can be anything in the collection."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        """Create plugin metadata."""
        return PluginMetadata(
            pid="one.ifelse.plugins.recommendation_agent",
            name="Recommendation Resources",
            version="1.0.0",
            description=(
                "Recommends resources from a Qdrant vector collection. "
                "The content can be anything stored in the collection—products, documents, items, etc."
            ),
            capabilities=[
                "get_recommendation_resources (get overview recommendation resources)",
                "get_resource_by_qdrant_id (get detailed resource by qdrant_id)",
                "get_resource_by_url (get detailed resource by url)",
            ],
            dependencies=[
                "cadence_sdk>=2.0.0,<3.0.0",
                "qdrant-client>=1.0.0,<2.0.0",
                "openai>=1.0.0,<2.0.0",
                "fastembed>=0.7.0,<1.0.0",
            ],
            stateless=True,
        )

    @staticmethod
    def create_agent() -> ProductRecommendationAgent:
        """Create and initialize product recommendation agent."""
        return ProductRecommendationAgent()
