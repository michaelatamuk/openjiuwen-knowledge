# Agent fundamentals and the loop

## 1. What's the difference between a chatbot and an agent

**General:** A chatbot maps one input to one model reply. An agent runs a loop: it calls the model, may call tools, feeds results back, and repeats until a stopping condition is met. The defining trait is the tool/reason loop and a termination rule, not the size of the model.

**Jiuwen:** There is no separate `Chatbot` class; the distinction is structural. A single model turn is the workflow LLM component, which calls `llm.invoke` once and has no tool branch. An agent is the loop in `ReActAgent.invoke`: it calls the model, and if the returned message has no tool calls it returns the answer; otherwise it executes the tools and iterates. `DeepAgent` wraps this with an outer task loop.

**Chatbot:**

```mermaid
flowchart TD
    I1(["input"]) --> M1["model"] --> O1(["reply"])
```

**Agent:**

```mermaid
flowchart TD
    I(["input"]) --> M
    subgraph LOOP["ReAct loop"]
    direction TB
        M["model call"] --> D{"tool calls?"}
        D -->|yes| T["run tools"] --> M
    end
    D -->|"no tool calls "| A(["final answer"])
    T ~~~ A
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/workflow/components/llm/llm_comp.py:524</code> — single model call, no tool branch<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2740</code> — the ReAct loop<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2793</code> — no tool calls → final answer<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2813</code> — execute tools and iterate<br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2694</code> — outer task loop</sub>

</details>

<sub>_Canonical source: `source/ai-agent-interview-questions_for_engineers.md`; also covered in: ai-agent, genai._</sub>

---

## 2. What's the difference between a workflow and an agent

**General:** A workflow is a pre-declared graph: you author the steps, edges, and branches, and execution follows that topology. An agent decides its next step at runtime from model output. Workflows are predictable and cheap; agents are flexible and variable. They compose: a workflow can contain an agent node.

**Jiuwen:** The workflow engine is a Pregel-style graph machine. Topology is declared up front via the start component, connections, and conditional connections, and execution terminates when the end component produces output. An agent loop instead branches on live `tool_calls`. A workflow can embed an agent as one node, where a single executable just calls the agent's `invoke`.

**Workflow (fixed topology):**

```mermaid
flowchart TD
    A1(["start"]) --> B1["step"] --> C1{"branch"}
    C1 -->|x| D1["step"] --> E1(["end"])
    C1 -->|y| E1
```

**Agent (decided at runtime):**

```mermaid
flowchart TD
    A2(["input"]) --> M
    subgraph LOOP["ReAct loop"]
    direction TB
        M["model call"] --> Q{"tool calls?"}
        Q -->|yes| X["run tool"] --> M
    end
    Q -->|"no tool calls"| Z(["answer"])
    X ~~~ Z
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/workflow/workflow.py:98</code> — <code>Workflow</code> class<br>&bull; <code>agent-core/openjiuwen/core/graph/pregel/engine.py:255</code> — graph execution driver<br>&bull; <code>agent-core/openjiuwen/core/workflow/workflow.py:136/279/311</code> — <code>set_start_comp</code> / <code>add_connection</code> / <code>add_conditional_connection</code><br>&bull; <code>agent-core/openjiuwen/core/workflow/workflow.py:551</code> — terminates when the end component produces output<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/llm/react/react_executable.py:41</code> — workflow node embedding an agent</sub>

</details>

<sub>_Canonical source: `source/ai-agent-interview-questions_for_engineers.md`; also covered in: ai-agent._</sub>

---

## 3. What's the difference between a linear chain and a graph with conditional branches

**General:** A linear chain is a fixed sequence where each step always activates the next. A graph adds branching and merging: a router selects successors based on state at runtime, and a join/barrier decides when a merge node is ready (all predecessors, or any of an exclusive group).

