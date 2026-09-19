<div class="topic-nav">
<a class="topic-nav__link topic-nav__prev" href="05-agent-fundamentals-and-the-loop.html"><span class="topic-nav__dir">← Previous</span><span class="topic-nav__name">Agent fundamentals and the loop</span></a>
<a class="topic-nav__link topic-nav__next" href="08-agent-frameworks.html"><span class="topic-nav__dir">Next →</span><span class="topic-nav__name">Agent frameworks</span></a>
</div>

# Agent harness and middleware

## 1. What is an agent harness and what does it add over a raw agent loop?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-basic">basic</span>

**TL;DR.** A harness wraps a raw agent loop with every production concern the reasoning loop cannot own: outer task loop, safety and injection filtering, permission and sensitive-data enforcement, resilience, memory, observability, and config-driven capability composition.

**Key points.**

- Raw loop: one ReAct episode — model → tools → repeat → final answer.
- Outer task loop: drives the inner agent across multiple episodes toward a long-horizon goal.
- Safety layer: injects guardrails before every model call; checks permissions and detects injection before every tool call.
- Resilience layer: detects LLM stream stalls, loop-detects repeated tool calls, retries transient failures.
- Memory layer: reads context before each pass, writes learned state after each pass.
- Observability layer: structured spans for every model call and tool call; cost metering and budget enforcement.
- Inner loop owns reasoning; harness owns everything else. Inner default 5 iterations, harness outer default 15.

**Concept.** A raw agent loop (ReAct) handles one reasoning episode: call model → execute tool calls → feed results back → return final answer. A harness wraps this with every production concern that cannot live inside the reasoning loop:

![diagram](assets/diagrams/0011cf7dcdf84878083435e086426c7dc8e6deaa.png)

