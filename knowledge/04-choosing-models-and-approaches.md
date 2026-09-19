# Choosing models and approaches

## 1. Deciding when a problem actually needs an LLM versus a simpler rule-based system

<span class="badge badge-type">Compare</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Use rules when logic is enumerable, must be auditable, or needs exact reproducibility (validation, pattern routing, permissions, arithmetic, parsing). Use an LLM when the task is semantic or open-ended.

**Key points.**

- Rules: enumerable, auditable, reproducible.
- LLM: semantic, ambiguous, open-ended.
- Prefer rules; add the LLM where needed.

**Concept.** Use a rule-based/deterministic system when the logic is enumerable, must be auditable, or needs exact reproducibility (validation, routing by known patterns, permission checks, arithmetic, parsing). Use an LLM when the task is semantic, open-ended, or handles ambiguity that rules cannot enumerate (summarization, intent, extraction from messy text). Rules for control, LLM for meaning; often both.

![diagram](assets/diagrams/8ad87aa43f3e7cfa39c57a16a4a3c26b8566b81a.png)

**In Jiuwen.** The codebase deliberately routes many decisions through deterministic code. The permission engine is a pure rule and AST engine — its docstring notes the model is not used on the permission path — evaluating tiered regex rules and a shell AST before falling back to ask. Safety-critical decisions are rule-based, not model-based.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

The codebase deliberately routes many decisions through deterministic code. The permission engine is a pure rule/AST engine — its docstring notes the model is not used on the permission path — evaluating tiered regex rules and a tree-sitter shell AST before falling back to ASK. The product's auto-permission layer has deterministic routes that hard-block/ask by URL scheme, egress fields, and capability side-effects before any reviewer is consulted. Lexical/deterministic retrieval coexists with vector paths (SQLite FTS5 BM25, RRF rank fusion), and structured JSON is extracted with deterministic parsers. Conversely, memory extraction uses an LLM key-information classifier because judging "is this worth remembering" is semantic.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/security/permission_engine/core.py:192` | docstring: LLM not used on the permission path |
| `agent-core/openjiuwen/harness/security/permission_engine/toolguard/tool_policy.py:588` | rule-based tiered policy; agent-core/openjiuwen/harness/security/permission_engine/toolguard/shell_ast.py:82 — deterministic parse |
| `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/permissions/auto_decision.py:73` | deterministic_guard_route; :116 deterministic_domain_route |
| `jiuwenswarm/jiuwenswarm/agents/harness/common/memory/internal.py:165` | bm25_rank_to_score; jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:1044 FTS BM25 |
| `agent-core/openjiuwen/core/retrieval/utils/fusion.py:15` | rrf_fusion; agent-core/openjiuwen/core/foundation/store/index/simple_memory_index.py:348 sort by score |
| `agent-core/openjiuwen/core/context_engine/context/message_buffer.py:74` | deterministic drop beyond 2× |
| `agent-core/openjiuwen/rsi/harness_rsi/auto_harness/infra/parsers.py:147` | deterministic JSON extraction |
| `agent-core/openjiuwen/core/memory/process/extract/memory_analyzer.py:26` | LLM classifier (semantic) |

</details>

---

## 2. Larger model vs. smaller, faster one for a given task

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Match capability to difficulty: a large model for reasoning/ambiguity, a small/fast one for classification, extraction, routing, and formatting; measure quality per task and weigh latency and cost.

**Key points.**

- Large for reasoning/ambiguity.
- Small/fast for classification/extraction/routing.
- Measure quality per task; weigh latency/cost.

**Concept.** Match model capability to task difficulty: use a large model for reasoning/ambiguity and a small/fast one for classification, extraction, routing, and formatting. Measure quality per task and weigh latency and cost; route by task, and fall back to the larger model only when needed. A leaderboard score is a prior, not a per-task decision.

![diagram](assets/diagrams/dd5563d6e052d9bcf4fae828491a201d943a8eca.png)

