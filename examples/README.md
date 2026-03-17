# SDK Examples

Reference implementations for building Cadence plugins. Each example demonstrates a distinct pattern for the two agent
base classes: `BaseSpecializedAgent` and `BaseScopedAgent`.

## Agent types at a glance

| Base class             | Participates in multi-agent orchestration | Supports grounded/scoped mode |
|------------------------|-------------------------------------------|-------------------------------|
| `BaseSpecializedAgent` | Yes                                       | No                            |
| `BaseScopedAgent`      | No                                        | Yes                           |
| Both                   | Yes                                       | Yes                           |

**Specialized agents** expose tools and participate in supervisor, coordinator, and handoff pipelines. The orchestrator
decides when to invoke them.

**Scoped agents** are anchored to a specific resource (a URL, a database record, a ticket). On the first conversation
turn the framework calls `load_anchor(resource_id)` to fetch the anchor context, then uses `build_scope_rules(context)`
to constrain what the agent is allowed to answer.

An agent may extend **both** base classes to support both modes with the same tool set.

---

## Examples

### `web_search_agent` — Specialized only

Searches the web via Serper.dev. Exposes `web_search` and `image_search` tools. A canonical example of a
specialized-only agent: it provides general-purpose search capability with no concept of anchoring to a specific
resource.

| Field        | Value                                 |
|--------------|---------------------------------------|
| Pattern      | `BaseSpecializedAgent`                |
| PID          | `one.ifelse.plugins.web_search_agent` |
| External API | Serper.dev API key required           |
| Data         | Live web                              |

→ [README](web_search_agent/README.md)

---

### `webpage_reader_agent` — Scoped only

Fetches a webpage by URL and anchors the conversation to its content. Exposes a single `find_in_page` tool for keyword
search within the loaded text. This agent has no value in multi-agent orchestration — it only makes sense when anchored
to a specific URL.

| Field        | Value                             |
|--------------|-----------------------------------|
| Pattern      | `BaseScopedAgent`                 |
| PID          | `one.ifelse.webpage_reader_agent` |
| External API | Any URL                           |
| Data         | Live page                         |

→ [README](webpage_reader_agent/README.md)

---

### `helpdesk_agent` — Both modes

Customer helpdesk agent with knowledge base search and ticket anchoring. In specialized mode it answers general support
questions. In scoped mode it anchors to a specific support ticket and scopes the conversation to that ticket's issue,
while the same KB search tools remain available for finding relevant articles.

All data is bundled in-memory — no external API required. The `data.py` module (tickets + KB articles) is intentionally
kept separate from agent logic to follow SoC.

| Field        | Value                                    |
|--------------|------------------------------------------|
| Pattern      | `BaseSpecializedAgent + BaseScopedAgent` |
| PID          | `one.ifelse.helpdesk_agent`              |
| External API | None                                     |
| Data         | Bundled mock                             |

→ [README](helpdesk_agent/README.md)

---

### `recommendation_agent` — Both modes

Recommends resources from a Qdrant vector collection using hybrid dense + sparse (BM25) search. In specialized mode it
handles recommendation queries; in scoped mode it anchors to a specific product or document and answers questions in
context. Demonstrates service composition and complex configuration.

| Field        | Value                                     |
|--------------|-------------------------------------------|
| Pattern      | `BaseSpecializedAgent + BaseScopedAgent`  |
| PID          | `one.ifelse.plugins.recommendation_agent` |
| External API | Qdrant + embeddings                       |
| Data         | Vector collection                         |

→ [README](recommendation_agent/README.md)

---

## Choosing a pattern

```
Does the agent need to be anchored to a specific record?
├── No  → BaseSpecializedAgent
└── Yes → Does it also provide general-purpose tools useful in a pipeline?
          ├── No  → BaseScopedAgent
          └── Yes → BaseSpecializedAgent + BaseScopedAgent
```

---

## Packaging and uploading

Each example can be packaged as a ZIP and uploaded to Cadence as a system or organization plugin.

```bash
# Package (from the sdk/examples/ directory)
zip -r web_search_agent.zip web_search_agent/ -x "**/__pycache__/*" "**/*.pyc"
```

Then upload:

```bash
curl -X POST http://localhost:8888/api/plugins/system \
  -H "Authorization: Bearer <token>" \
  -F "file=@web_search_agent.zip"
```

The framework validates the plugin structure on upload, installs declared dependencies, and makes the plugin available
for orchestrator configuration.

---

## Quick validation

```python
from cadence_sdk import validate_plugin_structure, PluginContract

from examples.helpdesk_agent.plugin import HelpdeskPlugin

ok, errors = validate_plugin_structure(HelpdeskPlugin)
print(ok, errors)  # True, []

contract = PluginContract(HelpdeskPlugin)
print(contract.is_specialized)  # True
print(contract.is_scoped)  # True
```
