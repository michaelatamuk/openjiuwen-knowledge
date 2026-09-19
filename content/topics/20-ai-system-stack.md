# AI system stack

## 1. The 7-layer AI application stack

**Definition:** A structured decomposition of a production AI application into seven layers, from the data pipeline up to infrastructure and observability.

**Jiuwen:** Layer 4: `core/retrieval/retriever/` (vector, hybrid, graph, agentic). Layer 5: `core/foundation/prompt/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/single_agent/agents/react_agent.py`. Layer 6: `harness/rails/security/` (prompt/tool security), `core/security/guardrail/builtin.py`, `harness/rails/subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/` and `extensions/observability/`. Layers 1-3 are external.

---

## 2. KV cache and prompt caching

**Definition:** The key-value cache in the transformer attention mechanism stores the K and V tensors for every processed token. On a subsequent request with the same prefix, the provider reuses the cached tensors, skipping recomputation and reducing input cost (typically ~10% of normal input token price for cache hits). The implication for application design: stable prompt prefixes (system prompt, few-shot examples) should go first; variable content at the end.

**Jiuwen:** `request_usage_from_metadata` (`core/context_engine/usage/provider_usage.py:14`) reads `cache_read_tokens` into `RequestKVCacheUsage` (`core/context_engine/usage/models.py:55`); `SessionKVCacheAggregator` (`core/context_engine/usage/session_aggregator.py:45`) aggregates the cache hit rate. `FullCompactProcessorConfig.trigger_total_tokens` defaults to 180k (`full_compact_processor.py:184`), which indirectly stabilizes prefixes. The framework observes hits; it does not control provider-side caching.

---

## 3. LLM API call lifecycle

**Definition:** What happens between calling `client.chat()` and receiving the first token, step by step, and which of those steps the provider owns versus the caller.

**Jiuwen:** Model clients send and stream the request via `invoke`/`stream` (`openai_model_client.py:1491`/`:1665`). `request_usage_from_metadata` (`provider_usage.py:14`) captures input, output, and cache token counts from response metadata. `OtelCallbackHandler` (`extensions/observability/callback_handler.py:371`) logs model-call events, and `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:101` is the session billing meter. Steps 1-3 (API gateway, load balancer, tokenization) are the provider's infrastructure.

---
