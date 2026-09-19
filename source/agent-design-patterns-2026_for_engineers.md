# Agent Design Patterns — 2026 Reference

> **The pattern worth noticing:** Interviewers distinguish candidates who can say "this is the right agent pattern for this problem" from those who reach for an agent by default. Being able to name workflow vs agent, MCP vs A2A, and centralized vs decentralized MAS — and explain when each applies — is the differentiator.

---

## 1. Workflows versus agents

**What it covers:** A workflow is a deterministic, pre-defined sequence of steps — the control flow is fixed by the developer. An agent is a dynamic, model-driven loop — the model decides which tools to call and when to stop. Workflows are predictable and auditable; agents are flexible but non-deterministic. The choice depends on whether the task structure is known in advance.

**What a strong answer includes:** Use workflows when the sequence is fixed (extract → transform → classify), costs must be bounded, or the path can be fully tested. Use agents when the task requires open-ended reasoning, tool selection is context-dependent, or the goal is under-specified. Many production systems combine both: a deterministic outer workflow calling agent sub-tasks where flexibility is needed.

**Jiuwen:** The graph path (Pregel workflow engine) handles known control flow with static and conditional routers, barriers, and OR-groups. The harness path (ReAct agent loop + rails) handles dynamic tool use. The framework supports both, and the design guidance is explicit: use the graph path for known control flow, the team path for flexible collaboration.

**Coverage map:** New entry 15-26 (non-deterministic agent testing).

---

## 2. MCP versus A2A protocol

**What it covers:** Two complementary protocols for extending AI systems. **MCP (Model Context Protocol):** One LLM connects to many tool providers. Centralized control — the agent decides which MCP server to call. Analogous to a single developer with a library of APIs. **A2A (Agent-to-Agent Protocol):** Agents coordinate with other agents. Decentralized execution — agents delegate to other agents asynchronously, potentially across deployments. Analogous to a team of specialists.

**What a strong answer includes:** MCP solves tool discovery and invocation for a single agent. A2A solves agent-to-agent communication across systems. They are complementary: MCP for tools, A2A for delegating to other agents. Know that most current frameworks implement MCP but A2A wire protocol support is still emerging.

**Jiuwen:** MCP: `McpServerConfig` (`core/foundation/tool/mcp/mcp_config.py:1`) configures MCP servers; the client discovers tools via `tools/list` and invokes via `tools/call`. A2A-style delegation: `SubagentRail` (`harness/rails/subagent/subagent_rail.py:1`) delegates tasks to sub-agents using `SubagentRequest`/`SubagentResponse` schemas — this is internal delegation, not the A2A wire protocol. Cross-deployment agent-to-agent communication is not implemented.

**Coverage map:** New entry 08-10.

---

## 3. Four multi-agent system architectures

**What it covers:** MAS architectures fall into four types:
- **Centralized:** A single supervisor assigns tasks and aggregates results. Simple to reason about, single point of failure.
- **Decentralized (peer-to-peer):** Agents communicate directly without a central coordinator. More resilient, harder to debug.
- **Hierarchical:** A tree of supervisors — a top-level agent delegates to mid-level agents, which delegate further. Scales to complex tasks; used in enterprise workflows.
- **Hybrid:** Combines patterns — e.g., centralized task assignment with peer-to-peer result sharing.

Every MAS needs five components: agents (capabilities and roles), communication (message schemas), coordination (task assignment), shared memory or state, and environment/tool access.

**What a strong answer includes:** Name the tradeoffs — centralized is auditable but bottlenecked; decentralized is resilient but emergent behavior is hard to test. Hierarchical is the default pattern for complex enterprise tasks. Know what the framework you use supports.

**Jiuwen:** Architecture is hierarchical via `SubagentRail` and `TaskPlanningRail`. No peer-to-peer pattern is implemented. Five components: agents (`SubagentSpec` configs), communication (`SubagentRequest`/`SubagentResponse`), coordination (`TaskPlanningRail`), shared memory (`LongTermMemory` + `EphemeralMemory`), environment (tools via `ToolCard` and MCP servers).

**Coverage map:** New entry 09-7.

---

## 4. Testing non-deterministic agents (invariant-based testing)

**What it covers:** You cannot assert exact output strings for agents — LLM outputs vary. Instead test invariants: properties that must always hold regardless of the specific output. Categories of invariants:
- **Tool invariants** — required tools were called, forbidden tools were not, parameters were valid
- **Termination invariants** — agent stopped within N steps, did not loop
- **Schema invariants** — outputs matched required schema
- **Safety invariants** — no prohibited content, no budget exceeded
- **Cost invariants** — token usage stayed within budget

The complementary approach is LLM-as-judge for behavioral correctness: define a rubric and use a judge model to score the output.

**What a strong answer includes:** Separate the two test types: deterministic invariant checks (fast, in CI) and LLM-judge behavioral tests (slower, offline or on a schedule). Know the mockable boundary — inject controlled model responses to test agent logic without live model calls.

**Jiuwen:** `ModelClientABC` (`core/foundation/llm/model_clients/base.py:1`) is the mockable boundary. Rail contract invariants: `CircuitBreakerRail` for termination, structured output tool for schema, `GuardrailRail` for safety, `usage_cost.py:101` for budget. Behavioral correctness: `LLMAsJudge` (`agent_evolving/evaluator/metrics/llm_as_judge.py:40`). Gap: no official test harness; the evaluator pipeline is offline, not integrated with pytest.

**Coverage map:** New entry 15-26.

---

## 5. Coverage-only topics (already in KB)

| Concept | KB entry |
|---|---|
| ReAct loop and agent fundamentals | 05-1, 05-2 |
| Tool reliability and idempotency | 06-11 |
| Memory types and contamination | 07-1, 07-15 |
| Multi-agent coordination patterns | 09-1 through 09-6 |
| Agentic RAG | 10-6, 10-7 |
| Hallucination mitigation | 01-14 |
| Agent failure modes | 13-1 through 13-11 |
| Observability and tracing | 16-14 |

---

## Coverage summary

| Concept | KB entry | Status |
|---|---|---|
| Workflows vs agents | 15-26 (testing) | New |
| MCP vs A2A | 08-10 | New |
| 4 MAS architecture types + 5 components | 09-7 | New |
| Invariant-based agent testing | 15-26 | New |
| Agent loop (ReAct) | 05-1, 05-2 | Previously covered |
| Tool use patterns | 06-1 through 06-11 | Previously covered |
| Multi-agent orchestration | 09-1 through 09-6 | Previously covered |