**In Jiuwen.** In Jiuwen, `DeepAgent` wraps a `ReActAgent` and owns every production concern that surrounds the reasoning loop. Production concerns are each a separate `DeepAgentRail`: `SafetyPromptRail` injects bilingual safety guardrails before every model call; `PermissionInterruptRail` checks tool calls against a permission engine and pauses for human confirmation on sensitive or destructive operations; `ToolCallResilienceRail` retries transport failures with exponential backoff; `ModelAnomalyDetectionRail` detects repeated tool-call loops and stream stalls; `MemoryRail` reads relevant memories before each pass and writes what was learned after; `AgentObservabilityRail` always runs last and emits a structured span for every lifecycle event. The inner `ReActAgent` defaults to 5 iterations per episode; the harness outer loop defaults to 15 passes.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`DeepAgent` wraps `ReActAgent`. Each production concern is a separate `DeepAgentRail` class registered in the pipeline. Core rails: `SafetyPromptRail` — injects bilingual safety guidelines before every model call. `PermissionInterruptRail` — checks tool calls against a `PermissionEngine`; triggers a HITL interrupt for ASK/ASK_USER decisions; parses shell commands for dangerous patterns. `ToolCallResilienceRail` — retries transport/timeout failures with backoff (0.5 s → 1.0 s → 2.0 s, budget 3 retries per invoke); skips retry for non-idempotent operations (write/shell/subagent-spawn). `ModelAnomalyDetectionRail` — detects consecutive identical tool-call rounds and stream-stall patterns; injects a loop-break warning or triggers a full model retry. `MemoryRail` — registers memory tools and injects a memory-usage prompt section; reads on BEFORE_TASK_ITERATION, writes on AFTER_TASK_ITERATION. `AgentObservabilityRail` — always the last rail in any spec; emits a typed span for every lifecycle event. `TaskCompletionRail` — drives the stop-condition evaluation after each outer pass. Inner default `max_iterations = 5` (`react_agent.py:288`); harness outer default 15 (`config.py:252`).

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/deep_agent.py:2694` | outer task loop in DeepAgent |
| `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288` | max_iterations: int = Field(default=5) |
| `agent-core/openjiuwen/harness/schema/config.py:252` | harness outer default 15 iterations |
| `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:1` | DeepAgentSpec: declarative rail list |
| `agent-core/openjiuwen/harness/rails/security/prompt_security_rail.py:1` | SafetyPromptRail: bilingual safety injection |
| `agent-core/openjiuwen/harness/rails/security/tool_security_rail.py:1` | PermissionInterruptRail: permission engine + HITL |
| `agent-core/openjiuwen/harness/rails/tool_call_resilience_rail.py:1` | ToolCallResilienceRail: retry with backoff |
| `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:1` | ModelAnomalyDetectionRail: loop and stall detection |
| `agent-core/openjiuwen/harness/rails/memory/memory_rail.py:1` | MemoryRail: memory tools + prompt section |
| `agent-core/openjiuwen/harness/rails/observability/agent_observability_rail.py:1` | AgentObservabilityRail: always last, traces all events |

</details>

---

## 2. What are lifecycle hooks (middleware) in an agent harness, and at which points can they fire?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Lifecycle hooks are callbacks registered at specific execution points; a complete hook set covers the invocation boundary, the task loop boundary, and the inner model/tool call boundary — each at a different granularity.

**Key points.**

- 10 event points total: BEFORE/AFTER_INVOKE, BEFORE/AFTER_TASK_ITERATION, BEFORE/AFTER_MODEL_CALL, BEFORE/AFTER_TOOL_CALL, ON_MODEL_EXCEPTION, ON_TOOL_EXCEPTION.
- Hooks at invocation level fire once per outer task; hooks at model-call level fire multiple times per outer pass.
- Hooks are priority-ordered — lower number fires first within each event.
- Hooks can read state, inject context, block an action, or emit observability events without the agent knowing.

**Concept.** Lifecycle hooks are callbacks registered by middleware components at specific points in the agent's execution. They can read state, inject content into the context, block or modify an action, or emit observability events — without the agent code knowing. A well-designed hook set covers: the full invocation boundary (before/after the entire task), the task loop iteration boundary (before/after each outer pass), and the inner reasoning steps (before/after each model call and each tool call, plus exception paths). Hooks that fire only at the invocation level cannot intercept a specific tool call; hooks that fire at the model-call level fire many times per outer pass.

![diagram](assets/diagrams/14d3549fa82857aaeaed3dde695d80bc85900a19.png)

**In Jiuwen.** In Jiuwen, `DeepAgentRail` defines 10 lifecycle event points. Six bridge into the inner `ReActAgent` callback manager so rails intercept at execution time — before and after each model call, before and after each tool call, and at each call-site exception. Four stay on the outer `DeepAgent`: BEFORE/AFTER_INVOKE (the full task boundary) and BEFORE/AFTER_TASK_ITERATION (each pass through the outer loop). Rails declare their priority; the callback manager fires lower numbers first within each event. Rails that register on the wrong event point will still fire — just at the wrong granularity.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`DeepAgentRail` base class (`harness/rails/base.py`) defines 10 hook points — two groups: inner events that bridge to `ReActAgent`'s callback manager (6: before/after model call, before/after tool call, on model exception, on tool exception) and outer events that stay on `DeepAgent` (4: before/after invoke, before/after task iteration). Rails are priority-ordered (lower number fires first). `get_callbacks()` returns the hooks a rail wants to register; the callback manager invokes them in priority order per event.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/rails/base.py:1` | DeepAgentRail: 10 hook point declarations |
| `agent-core/openjiuwen/core/single_agent/middleware/base.py:1` | AgentMiddleware base; AgentCallbackEvent enum |
| `agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:1` | priority-ordered callback dispatch |
| `agent-core/openjiuwen/harness/deep_agent.py:1` | _BRIDGE_EVENTS, _OUTER_ONLY_EVENTS, _DEEP_EVENTS |

</details>

---

## 3. What concerns belong in a lifecycle hook versus in the agent prompt versus in a tool?

