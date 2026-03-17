"""Webpage Reader Agent Plugin.

Fetches and discusses a specific webpage anchored by URL.
Designed for grounded/scoped mode only — does NOT participate in multi-agent orchestration.
"""

import re
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from cadence_sdk import (
    BasePlugin,
    BaseScopedAgent,
    Loggable,
    PluginMetadata,
    UvTool,
    plugin_settings,
    uvtool,
)

DEFAULT_MAX_CONTENT_LENGTH = 20000
MAX_FIND_RESULTS = 5
EXCERPT_CONTEXT_CHARS = 150


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


class FindInPageInput(BaseModel):
    query: str = Field(
        description="Keyword or phrase to search for within the loaded page text"
    )


class WebpageReaderAgent(BaseScopedAgent, Loggable):
    """Agent that fetches a webpage and answers questions scoped to its content.

    Scoped-only — has no value in multi-agent orchestration. Designed to be embedded
    in a grounded mode orchestrator anchored to a specific URL.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are a webpage reading assistant. You have fetched and loaded a specific webpage. "
        "Answer questions based solely on the page content. Use the find_in_page tool to locate "
        "relevant passages before forming your answer. Do not answer questions unrelated to the "
        "loaded page, and do not assume information that is not present in the page text."
    )

    def __init__(self) -> None:
        self._user_agent: Optional[str] = None
        self._max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH
        self._system_prompt: Optional[str] = None
        self._page_text: str = ""
        self._find_tool = self._create_find_tool()

    def initialize(self, config: Dict[str, Any]) -> None:
        self._user_agent = config.get("user_agent")
        self._max_content_length = config.get(
            "max_content_length", DEFAULT_MAX_CONTENT_LENGTH
        )
        self._system_prompt = config.get("system_prompt")

    async def load_anchor(self, resource_id: str) -> Dict[str, Any]:
        """Fetch the webpage at resource_id (a URL) and extract readable content.

        Parses title, meta description, and body text. Falls back to regex tag
        stripping if beautifulsoup4 is not installed.

        Args:
            resource_id: A full URL pointing to the page.

        Returns:
            Dict with url, title, description, and content keys, or {} on failure.
        """
        headers = {"User-Agent": self._user_agent} if self._user_agent else {}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(resource_id, headers=headers)
                resp.raise_for_status()
                html = resp.text
        except Exception as exc:
            self.logger.warning("Failed to fetch %s: %s", resource_id, exc)
            return {}

        title, meta_desc, body_text = self._parse_html(html)
        body_text = re.sub(r"\s+", " ", body_text).strip()[: self._max_content_length]
        self._page_text = body_text
        return {
            "url": resource_id,
            "title": title,
            "description": meta_desc,
            "content": body_text,
        }

    def build_scope_rules(self, context: Dict[str, Any]) -> str:
        label = context.get("title") or context.get("url", "the loaded page")
        return (
            f"Only answer questions about the content of: {label}. "
            "Do not answer questions unrelated to this page."
        )

    def _parse_html(self, html: str) -> tuple[str, str, str]:
        """Extract title, meta description, and body text from raw HTML.

        Tries beautifulsoup4 first; falls back to regex if unavailable.
        """
        try:
            return self._parse_with_bs4(html)
        except ImportError:
            return self._parse_with_regex(html)

    def _parse_with_bs4(self, html: str) -> tuple[str, str, str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = next(
            (
                tag.get("content", "")
                for tag in soup.find_all("meta")
                if tag.get("name", "").lower() == "description"
                or tag.get("property", "").lower() == "og:description"
            ),
            "",
        )
        for tag in soup(["script", "style", "noscript", "head"]):
            tag.decompose()
        return title, meta_desc, soup.get_text(separator=" ")

    def _parse_with_regex(self, html: str) -> tuple[str, str, str]:
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        title = title_match.group(1).strip() if title_match else ""
        meta_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE,
        )
        meta_desc = meta_match.group(1) if meta_match else ""
        return title, meta_desc, _strip_html_tags(html)

    def _create_find_tool(self) -> UvTool:
        @uvtool(args_schema=FindInPageInput)
        async def find_in_page(query: str) -> List[Dict[str, Any]]:
            """Search for a keyword or phrase within the loaded webpage text.

            Returns up to 5 matching excerpts with 150 chars of surrounding context.
            Use this to locate specific information before forming an answer.

            Args:
                query: The keyword or phrase to search for

            Returns:
                List of dicts with 'match' (bool) and 'excerpt' (str) fields.
            """
            if not self._page_text:
                return [{"match": False, "excerpt": "No page content loaded."}]

            text_lower = self._page_text.lower()
            query_lower = query.lower()
            matches = []
            start = 0
            while len(matches) < MAX_FIND_RESULTS:
                pos = text_lower.find(query_lower, start)
                if pos == -1:
                    break
                begin = max(0, pos - EXCERPT_CONTEXT_CHARS)
                end = min(
                    len(self._page_text), pos + len(query) + EXCERPT_CONTEXT_CHARS
                )
                excerpt = self._page_text[begin:end]
                if begin > 0:
                    excerpt = "…" + excerpt
                if end < len(self._page_text):
                    excerpt = excerpt + "…"
                matches.append({"match": True, "excerpt": excerpt})
                start = pos + len(query)

            if not matches:
                return [
                    {
                        "match": False,
                        "excerpt": f"No occurrences of '{query}' found on the page.",
                    }
                ]
            return matches

        return find_in_page

    def get_tools(self) -> List[UvTool]:
        return [self._find_tool]

    def get_system_prompt(self) -> str:
        return self._system_prompt or self.DEFAULT_SYSTEM_PROMPT


@plugin_settings(
    [
        {
            "key": "user_agent",
            "name": "HTTP User-Agent",
            "type": "str",
            "required": False,
            "description": "Custom User-Agent header for HTTP requests. Leave empty to use the httpx default.",
        },
        {
            "key": "max_content_length",
            "name": "Max Content Length",
            "type": "int",
            "default": DEFAULT_MAX_CONTENT_LENGTH,
            "required": False,
            "description": (
                "Maximum number of characters to keep from the page body text. "
                "Longer pages are truncated to this limit."
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
class WebpageReaderPlugin(BasePlugin):
    """Plugin that fetches a webpage and scopes conversation to its content.

    Scoped-only — does not participate in multi-agent orchestration.
    Requires a URL as the grounded mode resource_id.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="one.ifelse.webpage_reader_agent",
            name="Webpage Reader Agent",
            version="1.0.0",
            description=(
                "Fetches a webpage by URL and anchors the conversation to its content. "
                "Supports keyword search within the page. Designed for grounded mode only."
            ),
            capabilities=[
                "find_in_page: Search for keywords or phrases within the loaded webpage text",
            ],
            dependencies=[
                "cadence_sdk>=2.0.0,<3.0.0",
                "httpx>=0.27.0",
                "beautifulsoup4>=4.12.0",
            ],
            stateless=True,
        )

    @staticmethod
    def create_agent() -> WebpageReaderAgent:
        return WebpageReaderAgent()
