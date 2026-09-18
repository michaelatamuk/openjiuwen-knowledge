# LLM architecture patterns — how each is built + how Jiuwen maps

Based on the recurring list *Architecture Patterns I've Seen Repeatedly in LLM Projects*. Each of the seven patterns is described, then mapped to what this codebase actually provides (mechanism + anchors), including the gaps a real implementation would have to fill.

See [README](README.md) for the shared conventions (anchor format, repo layers).

---

## 1. Simple RAG pipeline

**Pattern:** the most common starting point. Query is embedded → a vector database returns top-k similar documents → documents are stuffed into a prompt → the LLM generates the answer.

**Used for:** FAQ bots, internal document search, basic knowledge assistants.

**Jiuwen:** Implemented end to end as composable pieces rather than a packaged app: ingest via `parse_files` → `chunk_documents` → `build_index`; query via `retrieve` → `vector_store.search`; the workflow `KnowledgeRetrievalComponent` concatenates results into a `context` string and `LLMComponent` formats it into the prompt. Gap: no single "simple RAG" agent, and retrieved context is inserted with no token budgeting.

```mermaid
flowchart LR
    Q["query"] --> QE["embed"] --> VDB["vector DB: top-k"]
    VDB --> STUFF["stuff into prompt"] --> LLM["generate"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:96/110/182</code> — ingest + retrieve<br>&bull; <code>agent-core/openjiuwen/core/retrieval/retriever/vector_retriever.py:78</code> — embed query → search<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/resource/knowledge_retrieval_comp.py:109/243</code> — context assembly<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/llm/llm_comp.py:654</code> — prompt template</sub>

</details>

## 2. Modular RAG with reranking

**Pattern:** the upgrade once simple RAG returns irrelevant context. A retriever pulls a larger candidate set, a reranker reorders by actual relevance to the query, and only the top results enter the prompt.

**Used for:** legal, medical, or research tools where retrieval accuracy affects trust.

**Jiuwen:** The reranker modules exist (`StandardReranker` cross-encoder, `ChatReranker` LLM-judge, `DashscopeReranker`) but are **not wired into the KB path** — only the graph store calls `rerank`, and `top_k` is static. So "retrieve N, rerank to K" is not available out of the box; the retrievers also drop metadata `filters`.

```mermaid
flowchart LR
    Q["query"] --> R["retriever: larger N"] --> RK["reranker: reorder"] --> K["top-K into prompt"]
    RK -.->|"KB path: not wired"| X["graph store only; static top_k=5"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/foundation/store/base_reranker.py:37/41</code> — <code>Reranker</code> ABC<br>&bull; <code>agent-core/openjiuwen/core/retrieval/reranker/standard_reranker.py:23</code> — <code>StandardReranker</code> (<code>/rerank</code>)<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/milvus/milvus_support.py:458</code> — reranker applied only in graph store<br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:182</code> — KB path calls no reranker<br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:46</code> — <code>top_k: int = 5</code></sub>

</details>

## 3. Agentic tool-calling pattern

**Pattern:** the model decides when to call external functions. It receives the query and a tool list, emits a structured tool call instead of an answer, the tool executes and the result is fed back, and the model either calls another tool or returns a final answer.

**Used for:** data lookups, sending emails, querying a database, checking live information.

**Jiuwen:** This is the ReAct loop plus the ability manager. Cards become JSON Schema via the callable schema extractor, the ability manager builds the model-facing tool list and dispatches parsed `tool_calls`, and `LocalFunction.invoke` validates arguments.

```mermaid
sequenceDiagram
    participant Model
    participant Host
    participant Tool
    Host->>Model: query + tools
    Model-->>Host: tool_call
    Host->>Tool: execute (validate args)
    Tool-->>Host: result
    Host->>Model: tool result
    Model-->>Host: answer (or another tool_call)
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2740/2793/2813</code> — loop / answer / execute<br>&bull; <code>agent-core/openjiuwen/core/single_agent/ability_manager.py:984/1078</code> — tool list + dispatch<br>&bull; <code>agent-core/openjiuwen/core/foundation/tool/utils/callable_schema_extractor.py:20</code> — card → JSON Schema<br>&bull; <code>agent-core/openjiuwen/core/foundation/tool/function/function.py:82</code> — argument validation</sub>

</details>

## 4. Planner–executor pattern

**Pattern:** a planner breaks a complex request into subtasks; one or more executors carry each out; results are combined into a final response. Common in multi-step agent systems.

**Used for:** research assistants, report generation, multi-source data analysis.

**Jiuwen:** Two paths. `DeepAgent`'s outer task loop runs a full inner ReAct invoke per round while a persistent `TaskPlan`/todos carry state; `TaskPlanningRail` registers the todo tools and injects planning guidance (`Plan` mode adds a `task_tool` to delegate). `agent_teams` adds supervisor/leader decomposition, and a dedicated plan subagent exists.

```mermaid
flowchart TD
    T["complex task"] --> P["planner: task plan / todos"]
    P --> E1["executor round 1 (inner ReAct)"]
    P --> E2["executor round 2"]
    E1 --> C["combine (task loop state)"]
    E2 --> C
    C --> A["final answer"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2694</code> — outer task loop<br>&bull; <code>agent-core/openjiuwen/harness/rails/task_planning_rail.py:31/108</code> — planning layer + todo tools<br>&bull; <code>agent-core/openjiuwen/harness/tools/todo.py:193</code> — <code>TodoCreateTool</code><br>&bull; <code>agent-core/openjiuwen/harness/tools/subagent/task_tool.py:194/657</code> — subagent delegation<br>&bull; <code>agent-core/openjiuwen/core/multi_agent/teams/hierarchical_tools/hierarchical_team.py:101/108</code> — supervisor (agents-as-tools); <code>agent-core/openjiuwen/harness/subagents/plan_agent.py:88</code> — plan subagent</sub>

</details>

## 5. Critic or reflection loop

**Pattern:** a self-check before returning. The primary agent drafts; a critic reviews it against the request or rules; if it fails, the primary revises. Adds a verification step for high-stakes output.

**Used for:** financial summaries, compliance checks, high-stakes outputs where a wrong answer is costly.

**Jiuwen:** There is no generic draft→critique→revise loop in the single-agent ReAct path, but the pieces exist: a **verification agent** restricted to read-only tools that must show verbatim evidence and emit PASS/FAIL/PARTIAL; an `agent_teams` reviewer that scores `Correctness`/completeness with rework thresholds; and the RSI weighted-rubric judge. These run as separate review layers, not as an in-loop reflection that blocks generation.

```mermaid
flowchart TD
    D["primary draft"] --> CR["critic: verification agent / reviewer / RSI judge"]
    CR -->|"pass"| OUT["return"]
    CR -->|"fail"| REV["revise"] --> CR
    CR -.->|"not in-loop: separate review layer"| X["no generic reflection loop"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/harness/rails/subagent/verification_rail.py:92</code> — <code>VerificationRail</code> allowlist; <code>agent-core/openjiuwen/harness/subagents/verification_agent.py:51</code> — PASS/FAIL/PARTIAL<br>&bull; <code>agent-core/openjiuwen/agent_teams/verification/reviewer.py:26/43/279</code> — review dimensions + rework thresholds<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:193</code> — weighted rubric judge</sub>

</details>

## 6. Memory-augmented agent

**Pattern:** context across sessions, not just one conversation. Short-term memory is the active context window; long-term memory is a vector store/DB of past interactions; retrieval decides what long-term memory is relevant to the current turn.

**Used for:** personal assistants, customer support.

**Jiuwen:** Short-term is `SessionModelContext` with a bounded `ContextMessageBuffer`; long-term is `LongTermMemory` with a typed taxonomy, and the product adds a SQLite/FTS5 hybrid index over markdown memory files. Retrieval-into-turn is a tool the model calls (`memory_search`), and `MemoryRail` suppresses it when daily memory is auto-loaded.

```mermaid
flowchart TD
    T["current turn"] --> ST["short-term: SessionModelContext (bounded buffer)"]
    T --> RT["retrieve relevant long-term memory (memory_search tool)"]
    LT["long-term: LongTermMemory / hybrid index"] --> RT
    ST --> M["model call"]
    RT --> M
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/context_engine/context/context.py:44</code> — <code>SessionModelContext</code>; <code>agent-core/openjiuwen/core/context_engine/context/message_buffer.py:11</code> — <code>ContextMessageBuffer</code><br>&bull; <code>agent-core/openjiuwen/core/memory/long_term_memory.py:69</code> — <code>LongTermMemory</code><br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:183/805</code> — product hybrid index<br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/tools/memory_tools.py:167</code> — <code>memory_search</code>; <code>agent-core/openjiuwen/harness/prompts/sections/memory.py:14</code> — when to call</sub>

</details>

## 7. Router pattern

**Pattern:** one entry point decides which subsystem handles the request. The query is classified and routed to a specialized agent/tool (SQL agent, search agent, summarization agent), so one generic prompt does not handle everything poorly.

**Used for:** mixed workloads where one prompt can't cover all request types.

**Jiuwen:** There is **no query-classification router**. Routing that exists is model tool choice (the model picks `memory_search` / retrieval / other tools), and `IntelliRouter` is model-**endpoint** routing (health/rate/latency), not query routing. `AgenticRetriever` derives its mode from `index_type`, not from the query.

```mermaid
flowchart TD
    Q["query"] --> C{"classify + route"}
    C -.->|"absent"| X["no query router"]
    Q --> TOOL["model tool choice (memory_search / retrieval / …)"]
    Q --> EP["IntelliRouter: endpoint routing (health/rate/latency)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/tools/memory_tools.py:167</code> — tool the model chooses<br>&bull; <code>agent-core/openjiuwen/agent_teams/models/allocator.py:559</code> — <code>build_model_allocator</code> (endpoint strategies)<br>&bull; <code>agent-core/openjiuwen/core/foundation/llm/model_clients/intelli_router_model_client.py:32</code> — <code>ReliableRouter</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/retriever/agentic_retriever.py:155</code> — mode from <code>index_type</code>, not the query</sub>

</details>

---

## Summary: pattern → Jiuwen status

| Pattern | Jiuwen status | Notes |
|---|---|---|
| 1. Simple RAG | Present (composable) | ingest/retrieve/prompt pieces; no packaged app, no context budgeting |
| 2. Modular RAG + rerank | Partial | reranker exists but not wired into KB; static `top_k`; filters dropped |
| 3. Agentic tool-calling | Strong | ReAct loop + ability manager + schema validation |
| 4. Planner–executor | Strong | DeepAgent task loop + TaskPlanningRail/todos + subagents + teams |
| 5. Critic / reflection | Partial | verification agent + reviewer + RSI judge, but no in-loop reflection |
| 6. Memory-augmented agent | Strong | SessionModelContext + LongTermMemory + product hybrid index + memory tool |
| 7. Router | Weak | no query router; only model tool choice + endpoint routing |