<span class="badge badge-type">Compare</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Prompts advise reasoning but cannot enforce it; tools execute a domain action but carry no policy; lifecycle hooks intercept at runtime and are the only layer that can block execution — use them for safety filtering, prompt injection detection, permission gating, sensitive-data enforcement, cost metering, and observability.

**Key points.**

- Prompt: advises reasoning — 'do not return passwords' can be ignored by the model.
- Tool: executes on demand with a defined I/O contract — carries no policy itself.
- Hook: the only layer that can block: BEFORE_TOOL_CALL hooks can veto a harmful action before it executes; AFTER_MODEL_CALL hooks can detect a response that contains a secret before it reaches the user.
- Safety / injection: a hook inspects the full context and vetoes; a prompt cannot intercept user input at call time.
- Permission gating: a hook checks the tool's permission tier before execution, regardless of which task requested it.
- Cost and observability: must intercept after every model call — impractical to encode in every prompt or tool.

**Concept.** Three distinct layers, each with its own job. **Prompt:** reasoning guidance — what the task is, how to think about it, what format to return. Prompts advise but cannot enforce. A prompt that says "do not return passwords" can be ignored by the model. **Tool:** domain capability with a defined I/O contract — fetch a URL, run a query, call an API. Tools execute when the model calls them and carry no policy. **Lifecycle hook:** cross-cutting policy that fires unconditionally, regardless of task or tool selection. Use a hook when the concern must *intercept or block* execution, not merely advise it:

![diagram](assets/diagrams/580a830897b6ec4e7f74e453a32533b4711ea8a2.png)

