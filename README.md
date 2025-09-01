# Cadence SDK

A comprehensive SDK for building custom AI agent plugins for the Cadence Framework.

## Overview

The Cadence SDK provides the tools and interfaces needed to create powerful, extensible AI agents that integrate
seamlessly with the Cadence multi-agent framework. Build agents with custom tools, sophisticated reasoning capabilities,
and domain-specific knowledge.

## Features

- **Agent Framework**: Create intelligent agents with custom behavior and system prompts
- **Tool System**: Build and integrate custom tools using the `@tool` decorator
- **Plugin Management**: Easy plugin discovery and registration with automatic loading
- **Type Safety**: Full Python type support with proper annotations
- **Extensible**: Plugin-based architecture for easy extension and customization
- **LangGraph Integration**: Seamless integration with LangGraph workflows
- **LLM Binding**: Automatic tool binding to language models

## Installation

```bash
pip install cadence-sdk
```

## Quick Start

### Key Imports

```python
# Core classes - import from main SDK module (recommended)
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, tool, register_plugin

# Alternative: import specific components if needed
from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.plugin import BasePlugin
from cadence_sdk.base.metadata import PluginMetadata
from cadence_sdk.tools.decorators import tool
from cadence_sdk import register_plugin, discover_plugins
```

**Note**: The main import approach is recommended for most use cases as it provides all necessary components in one import statement.

### Creating a Simple Agent

```python
from cadence_sdk import BaseAgent, PluginMetadata, tool


class CalculatorAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import math_tools
        return math_tools

    def get_system_prompt(self) -> str:
        return "You are a calculator agent that helps with mathematical calculations."


@tool
def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
```

### Plugin Structure

```
my_plugin/
├── __init__.py          # Plugin registration with register_plugin()
├── plugin.py            # Main plugin class (BasePlugin)
├── agent.py             # Agent implementation (BaseAgent)
├── tools.py             # Tool functions with @tool decorator
├── pyproject.toml       # Package configuration
└── README.md            # Documentation
```

**Required Files:**

- `__init__.py`: Must call `register_plugin(YourPlugin)` to auto-register the plugin
- `plugin.py`: Must implement `BasePlugin` with `get_metadata()` and `create_agent()` methods
- `agent.py`: Must implement `BaseAgent` with `get_tools()` and `get_system_prompt()` methods
- `tools.py`: Contains tool functions decorated with `@tool` decorator
- `pyproject.toml`: Package metadata and dependencies

### Plugin Registration

```python
from cadence_sdk import BasePlugin, PluginMetadata


class CalculatorPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="calculator",
            version="1.0.3",
            description="Mathematical calculation plugin",
            capabilities=["mathematics", "calculations"],
            llm_requirements={
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1
            },
            agent_type="specialized",
            dependencies=["cadence_sdk>=1.0.2,<2.0.0"]
        )

    @staticmethod
    def create_agent():
        from .agent import CalculatorAgent
        return CalculatorAgent(CalculatorPlugin.get_metadata())
```

## Configuration

### Plugin Registration

To make your plugin discoverable by the Cadence framework, you need to register it in your plugin's `__init__.py`:

```python
# plugins/src/cadence_example_plugins/my_plugin/__init__.py
from cadence_sdk import register_plugin
from .plugin import MyPlugin

# Register on import
register_plugin(MyPlugin)
```

### Environment Variables

```bash
# Set plugin directories (single path)
export CADENCE_PLUGINS_DIR="./plugins/src/cadence_plugins"

# Or multiple directories as JSON array
export CADENCE_PLUGINS_DIR='["/path/to/plugins", "/another/path"]'

# Plugin limits (configured in main application)
export CADENCE_MAX_AGENT_HOPS=25

export CADENCE_GRAPH_RECURSION_LIMIT=50

# LLM Provider Configuration
export CADENCE_DEFAULT_LLM_PROVIDER=openai
export CADENCE_OPENAI_API_KEY=your-api-key
```

### Plugin Discovery

The SDK automatically discovers plugins from:

- **Environment packages**: Pip-installed packages that depend on `cadence_sdk`
- **Directory paths**: File system directories specified in `CADENCE_PLUGINS_DIR`
- **Custom registries**: Programmatic plugin registration via `register_plugin()`

**Auto-registration**: When a plugin package is imported, it automatically calls `register_plugin()` to make itself available to the framework.

## Advanced Usage

### Custom Tool Decorators

```python
from cadence_sdk import tool


@tool
def weather_tool(city: str) -> str:
    """Get weather information for a city."""
    # Implementation here
    return f"Weather for {city}: Sunny, 72°F"


# Tools are automatically registered when using the decorator
weather_tools = [weather_tool]
```

### Agent State Management

