# General engineering

## 1. Deciding when a problem actually needs an LLM versus a simpler rule-based system

**Title.** When to use an LLM vs rules

**Summary.** Use rules when logic is enumerable, must be auditable, or needs exact reproducibility (validation, pattern routing, permissions, arithmetic, parsing). Use an LLM when the task is semantic or open-ended.

**Key points.**

- Rules: enumerable, auditable, reproducible.
- LLM: semantic, ambiguous, open-ended.
- Prefer rules; add the LLM where needed.

**General.** Use a rule-based/deterministic system when the logic is enumerable, must be auditable, or needs exact reproducibility (validation, routing by known patterns, permission checks, arithmetic, parsing). Use an LLM when the task is semantic, open-ended, or handles ambiguity that rules cannot enumerate (summarization, intent, extraction from messy text). Rules for control, LLM for meaning; often both.

![diagram](assets/diagrams/8ad87aa43f3e7cfa39c57a16a4a3c26b8566b81a.png)

**Jiuwen.** The codebase deliberately routes many decisions through deterministic code. The permission engine is a pure rule and AST engine — its docstring notes the model is not used on the permission path — evaluating tiered regex rules and a shell AST before falling back to ask. Safety-critical decisions are rule-based, not model-based.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The codebase deliberately routes many decisions through deterministic code. The permission engine is a pure rule/AST engine — its docstring notes the model is not used on the permission path — evaluating tiered regex rules and a tree-sitter shell AST before falling back to ASK. The product's auto-permission layer has deterministic routes that hard-block/ask by URL scheme, egress fields, and capability side-effects before any reviewer is consulted. Lexical/deterministic retrieval coexists with vector paths (SQLite FTS5 BM25, RRF rank fusion), and structured JSON is extracted with deterministic parsers. Conversely, memory extraction uses an LLM key-information classifier because judging "is this worth remembering" is semantic.

<sub>&bull; `agent-core/openjiuwen/harness/security/permission_engine/core.py:192` — docstring: LLM not used on the permission path<br>&bull; `agent-core/openjiuwen/harness/security/permission_engine/toolguard/tool_policy.py:588` — rule-based tiered policy; agent-core/openjiuwen/harness/security/permission_engine/toolguard/shell_ast.py:82 — deterministic parse<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/permissions/auto_decision.py:73` — deterministic_guard_route; :116 deterministic_domain_route<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/memory/internal.py:165` — bm25_rank_to_score; jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:1044 FTS BM25<br>&bull; `agent-core/openjiuwen/core/retrieval/utils/fusion.py:15` — rrf_fusion; agent-core/openjiuwen/core/foundation/store/index/simple_memory_index.py:348 sort by score<br>&bull; `agent-core/openjiuwen/core/context_engine/context/message_buffer.py:74` — deterministic drop beyond 2×<br>&bull; `agent-core/openjiuwen/rsi/harness_rsi/auto_harness/infra/parsers.py:147` — deterministic JSON extraction<br>&bull; `agent-core/openjiuwen/core/memory/process/extract/memory_analyzer.py:26` — LLM classifier (semantic)</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---

## 2. Larger model vs. smaller, faster one for a given task

**Title.** Larger vs smaller model

**Summary.** Match capability to difficulty: a large model for reasoning/ambiguity, a small/fast one for classification, extraction, routing, and formatting; measure quality per task and weigh latency and cost.

**Key points.**

- Large for reasoning/ambiguity.
- Small/fast for classification/extraction/routing.
- Measure quality per task; weigh latency/cost.

**General.** Match model capability to task difficulty: use a large model for reasoning/ambiguity and a small/fast one for classification, extraction, routing, and formatting. Measure quality per task and weigh latency and cost; route by task, and fall back to the larger model only when needed. A leaderboard score is a prior, not a per-task decision.

![diagram](assets/diagrams/dd5563d6e052d9bcf4fae828491a201d943a8eca.png)

**Jiuwen.** Model selection here is about availability and endpoint distribution, not task quality. A team can declare a pool of endpoints or a router config, and allocators pick an entry by rotation or an explicit model-name hint at member construction. Capability-based routing by task difficulty must be added by the caller.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Model selection here is about availability and endpoint distribution, not task quality. A team can declare a `model_pool` of endpoints or a `ModelRouterConfig`/`IntelliRouterConfig` convenience shape; allocators (`RoundRobin`, `ByModelName`, `Router`, `IntelliRouter`) pick an entry by rotation or an explicit `model_name` hint supplied per agent/task. IntelliRouter is rate-aware only through `tpm`/`rpm` budgets. The `ModelPoolEntry` metadata comment ("weights, affinity hints") is documented but not implemented.

