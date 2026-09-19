<div class="topic-nav">
<a class="topic-nav__link topic-nav__prev" href="19-foundational-papers.html"><span class="topic-nav__dir">← Previous</span><span class="topic-nav__name">Foundational papers</span></a>
<a class="topic-nav__link topic-nav__next" href="02-prompting-and-output-control.html"><span class="topic-nav__dir">Next →</span><span class="topic-nav__name">Prompting and output control</span></a>
</div>

# Model serving

## 1. The 7-layer AI application stack

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** A production AI application decomposes into seven layers, from the data pipeline to infrastructure and observability.

**Key points.**

- Data pipeline — ingestion, labeling, preprocessing, chunking
- Base model / training — pretrained foundation model or fine-tuned weights
- Inference engine — serving hardware, batching, KV cache, quantization
- RAG / retrieval — vector stores, rerankers, hybrid search
- Orchestration — agent loops, memory, tool use, context management
- Safety / guardrails — moderation, schema enforcement, circuit breakers
- Infrastructure / observability — load balancing, tracing, cost meters, deployment
- Identify which layers your code owns versus which are delegated to a provider or vendor
- Treat the model as one layer, not the entire stack

**Concept.** A structured decomposition of a production AI application into seven layers, from the data pipeline up to infrastructure and observability.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Layer 4: `core/retrieval/retriever/` (vector, hybrid, graph, agentic). Layer 5: `core/foundation/prompt/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/single_agent/agents/react_agent.py`. Layer 6: `harness/rails/security/` (prompt/tool security), `core/security/guardrail/builtin.py`, `harness/rails/subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/` and `extensions/observability/`. Layers 1-3 are external.

</details>

---

## 2. KV cache and prompt caching

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** The key-value cache in the transformer attention mechanism stores the K and V tensors for every processed token.

**Key points.**

- On a repeated prefix the provider reuses cached tensors, reducing input cost (cache hits are a fraction of normal input price)
- Put stable prompt prefixes (system prompt, few-shot examples) first; variable content last
- Distinguish the inference-layer KV cache (per-request, inside the GPU) from provider-level prompt caching (persisted across requests)
- The framework can observe cache hits via `cached_input_tokens` but cannot control provider-side cache policy

**Concept.** The key-value cache in the transformer attention mechanism stores the K and V tensors for every processed token. On a subsequent request with the same prefix, the provider reuses the cached tensors, skipping recomputation and reducing input cost (typically ~10% of normal input token price for cache hits). The implication for application design: stable prompt prefixes (system prompt, few-shot examples) should go first; variable content at the end.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`request_usage_from_metadata` (`core/context_engine/usage/provider_usage.py:14`) reads `cache_read_tokens` into `RequestKVCacheUsage` (`core/context_engine/usage/models.py:55`); `SessionKVCacheAggregator` (`core/context_engine/usage/session_aggregator.py:45`) aggregates the cache hit rate. `FullCompactProcessorConfig.trigger_total_tokens` defaults to 180k (`full_compact_processor.py:184`), which indirectly stabilizes prefixes. The framework observes hits; it does not control provider-side caching.

</details>

---

## 3. LLM API call lifecycle

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** The path from calling `client.chat()` to the first token: nine steps, of which the later ones are the provider's infrastructure.

**Key points.**

- SDK constructs a JSON payload
- HTTPS request to the provider API
- API gateway authenticates and rate-limits
- Load balancer selects a server
- Tokenizer converts the prompt to token IDs
- GPU executes prefill (all input tokens in parallel)
- GPU executes the decode loop (one token per step, KV cache active)
- Tokens stream back as SSE
- Usage metadata is attached to the final chunk
- Prefill is compute-bound; decode is memory-bandwidth-bound
- Your code controls request construction and the response; gateway, load balancer, tokenization, and serving are the provider's

**Concept.** What happens between calling `client.chat()` and receiving the first token, step by step, and which of those steps the provider owns versus the caller.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Model clients send and stream the request via `invoke`/`stream` (`openai_model_client.py:1491`/`:1665`). `request_usage_from_metadata` (`provider_usage.py:14`) captures input, output, and cache token counts from response metadata. `OtelCallbackHandler` (`extensions/observability/callback_handler.py:371`) logs model-call events, and `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:101` is the session billing meter. Steps 1-3 (API gateway, load balancer, tokenization) are the provider's infrastructure.

</details>

---
