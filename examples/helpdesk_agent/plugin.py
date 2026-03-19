"""Helpdesk Agent Plugin.

Customer helpdesk agent demonstrating both specialized and scoped/grounded modes:

- Specialized mode (multi-agent orchestration): answers general support questions
  by searching knowledge base articles via search_articles and get_article tools.

- Scoped/Grounded mode: anchors to a specific support ticket (by ID or slug) and
  scopes the conversation to that ticket's issue and resolution steps, while still
  allowing KB article lookups.

All data is bundled in-memory via data.py — no external API is required.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from cadence_sdk import (
    BasePlugin,
    BaseScopedAgent,
    BaseSpecializedAgent,
    Loggable,
    PluginMetadata,
    UvTool,
    plugin_settings,
    uvtool,
)
from .data import ARTICLES, build_article_index, build_ticket_index

ARTICLE_EXCERPT_LENGTH = 300


class SearchArticlesInput(BaseModel):
    query: str = Field(
        description="Keywords or phrase to search for in knowledge base articles"
    )


class GetArticleInput(BaseModel):
    article_id: str = Field(description="Knowledge base article ID (e.g. KB-001)")


class HelpdeskAgent(BaseSpecializedAgent, BaseScopedAgent, Loggable):
    """Customer helpdesk agent supporting both specialized and scoped/grounded modes.

    Specialized mode (multi-agent orchestration):
        Answers general support questions by searching knowledge base articles.
        Tools: search_articles, get_article.

    Scoped/Grounded mode:
        Anchors to a specific support ticket (by ID or slug) and scopes the
        conversation to that ticket's issue and resolution steps. The same KB
        search tools remain available for looking up relevant articles.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are a customer support assistant. Help users by searching the knowledge base "
        "for relevant articles. Use search_articles to find articles by topic, and "
        "get_article to retrieve full article content when you need specific details. "
        "Be concise, accurate, and empathetic."
    )

    def __init__(self) -> None:
        self._system_prompt: Optional[str] = None
        self._article_index: Dict[str, Dict[str, Any]] = build_article_index()
        self._ticket_index: Dict[str, Dict[str, Any]] = build_ticket_index()
        self._search_tool = self._create_search_articles_tool()
        self._get_article_tool = self._create_get_article_tool()

    def initialize(self, config: Dict[str, Any]) -> None:
        self._system_prompt = config.get("system_prompt")
        data_source = config.get("data_source", "bundled")
        if data_source != "bundled":
            self.logger.warning(
                "data_source '%s' is not supported; falling back to bundled mock data.",
                data_source,
            )

    @staticmethod
    def _create_search_articles_tool() -> UvTool:
        @uvtool(args_schema=SearchArticlesInput, stream=True)
        async def search_articles(query: str) -> List[Dict[str, Any]]:
            """Search knowledge base articles by keyword.

            Returns articles whose title, content, or tags contain the query.
            Use this to find relevant support documentation for a user's question.
            Follow up with get_article to retrieve the full content of a match.

            Args:
                query: Keywords or phrase to search for

            Returns:
                List of matching articles with id, title, excerpt, and tags.
                Returns a not-found message if no articles match.
            """
            query_lower = query.lower()
            results = []
            for article in ARTICLES:
                searchable = (
                    article["title"].lower()
                    + " "
                    + article["content"].lower()
                    + " "
                    + " ".join(article["tags"])
                )
                if query_lower in searchable:
                    content = article["content"]
                    excerpt = content[:ARTICLE_EXCERPT_LENGTH]
                    if len(content) > ARTICLE_EXCERPT_LENGTH:
                        excerpt += "…"
                    results.append(
                        {
                            "id": article["id"],
                            "title": article["title"],
                            "excerpt": excerpt,
                            "tags": article["tags"],
                        }
                    )
            if not results:
                return [{"message": f"No articles found for '{query}'."}]
            return results

        return search_articles

    def _create_get_article_tool(self) -> UvTool:
        @uvtool(args_schema=GetArticleInput)
        async def get_article(article_id: str) -> Dict[str, Any]:
            """Retrieve the full content of a knowledge base article by ID.

            Use this after search_articles identifies a relevant article to get
            the complete text before composing your answer.

            Args:
                article_id: Knowledge base article ID (e.g. KB-001)

            Returns:
                Full article dict with id, title, content, and tags.
                Returns an error dict if the article ID is not found.
            """
            article = self._article_index.get(article_id.upper())
            if article:
                return article
            return {"error": f"Article '{article_id}' not found."}

        return get_article

    def get_tools(self) -> List[UvTool]:
        return [self._search_tool, self._get_article_tool]

    def get_system_prompt(self) -> str:
        return self._system_prompt or self.DEFAULT_SYSTEM_PROMPT

    async def load_anchor(self, resource_id: str) -> Dict[str, Any]:
        """Load a support ticket by ID (e.g. TKT-001) or slug (e.g. login-2fa-not-working).

        Args:
            resource_id: Ticket ID or URL-friendly slug.

        Returns:
            Ticket dict with id, slug, summary, description, status, and tags.
            Returns {} if the ticket is not found.
        """
        ticket = self._ticket_index.get(resource_id) or self._ticket_index.get(
            resource_id.upper()
        )
        if not ticket:
            self.logger.warning("Ticket '%s' not found in mock data.", resource_id)
            return {}
        return dict(ticket)

    def build_scope_rules(self, context: Dict[str, Any]) -> str:
        ticket_id = context.get("id", "")
        summary = context.get("summary", "this support ticket")
        id_part = f"#{ticket_id}: " if ticket_id else ""
        return (
            f"Answer questions related to support ticket {id_part}{summary}. "
            "Focus on the issue, its description, and relevant resolution steps. "
            "You may search KB articles to help resolve the ticket."
        )


@plugin_settings(
    [
        {
            "key": "data_source",
            "name": "Data Source",
            "type": "str",
            "default": "bundled",
            "required": False,
            "description": (
                "Data source for tickets and articles. "
                "Currently only 'bundled' (in-memory mock data) is supported."
            ),
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
class HelpdeskPlugin(BasePlugin):
    """Plugin for customer helpdesk support with KB search and ticket anchoring.

    Supports both specialized mode (multi-agent orchestration) and scoped/grounded
    mode (ticket-anchored conversation). Uses bundled mock data — no external API
    required.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="one.ifelse.helpdesk_agent",
            name="Helpdesk Agent",
            version="1.0.0",
            description=(
                "Customer helpdesk agent with knowledge base search and ticket anchoring. "
                "In specialized mode, searches KB articles to answer general support questions. "
                "In scoped/grounded mode, anchors to a specific support ticket and scopes "
                "the conversation to that ticket's issue and resolution steps."
            ),
            capabilities=[
                "search_articles: Search knowledge base articles by keyword",
                "get_article: Retrieve full article content by ID",
            ],
            dependencies=["cadence_sdk>=2.0.0,<3.0.0"],
            stateless=True,
        )

    @staticmethod
    def create_agent() -> HelpdeskAgent:
        return HelpdeskAgent()
