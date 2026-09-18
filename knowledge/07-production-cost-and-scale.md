# Production, cost and scale

## 1. Where cost concentrates: embedding is cheap and one-time, generation scales with traffic

**Title.** Where cost concentrates

**Summary.** Embedding is a one-time, change-only indexing cost; the recurring traffic-scaling cost is generation, especially input tokens from long context. Optimize generation.

**Key points.**

- Embedding = one-time indexing cost.
- Generation scales with traffic.
- Input tokens dominate with long context.

**General.** Embedding is a one-time (or change-only) indexing cost and is cheap per token; the recurring, traffic-scaling cost is generation — especially input tokens when you stuff long context. So optimization effort should go to the generation loop (fewer iterations, smaller context, cheaper model) more than to embeddings. Measure input vs output tokens separately.

![diagram](assets/diagrams/678787d15a134709bd7c3e9d506f423f68401abd.png)

**Jiuwen.** Embedding is batched and effectively one-time (chunked with batch size 8 and concurrency 50, run at index or update time). Generation is what is metered: usage accumulates provider-reported input, output, and total tokens, and cost tracking focuses on session generation cost. Optimization effort belongs on generation.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Embedding is batched and effectively one-time: `APIEmbedding` chunks texts (`max_batch_size=8`, `max_concurrent=50`) and `compute_chunk_embeddings` runs at index/update time. Generation is what is metered: `usage_cost.add_session_usage` accumulates provider-reported `input_tokens`/`output_tokens`/`total_tokens` (and optional costs) per session, fed by every `chat.usage_metadata` event. Core tracks KV/prompt-cache hit rates (tokens, not dollars). The only per-token dollar rates are hardcoded estimates in the auto-harness budget rail.

