# Product Recommendation Agent

A Cadence SDK 2.0.x plugin that recommends resources from a Qdrant vector collection. The content can be anything stored
in the collection—products, documents, items, etc. Uses vector search with dense and sparse embeddings (Qdrant + hybrid
search).

## Tools

| Tool                           | Description                                                                                   |
|--------------------------------|-----------------------------------------------------------------------------------------------|
| `get_recommendation_resources` | Search resources using hybrid semantic and keyword matching across multiple search variations |
| `get_resource_by_qdrant_id`    | Retrieve detailed resource by Qdrant vector ID                                                |
| `get_resource_by_url`          | Retrieve resource details by URL                                                              |

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

## Plugin Info

| Field      | Value                                      |
|------------|--------------------------------------------|
| PID        | `com.shopapi.plugins.recommendation_agent` |
| Version    | `2.0.1`                                    |
| Agent type | `specialized`                              |
| Stateless  | Yes                                        |

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

## Packaging

Use the SDK's `build_plugin_zip` utility to create a deployable zip. It automatically includes
`plugin_manifest.json` (required by the upload API for fast validation):

```python
from cadence_sdk import build_plugin_zip

zip_bytes = build_plugin_zip("sdk/examples/recommendation_agent")
with open("recommendation_agent.zip", "wb") as f:
    f.write(zip_bytes)
```

Then upload:

```bash
curl -X POST http://localhost:8888/api/plugins/system \
  -H "Authorization: Bearer <token>" \
  -F "file=@recommendation_agent.zip"
```