**Jiuwen:** Both are built on the same `PregelGraph`. `add_connection` registers a static edge; at compile time `PregelGraph._compile` turns static edges into `StaticRouter` (1→N) or `BarrierChannel` (N→1, with CNF OR-groups for mutually exclusive predecessors). `add_conditional_connection` registers a branch router compiled to `ConditionalRouter`, whose `dispatch` calls the user selector and emits `TriggerMessage`s only for the chosen targets. A linear chain always activates its single successor; a conditional graph activates only the selector's targets, and `BranchRouter` raises `COMPONENT_BRANCH_EXECUTION_ERROR` if none match.

```mermaid
flowchart TD
    subgraph LIN["Linear chain"]
    direction LR
    L1(["start"]) --> L2["step"] --> L3["step"] --> L4(["end"])
    end
    subgraph COND["Conditional graph"]
    direction TB
    S(["start"]) --> P["step"] --> R{"BranchRouter / ConditionalRouter"}
    R -->|"condition x"| X["branch x"] --> M["BarrierChannel (merge)"]
    R -->|"condition y"| Y["branch y"] --> M
    M --> E(["end"])
    end
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/workflow/workflow.py:279</code> — <code>add_connection</code> (static); <code>:311</code> — <code>add_conditional_connection</code><br>&bull; <code>agent-core/openjiuwen/core/workflow/_workflow.py:221</code> — <code>BaseWorkflow.add_connection</code> → <code>self._graph.add_edge</code>; <code>:255</code> — <code>add_conditional_connection</code> wraps <code>BranchRouter</code> + <code>register_branch_targets</code><br>&bull; <code>agent-core/openjiuwen/core/graph/graph.py:103</code> — <code>add_edge</code>; <code>:122</code> — <code>add_conditional_edges</code>; <code>:267</code> <code>_compile</code>; <code>:300</code> adds branches to the Pregel builder<br>&bull; <code>agent-core/openjiuwen/core/graph/pregel/builder.py:28</code> — <code>add_edge</code> (N→1 <code>BarrierChannel</code>, 1→N <code>StaticRouter</code>); <code>:67</code> <code>add_branch</code><br>&bull; <code>agent-core/openjiuwen/core/graph/pregel/router.py:11</code> — <code>StaticRouter.dispatch</code>; <code>:26</code> <code>ConditionalRouter.dispatch</code><br>&bull; <code>agent-core/openjiuwen/core/graph/pregel/channels.py:104</code> — <code>TriggerChannel</code>; <code>:129</code> <code>BarrierChannel</code>; <code>:166</code> <code>is_ready</code> (CNF OR-groups)<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/flow/branch_router.py:92</code> — <code>BranchRouter.__call__</code></sub>

</details>

**Gap.** `branch_targets` (used for CNF OR-group resolution) is only populated for `BranchRouter`; arbitrary callable routers go through a `new_router` wrapper and never register target sets, so exclusive-branch merging degrades to plain AND barriers. There is no static validation that a conditional router's targets are declared nodes, and `ConditionalRouter.dispatch` passes `state=None` to selectors, so selectors cannot read graph state directly.

<sub>_Canonical source: `source/ai-agent-framework-interview-questions_for_engineers.md`; also covered in: framework._</sub>

---

## 4. What's the ReAct pattern?

**General:** ReAct alternates thought → action → observation. Each action's real result informs the next thought, so the agent grounds its reasoning in observed state rather than assumptions about it.

**Jiuwen:** The loop is exactly reason/act/observe: model call, branch on `tool_calls`, execute, feed `ToolMessage`s back as the next observation, repeat. The reasoning trace is retained by copying `reasoning_content` into the assistant message, and the iteration number is exposed to rails.

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2766</code> — model call (reason)<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2793</code> — branch on tool calls<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2813</code> — execute (act)<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2787</code> — retain <code>reasoning_content</code><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2742</code> — iteration exposed to rails<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:568</code> — <code>ReActAgent</code> documents the pattern</sub>

</details>

<sub>_Canonical source: `source/ai-agent-interview-questions_for_engineers.md`; also covered in: ai-agent._</sub>

---

## 5. Why interleave reasoning and actions instead of planning everything upfront?

**General:** A fully upfront plan executes with no feedback, so it cannot adapt when reality differs. Interleaving feeds each observation back into the next reasoning step, which corrects drift and grounds the plan in what the tools actually returned.

**Jiuwen:** Jiuwen's agent is a ReAct loop, not a plan-then-execute pipeline: every turn re-decides based on the latest observation and is bounded by `max_iterations` (default 5). The deep agent's outer task loop is likewise iterative — todos are updated as results arrive — rather than a fixed upfront plan.

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2793</code> — re-decides each turn from the latest observation<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2813</code> — acts, then loops on the result<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations=5</code> bounds the loop<br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2723</code> — outer task loop (iterative, hard ceiling)</sub>

</details>

<sub>_Canonical source: `source/ai-agent-interview-questions_for_engineers.md`; also covered in: ai-agent._</sub>

---

## 6. How do you set a hard limit on iterations or steps within a framework

**General:** Cap the loop with a max-iteration/max-round counter, plus optional token and wall-clock budgets, and *enforce* them rather than only reporting. Nested loops need a cap at each level, and the caps should be configurable.

**Jiuwen:** The inner ReAct loop is bounded by `ReActAgentConfig.max_iterations` (default 5) and exits with `{"result_type": "error", "output": "Max iterations reached without completion"}`. When `enable_task_loop=True`, DeepAgent raises the inner ReAct ceiling to `sys.maxsize` and moves the real bound to the outer task loop, where `LoopCoordinator.should_continue()` OR-evaluates a chain of `StopConditionEvaluator`s. `TaskCompletionRail.build_evaluators()` contributes `MaxRounds`/`Timeout`/`TokenBudget`/`CompletionPromise`; the `NoProgressAnswer` evaluator is added separately from `task_loop_no_progress_guard` (`deep_agent._build_task_loop_evaluators`). Independently, `_run_task_loop` hard-codes `max_outer_rounds = 50` and force-stops with `stop_reason: "MaxOuterRounds"`. Team members reuse the wiring via `TaskCompletionRail(max_rounds=...)`, and cooperative stops exist via `ctx.request_force_finish()` and `DeepAgent.abort()`.

```mermaid
flowchart TD
    I(["input"]) --> M
    subgraph INNER["Inner ReAct loop (max_iterations = 5, or sys.maxsize under task loop)"]
    direction TB
        M["model call"] --> D{"tool calls?"}
        D -->|yes| T["run tools"] --> M
    end
    D -->|"no tool calls"| A(["answer"])
    INNER -->|"enable_task_loop"| OUTER["Outer task loop: LoopCoordinator evaluator OR-chain"]
    OUTER --> EV["MaxRounds · TokenBudget · Timeout · NoProgress · CompletionPromise"]
    OUTER --> HARD["hard max_outer_rounds = 50 → stop_reason MaxOuterRounds"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations: int = Field(default=5)</code>; <code>:2740</code> the bounded loop; <code>:2852</code> exhaustion result<br>&bull; <code>agent-core/openjiuwen/harness/schema/stop_condition.py:134</code> — <code>MaxRoundsEvaluator.should_stop</code>; <code>:143</code> TokenBudget; <code>:162</code> Timeout<br>&bull; <code>agent-core/openjiuwen/harness/task_loop/loop_coordinator.py:139</code> — <code>should_continue()</code> OR-chain; <code>:110</code> <code>increment_iteration</code>; <code>:133</code> <code>request_abort</code><br>&bull; <code>agent-core/openjiuwen/harness/rails/task_completion_rail.py:168</code> — <code>build_evaluators()</code>; <code>:178-185</code> build MaxRounds/Timeout/TokenBudget<br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2723</code> — <code>max_outer_rounds = 50</code>; <code>:2725</code> <code>while coordinator.should_continue()</code>; <code>:2727-2739</code> force-stop; <code>:1116</code> inner cap swap; <code>:2338</code> <code>_build_task_loop_evaluators</code>; <code>:3380</code> <code>abort()</code><br>&bull; <code>agent-core/openjiuwen/agent_teams/agent/agent_configurator.py:436</code> — member <code>TaskCompletionRail(max_rounds=agent_spec.max_iterations)</code><br>&bull; <code>agent-core/openjiuwen/agent_teams/workflow/backends/budget_rail.py:88</code> — token-ceiling <code>ctx.request_force_finish</code>; <code>agent-core/openjiuwen/agent_teams/agent/scheduling/scheduler.py:300</code> — review-round cap</sub>

</details>

**Gap.** The 50-round ceiling is a literal local, not configurable. `TaskCompletionRail`'s `max_rounds`/`timeout_seconds`/`max_tokens` all default to `None`, so with the default auto-injected rail the LoopCoordinator chain is empty and only the 50-round literal and abort bound the outer loop. `NoProgressAnswerEvaluator` is gated by `TaskLoopNoProgressGuardConfig.enabled`, which defaults to `True`. Agent-teams review-round caps and swarmflow budget caps apply only in `scheduled` mode / when a budget is configured.

<sub>_Canonical source: `source/ai-agent-framework-interview-questions_for_engineers.md`; also covered in: framework, ai-agent._</sub>

---

## 7. What decides when an agent stops and returns a final answer instead of calling another tool

**General:** Usually the model itself: when it emits no tool calls, the answer is final. Around that sit hard limits — max iterations, token/time budgets, and explicit stop conditions — so a confused agent does not loop forever.

**Jiuwen:** Two levels. Inner: in `ReActAgent`, no tool calls means a final answer, bounded by `max_iterations` (default 5). Outer (`DeepAgent` task loop): the `LoopCoordinator` OR-evaluates a chain of stop evaluators — max rounds, timeout, token budget, completion promise, and no-progress answer. Completion can also arrive as a `<promise>…</promise>` marker extracted by `TaskCompletionRail`. A hardcoded ceiling of 50 outer rounds backstops everything.

```mermaid
flowchart TD
    I(["input"]) --> LOOP
    subgraph LOOP["ReAct loop (inner: max_iterations = 5)"]
    direction TB
        M["model call"] --> T{"tool calls?"}
        T -->|yes| R["run tools"] --> M
    end
    LOOP --> G{"DeepAgent outer task loop: rounds / time / budget / no-progress"}
    T -->|"no tool calls"| F(["final answer"])
    R ~~~ F
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2793</code> — no tool calls → final answer<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations</code> default 5<br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:2740</code> — inner loop<br>&bull; <code>agent-core/openjiuwen/harness/task_loop/loop_coordinator.py:139</code> — outer <code>should_continue</code><br>&bull; <code>agent-core/openjiuwen/harness/schema/stop_condition.py:124-331</code> — evaluator chain<br>&bull; <code>agent-core/openjiuwen/harness/rails/task_completion_rail.py:403</code> — completion-promise extraction<br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2723</code> — hard 50-round ceiling</sub>

</details>



<sub>_Canonical source: `source/ai-agent-interview-questions_for_engineers.md`; also covered in: ai-agent._</sub>

---

## 8. Preventing an agent from getting stuck in an infinite tool-calling loop

**General:** Cap iterations, detect repetition (same tool and arguments repeatedly), nudge or abort when no progress is made, and also cap rounds, tokens, and wall time. Detection should compare canonicalized arguments, not raw strings.

**Jiuwen:** Inner cap `max_iterations` (ReAct default 5, harness default 15). Repetition detection: `ModelAnomalyDetectionRail` finds consecutive identical `(tool_name, canonical_args)` rounds and either folds them into a warning or aborts; `ToolCallDeduplicationRail` counts repeated read-only calls and warns. Outer guards: `NoProgressAnswerEvaluator`, `MaxRoundsEvaluator`, and the hard 50-round ceiling. Agent teams add repeat-tool and ping-pong detectors.

```mermaid
flowchart TD
    M["model call"] --> D{"tool calls?"}
    D -->|yes| T["run tools"]
    T --> G{"loop guard"}
    G -->|"repeated (tool, args)"| W["compact/abort (ModelAnomalyDetectionRail)"]
    G -->|"repeated read-only"| DEDUP["ToolCallDeduplicationRail warn"]
    G -->|no| M
    G -->|"budget/rounds/time"| X(["stop"])
    D -->|no| A(["final answer"])
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations</code> default 5; <code>agent-core/openjiuwen/harness/schema/config.py:252</code> — harness default 15<br>&bull; <code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74/90</code> — tool-loop threshold + bailout<br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157</code> — cross-turn repeat counter<br>&bull; <code>agent-core/openjiuwen/harness/schema/stop_condition.py:181</code> — <code>NoProgressAnswerEvaluator</code><br>&bull; <code>agent-core/openjiuwen/harness/deep_agent.py:2723</code> — hard 50-round ceiling<br>&bull; <code>agent-core/openjiuwen/agent_teams/reliability/detectors/repeat_tool.py:15</code> — repeat-tool; <code>agent-core/openjiuwen/agent_teams/reliability/detectors/pingpong.py:12</code> — ping-pong</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`; also covered in: ai-agent, engineering, genai, llm-applied._</sub>

---

## 9. "The agent is stuck" tests whether you've shipped one, not studied one

**General:** Infinite tool loops, retries on a flaky API that never terminate, token spend that quietly spikes overnight. Vague answers ("I'd add safeguards") don't land; concrete answers do — `max_iterations=5`, a token budget per session, a circuit breaker after N consecutive tool failures. A strong answer includes: a hard iteration cap, repetition detection on canonicalized `(tool, args)`, per-session token/cost budget, retry with backoff only for idempotent reads, and a circuit breaker on repeated failures.

**Jiuwen:** Concrete caps exist: ReAct `max_iterations` (default 5, harness 15), `AgenticRetriever.max_iter` (default 2, clamped), `ModelAnomalyDetectionRail` (consecutive identical tool rounds → compact/abort) and `ToolCallDeduplicationRail`. A session cost cap is enforced when the provider reports cost, and `ModelBackupRail` fails over. What is **missing** is a circuit breaker after N consecutive failures and a durable token budget on the retrieval loop.

```mermaid
flowchart TD
    L["infinite loop / runaway spend"] --> I["max_iterations=5 (harness 15)"]
    L --> D["repetition detect: identical (tool,args)"]
    L --> B["session cost cap (if provider reports cost)"]
    L --> R["retry only idempotent reads"]
    L -.->|"absent"| CB["circuit breaker after N consecutive failures"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations: int = Field(default=5)</code>; <code>agent-core/openjiuwen/harness/schema/config.py:252</code> — harness default 15<br>&bull; <code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74</code> — <code>ToolLoopCompactConfig</code> (default off); <code>:90</code> bailout<br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157</code> — repeat counter/warning<br>&bull; <code>jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171/196</code> — enforced session cost cap<br>&bull; <code>agent-core/openjiuwen/core/single_agent/rail/model_backup.py:9</code> — <code>ModelBackupRail</code> failover (no circuit breaker)</sub>

</details>

---

## 10. "The agent is stuck in a loop" is testing production experience

**General:** max iteration limits per task, token budget caps per step, detecting and killing a failing loop before it burns cost, and retry logic on failed tool calls without infinite recursion. This separates people who have run one from people who have read about one. A strong answer includes: a hard iteration cap, a per-session/step token or cost budget, repetition detection on canonicalized `(tool, args)`, and bounded retries that never retry non-idempotent tools.

**Jiuwen:** Caps are concrete: ReAct `max_iterations` (5; harness 15), `AgenticRetriever.max_iter` (2, clamped), `ModelAnomalyDetectionRail` (identical tool rounds → compact/abort), `ToolCallDeduplicationRail`, and secure-by-default `idempotent=False` (non-idempotent tools never retried). A session cost cap is enforced when the provider reports cost; a per-step token budget in the task loop is wired but off by default.

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288</code> — <code>max_iterations=5</code>; <code>agent-core/openjiuwen/harness/schema/config.py:252</code> — harness 15<br>&bull; <code>agent-core/openjiuwen/core/retrieval/retriever/agentic_retriever.py:133</code> — <code>max_iter=2</code> clamped<br>&bull; <code>agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74/90</code> — loop compact/abort<br>&bull; <code>agent-core/openjiuwen/core/foundation/tool/base.py:109</code> — <code>idempotent</code> default <code>False</code><br>&bull; <code>agent-core/openjiuwen/harness/rails/tool_call_resilience_rail.py:128/145</code> — non-idempotent guard + retry budget<br>&bull; <code>jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171</code> — session cost cap</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-interview-patterns_for_engineers.md`; also covered in: ai-agent, ai-technical._</sub>

---

## 11. How do you detect and prevent divergence in an agent loop — not just cap iterations?

**General:** A hard iteration cap (`max_iterations`) prevents runaway loops by time but does not detect that the agent is *stuck repeating itself*. Divergence detection is a complementary mechanism: (1) hash `(tool_name, canonicalised_args)` on each turn and compare against prior turns — if the same call recurs, the agent is spinning; (2) compare model output text similarity across consecutive turns — if the reasoning text is structurally identical, the agent is not making progress; (3) on detection, trigger a compaction step (rewrite history to remove the reinforcing noise) before continuing, rather than simply aborting. The goal is to detect the loop early and repair the context, not just stop at a budget limit.

**Jiuwen:** `ToolCallDeduplicationRail` hashes `(tool, args)` per turn and emits warnings on repeat. `ModelAnomalyDetectionRail` detects consecutive identical tool-call rounds and can trigger compact-then-abort (`ToolLoopCompactConfig`), but this config is **off by default** — loops generate warnings but do not abort without explicit configuration. There is no output-text-similarity divergence check (only tool-call-level detection). Compaction on loop is available via `FullCompactProcessor` but is not automatically triggered by the dedup rail.

```mermaid
flowchart TD
    LOOP["agent appears stuck"] --> HASH["ToolCallDeduplicationRail: hash(tool,args) repeat → warn"]
    LOOP --> ANOM["ModelAnomalyDetectionRail: identical rounds → compact+abort (off by default)"]
    LOOP -.->|"absent"| TEXT["output-text-similarity divergence check"]
    LOOP -.->|"absent"| AUTO["auto-compaction triggered by dedup rail"]
    ANOM -.->|"must configure"| CONF["ToolLoopCompactConfig: must be explicitly enabled"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157` — repeat counter + warning<br>&bull; `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74` — `ToolLoopCompactConfig` (default off); `:90` compact+abort<br>&bull; `agent-core/openjiuwen/core/context_engine/processor/compressor/full_compact_processor.py` — compaction; not auto-triggered by dedup</sub>

</details>

**Gap.** `ToolLoopCompactConfig` is off by default — loops warn but do not abort. No output-text-similarity divergence check. Compaction is not automatically triggered on loop detection.

<sub>_Canonical source: `source/agent-failure-patterns_for_engineers.md`._</sub>

---

## 12. What are the explicit termination conditions an agent needs — beyond "stop when done"?

**General:** "Stop when done" is not a termination condition; it is an aspiration. A production agent needs at least three explicit paths: (1) **success** — the agent emits a final answer meeting a defined success condition (e.g., all required fields populated, context cited, schema valid); (2) **budget exhaustion** — hard cap on iterations and tokens, with a graceful degraded response (partial answer + "budget exceeded" notice) rather than silence or an error; (3) **human escalation** — when the agent cannot resolve the task within budget or detects irresolvable ambiguity, it hands off explicitly. Confidence threshold as a fourth optional path: if the model's self-assessed uncertainty is above a threshold, escalate before acting rather than produce an ungrounded answer.

**Jiuwen:** Multiple termination paths are implemented. `ReactAgent.max_iterations` is the hard iteration cap (default 5, harness 15). `WorkPlanApprovalRail` and `StructuredAskUserRail` provide the human-in-the-loop escalation path. `ModelAnomalyDetectionRail` can abort on anomaly detection. `AgentObservabilityRail` always runs last, ensuring every turn is logged even at termination. What is **absent**: no graceful degraded response on budget exhaustion (the agent aborts rather than returning a partial answer), no confidence-threshold-based escalation, and `WorkPlanApprovalRail` is opt-in per agent config.

```mermaid
flowchart TD
    T["termination decision"] --> S["success: final answer emitted (ReactAgent done)"]
    T --> B["budget: max_iterations (5/15) + session cost cap"]
    T --> E["escalation: WorkPlanApprovalRail / StructuredAskUserRail (opt-in)"]
    T --> A["anomaly abort: ModelAnomalyDetectionRail (off by default)"]
    T -.->|"absent"| D["graceful degraded response at budget exhaustion"]
    T -.->|"absent"| C["confidence-threshold auto-escalation"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288` — `max_iterations: int = Field(default=5)`<br>&bull; `agent-core/openjiuwen/harness/schema/config.py:252` — harness default 15<br>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171` — session cost cap<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/structured_ask_user_rail.py` — structured human escalation<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/code/rails/code_plan_approval_interrupt_rail.py` — `WorkPlanApprovalRail` (opt-in)</sub>

</details>

**Gap.** Budget exhaustion produces abort, not a graceful degraded response. Confidence-based escalation is absent. Human-in-the-loop rails are opt-in and not in the default profile.

<sub>_Canonical source: `source/agent-failure-patterns_for_engineers.md`._</sub>

---

## 13. When should you use a deterministic workflow instead of an autonomous agent?

**General:** A **workflow** is a fixed, developer-defined sequence of steps — the control flow is hardcoded. An **agent** is a model-driven loop where the model decides which tools to call and when to stop. The distinction matters for reliability, cost, and testability.

Choose a workflow when: (1) the task structure is fully known in advance (extract → validate → classify); (2) every execution must follow the same path for compliance or auditability; (3) failure modes must be enumerated and handled explicitly; (4) cost must be bounded (fixed number of model calls). Choose an agent when: (1) the next action depends on the previous result in ways you cannot enumerate; (2) the task requires open-ended tool use across many possible paths; (3) the goal is underspecified and the model must decompose it dynamically.

In practice most production systems are **hybrid**: a deterministic outer workflow that calls agent sub-tasks only where flexibility is genuinely required. Build the workflow path first; add agent autonomy only where the workflow cannot reach.

**Jiuwen:** The graph path (Pregel-based workflow engine with static and conditional routers, barriers, OR-groups) handles known control flow. The agent harness (ReAct loop with rails) handles dynamic tool use. Both are first-class: the framework design guidance is explicit — use graphs for known control flow, the agent harness for flexible collaboration.

```mermaid
flowchart TD
    TASK["task arrives"] --> Q{"structure known?"}
    Q -->|yes| WF["workflow: fixed steps, deterministic, bounded cost"]
    Q -->|no| AG["agent: model chooses tools, variable steps"]
    WF --> HYB["hybrid: workflow outer shell + agent sub-task where needed"]
    AG --> HYB
    WF --> TEST["unit-testable, enumerable failure modes"]
    AG --> INVAR["invariant-based testing (tool calls, schema, budget)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; `agent-core/openjiuwen/core/agentic/react_agent.py` — agent loop (dynamic)<br>&bull; `agent-core/openjiuwen/core/workflow/` — Pregel graph engine (deterministic)<br>&bull; `agent-core/openjiuwen/harness/rails/task_planning_rail.py` — task decomposition in the agent path</sub>

</details>

<sub>_Canonical source: `source/agent-design-patterns-2026_for_engineers.md`._</sub>
