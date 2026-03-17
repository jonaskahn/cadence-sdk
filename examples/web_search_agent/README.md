# Web Search Agent

A Cadence SDK plugin that searches the web using [Serper.dev](https://serper.dev) (Google Search API). Exposes web
search with site/time filtering and image search. Implements the specialized-only pattern — it provides general-purpose
search capability with no concept of anchoring to a specific resource.

## Modes Supported

| Mode                      | Supported |
|---------------------------|-----------|
| Specialized (multi-agent) | Yes       |
| Scoped / Grounded         | No        |

## Plugin Info

| Field     | Value                                 |
|-----------|---------------------------------------|
| PID       | `one.ifelse.plugins.web_search_agent` |
| Version   | `1.0.0`                               |
| Stateless | Yes                                   |

## Settings

| Key              | Type  | Required | Default | Description                                                             |
|------------------|-------|----------|---------|-------------------------------------------------------------------------|
| `serper_api_key` | `str` | Yes      | —       | Serper.dev API key. Get a free key at [serper.dev](https://serper.dev). |
| `max_results`    | `int` | No       | `10`    | Max results per query (1–20)                                            |
| `system_prompt`  | `str` | No       | —       | Override the default system prompt.                                     |

## Available Tools

| Tool           | Description                                                                              |
|----------------|------------------------------------------------------------------------------------------|
| `web_search`   | Search the web across multiple queries with optional site restriction and time filtering |
| `image_search` | Search Google Images for visual content by keyword                                       |

## File Structure

```
web_search_agent/
├── __init__.py   # Exports WebSearchPlugin
├── plugin.py     # Agent + plugin definition
└── README.md
```

## How and when to use

Use this agent when you need general-purpose web search in a multi-agent pipeline. Because it implements the
specialized-only pattern, it has no `load_anchor` or `build_scope_rules` — it is always available as a tool in a
supervisor/coordinator orchestrator.

### web_search

Accepts 1–5 search term objects. Each term supports:

- **`queries`** — comma-separated sub-queries (2–4 per term)
- **`site`** *(optional)* — restrict to a domain, e.g. `github.com`
- **`tbs`** *(optional)* — time filter: `qdr:d` (day), `qdr:w` (week), `qdr:m` (month), `qdr:y` (year)

Example request:

```json
{
  "search_terms": [
    {
      "queries": "langgraph multi-agent, langgraph supervisor pattern",
      "site": "github.com",
      "tbs": "qdr:m"
    }
  ],
  "query_intent": "Find recent LangGraph multi-agent examples on GitHub"
}
```

### image_search

```json
{
  "query": "golden retriever puppy",
  "num": 10
}
```