<sub>&bull; `agent-core/openjiuwen/agent_teams/models/pool.py:38` — ModelPoolEntry; :133 ModelRouterConfig; :241 IntelliRouterDeployment; :314 IntelliRouterConfig; :278 tpm/rpm rate-aware; :95 "weights/affinity hints" (documented, not implemented)<br>&bull; `agent-core/openjiuwen/agent_teams/models/allocator.py:176` — round-robin; :240 by-model-name; :452 IntelliRouter; :559 build_model_allocator; :28 allocation-vs-reliability docstring<br>&bull; `agent-core/openjiuwen/harness/schema/config.py:242` — / agent-core/openjiuwen/harness/schema/deep_agent_spec.py:441 — per-agent/task model config</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---

## 3. How do you evaluate whether a framework will scale with your team, not just your first prototype

**Title.** Will a framework scale with your team

**Summary.** Look for declarative registration and plugins, stable extension contracts, provider/config abstraction, schema'd config, and real docs. Be wary if every change means patching internals.

**Key points.**

- Declarative registration and plugins.
- Stable extension contracts.
- Provider/config abstraction.
- Schema'd config + docs.

**General.** Look for declarative registration and plugins, stable extension contracts, provider and config abstraction, schema'd configuration, and real documentation. Be wary of frameworks where every change means patching internals. Prototype speed is not the same as team-scale maintainability.

![diagram](assets/diagrams/760b6fa06927d5faa409ba04f26bb0b05a6cee8d.png)

**Jiuwen.** Extension is registry and manifest based rather than patch based. Provider modules declare element descriptors that a catalog registration converts into class registrations, and the deep agent can hot-load plugin, agent-template, and harness-config packages through one builder. Extension is by registration, not by patching internals.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Extension is registry/manifest based rather than patch based. Provider modules declare `@harness_element(kind, name, ...)` descriptors; `register_from_catalog()` converts the catalog into class registrations, and `DeepAgent.load_plugin` / `load_agent_template` / `load_harness_config` hot-load packages through one `BuildContext` apply path. Model providers auto-register via `BaseModelClient.__init_subclass__` into `ClientRegistry`, and team infrastructure uses `register_transport`/`register_storage` name→config registries. `Runner.resource_mgr` centralizes tool/workflow/agent/team/model/prompt managers, and the product demonstrates the pattern: `jiuwenswarm/agents/swarm/registry.py` imports provider modules and drives registration from the manifest catalog.

<sub>&bull; `agent-core/openjiuwen/harness/manifest/catalog.py:67` — @harness_element; :55 list_elements(); agent-core/openjiuwen/harness/manifest/registration.py:31 — register_from_catalog<br>&bull; `agent-core/openjiuwen/harness/deep_agent.py:2027` — load_plugin; :2076 load_agent_template; :2190 load_harness_config<br>&bull; `agent-core/openjiuwen/core/foundation/llm/model_clients/base_model_client.py:53` — __init_subclass__ auto-registration; agent-core/openjiuwen/core/common/clients/client_registry.py:19/50/94<br>&bull; `agent-core/openjiuwen/core/runner/resources_manager/resource_registry.py:13` — ResourceRegistry<br>&bull; `agent-core/openjiuwen/harness/schema/config.py:248` — ; agent-core/openjiuwen/harness/schema/deep_agent_spec.py:354 — config schema (Pydantic)<br>&bull; `agent-core/openjiuwen/agent_teams/schema/blueprint.py:99` — TransportSpec/StorageSpec registry pattern<br>&bull; `jiuwenswarm/jiuwenswarm/agents/swarm/registry.py:8-12` — product-side provider registration via the catalog</sub>

![diagram](assets/diagrams/c9abcea8619a4d4e41741e42e999f2b006a467b8.png)

</details>

<sub>_Canonical source: `source/ai-agent-framework-interview-questions_for_engineers.md`_</sub>

---

## 4. What's your rollback plan if a prompt or model update degrades output quality?

**Title.** Rollback plan for a bad update

