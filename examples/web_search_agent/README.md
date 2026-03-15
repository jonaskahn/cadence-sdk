# Web Search Agent

A Cadence SDK plugin that searches the web using [Serper.dev](https://serper.dev) (Google Search API).
Supports standard web search with site/time filtering and image search.

## Tools

| Tool           | Description                                                                              |
|----------------|------------------------------------------------------------------------------------------|
| `web_search`   | Search the web across multiple queries with optional site restriction and time filtering |
| `image_search` | Search Google Images for visual content by keyword                                       |

## Settings

| Key              | Type  | Required | Default | Description                  |
|------------------|-------|----------|---------|------------------------------|
| `serper_api_key` | `str` | Yes      | —       | Serper.dev API key           |
| `max_results`    | `int` | No       | `10`    | Max results per query (1–20) |

Get a free API key at [serper.dev](https://serper.dev).

## Plugin Info

| Field      | Value                                  |
|------------|----------------------------------------|
| PID        | `com.cadence.plugins.web_search_agent` |
| Version    | `1.0.0`                                |
| Agent type | `specialized`                          |
| Stateless  | Yes                                    |

## Usage

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

## File Structure

```
web_search_agent/
├── __init__.py   # Exports WebSearchPlugin
├── plugin.py     # Agent + plugin definition
└── README.md
```

## Packaging

```bash
zip -r web_search_agent.zip sdk/examples/web_search_agent/ -x "**/__pycache__/*" "**/*.pyc"
```

Then upload:

```bash
curl -X POST http://localhost:8888/api/plugins/system \
  -H "Authorization: Bearer <token>" \
  -F "file=@web_search_agent.zip"
```
