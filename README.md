# Cadence SDK

Framework-agnostic plugin development kit for the Cadence AI platform.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/cadence-sdk.svg)](https://badge.fury.io/py/cadence-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Write your plugin once — it works on LangGraph, OpenAI Agents SDK, and Google ADK without framework-specific code.

> **Full documentation:** [jonaskahn.github.io/cadence](https://jonaskahn.github.io/cadence)

---

## Installation

```bash
pip install cadence-sdk
```

---

## Quick Start

Create `my_plugin/plugin.py`:

```python
from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata, uvtool, plugin_settings, UvTool
from typing import List


class MyAgent(BaseAgent):
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
    {"key": "timeout",  "type": "int", "description": "Request timeout", "default": 30},
])
class MyPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.example.my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="Does something useful",
            stateless=True,
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MyAgent()
```

Cadence auto-discovers any `BasePlugin` subclass in a `plugin.py` file — no manual registration needed.

Package and upload using the SDK's `build_plugin_zip` utility:

```python
from cadence_sdk import build_plugin_zip

zip_bytes = build_plugin_zip("my_plugin")
with open("my_plugin.zip", "wb") as f:
    f.write(zip_bytes)
```

`build_plugin_zip` automatically includes `plugin_manifest.json` in the zip root — required by the
upload API for fast fail-fast validation before the subprocess runs.

---

## Core Concepts

| Concept            | Description                                                                     |
|--------------------|---------------------------------------------------------------------------------|
| `BasePlugin`       | Factory class — declares metadata and creates agent instances                   |
| `BaseAgent`        | Provides tools and system prompt; receives resolved settings via `initialize()` |
| `@uvtool`          | Wraps a sync or async function as a framework-agnostic tool                     |
| `@plugin_settings` | Declares the settings schema shown in the Cadence UI                            |
| `PluginMetadata`   | Declares `pid`, `name`, `version`, `description`, `stateless`, `dependencies`   |

### `PluginMetadata` fields

| Field          | Type      | Required | Description                                            |
|----------------|-----------|----------|--------------------------------------------------------|
| `pid`          | str       | Yes      | Reverse-domain unique ID, e.g. `com.example.my_plugin` |
| `name`         | str       | Yes      | Human-readable display name                            |
| `version`      | str       | Yes      | Semantic version string                                |
| `description`  | str       | Yes      | Human-readable description                             |
| `stateless`    | bool      | No       | `True` enables instance sharing (default: `True`)      |
| `capabilities` | List[str] | No       | Capability tags for filtering                          |
| `dependencies` | List[str] | No       | Pip requirements, e.g. `["requests>=2.28"]`            |
| `sdk_version`  | str       | No       | Compatible SDK range (default: `">=2.0.0,<3.0.0"`)     |

### `@plugin_settings` field types

`"str"`, `"int"`, `"float"`, `"bool"`, `"list"`, `"dict"`

Each entry: `key` (required), `type` (required), `description` (required), `name`, `default`, `required`, `sensitive`.

### `@uvtool` options

| Parameter       | Description                                                                       |
|-----------------|-----------------------------------------------------------------------------------|
| `name`          | Tool name (default: function name)                                                |
| `description`   | Tool description (default: docstring)                                             |
| `args_schema`   | Pydantic model for argument validation                                            |
| `stream`        | If `True`, stream tool result to client before synthesizer                        |
| `stream_filter` | Callable to filter result before streaming (e.g. expose only `url`, `product_id`) |
| `validate`      | If `True`, marks tool for LLM validation                                          |
| `cache`         | `True`, `False`, or `CacheConfig` for semantic caching                            |

---

## Examples

| Example                                                  | Description                                                                 |
|----------------------------------------------------------|-----------------------------------------------------------------------------|
| [`web_search_agent`](examples/web_search_agent/)         | Web search via Serper.dev; site/time filters, image search                  |
| [`recommendation_agent`](examples/recommendation_agent/) | Product recommendations via Qdrant hybrid search; dense + sparse embeddings |

Each example includes a full plugin, agent, tools, and README with packaging instructions.

---

## Agent Pattern — Tools as Closures

Tools that need agent state should be created as closures inside factory methods:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        self.api_key = None
        self._search_tool = self._make_search_tool()

    def _make_search_tool(self) -> UvTool:
        @uvtool
        def search(query: str) -> str:
            """Search using agent's API key."""
            return call_api(query, self.api_key)  # captures self
        return search
```

---

## Configurable System Prompt

To make the system prompt configurable via plugin settings:

1. Add ``system_prompt`` to @plugin_settings:

   ```python
   {"key": "system_prompt", "name": "System Prompt Override", "type": "str",
    "required": False, "description": "Optional override for the agent system prompt. Leave empty to use default."}
   ```

2. In ``initialize()``, store the value: ``self._system_prompt = config.get("system_prompt")``

3. In ``get_system_prompt()``, return the override or default:
   ``return self._system_prompt or self._default_system_prompt``

---

## Async Tools

```python
@uvtool
async def fetch(url: str) -> str:
    """Fetch URL asynchronously."""
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.text()

result = await fetch.ainvoke(url="https://example.com")
```

---

## Packaging & Deployment

```python
from cadence_sdk import build_plugin_zip

# Build a deployable zip with plugin_manifest.json included automatically
zip_bytes = build_plugin_zip("path/to/my_plugin")
with open("my_plugin.zip", "wb") as f:
    f.write(zip_bytes)
```

```bash
# Upload to Cadence
curl -X POST http://localhost:8888/api/plugins/system \
  -H "Authorization: Bearer <token>" \
  -F "file=@my_plugin.zip"
```

## Validation & Dependency Utilities

```python
from cadence_sdk import validate_plugin_structure, check_dependency_installed, install_dependencies

# Validate before deploying
is_valid, errors = validate_plugin_structure(MyPlugin)

# Check / install dependencies
if not check_dependency_installed("requests"):
    install_dependencies(["requests>=2.28"])
```

---

## Best Practices

- Set `stateless=True` when agents carry no mutable state — enables bundle sharing across orchestrators
- Declare `dependencies` in `PluginMetadata` so the platform can auto-install them
- Implement `async cleanup()` on agents that hold connections or file handles
- Use `validate_dependencies()` to surface missing env vars or packages at startup

---

## Development

```bash
git clone https://github.com/jonaskahn/cadence.git
cd cadence/sdk
poetry install --with dev

# Run tests
PYTHONPATH=src python -m pytest tests/ -v

# Run example
PYTHONPATH=src python examples/test_sdk.py
```

---

## License

MIT — see [LICENSE](LICENSE).
