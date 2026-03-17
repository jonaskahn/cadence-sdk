# Webpage Reader Agent

A Cadence SDK plugin that fetches a webpage by URL and anchors the conversation to its content. Implements the
scoped-only pattern — the agent extends `BaseScopedAgent` and does not participate in multi-agent orchestration.

## Modes Supported

| Mode                      | Supported |
|---------------------------|-----------|
| Specialized (multi-agent) | No        |
| Scoped / Grounded         | Yes       |

## Plugin Info

| Field     | Value                             |
|-----------|-----------------------------------|
| PID       | `one.ifelse.webpage_reader_agent` |
| Version   | `1.0.0`                           |
| Stateless | Yes                               |

## Settings

| Key                  | Type  | Required | Default | Description                                                                  |
|----------------------|-------|----------|---------|------------------------------------------------------------------------------|
| `user_agent`         | `str` | No       | —       | Custom `User-Agent` header for the HTTP request.                             |
| `max_content_length` | `int` | No       | `20000` | Maximum characters to retain from the page body. Longer pages are truncated. |
| `system_prompt`      | `str` | No       | —       | Override the default system prompt.                                          |

## Available Tools

| Tool           | Description                                                                                                                         |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `find_in_page` | Searches the loaded page text for a keyword or phrase. Returns up to 5 excerpts with 150 chars of surrounding context on each side. |

## File Structure

```
webpage_reader_agent/
├── __init__.py   # exports WebpageReaderPlugin
└── plugin.py     # WebpageReaderAgent + WebpageReaderPlugin
```

## How and when to use

Use `BaseScopedAgent` alone when your agent has no value outside of grounded mode. This agent only makes sense when
anchored to a specific URL — there is no general-purpose tool to expose in a supervisor pipeline.

The scoped flow has four steps:

1. The grounded orchestrator calls `load_anchor(url)` on the first turn.
2. The agent fetches the URL via `httpx`, parses the page with `beautifulsoup4` (falls back to regex stripping if
   unavailable), and stores the body text in `self._page_text`.
3. `build_scope_rules(context)` returns a scope instruction constraining the conversation to the page title/URL.
4. On each turn, the LLM can call `find_in_page(query)` to locate relevant passages before answering.

**Dependencies:** `httpx>=0.27.0`, `beautifulsoup4>=4.12.0`

```python
from examples.webpage_reader_agent.plugin import WebpageReaderPlugin
from cadence_sdk import validate_plugin_structure, PluginContract

ok, errors = validate_plugin_structure(WebpageReaderPlugin)
print(ok, errors)  # True, []

contract = PluginContract(WebpageReaderPlugin)
print(contract.is_scoped)  # True
print(contract.is_specialized)  # False
```