**In Jiuwen.** Model selection here is about availability and endpoint distribution, not task quality. A team can declare a pool of endpoints or a router config, and allocators pick an entry by rotation or an explicit model-name hint at member construction. Capability-based routing by task difficulty must be added by the caller.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Model selection here is about availability and endpoint distribution, not task quality. A team can declare a `model_pool` of endpoints or a `ModelRouterConfig`/`IntelliRouterConfig` convenience shape; allocators (`RoundRobin`, `ByModelName`, `Router`, `IntelliRouter`) pick an entry by rotation or an explicit `model_name` hint supplied per agent/task. IntelliRouter is rate-aware only through `tpm`/`rpm` budgets. The `ModelPoolEntry` metadata comment ("weights, affinity hints") is documented but not implemented.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/agent_teams/models/pool.py:38` | ModelPoolEntry; :133 ModelRouterConfig; :241 IntelliRouterDeployment; :314 IntelliRouterConfig; :278 tpm/rpm rate-aware; :95 "weights/affinity hints" (documented, not implemented) |
| `agent-core/openjiuwen/agent_teams/models/allocator.py:176` | round-robin; :240 by-model-name; :452 IntelliRouter; :559 build_model_allocator; :28 allocation-vs-reliability docstring |
| `agent-core/openjiuwen/harness/schema/config.py:242` | / agent-core/openjiuwen/harness/schema/deep_agent_spec.py:441 — per-agent/task model config |

</details>

---

## 3. "Compare two approaches" tests tradeoff reasoning tied to numbers, not a correct pick

<span class="badge badge-type">Mechanism</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** 'Compare two approaches' tests tradeoff reasoning tied to numbers, not a correct pick.

**Key points.**

- top_k defaults 5, no adaptive policy.
- Reranking absent from the KB path.
- Model allocation is availability-based.
- Session cost tracked and capped.

**Concept.** RAG vs. fine-tuning, 7B vs. 70B, top-5 vs. top-20 retrieval. "It depends" without naming the constraint (latency budget, cost per query, accuracy floor) is not enough; put a number on it — e.g. "at a 200ms budget, reranking 20 docs is not viable, so cap retrieval at 5." State the constraint, then the decision it forces, then the number. Tie retrieval size to latency/tokens, model size to accuracy floor vs cost, and reranking to the latency it buys in precision.

![diagram](assets/diagrams/05e403ee71c2ddfc9e280ece288ce292f189063b.png)

**In Jiuwen.** The relevant knobs are static and named: top-k defaults to 5 with no adaptive policy, reranking is not in the knowledge-base path, and model allocation is availability-based rather than cost or accuracy based, so routing easy queries to a smaller model is not automatic. Session cost is tracked and capped.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

The relevant knobs are static and named: `top_k` defaults to 5 (no adaptive policy), reranking is not in the KB path, and model allocation is availability-based, not cost/accuracy-based — so "smaller model for easy queries" is not automatic. Session cost is tracked and capped when the provider reports cost.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/core/retrieval/common/config.py:46` | top_k: int = 5 static |
| `agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:182` | no reranker in KB retrieve |
| `agent-core/openjiuwen/agent_teams/models/allocator.py:559` | build_model_allocator (availability strategies, not cost/accuracy) |
| `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171` | enforced session cost cap |

</details>

---

## 4. You're given a vague AI system design brief with no stated constraints — what do you ask first?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Extract the four binding constraints before proposing any architecture: latency budget, query volume, accuracy floor, and cost envelope.

**Key points.**

- Latency budget — real-time (≤200ms) or async? Rules out reranking and large-model calls in the critical path
- Query volume — p50/p99 RPS? Rules out expensive retrievers per query at scale
- Accuracy floor — what is the cost of a wrong answer? Rules out small/fast models for high-stakes tasks
- Cost envelope — $/query budget? Forces routing, caching, and smaller models when tight
- Propose an architecture only after these constraints are known

**Concept.** Before proposing any architecture, extract the four constraints that determine every significant tradeoff: (1) **latency budget** — is this real-time (≤200ms) or async? (2) **query volume** — requests per second, peak vs average; (3) **accuracy floor** — is a wrong answer a minor inconvenience or a safety/legal risk? (4) **cost envelope** — is this internal tooling or a consumer product at scale? These four drive every meaningful decision: latency budget rules out reranking or large-model calls in the critical path; accuracy floor rules out smaller models; volume rules out expensive retrievers. Propose an architecture only after these constraints are known.

