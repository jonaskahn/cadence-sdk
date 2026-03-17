<div align="center">
  <img src="https://github.com/user-attachments/assets/27847eea-5316-45c7-8df4-0549f3846150" alt="Cadence SDK" width="420"/>
  <br/>

  [![Python 3.13+](https://img.shields.io/badge/python-3.13+-f97316?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
  [![PyPI version](https://img.shields.io/pypi/v/cadence-sdk?style=flat-square&color=f59e0b&logo=pypi&logoColor=white)](https://pypi.org/project/cadence-sdk/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-fbbf24?style=flat-square)](https://opensource.org/licenses/MIT)
  [![Docs](https://img.shields.io/badge/docs-jonaskahn.github.io%2Fcadence-f97316?style=flat-square)](https://jonaskahn.github.io/cadence)
  <br/>

  <strong>Write your plugin once — works on LangGraph, OpenAI Agents SDK, and Google ADK.<strong>
</div>

---
## What is this?

Cadence SDK lets you build **AI agent plugins** that are completely decoupled from any orchestration framework. You
define tools and domain logic; the Cadence platform handles LLM configuration, routing, and multi-agent orchestration.

A plugin is two things:

- A **Plugin** (stateless factory) — declares metadata and creates agent instances
- An **Agent** — holds tools, a system prompt, and optional lifecycle hooks

The SDK provides the base classes, decorators, and types to wire these together.

---

## Installation

```bash
pip install cadence-sdk
```

---

## Quick Start

Create `my_plugin/plugin.py`:

```python
from cadence_sdk import BasePlugin, BaseSpecializedAgent, PluginMetadata, uvtool, plugin_settings, UvTool
from typing import List


class MyAgent(BaseSpecializedAgent):
    def initialize(self, config: dict) -> None:
        self.api_key = config["api_key"]
        self._search_tool = self._make_search_tool()

    def _make_search_tool(self) -> UvTool:
        @uvtool
        def search(query: str) -> str:
            """Search for information."""
            return call_api(query, self.api_key)

        return search

    def get_tools(self) -> List[UvTool]:
        return [self._search_tool]

    def get_system_prompt(self) -> str:
        return "You are a helpful assistant."


@plugin_settings([
    {"key": "api_key", "type": "str", "description": "API key", "sensitive": True, "required": True},
    {"key": "timeout", "type": "int", "description": "Request timeout in seconds", "default": 30},
])
class MyPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.example.my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="Does something useful",
        )

    @staticmethod
    def create_agent() -> MyAgent:
        return MyAgent()
```

Cadence auto-discovers any `BasePlugin` subclass in a `plugin.py` file — no manual registration needed.

Package:

```bash
zip -r my_plugin.zip my_plugin/ -x "**/__pycache__/*" "**/*.pyc"
```

---

## How to Use

### Agents

Every agent must implement two methods:

| Method                | Purpose                             |
|-----------------------|-------------------------------------|
| `get_tools()`         | Return a list of `UvTool` instances |
| `get_system_prompt()` | Return the system prompt string     |

Optional lifecycle hooks:

| Method               | Purpose                                                                        |
|----------------------|--------------------------------------------------------------------------------|
| `initialize(config)` | Set up state when the agent is created; `config` comes from `@plugin_settings` |
| `cleanup()`          | Async teardown — close connections, release resources                          |

Choose which base class to extend:

- **`BaseSpecializedAgent`** — tool-focused agent for any multi-agent mode (supervisor, coordinator, handoff)
- **`BaseScopedAgent`** — context-anchored agent for grounded mode; requires `load_anchor(resource_id)` and
  `build_scope_rules(context)`
- Both — extend both classes to support grounded *and* standard modes in one plugin

### Plugins

A plugin is a stateless factory. Implement two static methods:

| Method           | Purpose                                                     |
|------------------|-------------------------------------------------------------|
| `get_metadata()` | Return a `PluginMetadata` (pid, name, version, description) |
| `create_agent()` | Return a fresh agent instance                               |

Optional static methods: `validate_dependencies()`, `get_settings_schema()`, `health_check()`.

### Tools

Use `@uvtool` to wrap any sync or async function as a framework-agnostic tool:

```python
@uvtool
def search(query: str) -> str:
    """Search for information."""
    return do_search(query)


@uvtool(stream=True, validate=True)
async def fetch(url: str) -> dict:
    """Fetch URL content."""
    return await do_fetch(url)
```

`@uvtool` accepts: `name`, `description`, `args_schema` (Pydantic model), `stream`, `stream_filter`, `validate`.

### Settings

Use `@plugin_settings` on your plugin class to declare config shown in the Cadence UI:

```python
@plugin_settings([
    {"key": "api_key", "type": "str", "description": "API key", "sensitive": True, "required": True},
    {"key": "max_results", "type": "int", "description": "Max results", "default": 10},
])
class MyPlugin(BasePlugin): ...
```

Each entry requires: `key`, `type` (`"str"` `"int"` `"float"` `"bool"` `"list"` `"dict"`), `description`.  
Optional: `name` (display label), `default`, `required`, `sensitive`.

Settings are passed to `agent.initialize(config)` as a dict.

---

## Best Practices

- **Tools as closures** — tools that need agent state should be closures inside a `_make_*` factory method so they
  capture `self`
- **Stateless plugins** — set `stateless=True` (the default) when agents carry no mutable state; this enables instance
  sharing across orchestrators
- **Declare dependencies** — list pip requirements in `PluginMetadata.dependencies` so the platform auto-installs them
  on load
- **Async cleanup** — implement `async cleanup()` on agents that hold connections or file handles
- **Configurable system prompt** — add `system_prompt` to `@plugin_settings` and return
  `config.get("system_prompt") or default` from `get_system_prompt()`
- **Validate in CI** — use `validate_plugin_structure(MyPlugin)` to catch structural issues before deployment

---

## Examples

| Example                                                  | Description                        |
|----------------------------------------------------------|------------------------------------|
| [`web_search_agent`](examples/web_search_agent/)         | Web search via Serper.dev          |
| [`recommendation_agent`](examples/recommendation_agent/) | Product recommendations via Qdrant |
| [`helpdesk_agent`](examples/helpdesk_agent/)             | Helpdesk support agent             |
| [`webpage_reader_agent`](examples/webpage_reader_agent/) | Web page content reader            |

---

## Development

```bash
git clone https://github.com/jonaskahn/cadence.git
cd cadence/sdk
poetry install --with dev

# Run tests
PYTHONPATH=src python -m pytest tests/ -v
```

---

<div align="center">

MIT Licensed &nbsp;·&nbsp; [jonaskahn.github.io/cadence](https://jonaskahn.github.io/cadence)

</div>