<sub>&bull; `agent-core/openjiuwen/core/retrieval/embedding/api_embedding.py:45` — max_batch_size: int = 8, max_concurrent: int = 50; :167 batch + gather<br>&bull; `agent-core/openjiuwen/core/retrieval/indexing/indexer/embed_chunks.py:21` — compute_chunk_embeddings at index/update time<br>&bull; `agent-core/openjiuwen/core/context_engine/usage/provider_usage.py:14` — normalizes input/cache tokens; agent-core/openjiuwen/core/context_engine/usage/session_aggregator.py:45 — cache hit-rate aggregation<br>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:101` — add_session_usage; jiuwenswarm/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:17212 — usage events<br>&bull; `agent-core/openjiuwen/auto_harness/rails/budget_rail.py:24` — input 3e-6 / output 15e-6 USD per token; :85 cost computed</sub>

</details>

<sub>_Canonical source: `source/rag-practical-interview-questions_for_engineers.md`_</sub>

---

## 2. How would you reduce cost for a high-volume RAG system without degrading answer quality

**Title.** Reducing cost in high-volume RAG

**Summary.** Cut the dominant input-token/generation cost: rerank a larger candidate set down to a smaller k, cache (exact and semantic), route easy queries to smaller models, shorten prompts/context, and summarize history.

**Key points.**

- Rerank down to a smaller k.
- Cache exact and semantic.
- Route easy queries to smaller models.
- Shorten prompts/context; summarize history.

**General.** Cut the dominant (input-token/generation) cost: rerank a larger candidate set down to a smaller k, cache (exact and semantic), route easy queries to smaller models, shorten prompts (fewer examples, tighter context), summarize long chunks, and cap the agent's iterations. Prefer quality-preserving levers (rerank+tighten, cache, route) over blind k reduction.

![diagram](assets/diagrams/c7f7f483bc92419e0f660f0bc31e4fb0118a1e48.png)

**Jiuwen.** The product tracks provider session cost and enforces a cap; core caps repetition via max iterations, a team budget ledger, and anomaly and dedup rails; conversation compaction reduces context tokens. But embedding cost is not tracked, there is no semantic or response cache, no reranker, and routing is by availability — so several standard levers are absent.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The product tracks provider-reported session cost and enforces a per-session cap; core caps repetition via `max_iterations`, team `BudgetLedger`, and anomaly/dedup rails; conversation compaction reduces context tokens. But embedding cost is never tracked, there is no semantic/response cache, no rerank-to-K lever in the KB, and no query-difficulty/cost-aware model routing.

<sub>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171/196` — session cost cap<br>&bull; `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288` — max_iterations; agent-core/openjiuwen/harness/schema/config.py:252 — harness default<br>&bull; `agent-core/openjiuwen/agent_teams/workflow/engine/budget.py:27` — BudgetLedger<br>&bull; `agent-core/openjiuwen/core/context_engine/processor/compressor/full_compact_processor.py:184` — 180k compaction<br>&bull; `agent-core/openjiuwen/agent_teams/models/allocator.py:559` — availability routing (not cost/quality)</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`_</sub>

---

## 3. How do you control cost in a system where usage scales unpredictably

**Title.** Controlling unpredictable cost

**Summary.** Bound the loop (iterations/rounds/time), cap tokens per request and session, let cheap models do cheap work, cache, offload/summarize context, and surface per-run cost to budget and alert.

**Key points.**

- Bound iterations/time.
- Cap tokens per request/session.
- Cheap models for cheap work.
- Surface per-run cost.

**General.** Bound the loop (max iterations/rounds/time), cap tokens per request and per session, make cheap models do cheap work, cache, offload/summarize context, and surface per-run cost so it can be budgeted and alerted. Retries and huge tool outputs are common hidden cost sources.

![diagram](assets/diagrams/5daa572e4843c74dac123fdf41db6580efc6130d.png)

**Jiuwen.** The product tracks provider-reported session cost and enforces a per-session cap: totals accumulate under a lock, the limit is set only when provider cost metadata is available, and a check raises when over. Core limits repetition via max iterations and anomaly rails. There is no per-request token cap or time budget.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The product tracks provider-reported session cost and enforces a per-session cap: totals accumulate under a lock, `set_session_cost_limit` sets a ceiling only when provider cost metadata is available, and `raise_if_session_cost_limit_exceeded` raises when over. Core limits repetition via ReAct `max_iterations` (default 5, harness 15), team `BudgetLedger` token ceilings, and `ModelAnomalyDetectionRail`'s tool-loop compaction/bailout. `ToolCallDeduplicationRail` counts repeated read-only calls and warns.

<sub>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171` — raise_if_session_cost_limit_exceeded; :196 set_session_cost_limit (requires provider cost)<br>&bull; `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288` — max_iterations; agent-core/openjiuwen/harness/schema/config.py:252 — harness default 15<br>&bull; `agent-core/openjiuwen/agent_teams/workflow/engine/budget.py:27` — BudgetLedger<br>&bull; `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74/90` — tool-loop threshold + bailout<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157` — cross-turn repeat counter; agent-core/openjiuwen/harness/goal/evaluation.py:298 — max_attempts</sub>

![diagram](assets/diagrams/ddbd4a0f746840bd1e1c4ea0ec61564d8bed954f.png)

</details>

<sub>_Canonical source: `source/genai-interview-questions_for_engineers.md`_</sub>

---

## 4. First cut at 50% cost reduction: route simple queries to a smaller model, reduce top-k

**Title.** First cut: 50% cost reduction

**Summary.** Cheapest high-impact cuts: route easy queries to a smaller model, lower top-k, cache, shorten the prompt, and reduce the agent's iteration cap.

**Key points.**

- Route easy queries to a smaller model.
- Lower top-k.
- Cache.
- Shorten prompt; lower iteration cap.

**General.** The cheapest high-impact cuts: route easy queries to a smaller/cheaper model (classify query difficulty first), lower `top_k`, cache, shorten the prompt (fewer examples, tighter context), and reduce the agent's iteration cap. Start with model routing and top-k because they cut the dominant (generation/input-token) cost directly.

![diagram](assets/diagrams/99274c1c6f20b94d7c4a8e0f70d7b33e3fe5e207.png)

**Jiuwen.** Model selection here is about availability and endpoint distribution, not cost or query difficulty: the allocator dispatches strategies (round robin, by model name, router, intelli router), and allocation happens at member construction from a model-name hint and is immutable afterward. Difficulty-based routing to a cheaper model must be added.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Model selection is about availability and endpoint distribution, not cost or query difficulty. `build_model_allocator` dispatches four availability strategies (`round_robin`, `by_model_name`, `router`, `intelli_router`); allocation happens at member construction from a `model_name` hint and is immutable per member. `IntelliRouter` is rate-aware only through `tpm`/`rpm`. The only retrieval-size knob is the static `top_k` (default 5). There is no query-classification-to-model routing and no cost-aware top-k policy.

<sub>&bull; `agent-core/openjiuwen/agent_teams/models/allocator.py:559` — build_model_allocator (4 availability strategies); :240 ByModelNameAllocator; :520 resolve_member_model (no query awareness)<br>&bull; `agent-core/openjiuwen/agent_teams/models/pool.py:38` — ModelPoolEntry; :278 tpm/rpm rate-aware only<br>&bull; `agent-core/openjiuwen/core/retrieval/common/config.py:46` — top_k: int = 5 (only retrieval-size config)<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:773` — exact embedding cache (no semantic cache)</sub>

