# Agent harness and lifecycle hooks

## 1. What is an agent harness and what does it add over a raw agent loop?

**General:** A raw agent loop (ReAct) handles one reasoning episode: call model → execute tool calls → feed results back → return final answer. A harness wraps this with every production concern that cannot live inside the reasoning loop:

- **Outer task loop.** Drives the inner agent across multiple episodes toward a long-horizon goal, checking for completion after each pass.
- **Safety and injection filtering.** Injects guardrails into every model call; intercepts every tool call to detect prompt injection attempts and block harmful actions before they execute.
- **Permission and sensitive-data enforcement.** Checks each tool's permission tier before execution, pauses for human confirmation on sensitive or destructive operations, and prevents the agent from returning credentials or PII in output.
- **Resilience.** Detects LLM stream stalls, identifies repeated identical tool-call loops, retries transient failures with exponential backoff, and circuit-breaks when the loop stops making progress.
- **Memory and context.** Reads relevant memories before each pass, writes what was learned after each pass, and compresses the context window when it approaches capacity.
- **Observability and cost metering.** Emits a structured span for every model call and tool call, tracks token usage, enforces cost budgets, and archives the full execution trajectory.
- **Capability composition.** Declares which rails and tools are active per agent type via a manifest-driven spec, so the same framework powers a code agent, a web agent, and a data agent with different capability sets.

The inner loop owns reasoning. The harness owns everything else.

**Jiuwen:** `DeepAgent` wraps `ReActAgent`. Each production concern is a separate `DeepAgentRail` class registered in the pipeline. Core rails: `SafetyPromptRail` — injects bilingual safety guidelines before every model call. `PermissionInterruptRail` — checks tool calls against a `PermissionEngine`; triggers a HITL interrupt for ASK/ASK_USER decisions; parses shell commands for dangerous patterns. `ToolCallResilienceRail` — retries transport/timeout failures with a per-invoke budget of 3 attempts (`DEFAULT_MAX_ATTEMPTS = 3`) and skips retry for non-idempotent operations (write/shell/subagent-spawn). `ModelAnomalyDetectionRail` — detects consecutive identical tool-call rounds and stream-stall patterns; its backoff schedule is `_DEFAULT_BACKOFF_SECONDS = (0.5, 1.0, 2.0)`. `MemoryRail` — registers memory tools and injects a memory-usage prompt section; it hooks `before_invoke` and `before_model_call`. `AgentObservabilityRail` — a `core.observability` element at priority 10 that emits a typed span for every lifecycle event. The inner ReAct loop defaults to `max_iterations = 5` (`react_agent.py:288`); the harness `DeepAgentConfig.max_iterations = 15` is the per-invoke inner limit when the task loop is off, and the outer loop is capped at `max_outer_rounds = 50`.