**In Jiuwen.** In Jiuwen the three layers are explicit. The `SystemPromptBuilder` assembles system-prompt sections contributed by active rails — `SafetyPromptRail` injects a bilingual safety section, `TaskPlanningRail` injects planning instructions, `SkillUseRail` injects available-skills guidance. Tools are `ToolCard` objects with a schema and a permission tier; they execute only when the model calls them and carry no policy. Rails enforce policy: `PermissionInterruptRail` blocks tool calls whose permission tier requires confirmation; `SecurityRail` gates tool calls against a safety rule-set; `ToolCallResilienceRail` retries failures; `AgentObservabilityRail` traces everything. Removing a rail removes its policy for all agents and all tasks.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Prompt layer: `SystemPromptBuilder` assembles sections contributed by active rails — `SafetyPromptRail` adds a bilingual safety section, `TaskPlanningRail` adds planning instructions, `SkillUseRail` adds available-skills guidance. Tool layer: `ToolCard` defines schema, callable, and permission tier. Hook layer (selected examples): `SafetyPromptRail` fires on BEFORE_MODEL_CALL to inject safety guidelines — it advises but cannot block; `PermissionInterruptRail` fires on BEFORE_TOOL_CALL — it reads the permission tier from `ToolCard`, runs `PermissionEngine.decide()`, and either approves, blocks, or raises an interrupt for human confirmation (the only layer that can prevent a destructive shell command from running); `ModelAnomalyDetectionRail` fires on AFTER_MODEL_CALL — it detects repeated identical tool-call sequences and stream stalls that the model itself cannot report; `TokenTrackingRail` meters usage at AFTER_MODEL_CALL; `AgentObservabilityRail` fires last on every event and emits typed spans. Removing a hook removes its policy for every agent; removing a tool or prompt section affects only agents that use it.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/prompts/template.py:1` | SystemPromptBuilder; rail prompt section injection |
| `agent-core/openjiuwen/core/foundation/tool/base.py:1` | ToolCard schema and permission tier |
| `agent-core/openjiuwen/harness/rails/security/prompt_security_rail.py:1` | SafetyPromptRail: bilingual safety at BEFORE_MODEL_CALL |
| `agent-core/openjiuwen/harness/rails/security/tool_security_rail.py:1` | PermissionInterruptRail: permission engine + HITL at BEFORE_TOOL_CALL |
| `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:1` | ModelAnomalyDetectionRail: loop/stall detection at AFTER_MODEL_CALL |
| `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/execution_guard/circuit_breaker_rail.py:1` | CircuitBreakerRail: loop-count circuit breaker |
| `agent-core/openjiuwen/harness/rails/token_tracking_rail.py:1` | TokenTrackingRail: usage metering |

</details>

---

## 4. How are middleware components registered and assembled for a specific agent type?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Registration (declare a class in a manifest catalog) and assembly (resolve a spec to instances) are separate steps — capability authoring is decoupled from capability composition per agent type.

**Key points.**

- Registration: each middleware class is declared with a name in the manifest at import time.
- Spec: a declarative ordered list of named middleware types plus per-instance parameters.
- Assembly: spec entries are looked up in the registry, instantiated with their params, appended in order.
- Different agent types use different specs built from the same registry.

**Concept.** Registration and assembly are separate steps. Registration happens at import time: each middleware class is declared with a name in a manifest catalog. At agent construction, a spec — a declarative list of named middleware types plus per-instance parameters — is resolved against the registry: each entry is looked up, instantiated with its params, and appended to the pipeline in declaration order. Different agent types use different specs built from the same registry. This separates capability authoring (write the class, register it once) from capability composition (declare which classes to activate, per agent type).

![diagram](assets/diagrams/a103d12b433702f7ca99ef519ed81946a5b7ff69.png)

**In Jiuwen.** In Jiuwen, every built-in rail is registered once in `builtin_elements.py` under a short name like `"core.security"` or `"core.memory"`. At startup a provider registry syncs this catalog. Each agent type uses a `DeepAgentSpec` — a list of `RailSpec` items, each naming a type and carrying params — to declare its capability set. The factory resolves each name against the registry, instantiates the rail with its params, and appends it in declaration order. A base chat agent spec activates task-planning, security, system-operation, heartbeat, and observability rails. A code agent spec additionally activates code-specific planning and plan-approval rails.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`builtin_elements.py` (`harness/manifest/builtin_elements.py`) registers every built-in rail into the manifest catalog using `harness_element(ElementKind.RAIL, "core.security", SecurityRail)`. `registration.py` syncs the catalog to a provider registry at startup. At `DeepAgent` construction, `factory.py` resolves `DeepAgentSpec.rails` (a list of `RailSpec` items): each `RailSpec.type` string (e.g. `"core.task_planning"`) is looked up in the provider registry, instantiated with `RailSpec.params`, and appended. A base agent spec has `[core.task_planning, core.security, core.sys_operation, ...]`; a code agent spec adds `[code.task_planning, code.plan_approval, ...]` on top.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/manifest/builtin_elements.py:1` | harness_element() declarations for all built-in rails |
| `agent-core/openjiuwen/harness/manifest/registration.py:1` | catalog → provider registry sync |
| `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:1` | DeepAgentSpec.rails: list[RailSpec] |
| `agent-core/openjiuwen/harness/factory.py:1` | DeepAgent construction: spec → resolved rail instances |

</details>

---

## 5. How does the harness task loop differ from a single agent invocation?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** A single agent invocation runs one ReAct episode; the harness task loop calls it repeatedly, evaluating completion after each pass and giving middleware time to update working memory and check budgets between passes.

**Key points.**

- Single invocation: one ReAct episode, inner iteration limit.
- Task loop: BEFORE_TASK_ITERATION → inner agent → AFTER_TASK_ITERATION, repeated until done or budget exhausted.
- Between passes: middleware updates memory, checks cost quota, injects new context.
- Outer budget is separate from the inner max_iterations.

**Concept.** A single agent invocation runs one ReAct episode — the model and tools interact until the agent returns a final answer, hits its iteration limit, or encounters an error. The harness task loop calls this invocation repeatedly, evaluating whether the overall goal is complete after each pass. Between passes, task-iteration hooks fire, giving middleware time to update working memory, flush completed sub-tasks, check whether the budget allows another pass, and inject new context or instructions. This enables long-horizon tasks that require more reasoning steps than a single episode's iteration limit allows, without losing state between episodes.

![diagram](assets/diagrams/d5fed93e4278266b12a9b0e4d299437929c56450.png)