</details>

<sub>_Canonical source: `source/rag-practical-interview-questions_for_engineers.md`_</sub>

---

## 5. Designing caching for repeated or semantically similar queries

**Title.** Designing caching

**Summary.** Layer caches: exact-match response/prompt cache, provider prefix/prompt caching, an embedding cache, and a semantic cache that embeds the query and returns a prior answer above a similarity threshold.

**Key points.**

- Exact-match response cache.
- Provider prefix/prompt cache.
- Embedding cache.
- Semantic cache with a similarity threshold.

**General.** Layer caches: exact-match response/prompt cache, provider prefix/prompt caching, embedding cache, and — harder — a semantic cache that embeds the query and returns a prior answer for similar queries above a similarity threshold. The semantic cache needs a threshold and invalidation strategy, and exact-match caches need a stable key including model and parameters.

![diagram](assets/diagrams/c6dc3928a4fba131b5557e02420da9d3feb31929.png)

**Jiuwen.** Caching is exact-match, not semantic. Core has a session KV-cache runtime with affinity and lineage identities to reuse inference KV state; the product memory index keeps a SQLite embedding cache keyed by text hash; agent evolution has its own cache. There is no semantic response cache or general provider prefix caching.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Caching is exact-match, not semantic. Core has a session KV-cache runtime with affinity/lineage identities (parent/child sessions, team members, compressors) to reuse inference KV state. The product memory index keeps a SQLite `embedding_cache` keyed by text hash, and `agent_evolving` has its own embedding cache. `ToolCallDeduplicationRail` is an exact `(tool_name, args-hash)` per-turn result cache for read-only tools. Local vLLM/transformers use prefix/prompt caches.

<sub>&bull; `agent-core/openjiuwen/core/kv_cache/kv_cache_runtime.py:32` — KVCacheRuntime; agent-core/openjiuwen/core/kv_cache/__init__.py:10 — KVCacheAffinityConfig<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:31` — EMBEDDING_CACHE_TABLE; :773 text-hash lookup before embedding<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:47` — exact per-turn tool result cache<br>&bull; `agent-core/openjiuwen/core/retrieval/lazy_load.py:25` — lazy import cache; agent-core/openjiuwen/core/context_engine/token/tiktoken_counter.py:221 — reusable encodings<br>&bull; `agent-core/openjiuwen/agent_evolving/ttse/stores.py:522` — embedding cache limit; agent-core/openjiuwen/symphony/retrieval/llm/vllm/client.py:176 — prefix cache</sub>