![diagram](assets/diagrams/273ba137de748e5a5a1094f191d56ba73e713030.png)

**In Jiuwen.** The four constraint levers are each separately configurable: latency via ModelRequestConfig.timeout (agent-core/openjiuwen/core/foundation/llm/schema/config.py:214); volume via ModelPoolEntry tpm/rpm (agent-core/openjiuwen/agent_teams/models/pool.py:278); accuracy via score_threshold (agent-core/openjiuwen/core/retrieval/common/config.py:47); cost via auto_harness budget_rail dollar cap (agent-core/openjiuwen/auto_harness/rails/budget_rail.py:24). None are inferred automatically — operator must set based on use-case constraints.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

The deployment surface exposes these constraints as distinct configuration layers. Latency: `ModelRequestConfig.timeout` per call, agent `max_turns`. Volume/concurrency: `ModelPoolEntry` `tpm`/`rpm` caps, `APIEmbedding` `max_concurrent`. Accuracy tradeoff: `score_threshold` (retrieval), `temperature`, `max_tokens`. Cost: `auto_harness` budget rail (per-session dollar cap). None of these are inferred automatically — they must be set by the operator based on the use-case constraints.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/core/foundation/llm/schema/config.py:214` | ModelRequestConfig.timeout (latency) |
| `agent-core/openjiuwen/agent_teams/models/pool.py:278` | tpm/rpm (volume) |
| `agent-core/openjiuwen/core/retrieval/common/config.py:47` | score_threshold (accuracy lever) |
| `agent-core/openjiuwen/auto_harness/rails/budget_rail.py:24` | dollar cap (cost) |

</details>

---

## 5. How do you make a defensible model selection decision — what does the evaluation actually look like?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Define an eval set, run all candidates, record quality + latency + cost, plot the curves, and pick the knee — not the highest-accuracy option.

**Key points.**

- Eval set must be representative of the actual use-case distribution, not cherry-picked examples
- Run every candidate on the same eval set; record quality score, latency, and cost per query
- Plot cost-accuracy and latency-accuracy curves to find the knee: where extra spend buys diminishing quality gain
- Pick the option that meets the requirement with minimum overhead — not the top-accuracy option
- Jiuwen gap: evaluators measure quality only; cost and latency are not correlated to eval scores in the pipeline

**Concept.** "There's a tradeoff" is not an answer — it is the beginning of one. A defensible selection looks like: (1) define a representative eval set covering the actual use-case distribution (not cherry-picked examples); (2) run every candidate model (or configuration) on the same eval set; (3) record accuracy/quality score AND latency AND cost per query; (4) plot the cost-accuracy and latency-accuracy curves; (5) identify the **knee of the curve** — the point where additional cost or latency buys diminishing quality gain; (6) choose the option that meets the requirement with the least overhead, not the option with the highest absolute accuracy. Critically: the choice is a decision that follows from the requirement, not from intuition or a leaderboard.

![diagram](assets/diagrams/ca630e75b7187b71287dc7416fd4ded2649dfff7.png)

**In Jiuwen.** Quality measurement: FaithfulnessEvaluator, CorrectnessEvaluator, LLMAsJudge in agent-core/openjiuwen/agent_evolving/evaluator/metrics/. Session costs are tracked separately in jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:101 via add_session_usage. Gap: cost and latency are not correlated to per-query eval scores in the pipeline — the cost-accuracy curve must be assembled externally by the operator.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`agent_evolving/evaluator/` has `FaithfulnessEvaluator`, `CorrectnessEvaluator`, and `LLMAsJudge` — a principled eval framework for quality measurement. `dev_tools/tune/Trainer` supports `early_stop_score` for automated quality gating. Gaps: cost and latency are not recorded *alongside* quality in the eval pipeline — there is no built-in cost-accuracy curve generation. Session costs are tracked in `usage_cost.py` but not correlated to per-query eval scores.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/agent_evolving/evaluator/metrics/faithfulness_evaluator.py:1` | faithfulness metric |
| `agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:40` | LLM-as-judge (no cost/latency input) |
| `agent-core/openjiuwen/dev_tools/tune/trainer/trainer.py:38` | early_stop_score |
| `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:101` | session cost (not per-eval-query) |