**In Jiuwen.** In Jiuwen, the outer task loop (`execute_task()`) is coordinated by a `LoopCoordinator`. Before each pass: rails update the system-prompt sections, check token and cost quotas, and load relevant memories into the prompt. The inner `ReActAgent` runs its reasoning episode. After each pass: rails write memory, update skill files, and check whether the goal is satisfied. The loop exits on a goal-completion signal from `TaskCompletionRail`, a hard iteration cap, a token budget exhaustion, or a wall-clock timeout — whichever fires first. The outer budget and the inner per-episode limit are independent.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`DeepAgent.execute_task()` is the outer loop. Each iteration: BEFORE_TASK_ITERATION fires (rails update prompt sections, check token/cost quotas, load relevant memories); inner `ReActAgent.invoke()` runs up to 15 iterations; AFTER_TASK_ITERATION fires (rails write memory, update skill files via `SkillUseRail`, decide if goal is satisfied via `TaskCompletionRail`). If `TaskCompletionRail` signals complete, the loop exits. If the outer iteration budget is exhausted first, the loop exits with a truncation signal. The outer budget is separate from the inner `max_iterations`.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/deep_agent.py:2694` | execute_task(): outer task loop |
| `agent-core/openjiuwen/harness/schema/config.py:252` | outer and inner iteration defaults |
| `agent-core/openjiuwen/harness/rails/task_completion_rail.py:1` | completion signal |
| `agent-core/openjiuwen/harness/rails/skill_use_rail.py:1` | skill file update on AFTER_TASK_ITERATION |
| `agent-core/openjiuwen/harness/rails/memory_rail.py:1` | memory write on task iteration boundary |

</details>

---

## 6. How do you test a lifecycle hook in isolation from the LLM?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Structure hook tests around three concerns: which invariant to assert (blocked call, counter, emitted event), which paths to exercise (happy path and exception paths), and composition (state written by hook A at priority N is visible to hook B at priority N+1).

**Key points.**

- Mock the model client boundary — raise controlled exceptions on specific invocations to exercise ON_TOOL_EXCEPTION and ON_MODEL_EXCEPTION paths; a retry hook never tested on failure is functionally untested.
- Assert hook invariants, not output strings: blocked_calls list, trip_count, typed span log — output varies when any hook modifies context.
- Composition test: register two hooks at known priorities and assert that state written by the higher-priority hook is visible to the lower-priority hook at the same event point.
- No framework test harness exists — each test constructs DeepAgent manually with only the rails under test.

**Concept.** Inject a deterministic model client at the agent's model boundary and structure tests around three concerns:

![diagram](assets/diagrams/811bad8080329e2c56bc99df1d5472e578c42cfb.png)

**In Jiuwen.** In Jiuwen, the testable boundary is `ModelClientABC`. Subclass it to return deterministic responses on the happy path and to raise `ModelException` on demand for exception-path tests. Wrap a `ToolCard`'s callable to raise `ToolException` on a specific invocation to exercise `ON_TOOL_EXCEPTION` hooks — a retry rail never tested on failure is untested. Construct `DeepAgent` with only the rails under test and the mock client, call `execute_task()`, then assert on: `PermissionInterruptRail.blocked_calls` (pre-call blocking), `TokenTrackingRail` token counters (post-call state), `CircuitBreakerRail.trip_count` after N injected consecutive failures, `AgentObservabilityRail` typed span list (full execution trace). For composition tests: register two rails at known priorities, write a context field in the higher-priority rail's `before_tool_call`, and assert it is present in the lower-priority rail's `before_tool_call`.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`ModelClientABC` (`core/foundation/llm/model_clients/base.py`) is the injectable boundary. Subclass it: normal path returns a fixed tool-call sequence or a final answer; exception path raises `ModelException` on a specific invocation number. For tool exception paths: wrap the tool callable in the `ToolCard` to raise `ToolException` on demand. Assert on: `PermissionInterruptRail` — check `blocked_calls` list after a run with a disallowed tool; `TokenTrackingRail` — check cumulative token count after N model invocations; `CircuitBreakerRail.trip_count` after injecting N consecutive failures; `AgentObservabilityRail` event log (typed span list) after a full run. For composition: register two rails with known priority order and assert that the lower-priority rail's `before_tool_call` received the context field written by the higher-priority rail's `before_tool_call`. No framework test harness or fixture library exists — each test constructs `DeepAgent` manually.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/core/foundation/llm/model_clients/base.py:1` | ModelClientABC: injectable mock boundary |
| `agent-core/openjiuwen/harness/factory.py:1` | DeepAgent construction accepts model client override |
| `agent-core/openjiuwen/core/foundation/tool/base.py:1` | ToolCard callable wrapper: injectable error fixture |
| `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/execution_guard/circuit_breaker_rail.py:1` | trip_count assertable after N injected failures |
| `agent-core/openjiuwen/harness/rails/security/tool_security_rail.py:1` | blocked_calls assertable list |
| `agent-core/openjiuwen/harness/rails/observability/agent_observability_rail.py:1` | typed span event log assertable after run |

