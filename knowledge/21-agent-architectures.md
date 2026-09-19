# Agent architectures and protocols

## 1. Workflows versus agents

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** A workflow is a deterministic, pre-defined sequence of steps; an agent is a dynamic, model-driven loop.

**Key points.**

- Use workflows when the sequence is fixed (extract → transform → classify), costs must be bounded, or the path can be fully tested
- Use agents when the task requires open-ended reasoning, tool selection is context-dependent, or the goal is under-specified
- Many production systems combine both: a deterministic outer workflow calling agent sub-tasks where flexibility is needed

**Concept.** A workflow is a deterministic, pre-defined sequence of steps — the control flow is fixed by the developer. An agent is a dynamic, model-driven loop — the model decides which tools to call and when to stop. Workflows are predictable and auditable; agents are flexible but non-deterministic. The choice depends on whether the task structure is known in advance.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

The graph path (Pregel workflow engine) handles known control flow with static and conditional routers, barriers, and OR-groups. The harness path (ReAct agent loop + rails) handles dynamic tool use. The framework supports both, and the design guidance is explicit: use the graph path for known control flow, the team path for flexible collaboration.

</details>

---

## 2. MCP versus A2A protocol

<span class="badge badge-type">Compare</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Two complementary protocols for extending AI systems: MCP for tools, A2A for agent-to-agent delegation.

**Key points.**

- MCP (Model Context Protocol) — one LLM connects to many tool providers; centralized control, the agent decides which server to call
- A2A (Agent-to-Agent Protocol) — agents coordinate with other agents; decentralized execution, possibly across deployments
- They are complementary: MCP for tools, A2A for delegating to other agents
- Most current frameworks implement MCP; A2A wire-protocol support is still emerging

**Concept.** Two complementary protocols for extending AI systems. **MCP (Model Context Protocol):** One LLM connects to many tool providers. Centralized control — the agent decides which MCP server to call. Analogous to a single developer with a library of APIs. **A2A (Agent-to-Agent Protocol):** Agents coordinate with other agents. Decentralized execution — agents delegate to other agents asynchronously, potentially across deployments. Analogous to a team of specialists.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

MCP: `McpServerConfig` (`core/foundation/tool/mcp/mcp_config.py:1`) configures MCP servers; the client discovers tools via `tools/list` and invokes via `tools/call`. A2A-style delegation: `SubagentRail` (`harness/rails/subagent/subagent_rail.py:1`) delegates tasks to sub-agents using `SubagentRequest`/`SubagentResponse` schemas — this is internal delegation, not the A2A wire protocol. Cross-deployment agent-to-agent communication is not implemented.

</details>

---

## 3. Four multi-agent system architectures

<span class="badge badge-type">Design</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Multi-agent systems fall into four architectural types, and every one needs the same five components.

**Key points.**

- Centralized — a single supervisor assigns tasks and aggregates results; simple to reason about, single point of failure
- Decentralized (peer-to-peer) — agents communicate directly without a central coordinator; more resilient, harder to debug
- Hierarchical — a tree of supervisors: a top-level agent delegates to mid-level agents, which delegate further; scales to complex tasks
- Hybrid — combines patterns, e.g. centralized task assignment with peer-to-peer result sharing
- Five components: agents (capabilities and roles), communication (message schemas), coordination (task assignment), shared memory/state, and environment/tool access

**Concept.** Multi-agent systems fall into four architectural types, and every one of them needs the same five components.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Architecture is hierarchical via `SubagentRail` and `TaskPlanningRail`. No peer-to-peer pattern is implemented. Five components: agents (`SubagentSpec` configs), communication (`SubagentRequest`/`SubagentResponse`), coordination (`TaskPlanningRail`), shared memory (`LongTermMemory` + `EphemeralMemory`), environment (tools via `ToolCard` and MCP servers).

</details>

---

## 4. Testing non-deterministic agents (invariant-based testing)

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Exact output strings cannot be asserted for agents, so tests target invariants: properties that must always hold.

**Key points.**

- Tool invariants — required tools were called, forbidden tools were not, parameters were valid
- Termination invariants — the agent stopped within N steps and did not loop
- Schema invariants — outputs matched the required schema
- Safety invariants — no prohibited content, no budget exceeded
- Cost invariants — token usage stayed within budget
- Complement with LLM-as-judge for behavioral correctness, and inject controlled model responses to test agent logic without live calls

**Concept.** Exact output strings cannot be asserted for agents, so tests target invariants: properties that must always hold regardless of the specific output.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`ModelClientABC` (`core/foundation/llm/model_clients/base.py:1`) is the mockable boundary. Rail contract invariants: `CircuitBreakerRail` for termination, structured output tool for schema, `GuardrailRail` for safety, `usage_cost.py:101` for budget. Behavioral correctness: `LLMAsJudge` (`agent_evolving/evaluator/metrics/llm_as_judge.py:40`). The evaluator pipeline is offline and is not integrated with pytest.

</details>

---