</details>

---

## 6. What are the architectural layers of a modern AI product?

<span class="badge badge-type">Design</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Data → Model → Inference → Retrieval (RAG) → Orchestration → Safety → Infrastructure. Every production AI product runs all 7 simultaneously; most developers interact only with Layer 5.

**Key points.**

- Layer 1 Data: collection, cleaning, storage (vector DB/object store/data lake), versioning
- Layer 2 Model: base, fine-tuned, embedding, multimodal
- Layer 3 Inference: tokenizer, context window, temperature, KV cache, quantization
- Layer 4 RAG: vector store, retriever, reranker, context injection
- Layers 5-7: orchestration (prompt+memory+tools+agent loop), safety (guardrails+alignment+filter), infrastructure (GPU+LB+API GW+observability). Jiuwen covers Layers 4-6 directly.

**Concept.** A production AI system has seven functional layers, each independently scalable and debuggable: **(1) Data Layer** — raw collection, cleaning/deduplication/filtering, storage (vector DB, object store, data lake), and versioning (what data trained which model). **(2) Model Layer** — base model (raw language prediction), fine-tuned model (task-specific behavior), embedding model (text→vectors), multimodal model (text+image+audio). **(3) Inference Layer** — tokenizer, context window management, temperature/sampling controls, KV cache (reuse past token computations), quantization (reduce weight precision for speed/memory). **(4) Retrieval Layer** — vector store, retriever, reranker, context injection. **(5) Orchestration Layer** — prompt template, conversation memory, tools/function calling, agent loop (plan → act → observe → repeat), orchestration framework. **(6) Safety Layer** — guardrails, alignment (RLHF/CAI), content filter, hallucination detection. **(7) Infrastructure Layer** — GPU cluster (inference compute), load balancer, API gateway (auth/rate limiting/billing), observability (logs, latency, token counts, traces). Every production AI product runs all 7 layers simultaneously. Most developers interact only with Layer 5. The practical test: if something breaks, can you identify which layer it's in?

![diagram](assets/diagrams/596803976c5e2d9db77510d12bf828c3ab72d6fe.png)

**In Jiuwen.** The framework covers Layers 4-6 directly. Layer 4: agent-core/openjiuwen/core/retrieval/ (vector, hybrid, graph, agentic retrievers). Layer 5: harness/prompts/template.py (prompt), core/context_engine/ (memory + context), core/foundation/tool/base.py (tools), core/agentic/react_agent.py (agent loop). Layer 6: harness/rails/security_rail.py, guardrail_rail.py, subagent/verification_rail.py, guardian_rail.py. Layer 7 infrastructure is delegated: Milvus (vector store), vLLM (local inference), provider APIs, harness/observability/event.py (observability). Layers 1-3 (data pipeline, base model training, inference engine) are external.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

The framework maps onto Layers 4–6 directly and delegates the rest. **Layer 4**: full retrieval pipeline (vector, hybrid, graph, agentic retrievers). **Layer 5**: `PromptTemplate`, `ContextEngine`, `ToolCard` system, `ReactAgent` loop, framework rails. **Layer 6**: `SecurityRail`, `GuardrailRail`, `VerificationRail`, `GuardianRail`. Layer 7 infrastructure is provided by Milvus (vector store), vLLM (local inference), provider APIs (OpenAI, Anthropic), and `ObservabilityHandler`. Layers 1–3 (data pipeline, base model training, inference engine) are handled outside the framework.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/core/retrieval/` | full retrieval pipeline |
| `agent-core/openjiuwen/harness/prompts/template.py` | ; agent-core/openjiuwen/core/context_engine/; agent-core/openjiuwen/core/foundation/tool/base.py; agent-core/openjiuwen/core/agentic/react_agent.py |
| `agent-core/openjiuwen/harness/rails/security_rail.py` | ; agent-core/openjiuwen/harness/rails/guardrail_rail.py; agent-core/openjiuwen/harness/rails/subagent/verification_rail.py |
| `agent-core/openjiuwen/harness/observability/event.py` | ; Milvus + vLLM + provider APIs (external) |

</details>

---
