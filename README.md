# Cadence SDK 🤖

**Plugin Development Framework for Cadence AI Multi-Agent System**

[![PyPI version](https://badge.fury.io/py/cadence-sdk.svg)](https://badge.fury.io/py/cadence-sdk)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Cadence SDK provides a comprehensive framework for building custom AI agent plugins that integrate seamlessly with
the Cadence multi-agent conversational AI system. Built on LangChain and LangGraph, it offers powerful abstractions for
creating intelligent, tool-enabled agents with automatic routing and orchestration.

## 🚀 Features

- **🔌 Plugin Architecture**: Simple, extensible plugin system with automatic discovery
- **🤖 Agent Framework**: Complete agent lifecycle management with LangGraph integration
- **🛠️ Tool System**: Easy tool creation with the `@tool` decorator
- **📊 State Management**: Comprehensive state handling with type safety
- **🔄 Automatic Routing**: Intelligent agent-to-agent communication and routing
- **⚡ Parallel Execution**: Support for parallel tool calls for improved performance
- **🔍 Validation**: Built-in validation for plugins, agents, and tools
- **📝 Type Safety**: Full type hints and TypedDict support for robust development
- **🏥 Health Checks**: Built-in health monitoring and dependency validation
- **📦 Registry System**: Centralized plugin discovery and management

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install cadence-sdk
```

### From Source

```bash
git clone https://github.com/jonaskahn/cadence-sdk.git
cd cadence-sdk
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/jonaskahn/cadence-sdk.git
cd cadence-sdk
pip install -e ".[dev]"
```

## 🎯 Quick Start

### Basic Plugin Structure

```python
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, tool
from typing_extensions import Annotated, TypedDict


class SearchResponseSchema(TypedDict):
    """Schema for structured search responses"""
    title: Annotated[str, "Primary identifier or headline"]
    description: Annotated[str, "Contextual summary or metadata"]
    link: Annotated[str, "Canonical URI to the source"]
    thumbnail_link: Annotated[str, "Optional visual representation URI"]


class SearchPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="browse_internet",
            version="1.3.0",
            description="Internet Browser Search agent, using DuckDuckGo API",
            agent_type="specialized",
            response_schema=SearchResponseSchema,
            response_suggestion="When presenting search results, always include source citations with clickable links",
            capabilities=["web_search", "news_search", "image_search"],
            llm_requirements={
                "provider": "openai",
                "model": "gpt-4.1",
                "temperature": 0.2,
                "max_tokens": 1024,
            },
            dependencies=["cadence-sdk>=1.3.0,<2.0.0", "ddgs>=9.5.4,<10.0.0"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return SearchAgent(SearchPlugin.get_metadata())

    @staticmethod
    def health_check() -> dict:
        return {
            "healthy": True,
            "details": "Search plugin is operational",
            "checks": {"search_engine": "OK", "dependencies": "OK"},
        }


class SearchAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import search_tools
        return search_tools

    def get_system_prompt(self) -> str:
        return """You are the Search Agent, specialized in web search and information retrieval.

Your responsibilities:
    - Understand user search intent and information needs
    - Choose the most appropriate search tool for each query
    - Execute targeted searches with relevant keywords
    - Analyze and summarize search results clearly
    - Provide comprehensive, well-organized responses
    - Cite sources when presenting information
    - Always use the provided search decorators to find current information
"""


@tool
def web_search(query: str) -> str:
    """Search the web for information using DuckDuckGo.

    Args:
        query: The search query

    Returns:
        Search results from the web
    """
    try:
        from ddgs import DDGS
        results = DDGS().text(query)
        return results[:500]
    except Exception as e:
        return f"Web search error: {str(e)}"
```

### Plugin Registration

```python
from cadence_sdk import register_plugin
from .plugin import SearchPlugin

# Auto-register the plugin when imported
register_plugin(SearchPlugin)

# Or discover all plugins
from cadence_sdk import discover_plugins

plugins = discover_plugins()
```

## 📚 Core Components

### BasePlugin

The foundation of all Cadence plugins. Every plugin must implement:

- `get_metadata()`: Returns plugin metadata and configuration
- `create_agent()`: Creates and returns the plugin's agent instance
- `validate_dependencies()`: Optional dependency validation
- `health_check()`: Optional health monitoring

```python
class MyPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="Plugin description",
            capabilities=["capability1", "capability2"],
            agent_type="specialized",  # or "general", "utility"
            llm_requirements={
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 1024,
            },
            dependencies=["cadence-sdk>=1.3.0,<2.0.0"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MyAgent(MyPlugin.get_metadata())

    @staticmethod
    def validate_dependencies() -> list[str]:
        """Validate plugin dependencies."""
        errors = []
        # Add your validation logic
        return errors

    @staticmethod
    def health_check() -> dict:
        """Perform health check."""
        return {"healthy": True, "details": "Plugin is operational"}
```

### BaseAgent

The agent implementation that handles LLM interactions and tool execution:

```python
class MyAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata, parallel_tool_calls: bool = True):
        super().__init__(metadata, parallel_tool_calls)

    def get_tools(self) -> List[AgentTool]:
        """Return the decorators this agent exposes."""
        return [tool1, tool2, tool3]

    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        return "You are a helpful AI assistant."

    def initialize(self) -> None:
        """Initialize agent resources."""
        super().initialize()
        # Add custom initialization

    def cleanup(self) -> None:
        """Cleanup agent resources."""
        # Add custom cleanup
```

### PluginMetadata

Comprehensive metadata for plugin configuration:

```python
@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    llm_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    response_schema: Optional[Type[TypedDict]] = None
    response_suggestion: Optional[str] = None
    agent_type: str = "specialized"  # "specialized", "general", "utility"
    sdk_version: str = ">=1.3.0,<2.0.0"
```

### Tool System

Create tools using the `@tool` decorator:

```python
from cadence_sdk import tool
from ddgs import DDGS

@tool
def web_search(query: str) -> str:
    """Search the web for information using DuckDuckGo.

    Args:
        query: The search query

    Returns:
        Search results from the web
    """
    try:
        results = DDGS().text(query)
        return results[:500]
    except Exception as e:
        return f"Web search error: {str(e)}"

@tool
def search_news(query: str) -> str:
    """Search for recent news articles.

    Args:
        query: The news search query

    Returns:
        News search results
    """
    try:
        results = DDGS().news(query)
        return results[:500]
    except Exception as e:
        return f"News search error: {str(e)}"

@tool
def search_images(query: str) -> str:
    """Search for images and visual content related to the query.

    Args:
        query: The image search query

    Returns:
        Description of image search results
    """
    try:
        results = DDGS().images(query)
        return results[:500]
    except Exception as e:
        return f"Image search error: {str(e)}"

# Export decorators as a list for easy import
search_tools = [web_search, search_news, search_images]
```

## 🔄 State Management

The SDK provides comprehensive state management with type safety:

### AgentState

```python
class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    thread_id: Optional[str]
    current_agent: Optional[str]
    agent_hops: Optional[int]
    plugin_context: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    multi_agent: Optional[bool]
```

### State Helpers

```python
from cadence_sdk.types.state import StateHelpers, RoutingHelpers

# Safe state operations
messages = StateHelpers.safe_get_messages(state)
agent_hops = StateHelpers.safe_get_agent_hops(state)
plugin_context = StateHelpers.get_plugin_context(state)

# Update plugin context
updated_state = StateHelpers.update_plugin_context(
    state,
    routing_history=["agent1", "agent2"],
    tools_used=["tool1", "tool2"]
)

# Routing helpers
context = RoutingHelpers.add_to_routing_history(context, "my_agent")
context = RoutingHelpers.add_tool_used(context, "my_tool")
```

## 🔍 Validation

Built-in validation for plugins, agents, and tools:

```python
from cadence_sdk.utils.validation import (
    validate_plugin_structure,
    validate_plugin_structure_shallow,
    validate_metadata,
    validate_tools,
    validate_agent
)

# Validate plugin structure
errors = validate_plugin_structure(MyPlugin)
if errors:
    print(f"Validation errors: {errors}")

# Validate metadata
metadata = MyPlugin.get_metadata()
errors = validate_metadata(metadata)

# Validate decorators
tools = my_agent.get_tools()
errors = validate_tools(tools)
```

## 🏥 Health Monitoring

Implement health checks for your plugins:

```python
class MyPlugin(BasePlugin):
    @staticmethod
    def health_check() -> dict:
        """Perform comprehensive health check."""
        try:
            # Check dependencies
            import requests
            import numpy

            # Check external services
            response = requests.get("https://api.example.com/health", timeout=5)
            api_healthy = response.status_code == 200

            # Check configuration
            config_valid = os.getenv("MY_API_KEY") is not None

            return {
                "healthy": api_healthy and config_valid,
                "details": "All systems operational",
                "checks": {
                    "dependencies": "OK",
                    "api_connectivity": "OK" if api_healthy else "FAILED",
                    "configuration": "OK" if config_valid else "MISSING_API_KEY",
                },
            }

    except Exception as e:
    return {
        "healthy": False,
        "details": f"Health check failed: {e}",
        "error": str(e),
    }
```

## 🔧 Advanced Features

### Parallel Tool Execution

Enable parallel tool calls for improved performance:

```python
class MyAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        # Enable parallel tool calls (default: True)
        super().__init__(metadata, parallel_tool_calls=True)
```

### Custom Model Configuration

Configure LLM requirements in plugin metadata:

```python
def get_metadata() -> PluginMetadata:
    return PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="Plugin with custom LLM config",
        llm_requirements={
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 2048,
            "additional_params": {
                "top_p": 0.9,
                "frequency_penalty": 0.1,
            }
        },
    )
```

### Response Schemas

Define structured response schemas:

```python
from typing_extensions import Annotated, TypedDict


class SearchResponseSchema(TypedDict):
    """Unified schema for representing heterogeneous search response entities"""

    title: Annotated[
        str,
        "Primary identifier or headline of the search result. For news articles: the article headline; for images: descriptive caption or filename; for general search: the page title or primary heading that encapsulates the content's essence",
    ]

    description: Annotated[
        str,
        "Contextual summary or metadata providing substantive insight into the search result. For news: article excerpt or lead paragraph; for images: alt text, caption, or contextual description; for general search: meta description or extracted content snippet that offers semantic understanding of the result's relevance",
    ]

    link: Annotated[
        str,
        "Canonical URI representing the authoritative source location. This serves as the primary navigation endpoint, ensuring consistent access to the original resource regardless of search result type or content modality",
    ]

    thumbnail_link: Annotated[
        str,
        "Optional visual representation URI for enhanced user experience. For images: compressed preview version; for news articles: featured image or publication logo; for general search: favicon, screenshot, or representative visual element that aids in result recognition and selection",
    ]


class SearchPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="browse_internet",
            version="1.3.0",
            description="Internet Browser Search agent, using DuckDuckGo API",
            response_schema=SearchResponseSchema,
            response_suggestion="When presenting search results, always include source citations with clickable links, organize information by relevance and recency, provide context about the credibility of sources, and offer follow-up search suggestions when appropriate.",
        )
```

## 📁 Project Structure

### SDK Structure

```
cadence_sdk/
├── base/                  # Core base classes
│   ├── agent.py           # BaseAgent implementation
│   ├── plugin.py          # BasePlugin interface
│   ├── metadata.py        # PluginMetadata and ModelConfig
│   └── loggable.py        # Logging utilities
├── registry/              # Plugin discovery and management
│   ├── plugin_registry.py # PluginRegistry implementation
│   └── contracts.py       # Plugin contracts
├── tools/                 # Tool system
│   ├── decorators.py      # @tool decorator
│   └── __init__.py        # Tool type definitions
├── types/                 # Type definitions
│   ├── state.py           # AgentState and helpers
│   └── messages.py        # Message types
├── utils/                 # Utility functions
│   ├── validation.py      # Validation utilities
│   ├── helpers.py         # General helpers
│   ├── installers.py      # Installation utilities
│   └── environment_discovery.py  # Environment detection
└── examples/              # Example implementations
    └── template_plugin/   # Template plugin example
```

### Plugin Structure (Real Example)

Based on the search_agent implementation:

```
search_agent/
├── __init__.py            # Auto-registration
├── plugin.py              # Plugin class and metadata
├── agent.py               # Agent implementation
└── tools.py               # Tool definitions
```

**Key Files:**

- **`__init__.py`**: Auto-registers the plugin when imported
- **`plugin.py`**: Contains the `BasePlugin` implementation with metadata
- **`agent.py`**: Contains the `BaseAgent` implementation with system prompt
- **`tools.py`**: Contains tool definitions using `@tool` decorator

## 🧪 Testing

The SDK includes comprehensive testing utilities:

```python
# Test plugin structure
def test_plugin_structure():
    errors = validate_plugin_structure(MyPlugin)
    assert not errors, f"Plugin validation failed: {errors}"


# Test agent creation
def test_agent_creation():
    agent = MyPlugin.create_agent()
    assert isinstance(agent, BaseAgent)

    tools = agent.get_tools()
    assert len(tools) > 0

    system_prompt = agent.get_system_prompt()
    assert isinstance(system_prompt, str)


# Test tool validation
def test_tools():
    agent = MyPlugin.create_agent()
    tools = agent.get_tools()
    errors = validate_tools(tools)
    assert not errors, f"Tool validation failed: {errors}"
```

## 🔗 Integration with Cadence Core

The SDK is designed to integrate seamlessly with the Cadence core system:

1. **Automatic Discovery**: Plugins are automatically discovered and registered
2. **LangGraph Integration**: Agents work as LangGraph nodes out of the box
3. **State Synchronization**: State is automatically synchronized between agents
4. **Tool Binding**: Tools are automatically bound to LLM models
5. **Routing Logic**: Built-in routing decisions for agent-to-agent communication

## 📖 Examples

### Complete Plugin Example

See the `examples/template_plugin/` directory for a complete working example that demonstrates:

- Plugin metadata configuration
- Agent implementation with multiple tools
- Tool creation and validation
- Health checks and dependency validation
- Best practices for plugin development

### Real-World Plugin Ideas

- **Web Search Agent**: Search the web and return structured results
- **Code Analysis Agent**: Analyze code and provide suggestions
- **Data Processing Agent**: Process and transform data
- **API Integration Agent**: Integrate with external APIs
- **File Management Agent**: Handle file operations
- **Database Agent**: Query and manipulate databases

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on [LangChain](https://langchain.com/) for LLM integration
- Powered by [LangGraph](https://langchain.com/langgraph) for agent orchestration
- Type safety with [Pydantic](https://pydantic.dev/) and Python typing
- Plugin architecture inspired by modern plugin systems

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jonaskahn/cadence-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jonaskahn/cadence-sdk/discussions)
- **Documentation**: [Read the Docs](https://cadence-sdk.readthedocs.io/)

---

**Made with ❤️ by the Cadence AI Team**

_Build intelligent agents that work together seamlessly with the Cadence SDK._
