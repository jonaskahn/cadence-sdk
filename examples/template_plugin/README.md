# Template Plugin

This is a complete example plugin demonstrating Cadence SDK v3.0 features.

## Features Demonstrated

1. **Plugin Structure**
   - BasePlugin implementation
   - BaseAgent implementation
   - Metadata declaration

2. **Tools**
   - Synchronous tools (`@uvtool`)
   - Asynchronous tools (`@uvtool` on async functions)
   - Cached tools (`@uvtool(cache=...)` with CacheConfig)

3. **Settings**
   - Settings schema declaration (`@plugin_settings`)
   - Required and optional settings
   - Sensitive settings (api_key)
   - Settings initialization

4. **Agent Lifecycle**
   - `initialize()` for configuration
   - `cleanup()` for resource management
   - `get_tools()` for tool discovery
   - `get_system_prompt()` for prompt generation

## Usage

### Basic Usage

```python
from template_plugin import TemplatePlugin

# Get metadata
metadata = TemplatePlugin.get_metadata()
print(f"Plugin: {metadata.name} v{metadata.version}")
print(f"Capabilities: {metadata.capabilities}")

# Create agent
agent = TemplatePlugin.create_agent()

# Initialize with config
config = {
    "greeting": "Hi",
    "max_results": 5,
    "api_key": "sk-test-key"
}
agent.initialize(config)

# Get tools
tools = agent.get_tools()
print(f"Available tools: {[tool.name for tool in tools]}")

# Use a tool
greet_tool = next(t for t in tools if t.name == "greet")
result = greet_tool(name="World")
print(result)  # "Hi, World!"
```

### Tool Caching Example

The search tool demonstrates semantic caching:

```python
from cadence_sdk import uvtool, CacheConfig

@uvtool(cache=CacheConfig(ttl=3600, similarity_threshold=0.7))
def search(query: str) -> str:
    """Cached search - similar queries return cached results."""
    return perform_expensive_search(query)
```

Cache configuration:
- **TTL**: 3600 seconds (1 hour)
- **Similarity Threshold**: 0.7 (70% similarity for cache hits)
- **Cache Key Fields**: None (all parameters used)

### Async Tool Example

```python
# Get async tool
async_tool = next(t for t in tools if t.name == "async_fetch")

# Use async tool
result = await async_tool.ainvoke(url="https://example.com")
print(result)
```

## Registration

To register this plugin with the Cadence SDK:

```python
from cadence_sdk import register_plugin
from template_plugin import TemplatePlugin

register_plugin(TemplatePlugin)
```

## Plugin Tools

### 1. greet
- **Type**: Synchronous
- **Caching**: None
- **Description**: Greets a user by name
- **Parameters**:
  - `name` (str): Name of person to greet

### 2. search
- **Type**: Synchronous
- **Caching**: Enabled (1 hour TTL, 0.7 similarity)
- **Description**: Search for information (cached)
- **Parameters**:
  - `query` (str): Search query

### 3. async_fetch
- **Type**: Asynchronous
- **Caching**: None
- **Description**: Asynchronously fetch data from URL
- **Parameters**:
  - `url` (str): URL to fetch

## Settings Schema

The plugin declares the following settings:

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `greeting` | str | No | "Hello" | Greeting message to use |
| `max_results` | int | No | 10 | Maximum number of search results |
| `enable_cache` | bool | No | true | Enable result caching |
| `api_key` | str | **Yes** | - | API key for external service (sensitive) |

## Testing

Run the test suite to verify plugin functionality:

```bash
cd examples
python test_sdk.py
```

All tests should pass:
- ✓ Imports
- ✓ Plugin Structure
- ✓ Tool Execution (sync and async)
- ✓ Registration
- ✓ Validation
- ✓ Messages
- ✓ State

## Notes

- This plugin has **NO external dependencies** (`dependencies=[]`)
- All tools are **stateless** (`stateless=True`)
- The plugin demonstrates **best practices for SDK v3.0**
- **Framework-agnostic**: works with LangGraph, OpenAI Agents, and Google ADK
- Uses the new **integrated cache API** (no separate decorator needed)
