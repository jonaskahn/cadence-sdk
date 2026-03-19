# Helpdesk Agent

A Cadence SDK plugin demonstrating the both-modes pattern — extends `BaseSpecializedAgent` and `BaseScopedAgent` to work
in multi-agent pipelines and in grounded/scoped mode. Provides knowledge base search and ticket anchoring. All data is
bundled in-memory; no external API required.

## Modes Supported

| Mode                      | Supported |
|---------------------------|-----------|
| Specialized (multi-agent) | Yes       |
| Scoped / Grounded         | Yes       |

## Plugin Info

| Field     | Value                       |
|-----------|-----------------------------|
| PID       | `one.ifelse.helpdesk_agent` |
| Version   | `1.0.0`                     |
| Stateless | Yes                         |

## Settings

| Key             | Type  | Required | Default     | Description                                                                                              |
|-----------------|-------|----------|-------------|----------------------------------------------------------------------------------------------------------|
| `data_source`   | `str` | No       | `"bundled"` | Data source for tickets and articles. Only `"bundled"` is supported (reserved for future extensibility). |
| `system_prompt` | `str` | No       | —           | Override the default system prompt.                                                                      |

## Available Tools

| Tool              | Description                                                                                                                     |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `search_articles` | Searches knowledge base articles by keyword across title, content, and tags. Returns matching articles with a 300-char excerpt. |
| `get_article`     | Retrieves the full content of a KB article by ID (e.g. `KB-001`). Use after `search_articles` to get complete details.          |

## File Structure

```
helpdesk_agent/
├── __init__.py   # exports HelpdeskPlugin
├── plugin.py     # HelpdeskAgent + HelpdeskPlugin
└── data.py       # TICKETS, ARTICLES, build_article_index, build_ticket_index
```

## How and when to use

Use `BaseSpecializedAgent + BaseScopedAgent` together when your agent provides general-purpose tools that are equally
useful when anchored to a specific record. Here, the same KB search tools work both for answering general support
questions and for researching articles relevant to a specific ticket.

**Specialized mode:** The agent participates in a supervisor/coordinator/handoff orchestrator. The LLM routes support
questions to `search_articles` and `get_article` to look up KB content.

**Scoped/Grounded mode:** The grounded orchestrator calls `load_anchor(resource_id)` with a ticket ID (`TKT-001`) or
slug (`login-2fa-not-working`). `build_scope_rules(context)` returns a scope instruction focused on the ticket's
summary. The same KB search tools remain available, letting the LLM look up articles relevant to the ticket.

**Bundled mock data:** The dataset contains 5 tickets (auth, billing, export, password reset, API rate limits) and 10 KB
articles. No external dependencies beyond the SDK.

```python
from examples.helpdesk_agent.plugin import HelpdeskPlugin
from cadence_sdk import validate_plugin_structure, PluginContract

ok, errors = validate_plugin_structure(HelpdeskPlugin)
print(ok, errors)  # True, []

contract = PluginContract(HelpdeskPlugin)
print(contract.is_scoped)  # True
print(contract.is_specialized)  # True
```