```python
from cadence_sdk import BaseAgent, PluginMetadata


class StatefulAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        return []

    def get_system_prompt(self) -> str:
        return "You are a stateful agent that maintains context."

    def should_continue(self, state: dict) -> str:
        """Decide whether to continue processing or return to coordinator."""
        # Access conversation history
        history = state.get("messages", [])

        # Update state if needed
        if len(history) > 10:
            return "back"  # Return to coordinator

        return "continue"  # Continue processing
```

**State Management**: The `should_continue` method allows agents to control workflow flow by returning:

- `"continue"`: Keep processing with current agent
- `"back"`: Return control to the coordinator

### Plugin Registry

```python
from cadence_sdk import PluginRegistry

# Get plugin registry
registry = PluginRegistry()

# Register custom plugin
registry.register(CalculatorPlugin())

# Discover plugins
plugins = registry.discover()

# Get specific plugin
calculator_plugin = registry.get_plugin("calculator")
```

**Registry Features**: The plugin registry provides:

- Automatic plugin discovery and loading
- Plugin validation and health checks
- Metadata access and plugin management
- Integration with the main Cadence framework

## Examples

### Math Agent

```python
from cadence_sdk import BaseAgent, PluginMetadata, tool


class MathAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import math_tools
        return math_tools

    def get_system_prompt(self) -> str:
        return "You are a math agent specialized in mathematical operations. Use the calculator tool for calculations."


@tool
def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Invalid expression: {str(e)}"


@tool
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


math_tools = [calculate, add]
```

### Search Agent

```python
from cadence_sdk import BaseAgent, PluginMetadata, tool
import requests


class SearchAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import search_tools
        return search_tools

    def get_system_prompt(self) -> str:
        return "You are a search agent that helps users find information on the web. Use the web search tool to perform searches."


@tool
def web_search(query: str) -> str:
    """Search the web for information"""
    # Implementation would go here
    return f"Searching for: {query}"


@tool
def news_search(topic: str) -> str:
    """Search for news about a specific topic"""
    # Implementation would go here
    return f"Searching for news about: {topic}"


search_tools = [web_search, news_search]
```

## Best Practices

### Plugin Design Guidelines

1. **Single Responsibility**: Each plugin should focus on one specific domain or capability
2. **Clear Naming**: Use descriptive names for plugins, agents, and tools
3. **Proper Error Handling**: Always handle exceptions in tool functions
4. **Documentation**: Provide clear docstrings for all tools and methods
5. **Type Hints**: Use proper type annotations for better code quality
6. **Testing**: Include unit tests for your tools and agent logic

### Common Patterns

```python
# Tool function with proper error handling
@tool
def safe_operation(input_data: str) -> str:
    """Perform a safe operation with error handling."""
    try:
        # Your logic here
        result = process_data(input_data)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Agent with comprehensive tool collection
class ComprehensiveAgent(BaseAgent):
    def get_tools(self):
        from .tools import (
            primary_tools,
            utility_tools,
            validation_tools
        )
        return primary_tools + utility_tools + validation_tools

    def get_system_prompt(self) -> str:
        return (
            "You are a comprehensive agent with multiple capabilities. "
            "Use the appropriate tools based on the user's request. "
            "Always explain your reasoning and show your work."
        )
```

## Development

### Setting up Development Environment

```bash
# Clone the main repository
git clone https://github.com/jonaskahn/cadence.git
cd cadence

# Install SDK dependencies
cd sdk
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/cadence_sdk

# Run specific test categories
poetry run pytest -m "unit"
poetry run pytest -m "integration"
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**: Ensure `register_plugin()` is called in `__init__.py`
2. **Import Errors**: Check that `cadence_sdk` is properly installed and imported
3. **Tool Registration**: Verify tools are decorated with `@tool` and included in the tools list
4. **Metadata Issues**: Ensure all required fields are provided in `PluginMetadata`

### Debug Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check plugin registration
from cadence_sdk import discover_plugins
plugins = discover_plugins()
print(f"Discovered plugins: {[p.name for p in plugins]}")

# Verify tool decoration
from .tools import my_tool
print(f"Tool type: {type(my_tool)}")
print(f"Tool name: {getattr(my_tool, 'name', 'No name')}")
```

## Support

- **Documentation**: [Read the Docs](https://cadence.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/jonaskahn/cadence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jonaskahn/cadence/discussions)

## Quick Reference

### Essential Imports

```python
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, tool, register_plugin
```

### Required Methods

- **Plugin**: `get_metadata()`, `create_agent()`
- **Agent**: `get_tools()`, `get_system_prompt()`
- **Tools**: Use `@tool` decorator

### File Structure

```
my_plugin/
├── __init__.py          # register_plugin(MyPlugin)
├── plugin.py            # BasePlugin implementation
├── agent.py             # BaseAgent implementation
└── tools.py             # @tool decorated functions
```

### Environment Variables

```bash
export CADENCE_PLUGINS_DIR="./plugins"
export CADENCE_DEFAULT_LLM_PROVIDER=openai
export CADENCE_OPENAI_API_KEY=your-key
```

---

**Built with ❤️ for the Cadence AI community**