```mermaid
flowchart TD
    INV(["invoke()"]) --> BI["BEFORE_INVOKE\ninitialize rails · load skills · register tools"]
    BI --> BTI["BEFORE_TASK_ITERATION\nupdate prompt · check cost budget · load memory"]
    BTI --> BMC["BEFORE_MODEL_CALL\ninject safety guardrails · assemble system prompt"]
    BMC --> MODEL(["model call"])
    MODEL --> AMC["AFTER_MODEL_CALL\ndetect loops & stalls · count tokens · update cost"]
    AMC --> BTC["BEFORE_TOOL_CALL\ncheck permissions · block injection · confirm destructive ops"]
    BTC --> TOOL(["tool execution"])
    TOOL --> ATC["AFTER_TOOL_CALL\nretry transient failures · track tool usage"]
    ATC -->|"more tool calls"| BMC
    ATC -->|"no more calls"| ATI["AFTER_TASK_ITERATION\nwrite memory · update skill files · check goal"]
    ATI -->|"continue"| BTI
    ATI -->|"done / budget"| AI["AFTER_INVOKE\narchive trajectory · emit final spans · clean up"]
    AI --> DONE(["result"])
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/deep_agent.py:2692</code> — <code>_run_task_loop</code>: outer task loop in <code>DeepAgent</code>; <code>:2723</code> <code>max_outer_rounds = 50</code><br><code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations: int = Field(default=5)</code><br><code>agent-core/openjiuwen/harness/schema/config.py:252</code> — <code>DeepAgentConfig.max_iterations = 15</code> (per-invoke inner limit)<br><code>agent-core/openjiuwen/harness/schema/deep_agent_spec.py:433</code> — <code>DeepAgentSpec</code>; <code>:248</code> <code>RailSpec</code><br><code>agent-core/openjiuwen/harness/rails/security/prompt_security_rail.py:16</code> — <code>SafetyPromptRail</code>: bilingual safety injection<br><code>agent-core/openjiuwen/harness/rails/security/tool_security_rail.py:57</code> — <code>PermissionInterruptRail</code>: permission engine + HITL<br><code>agent-core/openjiuwen/harness/rails/tool_call_resilience_rail.py:24</code> — <code>ToolCallResilienceRail</code>; budget <code>:92</code><br><code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:110</code> — <code>ModelAnomalyDetectionRail</code>; backoff <code>:35</code><br><code>agent-core/openjiuwen/harness/rails/memory/memory_rail.py:25</code> — <code>MemoryRail</code><br><code>agent-core/openjiuwen/harness/observability/rail.py:355</code> — <code>AgentObservabilityRail</code> (priority 10)</sub>
</details>

---

## 2. What are lifecycle hooks in an agent harness, and at which points can they fire?

**General:** Lifecycle hooks are callbacks registered by lifecycle hooks at specific points in the agent's execution. They can read state, inject content into the context, block or modify an action, or emit observability events — without the agent code knowing. A well-designed hook set covers: the full invocation boundary (before/after the entire task), the task loop iteration boundary (before/after each outer pass), and the inner reasoning steps (before/after each model call and each tool call, plus exception paths). Hooks that fire only at the invocation level cannot intercept a specific tool call; hooks that fire at the model-call level fire many times per outer pass.

**Jiuwen:** `DeepAgentRail` base class (`harness/rails/base.py`) declares the hook points — inner events bridged to `ReActAgent` (before/after model call, before/after tool call, on model exception, on tool exception) and outer events on `DeepAgent` (before/after invoke, before/after task iteration). Rails are priority-ordered and **higher priority fires first** (`AgentCallbackManager.register_callback` documents “higher = runs first”). `get_callbacks()` returns the hooks a rail registers, and the callback manager invokes them in priority order per event.

```mermaid
flowchart LR
    subgraph OUTER["Outer (DeepAgent only)"]
        BI["BEFORE_INVOKE"]
        BTI["BEFORE_TASK_ITERATION"]
        ATI["AFTER_TASK_ITERATION"]
        AI["AFTER_INVOKE"]
    end
    subgraph INNER["Inner (bridged to ReActAgent)"]
        BMC["BEFORE_MODEL_CALL"]
        AMC["AFTER_MODEL_CALL"]
        BTC["BEFORE_TOOL_CALL"]
        ATC["AFTER_TOOL_CALL"]
        EMC["ON_MODEL_EXCEPTION"]
        ETC["ON_TOOL_EXCEPTION"]
    end
    BI --> BTI --> BMC --> AMC --> BTC --> ATC --> ATI --> AI
    BMC -.->|"may repeat"| BMC
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/rails/base.py:28</code> — <code>DeepAgentRail</code>: hook declarations<br><code>agent-core/openjiuwen/core/single_agent/rail/base.py:824</code> — <code>AgentRail</code> base; <code>:465</code> <code>AgentCallbackEvent</code><br><code>agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:11</code> — <code>AgentCallbackManager</code>; <code>:29</code> priority (“higher runs first”)<br><code>agent-core/openjiuwen/harness/deep_agent.py:158</code> — <code>_BRIDGE_EVENTS</code>; <code>:180</code> <code>_OUTER_ONLY_EVENTS</code>; <code>:188</code> <code>_DEEP_EVENTS</code></sub>
</details>

---

## 3. What concerns belong in a lifecycle hook versus in the agent prompt versus in a tool?

**General:** Three distinct layers, each with its own job. **Prompt:** reasoning guidance — what the task is, how to think about it, what format to return. Prompts advise but cannot enforce. A prompt that says "do not return passwords" can be ignored by the model. **Tool:** domain capability with a defined I/O contract — fetch a URL, run a query, call an API. Tools execute when the model calls them and carry no policy. **Lifecycle hook:** cross-cutting policy that fires unconditionally, regardless of task or tool selection. Use a hook when the concern must *intercept or block* execution, not merely advise it:

