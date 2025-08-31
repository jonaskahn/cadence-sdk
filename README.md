# Cadence SDK

A comprehensive SDK for building custom AI agent plugins for the Cadence Framework.

## Overview

The Cadence SDK provides the tools and interfaces needed to create powerful, extensible AI agents that integrate
seamlessly with the Cadence multi-agent framework. Build agents with custom tools, sophisticated reasoning capabilities,
and domain-specific knowledge.

## Features

- **Agent Framework**: Create intelligent agents with custom behavior
- **Tool System**: Build and integrate custom tools for agents
- **Plugin Management**: Easy plugin discovery and registration
- **Type Safety**: Full TypeScript/Python type support
- **Extensible**: Plugin-based architecture for easy extension

## Installation

```bash
pip install cadence-sdk
```

## Quick Start

### Key Imports

```python
# Core classes
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata
from cadence_sdk.tools import Tool
from cadence_sdk import tool, register_plugin

# Registry functions
from cadence_sdk import discover_plugins, register_plugin
```

### Creating a Simple Agent

```python
from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.metadata import PluginMetadata
from cadence_sdk.tools import Tool


class CalculatorAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import CalculatorTool
        return [CalculatorTool()]

    def get_system_prompt(self) -> str:
        return "You are a calculator agent that helps with mathematical calculations."


class CalculatorTool(Tool):
    name = "calculate"
    description = "Perform mathematical calculations"

    def execute(self, expression: str) -> str:
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
```

### Plugin Structure

```
my_plugin/
├── __init__.py          # Plugin registration
├── plugin.py            # Main plugin class (BasePlugin)
├── agent.py             # Agent implementation (BasePluginAgent)
└── tools.py             # Tool functions and classes
```

**Required Files:**

- `__init__.py`: Must call `register_plugin(YourPlugin)`
- `plugin.py`: Must implement `BasePlugin` with `get_metadata()` and `create_agent()`
- `agent.py`: Must implement `BaseAgent` with `get_tools()` and `get_system_prompt()`
- `tools.py`: Contains the actual tool implementations

### Plugin Registration

```python
from cadence_sdk.base.plugin import BasePlugin
from cadence_sdk.base.metadata import PluginMetadata


class CalculatorPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="calculator",
            version="1.0.1",
            description="Mathematical calculation plugin",
            capabilities=["mathematics", "calculations"],
            llm_requirements={
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1
            },
            agent_type="specialized",
            dependencies=[]
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
# Set plugin directories (single path or JSON list)
export CADENCE_PLUGINS_DIR="./plugins/src/cadence_plugins"

# Or multiple directories as JSON array
export CADENCE_PLUGINS_DIR='["/path/to/plugins", "/another/path"]'

# Plugin limits (configured in main application)
export CADENCE_MAX_AGENT_HOPS=25
export CADENCE_MAX_TOOL_HOPS=50
export CADENCE_GRAPH_RECURSION_LIMIT=50
```

### Plugin Discovery

The SDK automatically discovers plugins from:

- Environment packages
- Directory paths
- Custom registries

## Advanced Usage

### Custom Tool Decorators

```python
from cadence_sdk.tools.decorators import tool


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
from cadence_sdk.types.state import AgentState


class StatefulAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        return []

    def get_system_prompt(self) -> str:
        return "You are a stateful agent that maintains context."

    def should_continue(self, state: AgentState) -> str:
        # Access conversation history
        history = state.conversation_history

        # Update state if needed
        if len(history) > 10:
            return "back"  # Return to coordinator

        return "continue"  # Continue processing
```

### Plugin Registry

```python
from cadence_sdk.registry.plugin_registry import PluginRegistry

# Get plugin registry
registry = PluginRegistry()

# Register custom plugin
registry.register(CalculatorPlugin())

# Discover plugins
plugins = registry.discover()
```

## Examples

### Math Agent

```python
from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.metadata import PluginMetadata
from cadence_sdk.tools import Tool


class MathAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import CalculatorTool
        return [CalculatorTool()]

    def get_system_prompt(self) -> str:
        return "You are a math agent specialized in mathematical operations. Use the calculator tool for calculations."


class CalculatorTool(Tool):
    name = "calculator"
    description = "Perform mathematical calculations"

    def execute(self, expression: str) -> str:
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return "Invalid expression"
```

### Search Agent

```python
from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.metadata import PluginMetadata
from cadence_sdk.tools import Tool
import requests


class SearchAgent(BaseAgent):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)

    def get_tools(self):
        from .tools import WebSearchTool
        return [WebSearchTool()]

    def get_system_prompt(self) -> str:
        return "You are a search agent that helps users find information on the web. Use the web search tool to perform searches."


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information"

    def execute(self, query: str) -> str:
        # Implementation would go here
        return f"Searching for: {query}"
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

## Support

- **Documentation**: [Read the Docs](https://cadence.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/jonaskahn/cadence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jonaskahn/cadence/discussions)

---

**Built with ❤️ for the Cadence AI community**
