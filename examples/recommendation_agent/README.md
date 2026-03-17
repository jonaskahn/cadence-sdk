# Product Recommendation Agent

A Cadence SDK plugin that recommends resources from a Qdrant vector collection using hybrid dense + sparse (BM25) search. Implements the both-modes pattern — handles recommendation queries in multi-agent pipelines and anchors to a specific resource in scoped mode. Demonstrates service composition and complex configuration.

## Modes Supported

| Mode                      | Supported |
|---------------------------|-----------|
| Specialized (multi-agent) | Yes       |
| Scoped / Grounded         | No        |

## Plugin Info

| Field     | Value                                     |
|-----------|-------------------------------------------|
| PID       | `one.ifelse.plugins.recommendation_agent` |
| Version   | `1.0.0`                                   |
| Stateless | Yes                                       |

## Settings

All configuration is injected at runtime via `@plugin_settings`. No environment variables.

| Key                        | Type  | Required | Default                  | Description                                              |
|----------------------------|-------|----------|--------------------------|----------------------------------------------------------|
| `qdrant_url`               | str   | Yes      | `http://127.0.0.1:6333`  | Qdrant server URL                                        |
| `qdrant_api_key`           | str   | No       | `-`                      | Qdrant api key                                           |
| `qdrant_collection_name`   | str   | Yes      | `-`                      | Qdrant collection name                                   |
| `qdrant_timeout`           | int   | No       | `60`                     | Qdrant client timeout (seconds)                          |
| `qdrant_prefer_grpc`       | bool  | No       | `false`                  | Use gRPC protocol                                        |
| `qdrant_retry_count`       | int   | No       | `3`                      | Retry attempts for Qdrant operations                     |
| `qdrant_retry_delay`       | float | No       | `1.0`                    | Delay between retries (seconds)                          |
| `qdrant_dense_vector_name` | str   | No       | `text-embedding-3-large` | Dense vector name in Qdrant                              |
| `embedding_provider`       | str   | No       | `azure`                  | openai, azure, google, voyage                            |
| `embedding_provider_*`     | —     | —        | —                        | Provider-specific model/API key/endpoint (see plugin.py) |
| `system_prompt`            | str   | No       | —                        | Optional override for the agent system prompt            |

## Available Tools

| Tool                           | Description                                                                                   |
|--------------------------------|-----------------------------------------------------------------------------------------------|
| `get_recommendation_resources` | Search resources using hybrid semantic and keyword matching across multiple search variations |
| `get_resource_by_qdrant_id`    | Retrieve detailed resource by Qdrant vector ID                                                |
| `get_resource_by_url`          | Retrieve resource details by URL                                                              |

## File Structure

```
recommendation_agent/
├── __init__.py
├── plugin.py          # Agent + Plugin + tools
├── schemas.py
├── README.md
└── services/
    ├── __init__.py
    ├── embedding_service.py
    ├── search_service.py
    └── sparse_embedding_service.py
```

## How and when to use

Use this agent when recommendation queries need hybrid semantic + keyword search over a Qdrant collection. The content can be anything stored in the collection — products, documents, items, etc.

**Embedding providers:** Configure `embedding_provider` to one of `openai`, `azure`, `google`, or `voyage`. Each provider requires its own set of `embedding_provider_*` keys (model name, API key, endpoint); see `plugin.py` for the full list.

**Specialized mode:** The agent participates in a multi-agent pipeline and answers recommendation queries via `get_recommendation_resources`. Use `get_resource_by_qdrant_id` or `get_resource_by_url` for direct lookups.

**Scoped/Grounded mode:** The orchestrator calls `load_anchor(resource_id)` to anchor the conversation to a specific product or document. The same search tools remain available, scoped to the context of that resource.

This agent requires a running Qdrant instance and a configured embedding provider — there is no bundled mock data.