- **Safety / prompt injection** — a user message containing "ignore previous instructions" is not a prompt concern (prompts don't see user input at hook time); a BEFORE_TOOL_CALL hook can inspect the full context and veto the action.
- **Sensitive-data enforcement** — preventing the agent from executing a shell command that would print a secret, or from returning a password in its final answer, requires a hook that fires at BEFORE_TOOL_CALL or AFTER_MODEL_CALL and can block before the output reaches the user.
- **Permission gating** — if a tool requires elevated privileges, a hook checks the caller's permission tier before letting execution proceed, rather than trusting the tool to check itself.
- **Cost and budget** — token metering must intercept after every model call; encoding this in the prompt or in every tool is impractical.
- **Observability** — tracing every event requires a hook that fires last on every event point, regardless of which tools or prompts are active.

If a concern must apply to every agent regardless of purpose, it belongs in a hook, not in every tool or in every prompt.

**Jiuwen:** Prompt layer: `SystemPromptBuilder` assembles sections contributed by active rails — `SafetyPromptRail` adds a bilingual safety section, `TaskPlanningRail` adds planning instructions, `SkillUseRail` adds available-skills guidance. Tool layer: `ToolCard` defines schema, callable, and permission tier. Hook layer: `SafetyPromptRail` fires on BEFORE_MODEL_CALL (advises, cannot block); `PermissionInterruptRail` fires on BEFORE_TOOL_CALL — it reads the permission tier from `ToolCard`, runs `PermissionEngine.check_permission()`, and approves, blocks, or raises a human-confirmation interrupt (the only layer that can prevent a destructive shell command from running); `ModelAnomalyDetectionRail` fires on AFTER_MODEL_CALL to detect repeated tool-call sequences and stream stalls; `TokenTrackingRail` meters usage at AFTER_MODEL_CALL; `AgentObservabilityRail` (priority 10) emits typed spans at each event.

```mermaid
flowchart TD
    TASK["agent task"] --> PROMPT["Prompt layer\n(advises reasoning)"]
    TASK --> TOOL["Tool layer\n(executes on demand)"]
    TASK --> HOOK["Hook layer\n(intercepts · blocks · meters · traces)"]
    PROMPT -.->|"advises only\ncannot block"| PROMPT
    TOOL -.->|"I/O contract only\nno policy"| TOOL
    HOOK --> H1["SafetyPromptRail\nBEFORE_MODEL_CALL\n→ inject guardrails"]
    HOOK --> H2["PermissionInterruptRail\nBEFORE_TOOL_CALL\n→ check tier · block / confirm"]
    HOOK --> H3["ModelAnomalyDetectionRail\nAFTER_MODEL_CALL\n→ detect loops & stalls"]
    HOOK --> H4["TokenTrackingRail\nAFTER_MODEL_CALL\n→ meter cost · enforce budget"]
    HOOK --> H5["ToolCallResilienceRail\nON_TOOL_EXCEPTION\n→ retry transient failures"]
    HOOK --> H6["AgentObservabilityRail\nlast on every event\n→ emit typed span"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/prompts/builder.py:28</code> — <code>SystemPromptBuilder</code>; rail prompt-section injection<br><code>agent-core/openjiuwen/core/foundation/tool/base.py:78</code> — <code>ToolCard</code> schema and permission tier<br><code>agent-core/openjiuwen/harness/rails/security/prompt_security_rail.py:16</code> — <code>SafetyPromptRail</code> (BEFORE_MODEL_CALL, advisory)<br><code>agent-core/openjiuwen/harness/rails/security/tool_security_rail.py:57</code> — <code>PermissionInterruptRail</code>; <code>PermissionEngine.check_permission()</code> at <code>agent-core/openjiuwen/harness/security/permission_engine/core.py:272</code><br><code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:110</code> — <code>ModelAnomalyDetectionRail</code> (AFTER_MODEL_CALL)<br><code>agent-core/openjiuwen/harness/cli/rails/token_tracker.py:15</code> — <code>TokenTrackingRail</code>: usage metering</sub>
</details>

---

## 4. How are lifecycle hooks registered and assembled for a specific agent type?

**General:** Registration and assembly are separate steps. Registration happens at import time: each lifecycle-hook class is declared with a name in a manifest catalog. At agent construction, a spec — a declarative list of named lifecycle-hook types plus per-instance parameters — is resolved against the registry: each entry is looked up, instantiated with its params, and appended to the pipeline in declaration order. Different agent types use different specs built from the same registry. This separates capability authoring (write the class, register it once) from capability composition (declare which classes to activate, per agent type).

**Jiuwen:** `builtin_elements.py` declares every built-in rail with `harness_element(kind=ElementKind.RAIL, name=..., description=..., builder=SecurityRail)`. `registration.py` syncs the catalog to a provider registry at startup. `DeepAgentSpec.rails` is a list of `RailSpec`; `DeepAgentSpec.build()` looks each `RailSpec.type` up in the registry, instantiates it with `RailSpec.params`, and appends it — the `create_deep_agent` factory itself takes already-built `AgentRail` instances. A base agent spec has `[core.task_planning, core.security, core.sys_operation, …]`; the product code agent adds `[swarm.code_task_planning, swarm.team_plan_approval, …]`.

```mermaid
flowchart LR
    REG["builtin_elements.py\nharness_element('core.security', SecurityRail)"]
    REG --> CAT["manifest catalog"]
    CAT --> PROV["provider registry\n(registration.py)"]
    PROV --> SPEC["DeepAgentSpec\nrails: [RailSpec('core.security', params={}), ...]"]
    SPEC --> INST["instantiate each rail\nfrom registry"]
    INST --> PIPE["ordered rail pipeline\nattached to DeepAgent"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/manifest/builtin_elements.py:450</code> — <code>harness_element(kind=…, name=…, builder=SecurityRail)</code><br><code>agent-core/openjiuwen/harness/manifest/registration.py:31</code> — catalog → provider registry sync (<code>register_from_catalog</code>)<br><code>agent-core/openjiuwen/harness/schema/deep_agent_spec.py:248</code> — <code>RailSpec</code>; <code>:433</code> <code>DeepAgentSpec</code>; <code>:581</code> <code>build()</code><br><code>agent-core/openjiuwen/harness/factory.py:460</code> — <code>create_deep_agent</code>: takes rail instances</sub>
</details>

---

## 5. How does the harness task loop differ from a single agent invocation?

**General:** A single agent invocation runs one ReAct episode — the model and tools interact until the agent returns a final answer, hits its iteration limit, or encounters an error. The harness task loop calls this invocation repeatedly, evaluating whether the overall goal is complete after each pass. Between passes, task-iteration hooks fire, giving hooks time to update working memory, flush completed sub-tasks, check whether the budget allows another pass, and inject new context or instructions. This enables long-horizon tasks that require more reasoning steps than a single episode's iteration limit allows, without losing state between episodes.

**Jiuwen:** `DeepAgent._run_task_loop()` is the outer loop. Each iteration: BEFORE_TASK_ITERATION fires (rails update prompt sections, check token/cost quotas, load memories); the inner `ReActAgent` runs (with `max_iterations` raised to `sys.maxsize` when `enable_task_loop`); AFTER_TASK_ITERATION fires (rails write memory; `TaskCompletionRail` decides whether the goal is satisfied). The outer loop is capped at `max_outer_rounds = 50`.

```mermaid
flowchart TD
    START(["task"]) --> BI["BEFORE_INVOKE"]
    BI --> LOOP{{"outer task loop"}}
    LOOP --> BTI["BEFORE_TASK_ITERATION\n(update context, check budget)"]
    BTI --> INNER["ReActAgent.invoke()\n(up to max_iterations=15)"]
    INNER --> ATI["AFTER_TASK_ITERATION\n(write memory, check done)"]
    ATI -->|"goal satisfied"| DONE(["done"])
    ATI -->|"budget exhausted"| DONE
    ATI -->|"continue"| LOOP
    DONE --> AI["AFTER_INVOKE"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/deep_agent.py:2692</code> — <code>_run_task_loop</code>: outer task loop; <code>:2723</code> <code>max_outer_rounds = 50</code><br><code>agent-core/openjiuwen/harness/schema/config.py:252</code> — <code>DeepAgentConfig.max_iterations = 15</code><br><code>agent-core/openjiuwen/harness/rails/task_completion_rail.py:74</code> — completion signal<br><code>agent-core/openjiuwen/harness/rails/memory/memory_rail.py:25</code> — memory rail</sub>
</details>

---

## 6. How do you test a lifecycle hook in isolation from the LLM?

**General:** Inject a deterministic model client at the agent's model boundary and structure tests around three concerns:

1. **What invariant to assert.** A pre-call hook's job is to block, modify, or annotate the action — assert on whether it blocked (call not made), what it modified (args changed), or what it annotated (context field set). A post-call hook's job is to update state or gate output — assert on counters, emitted events, or downstream blocks. Asserting on output strings fails when any hook in the stack modifies context between your hook and the model.

2. **Which paths to exercise.** The happy path (model returns an answer, tools succeed) tests BEFORE/AFTER hooks. The exception paths — ON_TOOL_EXCEPTION and ON_MODEL_EXCEPTION — require the fixture to raise controlled errors on demand. This matters: a retry hook that never sees a failure is functionally untested. A blocking hook that only triggers on specific error codes needs an error fixture that produces those codes.

3. **Hook composition.** Isolated tests verify each hook's invariants individually. Composition tests verify that state written by a higher-priority hook at a given event point is visible to lower-priority hooks at the same event. If hook A at priority 10 tags a context field and hook B at priority 20 reads it to decide whether to block, testing them separately misses the interaction.

**Jiuwen:** `BaseModelClient` (`core/foundation/llm/model_clients/base_model_client.py`) is the injectable boundary. Subclass it: the normal path returns a fixed tool-call sequence or a final answer; the exception path raises `ModelException`. For tool exception paths, wrap the tool callable in the `ToolCard` to raise on demand. Assert on observable effects — that a blocked tool was never invoked, cumulative token counts (`TokenTrackingRail`), retry counts, and the `AgentObservabilityRail` typed span log. For composition, register two rails with a known priority order and assert the lower-priority rail's `before_tool_call` sees the context field written by the higher-priority rail. No framework test harness exists — each test constructs `DeepAgent` via `create_deep_agent(…)` manually.

```mermaid
flowchart TD
    subgraph FIXTURE["test fixture"]
        MC["MockModelClient\n(returns tool call on call 1,\nfinal answer on call 2,\nraises exception on call 3)"]
        MT["MockTool\n(succeeds / raises on demand)"]
    end
    FIXTURE --> AGENT["DeepAgent\n(rails under test only)"]
    AGENT --> RUN["execute_task(task)"]
    RUN --> P1["assert happy-path invariants\n(BEFORE/AFTER hooks)"]
    RUN --> P2["assert exception-path invariants\n(ON_EXCEPTION hooks)"]
    RUN --> P3["assert composition invariants\n(hook A state visible to hook B)"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/core/foundation/llm/model_clients/base_model_client.py:45</code> — <code>BaseModelClient</code>: injectable mock boundary<br><code>agent-core/openjiuwen/harness/factory.py:460</code> — <code>create_deep_agent</code>: model client override<br><code>agent-core/openjiuwen/core/foundation/tool/base.py:78</code> — <code>ToolCard</code> callable wrapper: injectable error fixture<br><code>agent-core/openjiuwen/harness/observability/rail.py:355</code> — <code>AgentObservabilityRail</code>: typed span log to assert on</sub>
</details>

---

## 7. What is the event bridge model — which events propagate to the inner agent and which stay on the outer harness?

**General:** The outer harness and the inner agent loop are separate event domains. Inner-agent events (model call, tool call, exceptions at those call sites) must bridge into the inner loop's callback manager because they occur during active reasoning — a security hook that blocks a specific tool call must fire at the point of execution, inside the inner loop, not before the loop starts. Outer events (full invocation boundary, task loop iteration boundary) stay on the outer harness because the inner loop does not know it is being called multiple times toward a long-horizon goal. Incorrectly wiring a hook to the wrong domain causes it to fire at the wrong granularity — a per-model-call cost meter registered as a per-invocation hook only fires once per outer pass and misses all intermediate calls.

**Jiuwen:** Three event sets are defined in `deep_agent.py`: `_BRIDGE_EVENTS` (9) — BEFORE/AFTER_MODEL_CALL, ON_MODEL_EXCEPTION, BEFORE/AFTER_TOOL_CALL, ON_TOOL_EXCEPTION, AFTER_REACT_ITERATION, ON_USER_MESSAGE, BEFORE_STEERING_DRAIN — are routed to the inner agent's callback manager (`_register_rail_selective`) so rails intercept at execution time. `_OUTER_ONLY_EVENTS` (2) — BEFORE_INVOKE, AFTER_INVOKE — stay on `DeepAgent`. `_DEEP_EVENTS` (2) — BEFORE_TASK_ITERATION, AFTER_TASK_ITERATION — are fired by the outer task-loop controller. Priority ordering within each event point determines which rail fires first (higher priority first).

```mermaid
flowchart TD
    subgraph DEEP["DeepAgent event domain"]
        BI2["BEFORE_INVOKE"]
        BTI2["BEFORE_TASK_ITERATION"]
        ATI2["AFTER_TASK_ITERATION"]
        AI2["AFTER_INVOKE"]
    end
    subgraph BRIDGE["Bridged → also in ReActAgent"]
        BMC2["BEFORE_MODEL_CALL"]
        AMC2["AFTER_MODEL_CALL"]
        EMC2["ON_MODEL_EXCEPTION"]
        BTC2["BEFORE_TOOL_CALL"]
        ATC2["AFTER_TOOL_CALL"]
        ETC2["ON_TOOL_EXCEPTION"]
    end
    DEEP -->|"wraps"| BRIDGE
    BRIDGE --> REACT["ReActAgent\ncallback_manager"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/deep_agent.py:158</code> — <code>_BRIDGE_EVENTS</code> (9); <code>:180</code> <code>_OUTER_ONLY_EVENTS</code>; <code>:188</code> <code>_DEEP_EVENTS</code>; <code>:2283</code> <code>_register_rail_selective</code> routes bridged events to the inner agent<br><code>agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:11</code> — inner callback manager<br><code>agent-core/openjiuwen/core/single_agent/base.py:160</code> — <code>BaseAgent.agent_callback_manager</code></sub>
</details>

**Gap.** No runtime check prevents a rail from registering on a DEEP event and expecting per-model-call granularity. The mismatch is a silent design error — the hook fires, just at the wrong rate.

---

## 8. How does hot-loading lifecycle hooks into a running agent work and when would you need it?

**General:** Standard lifecycle hooks are bound at construction — the spec is resolved, instances are created, and the pipeline is fixed. Hot-loading binds new lifecycle hooks to a live agent without stopping and restarting it. This is needed when the full capability set is not known at construction time: an agent discovers a skill library during a task and must load the tools and hooks declared in it; a user grants a new permission mid-session; an external plugin is installed while the agent is running. Hot-loading must preserve the existing pipeline state — the new hook joins the priority order without disrupting hooks that are mid-execution. Because agent invocations are async, binding a new callback during an active model call creates a race; the implementation must guard against partial registration.

**Jiuwen:** Hot-loading is implemented by `apply_expert_harness_hot()` (`harness/expert_harness_runtime.py`), which reads an `ExpertHarnessSpec`, resolves new rails and tools, and calls `_hot_bind_rail(agent, rail)` for each — which calls `await agent.register_rail(rail)` — plus `_hot_bind_prompt_section()` to inject the prompt section. `apply_expert_harness_hot()` wraps the binds in try/except and rolls back via `unapply_expert_harness_hot()` on failure. `_hot_bind_rail` itself is not lock-protected, so a rail loaded during a concurrent model call may register incompletely.

```mermaid
flowchart TD
    SKILL["SKILL.md / ExpertHarnessSpec"] --> EH["ExpertHarness\n(expert_harness_runtime.py)"]
    EH --> RESOLVE["resolve new rails + tools\nfrom spec"]
    RESOLVE --> HOT["_hot_bind_rail(agent, rail)\nfor each new rail"]
    HOT --> CBM["append to callback_manager\nat priority position"]
    HOT --> SPB["inject prompt section\ninto SystemPromptBuilder"]
    CBM & SPB --> LIVE["live DeepAgent\nnow has new capability"]
    LIVE -.->|"risk"| RACE["race condition:\nnot lock-protected"]
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/expert_harness_runtime.py:33</code> — <code>apply_expert_harness_hot()</code>; <code>:190</code> <code>_hot_bind_rail()</code>; <code>:198</code> <code>_hot_bind_prompt_section()</code><br><code>agent-core/openjiuwen/harness/schema/expert_harness_spec.py:119</code> — <code>ExpertHarnessSpec</code><br><code>agent-core/openjiuwen/harness/prompts/builder.py:28</code> — <code>SystemPromptBuilder</code><br><code>agent-core/openjiuwen/core/single_agent/agent_callback_manager.py:11</code> — live callback registration target</sub>
</details>

**Gap.** `_hot_bind_rail` is not protected by a lock; a rail loaded while the agent is mid-model-call may register incompletely. No rollback mechanism exists if hot-bind fails partway through.

---

## 9. How does a harness accumulate experience — what is the skill evolution pipeline?

**General:** A harness that intercepts every model call and tool call already has the data needed to improve itself: which tool sequences solved the problem, which reasoning patterns were reused, which sub-task plans worked. Skill evolution captures this data, extracts reusable patterns from it, and persists them as skill experience records that future agents load at task start. Without an evolution pipeline, every agent run starts from zero; with it, the agent population improves across sessions without retraining the underlying model. Three design decisions shape any evolution pipeline: (1) **what to capture** — the full execution trajectory or only successful final passes; (2) **what quality gate** prevents low-quality or noisy patterns from being persisted; (3) **whether human approval** is required before a pattern becomes a permanent skill (human-in-the-loop evolution) or whether the system auto-saves (fully autonomous evolution). The approval gate is the main lever for controlling how much the agent is trusted to modify its own future behaviour.

**Jiuwen:** `EvolutionRail` is the base class: it subscribes to a trajectory processor, collects execution spans into scope-local clean windows, applies quality gates, and suppresses capture during evolution work itself (to prevent skills about writing skills). `SkillEvolutionRail` extends it for single-agent experience: after each invoke it scans the trajectory for reusable patterns, stages candidate experience records, and routes them through `EvolutionInterruptRail` for user approval before `EvolutionStore` persistence — or auto-saves if `auto_save=True`. `TeamSkillEvolutionRail` extends it for multi-agent collaboration: it waits for a team completion event, aggregates trajectories from all member agents, detects the collaboration pattern, and generates a team skill record. `TrajectoryRail` (priority 10, shared tier with `TaskCompletionRail` and `AgentObservabilityRail`) archives one canonical trajectory per invoke to a `FileTrajectoryStore` for offline analysis. Trigger flags (`signal_trigger`, `review_trigger`) are declared `Optional[bool] = None` and coerced with `bool()`, i.e. off by default; an explicit `/evolve` command also dispatches evolution.

```mermaid
flowchart TD
    RUN(["agent invoke completes"]) --> TRAJ["TrajectoryRail\narchive canonical trajectory\nto FileTrajectoryStore"]
    RUN --> EVO["EvolutionRail base\ncollect spans into clean window\napply quality gate"]
    EVO -->|"single-agent"| SKE["SkillEvolutionRail\ndetect reusable pattern\nstage experience record"]
    EVO -->|"multi-agent"| TSE["TeamSkillEvolutionRail\nwait for team completion\naggregate member trajectories\ndetect collaboration pattern"]
    SKE --> GATE{"approval gate"}
    TSE --> GATE
    GATE -->|"auto_save=True"| STORE["EvolutionStore\n(persist skill record)"]
    GATE -->|"requires approval"| INT["EvolutionInterruptRail\nroute to user confirmation"]
    INT -->|"approved"| STORE
    INT -->|"rejected"| DISC(["discard"])
    STORE --> NEXT(["future agents load\nskill at task start"])
```

<details>
<summary>Anchors</summary>
<sub><code>agent-core/openjiuwen/harness/rails/evolution/evolution_rail.py:241</code> — <code>EvolutionRail</code> base<br><code>agent-core/openjiuwen/harness/rails/evolution/skill_evolution_rail.py:141</code> — <code>SkillEvolutionRail</code><br><code>agent-core/openjiuwen/harness/rails/evolution/team_skill_evolution_rail.py:137</code> — <code>TeamSkillEvolutionRail</code><br><code>agent-core/openjiuwen/harness/rails/evolution/evolution_interrupt_rail.py:37</code> — <code>EvolutionInterruptRail</code><br><code>agent-core/openjiuwen/harness/rails/evolution/trajectory_rail.py:23</code> — <code>TrajectoryRail</code> (priority 10, <code>:32</code>)</sub>
</details>
