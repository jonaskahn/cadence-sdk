# Helpdesk Agent

Customer helpdesk agent demonstrating the **both-modes** pattern — the agent extends both `BaseSpecializedAgent` and `BaseScopedAgent`, making it usable in multi-agent pipelines and in grounded/scoped mode.

## When to use this pattern

Use `BaseSpecializedAgent + BaseScopedAgent` together when your agent provides general-purpose tools that are equally useful when anchored to a specific record. Here, the same KB search tools work both for answering general support questions and for researching articles relevant to a specific ticket.

## Modes supported

| Mode | Supported |
|------|-----------|
| Specialized (multi-agent) | Yes |
| Scoped / Grounded | Yes |

## How it works

### Specialized mode

The agent participates in a supervisor/coordinator/handoff orchestrator. The LLM routes support questions to `search_articles` and `get_article` to look up KB content.

### Scoped/Grounded mode

1. The grounded orchestrator calls `load_anchor(resource_id)` with a ticket ID (`TKT-001`) or slug (`login-2fa-not-working`).
2. `build_scope_rules(context)` returns a scope instruction focused on the ticket's summary.
3. The same KB search tools remain available, letting the LLM look up articles relevant to the ticket.

## Tools

| Tool | Description |
|------|-------------|
| `search_articles` | Searches knowledge base articles by keyword across title, content, and tags. Returns matching articles with a 300-char excerpt. |
| `get_article` | Retrieves the full content of a KB article by ID (e.g. `KB-001`). Use after `search_articles` to get complete details. |

## Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `data_source` | `str` | `"bundled"` | Data source for tickets and articles. Only `"bundled"` is supported (reserved for future extensibility). |
| `system_prompt` | `str` | — | Override the default system prompt. |

## Dependencies

None beyond the SDK — all data is bundled in-memory.

## File structure

```
helpdesk_agent/
├── __init__.py   # exports HelpdeskPlugin
├── plugin.py     # HelpdeskAgent + HelpdeskPlugin
└── data.py       # TICKETS, ARTICLES, build_article_index, build_ticket_index
```

## Mock data

The bundled dataset contains:

- **5 tickets** covering auth, billing, export, password reset, and API rate limits
- **10 KB articles** covering 2FA setup, login troubleshooting, invoices, data export, password reset, API rate limits, billing management, API auth, account security, and contacting support

Ticket lookup supports both the canonical ID (`TKT-001`) and the URL-friendly slug (`login-2fa-not-working`).

## Quick validation

```python
from examples.helpdesk_agent.plugin import HelpdeskPlugin
from cadence_sdk import validate_plugin_structure, PluginContract

ok, errors = validate_plugin_structure(HelpdeskPlugin)
print(ok, errors)  # True, []

contract = PluginContract(HelpdeskPlugin)
print(contract.is_scoped)       # True
print(contract.is_specialized)  # True
```
