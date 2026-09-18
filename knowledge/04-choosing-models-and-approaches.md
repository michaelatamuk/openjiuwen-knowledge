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

**Concept.** RAG vs. fine-tuning, 7B vs. 70B, top-5 vs. top-20 retrieval. "It depends" without naming the constraint (latency budget, cost per query, accuracy floor) reads as a dodge. The strongest answers put a number on it — e.g. "at a 200ms budget, reranking 20 docs isn't viable, so I'd cap retrieval at 5." A strong answer includes: state the constraint, then the decision it forces, then the number. Tie retrieval size to latency/tokens, model size to accuracy floor vs cost, and reranking to the latency it buys you in precision.

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