![diagram](assets/diagrams/82f41b4e178809cfcfdf4dc9e5bdab722df1857e.png)

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---

## 6. Reducing latency in a multi-step LLM pipeline

**Title.** Reducing latency

**Summary.** Stream tokens so time-to-first-token matters more than total; parallelize independent steps; cache prompts/embeddings; route easy steps to faster models; don't block the event loop.

**Key points.**

- Stream (optimize TTFT).
- Parallelize independent steps.
- Cache prompts/embeddings.
- Route easy steps to faster models.

**General.** Stream tokens so time-to-first-token matters more than total; run independent steps in parallel; cache prompts/prefixes and embeddings; route easy steps to faster/smaller models; and avoid blocking the event loop. Measure TTFT and per-stage latency to find the bottleneck.

![diagram](assets/diagrams/0fa009061ba7b7cab8222abab8913c5b5b81617d.png)

**Jiuwen.** End-to-end streaming is supported and TTFT is measured per model call. Shared persistent HTTP clients avoid per-call TLS setup, parallel tool execution shortens multi-tool turns, and local inference uses prompt and prefix KV caching. Streaming, connection reuse, and TTFT measurement are in place.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

End-to-end streaming is supported (ReAct `stream` → session stream iterator → WebSocket chunk frames), and TTFT is measured per model call (`ttft_ms`). Shared persistent HTTP clients avoid per-call TLS setup, parallel tool execution shortens multi-tool turns, and local inference uses prompt/prefix KV-cache reuse. `IntelliRouter` provides a reliable router across deployments, and the product caches built model objects by name.

