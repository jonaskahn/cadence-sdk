"""Web Search Agent Plugin.

Searches the web using Google Search via Serper.dev.
Supports site-specific searches, time-based filtering, and image search.
"""

import re
from typing import Any, Dict, List, Optional

import httpx

from pydantic import BaseModel, Field

from cadence_sdk import (
    BaseAgent,
    BasePlugin,
    PluginMetadata,
    UvTool,
    plugin_settings,
    uvtool,
)

DEFAULT_MAX_RESULTS = 10


def _stream_search_urls(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Stream filter for web_search: expose only URL and title to the client.

    The full result (including snippet and date) continues to flow through the
    internal pipeline so the synthesizer can build a complete answer.  Only
    the lightweight url/title pairs are sent as a ``tool`` SSE event so the
    client can render source links immediately, before the synthesizer finishes.

    Args:
        results: Raw list of search result dicts produced by web_search.

    Returns:
        List of ``{"title": ..., "url": ...}`` dicts — one per result.
    """
    return [
        {"title": r.get("title", ""), "url": r.get("url", "")}
        for r in (results or [])
        if r.get("url")
    ]


class WebSearchTerm(BaseModel):
    queries: str = Field(
        description=(
            "A collection of 2-4 queries based on user intent, each separated by comma. "
            "Each query focuses on a specific aspect of the user intent."
        )
    )
    site: Optional[str] = Field(
        default=None,
        description="Restrict search to a specific domain (e.g. mobile.de, indeed.com)",
    )
    tbs: Optional[str] = Field(
        default=None,
        description=(
            "Time-based search filter. Use Serper tbs format: "
            "qdr:d (past day), qdr:w (past week), qdr:m (past month), qdr:y (past year)"
        ),
    )


class SearchByKeywordInput(BaseModel):
    search_terms: List[WebSearchTerm] = Field(
        description="List of search term objects",
        min_length=1,
        max_length=5,
    )


class ImageSearchInput(BaseModel):
    query: str = Field(description="Image search query")
    num: Optional[int] = Field(
        default=DEFAULT_MAX_RESULTS,
        description="Number of image results to return (1–100)",
    )


class WebSearchAgent(BaseAgent):
    """Web search agent using Serper.dev Google Search API."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are a web search agent. Analyze user queries to generate precise search terms "
        "and route them to the appropriate tool. Use web_search for general web content; "
        "use image_search when the user explicitly asks for images or visual content. "
        "Use site restrictions when the user targets a specific website, and apply time "
        "filters when recency matters."
    )

    def __init__(self):
        self._serper_api_key: str = ""
        self._max_results: int = DEFAULT_MAX_RESULTS
        self._system_prompt: Optional[str] = None
        self._search_tool = self._create_search_tool()
        self._image_search_tool = self._create_image_search_tool()

    def initialize(self, config: Dict[str, Any]) -> None:
        api_key = config.get("serper_api_key")
        if not api_key:
            raise ValueError("serper_api_key is required but not configured")
        self._serper_api_key = api_key
        self._max_results = config.get("max_results", DEFAULT_MAX_RESULTS)
        self._system_prompt = config.get("system_prompt")

    async def _serper_request(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(verify=True) as client:
            resp = await client.post(
                f"https://google.serper.dev{endpoint}",
                json=payload,
                headers={
                    "X-API-KEY": self._serper_api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def _serper_search(
        self, query: str, tbs: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"q": query, "num": self._max_results}
        if tbs:
            payload["tbs"] = tbs
        data = await self._serper_request("/search", payload)
        return data.get("organic", [])

    async def _serper_image_search(self, query: str, num: int) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"q": query, "num": num}
        data = await self._serper_request("/images", payload)
        return data.get("images", [])

    def _create_search_tool(self) -> UvTool:
        @uvtool(
            args_schema=SearchByKeywordInput,
            stream=True,
            stream_filter=_stream_search_urls,
            validate=True,
        )
        async def web_search(
            search_terms: List[WebSearchTerm],
        ) -> Dict[str, Any]:
            """
            Searches the web using Google Search (via Serper.dev) and returns organic results.

            Supports multiple search terms with optional site restriction and time filtering.
            Each search term can target a specific domain and time range.
            """
            seen_urls: set = set()
            final_results: List[Dict[str, Any]] = []

            for term in search_terms:
                for raw_query in re.split(r"[,;]", term.queries or ""):
                    query = (
                        f"site:{term.site} {raw_query.strip()}"
                        if term.site
                        else raw_query.strip()
                    )
                    for item in await self._serper_search(query, term.tbs):
                        url = item.get("link")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            final_results.append(
                                {
                                    "title": item.get("title"),
                                    "url": url,
                                    "snippet": item.get("snippet"),
                                    "date": item.get("date"),
                                }
                            )

            return final_results

        return web_search

    def _create_image_search_tool(self) -> UvTool:
        @uvtool(args_schema=ImageSearchInput)
        async def image_search(
            query: str,
            num: Optional[int] = DEFAULT_MAX_RESULTS,
        ) -> Dict[str, Any]:
            """
            Searches for images using Google Images (via Serper.dev).

            Returns image results including URLs, thumbnails, dimensions, and source information.
            Use this when the user explicitly asks for images or visual content.
            """
            items = await self._serper_image_search(query, num or DEFAULT_MAX_RESULTS)
            results = [
                {
                    "title": item.get("title"),
                    "image_url": item.get("imageUrl"),
                    "image_width": item.get("imageWidth"),
                    "image_height": item.get("imageHeight"),
                    "thumbnail_url": item.get("thumbnailUrl"),
                    "source": item.get("source"),
                    "link": item.get("link"),
                    "position": item.get("position"),
                }
                for item in items
            ]

            return results

        return image_search

    def get_tools(self) -> List[UvTool]:
        return [self._search_tool, self._image_search_tool]

    def get_system_prompt(self) -> str:
        return self._system_prompt or self.DEFAULT_SYSTEM_PROMPT


@plugin_settings(
    [
        {
            "key": "serper_api_key",
            "name": "Serper API Service Key",
            "type": "str",
            "required": True,
            "sensitive": True,
            "description": "Serper.dev API key for Google Search",
        },
        {
            "key": "max_results",
            "name": "Max Search Results",
            "type": "int",
            "default": DEFAULT_MAX_RESULTS,
            "required": False,
            "description": "Maximum number of search results per query (1–20)",
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
class WebSearchPlugin(BasePlugin):
    """Plugin for web search using Serper.dev Google Search API."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.cadence.plugins.web_search_agent",
            name="Web Search Agent",
            version="1.0.1",
            description=(
                "Searches the web using Google Search via Serper.dev. "
                "Supports site-specific searches, time-based filtering, and image search."
            ),
            agent_type="specialized",
            capabilities=[
                "web_search: Searches the web for relevant content using Google Search results",
                "image_search: Searches Google Images for visual content by keyword",
            ],
            dependencies=[
                "cadence_sdk>=2.0.0,<3.0.0",
                "httpx>=0.27.0",
            ],
            stateless=True,
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return WebSearchAgent()
