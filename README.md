# Cadence SDK

**Framework-agnostic plugin development kit for multi-tenant AI agent platforms**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/cadence-sdk.svg)](https://badge.fury.io/py/cadence-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Cadence SDK is a Python library that enables developers to build AI agent plugins that work seamlessly across multiple
orchestration frameworks (LangGraph, OpenAI Agents SDK, Google ADK) without framework-specific code.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Plugin Development](#plugin-development)
- [Tool Development](#tool-development)
- [Caching](#caching)
- [State Management](#state-management)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Contributing](#contributing)

## Features

### 🎯 Framework-Agnostic Design

Write your plugin once, run it on any supported orchestration framework:

- **LangGraph** (LangChain-based)
- **OpenAI Agents SDK**
- **Google ADK** (Agent Development Kit)

### 🔧 Simple Tool Declaration

Define tools with a single decorator - no framework-specific code:

```python
@uvtool
def search(query: str) -> str:
    """Search for information."""
    return perform_search(query)
```

### 💾 Integrated Caching

Built-in semantic caching for expensive operations:

```python
@uvtool(cache=CacheConfig(ttl=3600, similarity_threshold=0.85))
def expensive_api_call(query: str) -> str:
    """Cached API call."""
    return call_external_api(query)
```

### 🔌 Plugin System

- **Plugin discovery** from multiple sources (pip packages, directories, system-wide)
- **Settings schema** with type validation
- **Dependency management** with auto-installation
- **Version conflict resolution**
- **Health checks** and lifecycle management

### 📦 Type Safety

Fully typed with Pydantic for excellent IDE support and runtime validation.

### ⚡ Async Support

First-class support for async tools with automatic detection and invocation.

## Installation

### From PyPI (when published)

```bash
pip install cadence-sdk
```

### From Source

```bash
git clone https://github.com/jonaskahn/cadence-sdk.git
cd cadence-sdk
poetry install
```

### Development Installation

```bash
poetry install --with dev
```

## Quick Start

### 1. Create Your First Plugin

```python
# my_plugin/plugin.py
from cadence_sdk import (
    BasePlugin, BaseAgent, PluginMetadata,
    uvtool, UvTool, plugin_settings
)
from typing import List


class MyAgent(BaseAgent):
    """My custom agent."""

    @uvtool
    def greet(self, name: str) -> str:
        """Greet a user by name."""
        return f"Hello, {name}!"

    @uvtool(cache=True)  # Enable caching with defaults
    def search(self, query: str) -> str:
        """Search for information (cached)."""
        # Your search implementation
        return f"Results for: {query}"

    def get_tools(self) -> List[UvTool]:
        """Return list of tools."""
        return [self.greet, self.search]

    def get_system_prompt(self) -> str:
        """Return system prompt."""
        return "You are a helpful assistant."


@plugin_settings([
    {
        "key": "api_key",
        "type": "str",
        "required": True,
        "sensitive": True,
        "description": "API key for external service"
    }
])
class MyPlugin(BasePlugin):
    """My custom plugin."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.example.my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="My awesome plugin",
            capabilities=["greeting", "search"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MyAgent()
```

### 2. Register Your Plugin

```python
from cadence_sdk import register_plugin
from my_plugin import MyPlugin

# Register plugin
register_plugin(MyPlugin)
```

### 3. Use Your Plugin

Your plugin is now ready to be loaded by the Cadence platform and will work with any supported orchestration framework!

## Core Concepts

### Plugins

Plugins are factory classes that create agent instances. They declare metadata, settings schema, and provide health
checks. The `pid` (plugin ID) is a required reverse-domain identifier (e.g., `com.example.my_plugin`) used as the
registry key.

```python
class MyPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            pid="com.example.my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="Description",
            capabilities=["cap1", "cap2"],
            dependencies=["requests>=2.0"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        """Create and return agent instance."""
        return MyAgent()
```

### Agents

Agents provide tools and system prompts. They can maintain state and be initialized with configuration.

```python
class MyAgent(BaseAgent):
    def initialize(self, config: dict) -> None:
        """Initialize with configuration."""
        self.api_key = config.get("api_key")

    def get_tools(self) -> List[UvTool]:
        """Return available tools."""
        return [self.tool1, self.tool2]

    def get_system_prompt(self) -> str:
        """Return system prompt."""
        return "You are a helpful assistant."

    async def cleanup(self) -> None:
        """Clean up resources."""
        # Close connections, etc.
        pass
```

### Tools

Tools are functions that agents can invoke. They can be synchronous or asynchronous.

```python
from cadence_sdk import uvtool, CacheConfig
from pydantic import BaseModel


# Simple tool
@uvtool
def simple_tool(text: str) -> str:
    """A simple tool."""
    return text.upper()


# Tool with args schema
class SearchArgs(BaseModel):
    query: str
    limit: int = 10


@uvtool(args_schema=SearchArgs)
def search(query: str, limit: int = 10) -> str:
    """Search with validation."""
    return f"Top {limit} results for: {query}"


# Cached tool
@uvtool(cache=CacheConfig(
    ttl=3600,
    similarity_threshold=0.85,
    cache_key_fields=["query"]  # Only cache by query
))
def expensive_search(query: str, options: dict = None) -> str:
    """Expensive operation with selective caching."""
    return perform_expensive_search(query, options)


# Async tool
@uvtool
async def async_fetch(url: str) -> str:
    """Asynchronous tool."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

### Messages

Framework-agnostic message types for agent communication:

```python
from cadence_sdk import (
    UvHumanMessage,
    UvAIMessage,
    UvSystemMessage,
    UvToolMessage,
    ToolCall
)

# Human message
human = UvHumanMessage(content="Hello!")

# AI message with tool calls
ai = UvAIMessage(
    content="Let me search for that.",
    tool_calls=[
        ToolCall(name="search", args={"query": "Python"})
    ]
)

# System message
system = UvSystemMessage(content="You are helpful.")

# Tool result message
tool_result = UvToolMessage(
    content="Search results: ...",
    tool_call_id="call_123",
    tool_name="search"
)
```

### State

Unified state management across frameworks:

```python
from cadence_sdk import UvState, StateHelpers, create_initial_state

# Create initial state
state = create_initial_state(
    messages=[UvHumanMessage(content="Hello")],
    thread_id="thread_123"
)

# Use state helpers
thread_id = StateHelpers.safe_get_thread_id(state)
messages = StateHelpers.safe_get_messages(state)
hops = StateHelpers.safe_get_agent_hops(state)

# Update state
state = StateHelpers.increment_agent_hops(state)
update = StateHelpers.create_state_update(current_agent="my_agent")
state = {**state, **update}
```

## Plugin Development

### Settings Declaration

Declare settings schema for your plugin:

```python
from cadence_sdk import plugin_settings


@plugin_settings([
    {
        "key": "api_key",
        "type": "str",
        "required": True,
        "sensitive": True,
        "description": "API key for service"
    },
    {
        "key": "max_results",
        "type": "int",
        "default": 10,
        "required": False,
        "description": "Maximum results to return"
    },
    {
        "key": "endpoints",
        "type": "list",
        "default": ["https://api.example.com"],
        "description": "API endpoints"
    }
])
class MyPlugin(BasePlugin):
    pass
```

### Agent Initialization

Agents receive resolved settings during initialization:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        self.api_key = None
        self.max_results = 10

    def initialize(self, config: dict) -> None:
        """Initialize with resolved configuration.

        Config contains:
        - Declared settings with defaults applied
        - User-provided overrides
        - Framework-resolved values
        """
        self.api_key = config["api_key"]
        self.max_results = config.get("max_results", 10)
```

### Resource Cleanup

Implement cleanup for proper resource management:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        self.db_connection = None
        self.http_client = None

    async def cleanup(self) -> None:
        """Clean up resources when agent is disposed."""
        if self.db_connection:
            await self.db_connection.close()

        if self.http_client:
            await self.http_client.aclose()
```

## Tool Development

### Basic Tool

```python
@uvtool
def greet(name: str) -> str:
    """Greet a user by name.

    Args:
        name: Name of the person to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"
```

### Tool with Schema Validation

```python
from pydantic import BaseModel, Field


class SearchArgs(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Max results")
    filters: dict = Field(default_factory=dict, description="Search filters")


@uvtool(args_schema=SearchArgs)
def search(query: str, limit: int = 10, filters: dict = None) -> str:
    """Search with validated arguments."""
    # Arguments are validated against SearchArgs schema
    return perform_search(query, limit, filters or {})
```

### Async Tool

```python
@uvtool
async def fetch_data(url: str) -> dict:
    """Asynchronously fetch data from URL.

    The SDK automatically detects async functions and handles
    invocation correctly.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


# Invoke async tool
result = await fetch_data.ainvoke(url="https://api.example.com")
```

### Tool Invocation

```python
# Sync tool - direct call
result = greet(name="Alice")

# Sync tool - explicit invoke
result = greet.invoke(name="Alice")

# Async tool - must use ainvoke
result = await fetch_data.ainvoke(url="https://example.com")

# Check if tool is async
if fetch_data.is_async:
    result = await fetch_data.ainvoke(...)
else:
    result = fetch_data(...)
```

## Caching

### Cache Configuration

```python
from cadence_sdk import uvtool, CacheConfig


# Method 1: CacheConfig instance (recommended)
@uvtool(cache=CacheConfig(
    ttl=3600,  # Cache for 1 hour
    similarity_threshold=0.85,  # 85% similarity for cache hits
    cache_key_fields=["query"]  # Only cache by query parameter
))
def cached_search(query: str, limit: int = 10) -> str:
    """Different limits use same cached result."""
    return expensive_search(query, limit)


# Method 2: Dictionary
@uvtool(cache={
    "ttl": 7200,
    "similarity_threshold": 0.9
})
def another_cached_tool(text: str) -> str:
    return process(text)


# Method 3: Boolean (use defaults)
@uvtool(cache=True)  # TTL=3600, threshold=0.85
def simple_cached_tool(input: str) -> str:
    return expensive_operation(input)


# Disable caching
@uvtool(cache=False)
# or simply:
@uvtool
def no_cache_tool(data: str) -> str:
    return realtime_data()
```

### Cache Configuration Options

| Field                  | Type      | Default | Description                              |
|------------------------|-----------|---------|------------------------------------------|
| `enabled`              | bool      | `True`  | Whether caching is enabled               |
| `ttl`                  | int       | `3600`  | Time-to-live in seconds                  |
| `similarity_threshold` | float     | `0.85`  | Cosine similarity threshold (0.0-1.0)    |
| `cache_key_fields`     | List[str] | `None`  | Fields to use for cache key (None = all) |

### How Caching Works

1. **Semantic Matching**: Uses embeddings to find similar queries
2. **Threshold**: Only returns cached results above similarity threshold
3. **TTL**: Cached results expire after TTL seconds
4. **Selective Keys**: Cache only by specific parameters

Example:

```python
@uvtool(cache=CacheConfig(
    ttl=3600,
    similarity_threshold=0.85,
    cache_key_fields=["query"]
))
def search(query: str, limit: int = 10, format: str = "json") -> str:
    """Cache by query only, ignore limit and format."""
    pass


# These will use the same cached result:
search("Python programming", limit=10, format="json")
search("Python programming", limit=50, format="xml")

# This might get a cache hit if similarity > 0.85:
search("Python coding", limit=10, format="json")
```

## State Management

### Creating State

```python
from cadence_sdk import create_initial_state, UvHumanMessage

state = create_initial_state(
    messages=[
        UvHumanMessage(content="Hello")
    ],
    thread_id="thread_123",
    metadata={"user_id": "user_456"}
)
```

### Reading State

```python
from cadence_sdk import StateHelpers

# Safe getters (return None if not present)
thread_id = StateHelpers.safe_get_thread_id(state)
messages = StateHelpers.safe_get_messages(state)
agent_hops = StateHelpers.safe_get_agent_hops(state)
current_agent = StateHelpers.safe_get_current_agent(state)
metadata = StateHelpers.safe_get_metadata(state)

# Plugin context
context = StateHelpers.get_plugin_context(state)
routing_history = context.get("routing_history", [])
tools_used = context.get("tools_used", [])
```

### Updating State

```python
from cadence_sdk import StateHelpers, RoutingHelpers

# Increment agent hops
state = StateHelpers.increment_agent_hops(state)

# Create state update (returns dict to merge)
update = StateHelpers.create_state_update(
    current_agent="my_agent",
    metadata={"step": "processing"}
)
state = {**state, **update}

# Update plugin context
state = StateHelpers.update_plugin_context(
    state,
    {"custom_data": "value"}
)

# Routing helpers
state = RoutingHelpers.add_to_routing_history(state, "agent1")
state = RoutingHelpers.add_tool_used(state, "search")
```

## Examples

### Complete Plugin Example

See the [template_plugin](examples/template_plugin/) for a complete, working example that demonstrates:

- Plugin and agent structure
- Sync and async tools
- Caching configuration
- Settings schema
- State management
- Resource cleanup

### Running the Example

```bash
# From cadence-sdk root, with SDK on path
cd cadence-sdk
PYTHONPATH=src python examples/test_sdk.py
```

### Running the Test Suite

```bash
cd cadence-sdk
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/ -v
```

## API Reference

### Core Classes

#### `BasePlugin`

Abstract base class for plugins.

**Methods:**

- `get_metadata()` (static) → `PluginMetadata`: Return plugin metadata
- `create_agent()` (static) → `BaseAgent`: Create agent instance
- `validate_dependencies()` (static) → `List[str]`: Validate dependencies
- `health_check()` (static) → `dict`: Perform health check

#### `BaseAgent`

Abstract base class for agents.

**Methods:**

- `get_tools()` → `List[UvTool]`: Return list of tools (required)
- `get_system_prompt()` → `str`: Return system prompt (required)
- `initialize(config: dict)` → `None`: Initialize with config (optional)
- `cleanup()` → `None`: Clean up resources (optional)

#### `UvTool`

Tool wrapper class.

**Attributes:**

- `name`: Tool name
- `description`: Tool description
- `func`: Underlying callable
- `args_schema`: Pydantic model for arguments
- `cache`: Cache configuration
- `metadata`: Additional metadata
- `is_async`: Whether tool is async

**Methods:**

- `__call__(*args, **kwargs)`: Sync invocation
- `ainvoke(*args, **kwargs)`: Async invocation
- `invoke(*args, **kwargs)`: Sync invocation alias

#### `CacheConfig`

Cache configuration dataclass.

**Fields:**

- `enabled` (bool): Whether caching is enabled
- `ttl` (int): Time-to-live in seconds
- `similarity_threshold` (float): Similarity threshold (0.0-1.0)
- `cache_key_fields` (Optional[List[str]]): Fields for cache key

### Message Types

- `UvHumanMessage`: User message
- `UvAIMessage`: Assistant message (with optional tool calls)
- `UvSystemMessage`: System message
- `UvToolMessage`: Tool result message
- `ToolCall`: Tool invocation record

### Decorators

#### `@uvtool`

Convert function to UvTool.

**Parameters:**

- `name` (str, optional): Tool name (default: function name)
- `description` (str, optional): Description (default: docstring)
- `args_schema` (Type[BaseModel], optional): Pydantic model for validation
- `cache` (Union[CacheConfig, bool, dict], optional): Cache configuration
- `**metadata`: Additional metadata

#### `@plugin_settings`

Declare plugin settings schema.

**Parameters:**

- `settings` (List[dict]): List of setting definitions

**Setting Definition:**

- `key` (str): Setting key
- `type` (str): Type ("str", "int", "float", "bool", "list", "dict")
- `default` (Any, optional): Default value
- `description` (str): Setting description
- `required` (bool): Whether setting is required
- `sensitive` (bool): Whether value is sensitive (e.g., API key)

### Utility Functions

- `register_plugin(plugin_class)`: Register plugin
- `discover_plugins(search_paths, auto_register=True)`: Discover plugins in directory or list of directories
- `validate_plugin_structure(plugin_class)`: Validate plugin structure
- `create_initial_state(...)`: Create initial UvState

## Best Practices

### 1. Keep Plugins Stateless

When possible, design plugins to be stateless (`stateless=True` in metadata). This allows the framework to share plugin
instances across multiple orchestrators for better memory efficiency.

```python
PluginMetadata(
    pid="com.example.my_plugin",
    name="My Plugin",
    version="1.0.0",
    description="Plugin description",
    stateless=True,  # Enable sharing
)
```

### 2. Use Type Hints

Always use type hints for better IDE support and runtime validation:

```python
@uvtool
def my_tool(query: str, limit: int = 10) -> str:
    """Type hints improve IDE support."""
    return search(query, limit)
```

### 3. Provide Good Descriptions

Tools and plugins should have clear, concise descriptions:

```python
@uvtool
def search(query: str) -> str:
    """Search for information using the external API.

    This tool performs semantic search across our knowledge base
    and returns the top matching results.

    Args:
        query: The search query string

    Returns:
        Formatted search results
    """
    return perform_search(query)
```

### 4. Handle Errors Gracefully

```python
@uvtool
def api_call(endpoint: str) -> str:
    """Make API call with proper error handling."""
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"Error: {str(e)}"
```

### 5. Use Selective Caching

Only cache by parameters that affect the result:

```python
@uvtool(cache=CacheConfig(
    cache_key_fields=["query", "language"],  # Ignore format, limit
))
def translate(query: str, language: str, format: str = "text", limit: int = 100) -> str:
    """Cache by query and language only."""
    pass
```

### 6. Clean Up Resources

Always implement cleanup for resources:

```python
class MyAgent(BaseAgent):
    async def cleanup(self) -> None:
        """Clean up connections and resources."""
        if hasattr(self, 'db'):
            await self.db.close()
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()
```

### 7. Version Your Plugins

Use semantic versioning and declare dependencies explicitly:

```python
PluginMetadata(
    pid="com.example.my_plugin",
    name="My Plugin",
    version="1.2.3",  # Semantic versioning
    description="Plugin description",
    sdk_version=">=3.0.0,<4.0.0",  # Compatible SDK versions
    dependencies=["requests>=2.28.0", "aiohttp>=3.8.0"],
)
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/jonaskahn/cadence-sdk.git
cd cadence-sdk

# Install with development dependencies
poetry install --with dev

# Run tests
PYTHONPATH=src python -m pytest tests/

# Run linting
poetry run black .
poetry run isort .
poetry run mypy .
```

### Running Tests

```bash
# All tests
PYTHONPATH=src python -m pytest tests/

# With coverage
PYTHONPATH=src python -m pytest tests/ --cov=cadence_sdk --cov-report=term-missing

# Specific test file
PYTHONPATH=src python -m pytest tests/test_sdk_tools.py -v

# Run example script
PYTHONPATH=src python examples/test_sdk.py
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://docs.cadence.dev](https://docs.cadence.dev)
- **Issues**: [GitHub Issues](https://github.com/jonaskahn/cadence-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jonaskahn/cadence-sdk/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**Built with ❤️ for the AI agent development community**
