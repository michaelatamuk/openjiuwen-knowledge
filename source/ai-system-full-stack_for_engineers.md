# AI System Full-Stack Concepts — Engineer Reference

> **The pattern worth noticing:** Interviewers at infrastructure-aware companies expect you to reason from the model call outward — API gateway, tokenization, context window, and inference cost — not just from the application layer. Knowing the 7-layer stack and where your code sits is a stronger signal than memorizing benchmarks.

---

## 1. The 7-layer AI application stack

**What it covers:** A structured decomposition of a production AI application into seven layers:
1. **Data pipeline** — ingestion, labeling, preprocessing, chunking
2. **Base model / training** — pretrained foundation model or fine-tuned weights
3. **Inference engine** — serving hardware, batching, KV cache, quantization
4. **RAG / retrieval** — vector stores, rerankers, hybrid search
5. **Orchestration** — agent loops, memory, tool use, context management
6. **Safety / guardrails** — moderation, schema enforcement, circuit breakers
7. **Infrastructure / observability** — load balancing, tracing, cost meters, deployment

**What a strong answer includes:** Identify which layers your code owns versus which are delegated to a provider or vendor. A common interview gap is treating the model as the entire stack.

**Jiuwen:** Layer 4: `agent-core/openjiuwen/core/retrieval/` (vector, hybrid, graph, agentic). Layer 5: `harness/prompts/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/agentic/react_agent.py`. Layer 6: `harness/rails/security_rail.py`, `guardrail_rail.py`, `subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/event.py`. Layers 1-3 are external.

**Coverage map:** New entry 04-6.

---

## 2. KV cache and prompt caching

**What it covers:** The key-value cache in the transformer attention mechanism stores the K and V tensors for every processed token. On a subsequent request with the same prefix, the provider reuses the cached tensors, skipping recomputation and reducing input cost (typically ~10% of normal input token price for cache hits). The implication for application design: stable prompt prefixes (system prompt, few-shot examples) should go first; variable content at the end.

**What a strong answer includes:** Distinguish the inference-layer KV cache (per-request, inside the GPU) from provider-level prompt caching (persisted across requests). Explain that the framework can observe cache hits via `cached_input_tokens` in usage metadata but cannot control provider-side cache policy.

**Jiuwen:** `ProviderUsage` (`core/context_engine/usage/provider_usage.py:14`) normalizes `cached_input_tokens` from provider usage metadata. `session_aggregator.py:45` tracks cache hit rates. `full_compact_processor.py:184` compacts at 180 k tokens — this indirectly stabilizes prefixes. The framework observes hits; it does not control caching.

**Coverage map:** New entry 01-24.

---

## 3. Base model versus instruct model

**What it covers:** A base model is the raw pretrained checkpoint — next-token prediction on web-scale data, no instruction following. An instruct (or chat) model is the same weights after the alignment pipeline: supervised fine-tuning (SFT) on demonstration data, reward model training, and RLHF or DPO to match human preferences. The practical difference: a base model will continue text; an instruct model will follow instructions, decline harmful requests, and produce structured responses.

**What a strong answer includes:** Know the pipeline: pretrain → SFT → reward model → RL fine-tuning. Understand that RLHF and DPO are alternatives for the RL step. Understand that a guardrail layer at inference time supplements but does not substitute for alignment training.

**Jiuwen:** `agent_rl/online/backends/sft/trainer.py` is the SFT stage that produces instruct-model-like behavior from demonstration data. `GuardrailRail` (`harness/rails/guardrail_rail.py`) provides inference-time safety supplement. The framework does not tag served models as base vs instruct in the config schema — `ProviderType + model_name` selects a model.

**Coverage map:** New entry 01-25.

---

## 4. LLM API call lifecycle

**What it covers:** What happens between your code calling `client.chat()` and receiving the first token: (1) SDK constructs a JSON payload; (2) HTTPS request to provider API; (3) API gateway authenticates and rate-limits; (4) load balancer selects a server; (5) tokenizer converts your prompt to token IDs; (6) GPU executes prefill (all input tokens in parallel); (7) GPU executes decode loop (one token per step, KV cache active); (8) tokens stream back as SSE; (9) usage metadata attached to the final chunk.

**What a strong answer includes:** Know that prefill is compute-bound (all tokens parallel) while decode is memory-bandwidth-bound (sequential). Understand that your code controls request construction and handles the response — gateway, load balancer, tokenization, and serving hardware are the provider's concern.

**Jiuwen:** Model clients (`core/foundation/llm/model_clients/openai_model_client.py:865`) send requests and receive streamed responses. `ProviderUsage` (`provider_usage.py:14`) captures input, output, and cached tokens from response metadata. `ObservabilityHandler` (`harness/observability/event.py:1`) logs model call events. `usage_cost.py:101` is the session billing meter. Steps 1-3 (API gateway, load balancer, tokenization) are the provider's infrastructure.

**Coverage map:** New entry 01-26.

---

## Coverage summary

| Concept | KB entry | Status |
|---|---|---|
| 7-layer AI stack | 04-6 | New |
| KV cache / prompt caching | 01-24 | New |
| Base vs instruct model | 01-25 | New |
| LLM API call lifecycle | 01-26 | New |
| Model-size tradeoff thinking | 04-2 | Previously covered |
| Context window management | 01-8, 01-9, 01-16 | Previously covered |
| Inference cost tracking | 04-4, 04-5, 16-1 | Previously covered |
