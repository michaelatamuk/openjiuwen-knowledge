# AI system stack

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

Layer 4: `agent-core/openjiuwen/core/retrieval/` (vector, hybrid, graph, agentic). Layer 5: `harness/prompts/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/agentic/react_agent.py`. Layer 6: `harness/rails/security_rail.py`, `guardrail_rail.py`, `subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/event.py`. Layers 1-3 are external.

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

`ProviderUsage` (`core/context_engine/usage/provider_usage.py:14`) normalizes `cached_input_tokens` from provider usage metadata. `session_aggregator.py:45` tracks cache hit rates. `full_compact_processor.py:184` compacts at 180 k tokens — this indirectly stabilizes prefixes. The framework observes hits; it does not control caching.

</details>

---

## 3. Base model versus instruct model

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** A base model is the raw pretrained checkpoint; an instruct model is the same weights after the alignment pipeline.

**Key points.**

- Alignment pipeline: pretrain → SFT on demonstrations → reward model → RL fine-tuning (RLHF or DPO)
- A base model continues text; an instruct model follows instructions and produces structured responses
- A guardrail layer at inference time supplements but does not substitute for alignment training

**Concept.** A base model is the raw pretrained checkpoint — next-token prediction on web-scale data, no instruction following. An instruct (or chat) model is the same weights after the alignment pipeline: supervised fine-tuning (SFT) on demonstration data, reward model training, and RLHF or DPO to match human preferences. The practical difference: a base model will continue text; an instruct model will follow instructions, decline harmful requests, and produce structured responses.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`agent_rl/online/backends/sft/trainer.py` is the SFT stage that produces instruct-model-like behavior from demonstration data. `PromptInjectionGuardrail` (`harness/rails/guardrail_rail.py`) provides inference-time safety supplement. The framework does not tag served models as base vs instruct in the config schema — `ProviderType + model_name` selects a model.

</details>

---

## 4. LLM API call lifecycle

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

Model clients (`core/foundation/llm/model_clients/openai_model_client.py:865`) send requests and receive streamed responses. `ProviderUsage` (`provider_usage.py:14`) captures input, output, and cached tokens from response metadata. `ObservabilityHandler` (`harness/observability/event.py:1`) logs model call events. `usage_cost.py:101` is the session billing meter. Steps 1-3 (API gateway, load balancer, tokenization) are the provider's infrastructure.

</details>

---