**Summary.** Make every change reversible and observable: version the prompt/model, ship behind a flag or canary, define a one-command rollback, gate rollout on a fixed eval, and monitor quality (not just errors).

**Key points.**

- Version prompts/models.
- Ship behind flag/canary.
- One-command rollback.
- Gate on eval; monitor quality.

**General.** Make every change reversible and observable: version the prompt/model, ship behind a flag or canary, define a one-command rollback, and gate broad rollout on a fixed eval. Monitor quality (not just errors) so you detect the degradation, and keep the previous version warm.

![diagram](assets/diagrams/2a872457a2005995a61b90e4d6e0fa92167c3d01.png)

**Jiuwen.** Rollback exists for whole RSI harness packages: a rollback call refuses while tasks are active, validates the target hash, hot-reloads the prior version, and compensates if the pointer write fails, exposed over the WebSocket protocol. Behavior changes are gated by enable flags and a human accept/reject. Prompt-level versioning is weaker.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Rollback exists for whole RSI **harness packages**: `rollback(installation_id)` refuses while tasks are active, validates the target hash, hot-reloads the prior version, and compensates if the pointer write fails — exposed over the WebSocket protocol. Behavior is gated by `enable_*` flags and a human `accept`/`reject` activation step. But there is **no prompt-level rollback** and no eval-threshold release gate, so a bad prompt change is only reversible if it was packaged as a harness version.

<sub>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rsi/harness_activation.py:617` — rollback; :682 _assert_rollback_allowed; :694 validate target hash<br>&bull; `jiuwenswarm/jiuwenswarm/server/rsi/rsi_handlers.py:218/224` — versions list + rollback RPC<br>&bull; `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:448` — enable_* flags<br>&bull; `agent-core/openjiuwen/auto_harness/stages/activate.py:118` — explicit accept/reject<br>&bull; `agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21` — no eval gate</sub>

</details>

<sub>_Canonical source: `source/llm-applied-interview-questions_for_engineers.md`_</sub>

---

## 5. A stakeholder wants to ship before your eval scores are ready, how do you handle it

**Title.** Shipping before eval is ready

**Summary.** Mostly process: de-risk instead of refusing — ship behind a flag or canary, define a rollback path, cap the blast radius, agree on a minimal offline eval, and add monitoring so a quality drop is visible.

**Key points.**

- Ship behind flag/canary.
- Define rollback and cap blast radius.
- Minimal offline eval gate.
- Monitoring to detect drops.

**General.** This is mostly process. De-risk instead of refusing: ship behind a flag or to a small canary, define a rollback path, cap the blast radius, agree on a minimal offline eval before broad rollout, and add monitoring so a quality drop is caught quickly. Make the tradeoff explicit (what's unmeasured, what the fallback is) and put a date on the missing eval.

![diagram](assets/diagrams/151440f699ba051e3de09d166123ea5125df8f01.png)

**Jiuwen.** The closest code mechanisms are CI gates and explicit human activation, not an eval-score gate. The auto-harness gate runner loads gates from a config and returns pass/fail; the activate stage requires an explicit user accept/reject before an extension is hot-loaded; and product harness activation is similar. Gating is human and CI based rather than eval-score based.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The closest code mechanisms are CI gates and explicit human activation, not an eval-score gate. The auto-harness `CIGateRunner` loads gates from `ci_gate.yaml` and returns pass/fail; the activate stage requires an explicit user `accept`/`reject` before an extension is hot-loaded; and the product's RSI harness activation supports rollback (refuses while tasks are active, validates the target hash, hot-loads the old version). Behavior gating is done with `enable_*` config flags. There is no release gate tied to eval thresholds and no canary/percentage rollout.

<sub>&bull; `agent-core/openjiuwen/auto_harness/infra/ci_gate_runner.py:168` — load gates; :1153 run + aggregate passed<br>&bull; `agent-core/openjiuwen/auto_harness/stages/activate.py:118` — explicit accept/reject interaction before hot-load<br>&bull; `agent-core/openjiuwen/auto_harness/stages/merge.py:95` — static-check retry (max 3) then fail-fast<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rsi/harness_activation.py:617` — rollback; :682 _assert_rollback_allowed; :694 validate target hash<br>&bull; `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:448` — enable_* config flags</sub>

</details>

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`_</sub>

---
