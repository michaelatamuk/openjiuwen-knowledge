# Agent failure modes

## 1. Tool call failures and idempotency

**Definition:** A tool call can time out after its action has already executed. Reads are idempotent and safe to retry with backoff; writes must track whether they were confirmed or only attempted. The standard fix is an **idempotency key** — a unique request ID passed with every write, which the server uses to deduplicate. State must persist across retries so the agent knows that `payment_id=abc123` was *attempted*, not merely that the last call failed. Any irreversible action needs a human-escalation path.

**Jiuwen:** Retry logic lives in the model-client layer (a per-provider retry decorator in `openai_model_client.py`). Tool calls are deduplicated at the argument level by `ToolCallDeduplicationRail`, which detects repeated `(tool, args)` hashes and warns or compacts. Idempotency keys, attempted-vs-confirmed state tracking, and a read/write tool taxonomy are not built in; `ToolCard` has no `idempotent` field, so retry safety is a design decision the developer encodes.

```mermaid
flowchart TD
    TOUT["tool call → timeout"] --> Q{"was action already executed?"}
    Q -->|"idempotent read"| RETRY["safe to retry with backoff"]
    Q -->|"write / side effect"| IK["idempotency key: pass unique ID, server deduplicates"]
    IK --> ST["state tracking: attempted vs confirmed"]
    ST -->|"unconfirmed"| RETRY2["safe to retry with same key"]
    ST -->|"confirmed but timed out"| ESC["human escalation / skip retry"]
    RETRY & RETRY2 -.->|"Jiuwen: model-client retry decorator"| MC["openai_model_client.py retry"]
    IK -.->|"not built in"| GAP["no ToolCard.idempotent flag, no idempotency-key pattern"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/foundation/llm/model_clients/openai_model_client.py</code> — per-provider retry decorator on API errors<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157</code> — <code>ToolCallDeduplicationRail</code>: repeated <code>(tool, args)</code> → warn/compact<br><code>agent-core/openjiuwen/core/foundation/tool/base.py</code> — <code>ToolCard</code> schema; no <code>idempotent</code> field<br><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py</code> — tool execution path; no confirmed-vs-attempted state</sub>
</details>

---

## 2. Stuck loops and loop invariants

**Definition:** Agents rarely crash visibly — they loop. A wrong conclusion is written back into context and reinforces itself; a bad tool call is retried unchanged. The mechanisms that prevent this are: a hard step cap (`max_iterations`); **divergence detection** that aborts when the last N tool calls or the output are structurally identical; **state deduplication** that canonicalises `(tool, input_hash)` and rejects re-execution of a confirmed call; **context compaction** to clear the noise that is reinforcing the wrong path; and a forced final answer at budget exhaustion.

**Jiuwen:** Concrete mechanisms exist: `ReactAgent.max_iterations` defaults to 5 (the harness raises it to 15); `ModelAnomalyDetectionRail` detects consecutive identical tool-call rounds via `ToolLoopCompactConfig` (off by default; it compacts then aborts); `ToolCallDeduplicationRail` counts repeated `(tool, args)`; `AgenticRetriever.max_iter` defaults to 2. Output-similarity divergence checks and a forced final answer at budget are not included, and `ToolLoopCompactConfig` must be enabled explicitly.

```mermaid
flowchart TD
    LOOP["agent stuck in loop"] --> CAP["max_iterations=5 (harness 15)"]
    LOOP --> DED["ToolCallDeduplicationRail: hash(tool,args) repeat counter"]
    LOOP --> ANOM["ModelAnomalyDetectionRail: identical tool rounds → compact (off by default)"]
    LOOP --> RETR["AgenticRetriever.max_iter=2 (clamped)"]
    LOOP -.->|"not included"| DIV["divergence check on output similarity"]
    LOOP -.->|"not included"| FORCE["forced final answer at budget exhaustion"]
    ANOM -.->|"off by default"| WARN["ToolLoopCompactConfig must be explicitly enabled"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations: int = Field(default=5)</code><br><code>agent-core/openjiuwen/harness/schema/config.py:252</code> — harness default iterations 15<br><code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74</code> — <code>ToolLoopCompactConfig</code> (default off); <code>:90</code> loop → compact → abort<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157</code> — repeat counter/warning<br><code>agent-core/openjiuwen/core/retrieval/retriever/agentic_retriever.py</code> — <code>max_iter=2</code> clamped</sub>
</details>

---

## 3. Output validation and ungrounded confidence

**Definition:** A fluent answer is not a correct one, so validation is an architectural stage rather than a review step. For factual claims, extract each claim and verify it against the retrieved sources (an NLI model or LLM-as-judge). For structured output, validate against the expected schema (JSON Schema, Pydantic) before acting. For high-stakes actions, insert a separate verification step before the result is trusted. Treat "the model said X" as a hypothesis, not a fact.

**Jiuwen:** Structured output validation is present through `StructuredAskUserRail` and Pydantic parsing of `ToolCall` responses in the tool-call path; the `SecurityRail` guardrail layer validates inputs and outputs for safety policy. Claim-level citation verification against retrieved context is not in the live path — the faithfulness evaluator in `agent_evolving/eval/` runs offline — and there is no general pre-action verification step; schema-guided generation constrains format but not content accuracy.

```mermaid
flowchart TD
    OUT["model output"] --> SV["schema validation: JSON/Pydantic (tool call parsing)"]
    OUT --> GV["guardrail: safety policy (SecurityRail)"]
    OUT -->|"factual claims"| CIT["citation check: claim vs retrieved context (not in live path)"]
    OUT -->|"high-stakes action"| VER["pre-action verification step (not included)"]
    SV -.->|"Jiuwen"| TOOL["ToolCall Pydantic parsing in react_agent"]
    GV -.->|"Jiuwen"| SEC["SecurityRail / guardrail backends"]
    CIT -.->|"offline only"| EVAL["agent_evolving/eval/"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py</code> — <code>ToolCall</code> Pydantic parsing; schema-validated tool calls<br><code>agent-core/openjiuwen/core/security/guardrail/builtin.py</code> — <code>SecurityRail</code> content classification<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/ask_user_rail.py</code> — structured output rail<br><code>agent-core/openjiuwen/agent_evolving/eval/</code> — faithfulness evaluation (offline)</sub>
</details>

---

## 4. Memory as a source of compounding error

**Definition:** Memory is a liability as well as a feature: a wrong assumption stored early can quietly shape every later decision. Mitigations: scope memory by task or session so assumptions do not leak across sessions; when a tool returns contradictory evidence, flag or discard the related memory instead of letting both coexist; tag memories with the context that produced them so superseded ones can be identified as stale; and compact the context window rather than accumulate it.

**Jiuwen:** Memory is session-scoped: `session_id` is the isolation unit and contexts do not cross sessions. The context engine compresses history (compressors at a 0.9× token budget and a full compaction at 180k tokens), and `MemoryForbiddenRail` blocks specific write patterns. Contradiction detection, per-memory staleness tags, and targeted invalidation are not provided — compaction is all-or-nothing.

```mermaid
flowchart TD
    SCOPE["memory scoping: session_id isolation"] -.-> SE["Jiuwen: session boundary is context isolation"]
    COMP["compaction: old rounds → summary block"] -.-> CE["ContextEngine: compressors at 0.9× / 180k tokens"]
    BLOCK["memory write blocking"] -.-> MFR["MemoryForbiddenRail"]
    INVAL["contradiction detection + targeted invalidation"] -.->|"not provided"| GAP1["no conflict check between new tool output and stored assumption"]
    STALE["per-memory staleness tagging"] -.->|"not provided"| GAP2["no provenance or TTL on stored context"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/context_engine/context_engine.py</code> — session-scoped context; <code>recover_from_model_exception</code> for overflow<br><code>agent-core/openjiuwen/core/context_engine/processor/compressor/round_level_compressor.py:104</code> — <code>trigger_context_ratio=0.9</code><br><code>agent-core/openjiuwen/core/context_engine/processor/compressor/full_compact_processor.py</code> — full compaction at 180k tokens<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/memory_forbidden_rail.py</code> — <code>MemoryForbiddenRail</code></sub>
</details>

---

## 5. Observability and auditing agent decisions

**Definition:** If the only artifact is the final transcript, no one can audit why the agent chose one tool or path over another. Structured tracing records, per turn: the model's reasoning text, which tools were called with what inputs, the raw tool outputs, and the rail/guard decisions that shaped the response, each stamped with a time and a session/turn identifier. Production uses a sampling strategy (full trace on errors, sampled on success) and supports replaying a specific trace to reproduce a failure.

**Jiuwen:** `AgentObservabilityRail` is always the last rail in the profile and captures per-turn observable events; the `harness/observability` module structures them, `JiuSwarmStreamEventRail` emits streaming per-turn events, and tool names and reasoning steps surface as `onActivity` events. A structured JSON-line sink, capture of raw tool input/output (only the processed result surfaces), and trace-ID-based replay are not included out of the box — events require a subscribing consumer.

```mermaid
flowchart TD
    TURN["agent turn"] --> OBS["AgentObservabilityRail: observable events (always last rail)"]
    TURN --> STR["JiuSwarmStreamEventRail: streaming per-turn events"]
    TURN --> ACT["onActivity: tool names + reasoning steps"]
    OBS -.->|"no default sink"| SINK["consumer must subscribe; no JSON-line log out of box"]
    ACT -.->|"raw tool I/O"| RAW["raw tool input/output not captured, only processed result"]
    OBS -.->|"no replay"| REPLAY["no trace-ID-based replay mechanism"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/observability/__init__.py</code> — <code>AgentObservabilityRail</code>; always last in profile<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py</code> — <code>JiuSwarmStreamEventRail</code><br><code>agent-core/openjiuwen/harness/rails/</code> — rail pipeline; <code>AgentObservabilityRail</code> appended last<br><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py</code> — tool call execution; raw I/O not persisted separately</sub>
</details>

---

## 6. Termination conditions

**Definition:** "Stop when done" is not a termination condition. An agent needs at least three explicit paths: **success** (a final answer meeting a defined condition, such as required fields populated or context cited); **budget exhaustion** (a hard cap on iterations and tokens, with a graceful degraded response rather than silence); and **human escalation** (handing off when budget is exhausted or ambiguity is unresolvable). A confidence threshold can add a fourth: escalate before acting when the model's uncertainty is high.

**Jiuwen:** Several termination paths exist: `ReactAgent.max_iterations` is the hard iteration cap (5, or 15 in the harness); `PlanApprovalInterruptRail` and `StructuredAskUserRail` provide human-in-the-loop escalation; `ModelAnomalyDetectionRail` can abort on anomaly detection; and `AgentObservabilityRail` logs every turn. A graceful degraded response at budget exhaustion and confidence-threshold auto-escalation are not included, and the approval rails are opt-in per agent config.

```mermaid
flowchart TD
    T["termination decision"] --> S["success: final answer emitted (ReactAgent done)"]
    T --> B["budget: max_iterations (5 / 15) + session cost cap"]
    T --> E["escalation: PlanApprovalInterruptRail / StructuredAskUserRail (opt-in)"]
    T --> A["anomaly abort: ModelAnomalyDetectionRail (off by default)"]
    T -.->|"not included"| D["graceful degraded response at budget exhaustion"]
    T -.->|"not included"| C["confidence-threshold-based auto-escalation"]
    E -.->|"opt-in only"| CONF["PlanApprovalInterruptRail must be in profile config"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations: int = Field(default=5)</code><br><code>agent-core/openjiuwen/harness/schema/config.py:252</code> — harness default iterations 15<br><code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74</code> — anomaly abort (off by default)<br><code>jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171</code> — session cost cap<br><code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/ask_user_rail.py</code> — structured human escalation<br><code>jiuwenswarm/jiuwenswarm/agents/harness/code/rails/code_plan_approval_interrupt_rail.py</code> — <code>PlanApprovalInterruptRail</code> (opt-in)</sub>
</details>

---

## 7. What does structured agent tracing look like, and why does print-debugging fail at scale?

**General:** Print/log statements produce unstructured text: you can't query "all tool calls in session X", can't aggregate latency by tool, and can't correlate a wrong answer back to which retrieval chunk was in context. Structured tracing means emitting a typed event for every meaningful action — model call started/completed, tool called/returned, retrieval executed, decision made — with a shared trace/span ID so events from the same agent run can be grouped. Each event carries: timestamp, latency, token counts, tool name + arguments, retrieval score, model response. This enables offline debugging (replay a trace), production monitoring (alert on p99 latency), and eval (attach ground truth to a trace for scoring). The minimum viable schema: `trace_id`, `span_id`, `event_type`, `payload`, `duration_ms`.

**Jiuwen:** `AgentObservabilityRail` (`harness/observability/rail.py`) emits typed observability events at the major points of each turn — model call, tool call, final answer — and is always the last rail in the profile. Token and cost figures come from the model response's usage metadata. Events are delivered to a subscribing consumer: there is no default log sink, and retrieval details (which chunks, their scores) are not emitted as structured spans — they appear only in tool-result text, so cross-run retrieval analytics need manual instrumentation.

```mermaid
flowchart TD
    PRINT["print debugging"] -.->|"unqueryable, no correlation"| BAD["fails at scale"]
    STRUCT["structured tracing"] --> EV["typed event per action"]
    EV --> MC["model call (tokens, latency)"]
    EV --> TC["tool call (name, args, result)"]
    EV --> RET["retrieval (chunks, scores)"]
    EV --> DEC["decision (plan step, branch)"]
    EV --> TID["shared trace_id + span_id for grouping"]
    JIW["Jiuwen"] --> OBS["AgentObservabilityRail: typed per-turn events"]
    JIW -.->|"absent"| SINK["default log sink / trace replay"]
    JIW -.->|"absent"| RETEV["retrieval events as structured spans"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/harness/observability/rail.py:355</code> — <code>AgentObservabilityRail</code> (typed events)<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:1328</code> — <code>_emit_context_usage</code> (token/usage emission)<br>&bull; <code>agent-core/openjiuwen/core/foundation/llm/schema/generation_response.py:9</code> — <code>GenerationResponse</code> usage/token counts</sub>

</details>

**Gap.** Retrieval events (chunk ids, scores, query) are not emitted as structured observability spans; they appear only in the tool result text, making cross-run retrieval analysis require custom instrumentation.

<sub>_Canonical source: `source/agent-failure-patterns_for_engineers.md`; also covered in: agent-failure._</sub>

---
