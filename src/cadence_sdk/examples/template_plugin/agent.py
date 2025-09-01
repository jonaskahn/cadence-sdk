"""Template agent implementation."""

from typing import List

from cadence_sdk import BaseAgent, tool
from cadence_sdk.base.metadata import PluginMetadata


class TemplateAgent(BaseAgent):
    """Template agent demonstrating SDK usage."""

    def __init__(self, metadata: PluginMetadata, parallel_tool_calls: bool = False):
        """Initialize template agent."""
        super().__init__(metadata, parallel_tool_calls)

    def get_tools(self) -> List:
        """Get available tools for this agent."""
        return [
            template_tool,
            cadence_tool,
            format_text_tool,
        ]

    def get_system_prompt(self) -> str:
        """Get system prompt for this agent."""
        return (
            "You are the Template Agent, a demonstration agent for the Cadence Plugin SDK. "
            "You have access to template tools for example operations. "
            "Your purpose is to show how to build plugins using the SDK. "
            "Always be helpful and demonstrate best practices for tool usage."
        )


@tool
def template_tool(operation: str, data: str) -> str:
    """Perform a template operation on data.

    Args:
        operation: Type of operation to perform
        data: Data to process

    Returns:
        str: Processed result
    """
    operations = {
        "uppercase": data.upper(),
        "lowercase": data.lower(),
        "reverse": data[::-1],
        "length": f"Length: {len(data)}",
        "words": f"Word count: {len(data.split())}",
    }

    result = operations.get(operation, f"Unknown operation: {operation}")
    return f"Template operation '{operation}' result: {result}"


@tool
def cadence_tool(message: str) -> str:
    """Cadence a message back.

    Args:
        message: Message to cadence

    Returns:
        str: Cadenceed message
    """
    return f"Cadence: {message}"


@tool
def format_text_tool(text: str, format_type: str = "markdown") -> str:
    """Format text in specified format.

    Args:
        text: Text to format
        format_type: Format type (markdown, html, plain)

    Returns:
        str: Formatted text
    """
    formatters = {
        "markdown": f"**{text}**",
        "html": f"<strong>{text}</strong>",
        "plain": text,
        "code": f"`{text}`",
        "quote": f'"{text}"',
    }

    formatted = formatters.get(format_type, text)
    return f"Formatted as {format_type}: {formatted}"