</details>

---

## 7. What is the event bridge model — which events propagate to the inner agent and which stay on the outer harness?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Inner-agent events (model call, tool call, exceptions) bridge into the inner loop's callback manager so hooks fire at execution time; outer events (invocation boundary, task loop boundary) stay on the outer harness because the inner loop does not know it is being called repeatedly.

**Key points.**

- 6 bridged events: BEFORE/AFTER_MODEL_CALL, BEFORE/AFTER_TOOL_CALL, ON_MODEL/TOOL_EXCEPTION — registered in both outer and inner callback managers.
- 2 outer-only: BEFORE/AFTER_INVOKE — on the harness only.
- 2 deep-only: BEFORE/AFTER_TASK_ITERATION — fired by the outer task loop, no inner equivalent.
- Registering a per-model-call hook as a per-invocation hook is a silent design error — it fires, just at the wrong rate.

**Concept.** The outer harness and the inner agent loop are separate event domains. Inner-agent events (model call, tool call, exceptions at those call sites) must bridge into the inner loop's callback manager because they occur during active reasoning — a security hook that blocks a specific tool call must fire at the point of execution, inside the inner loop, not before the loop starts. Outer events (full invocation boundary, task loop iteration boundary) stay on the outer harness because the inner loop does not know it is being called multiple times toward a long-horizon goal. Incorrectly wiring a hook to the wrong domain causes it to fire at the wrong granularity — a per-model-call cost meter registered as a per-invocation hook only fires once per outer pass and misses all intermediate calls.

![diagram](assets/diagrams/b21b57888f8c9e87607d8d7a510ac9c8e355fdcc.png)

