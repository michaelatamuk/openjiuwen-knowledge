# AI Gateway Architecture — Coverage Map

An AI gateway sits between the application and LLM providers, centralizing routing, rate limiting, authentication, cost tracking, observability, and safety enforcement. This source covers the pattern and its components. All material maps to existing KB entries.

---

## What an AI gateway does

An AI gateway is the infrastructure layer that:
- **Routes** requests to multiple providers (OpenAI, Anthropic, local models) based on cost, latency, or availability
- **Rate-limits** per-tenant or per-user to prevent cost overruns
- **Authenticates** and isolates API keys from application code
- **Caches** semantically similar queries to reduce redundant model calls
- **Enforces safety** at the gateway level (before the request reaches the model)
- **Observes** every call with span/trace/cost metadata

---

## Coverage map

| Gateway concept | KB entry |
|---|---|
| Multi-provider routing | 16-15 |
| Fallback sequence across providers | 16-16 |
| Rate limiting and cost caps | 16-1, 16-4 |
| Semantic caching | 16-2 |
| Load balancing and endpoint health | 04-2 |
| Observability and cost tracking | 16-14 |
| Safety enforcement at infrastructure layer | 18-1 through 18-5 |
| Request budget and circuit breaking | 05-10 |

**No new entries added.** All material was already present in the KB, primarily under topics 16 (production cost and scale) and 18 (security and safety).

---

## Jiuwen relationship

Jiuwen's equivalent is a router config in `ModelPoolEntry` (allocator, rotation, by-model-name strategies) with health, rate, and latency scoring — infrastructure routing rather than a standalone gateway product. A dedicated AI gateway would sit upstream of Jiuwen's model clients.