<sub>&bull; `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2938` — stream entry; :1758 ttft_ms<br>&bull; `agent-core/openjiuwen/core/foundation/llm/model.py:197` — stream first-chunk/idle timeouts<br>&bull; `agent-core/openjiuwen/core/kv_cache/kv_cache_runtime.py:32` — session KV-cache runtime<br>&bull; `agent-core/openjiuwen/symphony/retrieval/llm/vllm/client.py:176` — prepare_prefix_cache<br>&bull; `agent-core/openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py:32` — ReliableRouter<br>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:6353` — model object cache by name</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---

## 7. Multithreading vs. multiprocessing, which matters more for I/O-bound LLM API calls

**Title.** Threads vs processes for I/O-bound LLM calls

**Summary.** For I/O-bound calls, async or threads beat multiprocessing: the CPU is idle while waiting, so you want concurrency, not extra processes. Async is the most efficient.

**Key points.**

- I/O-bound → concurrency, not processes.
- Async is most efficient.
- Multiprocessing only for CPU-bound work.

**General.** For I/O-bound work (network calls to LLM APIs, vector DBs), async I/O or threads beat multiprocessing: the CPU is idle while waiting, so you want concurrency, not extra processes. Async is the most efficient (no thread-per-request overhead) when your stack is async end to end; threads are the fallback for blocking SDKs. Multiprocessing only pays off for CPU-bound work (local inference, heavy parsing) because it escapes the GIL.

![diagram](assets/diagrams/a7dce77e816d5bf9a10f12b0ba6a897b61d6ace3.png)

**Jiuwen.** The LLM path is single-process asyncio/anyio: async HTTP clients share a process-global connection pool, and async model clients are cached process-wide with bounded limits. Blocking work is offloaded to threads. It is async-first with a shared connection pool, matching I/O-bound guidance.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The LLM path is single-process asyncio/anyio. `httpx.AsyncClient` instances share a process-global `AsyncConnectionPool` via `HttpXConnectorPool`, and `AsyncOpenAI`/`AsyncAnthropic` clients are cached process-wide with `httpx.Limits(max_connections=100, max_keepalive_connections=20)`. Blocking work is offloaded with `asyncio.to_thread`/`run_in_executor`, never `multiprocessing`. Embeddings use an `asyncio.Semaphore(max_concurrent)` (default 50), with a `ThreadPoolExecutor` only for the sync facade. `multiprocessing` appears in tests, the observability trace store, process isolation, and `agent_rl`'s offline `parallel_executor` — not as an LLM throughput strategy.

<sub>&bull; `agent-core/openjiuwen/core/common/clients/llm_client.py:52` — HttpXConnectorPool (AsyncConnectionPool)<br>&bull; `agent-core/openjiuwen/core/foundation/llm/model_clients/openai_model_client.py:383` — process-wide _client_cache; :1118 httpx.Limits(max_connections=100, max_keepalive_connections=20)<br>&bull; `agent-core/openjiuwen/core/foundation/llm/model_clients/anthropic_model_client.py:719` — same pooling for AsyncAnthropic<br>&bull; `agent-core/openjiuwen/core/retrieval/embedding/api_embedding.py:55` — asyncio.Semaphore(max_concurrent); :120 ThreadPoolExecutor for sync path<br>&bull; `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:5326` — asyncio.to_thread(...) offload; jiuwenswarm/jiuwenswarm/server/runtime/agent_warm_pool.py:154 — semaphore-bounded warm pool</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---

## 8. What happens to your architecture at 10x current traffic

**Title.** Architecture at 10x traffic

**Summary.** You hit dependencies and queues before arithmetic: provider rate limits and 429s, serialized tool/DB access, memory pressure from context, and connection pools. Cost scales with tokens.

**Key points.**

- Provider rate limits/429s first.
- Serialized tool/DB access.
- Memory pressure from context.
- Connection pools.

**General.** You hit dependencies and queues before arithmetic: provider rate limits and 429s, serialized tool/DB access, memory pressure from context, and connection pools. Costs scale roughly linearly with tokens but can super-linearly if retries or coordination rise. Fixes are caching, concurrency limits, queues/shards, backpressure, and cheaper routing — plus autoscaling at the process boundary.

![diagram](assets/diagrams/a02ada8ba84ef2055a581248203f1c890326a0af.png)

**Jiuwen.** The system has per-process bounded resources rather than elastic scaling: LLM HTTP concurrency is capped by a shared pool (100 connections, 20 keepalive), embeddings by a semaphore (default 50, batch 8), team sub-agent fan-out by a semaphore (default 10), and the warm pool and messaging have their own bounds. At 10x the first limits are these per-process caps.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The system has per-process bounded resources rather than elastic scaling. LLM HTTP concurrency is capped by a shared httpx pool (`max_connections=100`, keepalive 20); embeddings by a semaphore (default 50) with batch size 8; team sub-agent fan-out by a semaphore (default 10); the warm pool and message queues have their own bounds. Internal channels use bounded `asyncio.Queue(maxsize=...)`; workflow HTTP supports token-bucket rate limiting; retries/backoff exist at model and tool layers. There is no autoscaling.

<sub>&bull; `agent-core/openjiuwen/core/common/clients/connector_pool.py:21` — limit: 100, limit_per_host: 30; agent-core/openjiuwen/core/foundation/llm/model_clients/openai_model_client.py:1118 — pool limits<br>&bull; `agent-core/openjiuwen/core/retrieval/embedding/api_embedding.py:55` — concurrency semaphore<br>&bull; `agent-core/openjiuwen/core/multi_agent/teams/hierarchical_msgbus/p2p_ability_manager.py:34` — max parallel sub-agents<br>&bull; `agent-core/openjiuwen/core/workflow/components/tool/http/http_request_component.py:110` — HttpRateLimitConfig<br>&bull; `agent-core/openjiuwen/core/runner/message_queue_inmemory.py:34` — bounded queue; agent-core/openjiuwen/harness/subagent_runtime/activity_events.py:53 — bounded activity queue<br>&bull; `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:35` — backoff schedule; jiuwenswarm/jiuwenswarm/server/runtime/agent_warm_pool.py:154 — warm-pool semaphore split</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---