**In Jiuwen.** In Jiuwen, `DeepAgent` defines three event sets. Bridged events are registered in both the outer callback manager and the inner `ReActAgent` callback manager — so a security rail registered on BEFORE_TOOL_CALL intercepts at the actual moment of tool execution, inside the reasoning loop, not just at the outer task boundary. Outer-only events (BEFORE/AFTER_INVOKE) and task-iteration events (BEFORE/AFTER_TASK_ITERATION) stay on the outer harness; the inner loop does not know it is one episode in a longer-running task. The mismatch is silent: a cost-metering rail registered on BEFORE_INVOKE instead of AFTER_MODEL_CALL fires once per outer pass and misses all intermediate model calls.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Three event sets are defined in `deep_agent.py`: `_BRIDGE_EVENTS` (6) — BEFORE_MODEL_CALL, AFTER_MODEL_CALL, ON_MODEL_EXCEPTION, BEFORE_TOOL_CALL, AFTER_TOOL_CALL, ON_TOOL_EXCEPTION — are registered into both the outer callback manager and the inner `ReActAgent.callback_manager` so rails intercept at execution time. `_OUTER_ONLY_EVENTS` (2) — BEFORE_INVOKE, AFTER_INVOKE — stay on `DeepAgent` only. `_DEEP_EVENTS` (2) — BEFORE_TASK_ITERATION, AFTER_TASK_ITERATION — are fired by the outer task loop controller and have no equivalent in the inner loop. Priority ordering within each event point determines which rail fires first.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/deep_agent.py:1` | _BRIDGE_EVENTS, _OUTER_ONLY_EVENTS, _DEEP_EVENTS definitions |
| `agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:1` | inner callback manager that receives bridged events |
| `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:1` | callback_manager field; tool/model call sites that invoke it |

</details>

---

## 8. How does hot-loading middleware into a running agent work and when would you need it?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Hot-loading binds new middleware to a live agent without restarting it; needed when capabilities are discovered at runtime (skill libraries, mid-session permission grants, external plugins).

**Key points.**

- Standard middleware is bound at construction and fixed; hot-loading appends to the live pipeline.
- New hook joins the priority order without disrupting hooks that are mid-execution.
- Race risk: binding a callback during an active model call requires lock protection.
- No rollback if hot-bind fails partway through.

**Concept.** Standard middleware is bound at construction — the spec is resolved, instances are created, and the pipeline is fixed. Hot-loading binds new middleware to a live agent without stopping and restarting it. This is needed when the full capability set is not known at construction time: an agent discovers a skill library during a task and must load the tools and hooks declared in it; a user grants a new permission mid-session; an external plugin is installed while the agent is running. Hot-loading must preserve the existing pipeline state — the new hook joins the priority order without disrupting hooks that are mid-execution. Because agent invocations are async, binding a new callback during an active model call creates a race; the implementation must guard against partial registration.

![diagram](assets/diagrams/50bc4f1174dc3b7b854bb9001ffb188a6d7466a1.png)

**In Jiuwen.** In Jiuwen, `ExpertHarness` enables hot-loading of middleware from a `SKILL.md` file or a spec JSON. It resolves new rails and tools from the spec, then for each new rail appends it to the live rail list, registers its callbacks into the running callback manager at the correct priority position, and injects its prompt section into the `SystemPromptBuilder`. This is how a skill library can declare its own custom tools and middleware that activate mid-session, without restarting the agent. The binding is not lock-protected, so loading a skill while the agent is mid-model-call carries a race condition risk.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`ExpertHarness` (`harness/expert_harness_runtime.py:1`) implements hot-loading. It reads an `ExpertHarnessSpec` from a SKILL.md file or a spec JSON, resolves new rails and tools from it, then calls `_hot_bind_rail(agent, rail)` for each: the rail is appended to `self._rails`, its callbacks are registered into the live `callback_manager` at the correct priority, and its prompt section is injected into the `SystemPromptBuilder`. This is how skills can declare custom tools and middleware that activate when the skill is loaded mid-session. Atomicity is not guaranteed under concurrent invocations — `_hot_bind_rail` is not lock-protected.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/expert_harness_runtime.py:1` | ExpertHarness; _hot_bind_rail() |
| `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:1` | ExpertHarnessSpec schema |
| `agent-core/openjiuwen/harness/prompts/template.py:1` | SystemPromptBuilder: prompt section injection |
| `agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:1` | live callback registration target |

</details>

---

## 9. How does a harness accumulate experience — what is the skill evolution pipeline?

<span class="badge badge-type">Mechanism</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** The harness observes every execution and can extract reusable patterns from those trajectories, stage them as skill experience records, and — with a configurable approval gate — persist them so future agents start with accumulated knowledge rather than from zero.

**Key points.**

- Capture: EvolutionRail collects execution spans into clean windows and applies quality gates before staging.
- Single-agent: SkillEvolutionRail detects reusable tool/reasoning patterns; persists via EvolutionStore.
- Multi-agent: TeamSkillEvolutionRail waits for team completion, aggregates member trajectories, detects collaboration patterns.
- Approval gate: EvolutionInterruptRail routes staged records to user confirmation before persistence (auto_save=True bypasses this).
- Trajectory archive: TrajectoryRail (always last, priority 10) writes one canonical trajectory per invoke for offline analysis, independent of evolution rails.
- Trigger paths: passive signal scanning, periodic self-check follow-up, or explicit /evolve command.

**Concept.** A harness that intercepts every model call and tool call already has the data needed to improve itself: which tool sequences solved the problem, which reasoning patterns were reused, which sub-task plans worked. Skill evolution captures this data, extracts reusable patterns from it, and persists them as skill experience records that future agents load at task start. Without an evolution pipeline, every agent run starts from zero; with it, the agent population improves across sessions without retraining the underlying model. Three design decisions shape any evolution pipeline: (1) **what to capture** — the full execution trajectory or only successful final passes; (2) **what quality gate** prevents low-quality or noisy patterns from being persisted; (3) **whether human approval** is required before a pattern becomes a permanent skill (human-in-the-loop evolution) or whether the system auto-saves (fully autonomous evolution). The approval gate is the main lever for controlling how much the agent is trusted to modify its own future behaviour.

![diagram](assets/diagrams/008d40d4ab6f8767f4c7cdf80c71eb0e5d32c7b8.png)

**In Jiuwen.** In Jiuwen, `EvolutionRail` is the base class for all evolution rails: it subscribes to a trajectory processor, collects execution spans into clean windows, applies quality gates, and suppresses capture while evolution work is running. `SkillEvolutionRail` extends it for single-agent experience: after each invoke it detects reusable patterns in the clean window, stages candidate experience records, and routes them through `EvolutionInterruptRail` — which raises an interrupt for user approval before `EvolutionStore` persistence, or auto-saves if `auto_save=True`. `TeamSkillEvolutionRail` does the same for multi-agent runs: it monitors the `view_task` tool result to detect team completion, then aggregates all member trajectories and generates a team skill record. `TrajectoryRail` runs last on every invoke (priority 10) and archives one canonical trajectory to `FileTrajectoryStore` independently of whether evolution rails are active. Trigger paths: `signal_trigger` (passive post-invoke scan, default False), `review_trigger` (periodic self-check, default False), or explicit `/evolve` command dispatch.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`EvolutionRail` is the base class: it subscribes to a trajectory processor, collects execution spans into scope-local clean windows, applies quality gates, and suppresses capture during evolution work itself (to prevent skills about writing skills). `SkillEvolutionRail` extends it for single-agent experience: after each invoke it scans the trajectory for reusable patterns, stages candidate experience records, and routes them through `EvolutionInterruptRail` for user approval before `EvolutionStore` persistence — or auto-saves if `auto_save=True`. `TeamSkillEvolutionRail` extends it for multi-agent collaboration: it waits for a team completion event, aggregates trajectories from all member agents, detects the collaboration pattern, and generates a team skill record. `TrajectoryRail` (lowest priority, always last) archives one canonical trajectory per invoke to a `FileTrajectoryStore` for offline analysis, independent of whether evolution rails are active. Trigger paths: passive signal scanning (`signal_trigger`, default `False`), periodic self-check follow-up (`review_trigger`, default `False`), or explicit `/evolve` command dispatch.

**Code anchors**

| Code anchor | What it points to |
|---|---|
| `agent-core/openjiuwen/harness/rails/evolution/evolution_rail.py:1` | EvolutionRail base: trajectory capture, quality gate, clean window |
| `agent-core/openjiuwen/harness/rails/evolution/skill_evolution_rail.py:1` | SkillEvolutionRail: single-agent experience staging and persistence |
| `agent-core/openjiuwen/harness/rails/evolution/team_skill_evolution_rail.py:1` | TeamSkillEvolutionRail: multi-agent collaboration pattern detection |
| `agent-core/openjiuwen/harness/rails/evolution/evolution_interrupt_rail.py:1` | EvolutionInterruptRail: approval bridge |
| `agent-core/openjiuwen/harness/rails/evolution/trajectory_rail.py:1` | TrajectoryRail: canonical trajectory archive (priority 10, always last) |

</details>

---
