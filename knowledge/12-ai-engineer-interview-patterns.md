# AI engineer interview patterns

## 1. "Design a RAG system" tests failure mode awareness, not architecture recall

**Title.** Design a RAG system: tests failure-mode awareness

**Summary.** 'Design a RAG system' tests whether you know how it fails, not whether you can draw boxes.

**Key points.**

- Dense fallback only on empty, not on wrong.
- score_threshold defaults none → weak chunks pass.
- KB path never reranks.
- Metadata filters dropped at the retriever.

![diagram](assets/diagrams/72c5aa00ecbd3b58619ea524d274ca8fe1fef893.png)

**Jiuwen.** The failure points are concrete: dense retrieval falls back to sparse only when it returns empty, not when it is wrong; score threshold defaults to none so weak chunks pass; the knowledge-base path never reranks; and metadata filters are dropped at the retriever boundary.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The failure points are concrete. Dense retrieval falls back to sparse only when it returns *empty*, not when it is wrong; `score_threshold` defaults to `None` so weak chunks pass; the KB path never reranks; and metadata `filters` are dropped at the retriever boundary, so an "authorized docs only" filter silently does nothing.

<sub>&bull; `agent-core/openjiuwen/core/retrieval/retriever/vector_retriever.py:83` — dense-empty → sparse fallback only; :88 filters=None; :94 threshold applied only when supplied<br>&bull; `agent-core/openjiuwen/core/retrieval/common/config.py:47` — score_threshold defaults None<br>&bull; `agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:182` — KB path calls no reranker<br>&bull; `agent-core/openjiuwen/core/retrieval/indexing/processor/chunker/text_splitter.py:56` — char chunker cuts at fixed offsets</sub>

</details>

---

## 2. "Compare two approaches" tests tradeoff reasoning tied to numbers, not a correct pick

**Title.** Compare two approaches: tests tradeoff reasoning

**Summary.** 'Compare two approaches' tests tradeoff reasoning tied to numbers, not a correct pick.

**Key points.**

- top_k defaults 5, no adaptive policy.
- Reranking absent from the KB path.
- Model allocation is availability-based.
- Session cost tracked and capped.

![diagram](assets/diagrams/05e403ee71c2ddfc9e280ece288ce292f189063b.png)

**Jiuwen.** The relevant knobs are static and named: top-k defaults to 5 with no adaptive policy, reranking is not in the knowledge-base path, and model allocation is availability-based rather than cost or accuracy based, so routing easy queries to a smaller model is not automatic. Session cost is tracked and capped.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The relevant knobs are static and named: `top_k` defaults to 5 (no adaptive policy), reranking is not in the KB path, and model allocation is availability-based, not cost/accuracy-based — so "smaller model for easy queries" is not automatic. Session cost is tracked and capped when the provider reports cost.

<sub>&bull; `agent-core/openjiuwen/core/retrieval/common/config.py:46` — top_k: int = 5 static<br>&bull; `agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:182` — no reranker in KB retrieve<br>&bull; `agent-core/openjiuwen/agent_teams/models/allocator.py:559` — build_model_allocator (availability strategies, not cost/accuracy)<br>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171` — enforced session cost cap</sub>

</details>

---

## 3. "The agent is stuck" tests whether you've shipped one, not studied one

**Title.** 'The agent is stuck': tests shipped experience

**Summary.** 'The agent is stuck' tests whether you've shipped one, not studied one.

**Key points.**

- ReAct max_iterations (5; harness 15).
- Agentic retriever max iter (2, clamped).
- Anomaly rail: identical rounds → compact/abort.
- Dedup rail + session cost cap.

![diagram](assets/diagrams/9697b9de619b0d05f8cba0f45f509f36f6ce3157.png)

**Jiuwen.** Concrete caps exist: ReAct max iterations (default 5, harness 15), agentic-retriever max iterations (default 2, clamped), an anomaly-detection rail (consecutive identical tool rounds trigger compaction or abort), and a tool-call dedup rail. A session cost cap is enforced.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Concrete caps exist: ReAct `max_iterations` (default 5, harness 15), `AgenticRetriever.max_iter` (default 2, clamped), `ModelAnomalyDetectionRail` (consecutive identical tool rounds → compact/abort) and `ToolCallDeduplicationRail`. A session cost cap is enforced when the provider reports cost, and `ModelBackupRail` fails over. What is **missing** is a circuit breaker after N consecutive failures and a durable token budget on the retrieval loop.

<sub>&bull; `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:288` — max_iterations: int = Field(default=5); agent-core/openjiuwen/harness/schema/config.py:252 — harness default 15<br>&bull; `agent-core/openjiuwen/harness/rails/model_anomaly_detection_rail.py:74` — ToolLoopCompactConfig (default off); :90 bailout<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:157` — repeat counter/warning<br>&bull; `jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171/196` — enforced session cost cap<br>&bull; `agent-core/openjiuwen/core/single_agent/rail/model_backup.py:9` — ModelBackupRail failover (no circuit breaker)</sub>

</details>

---

## 4. "How do you know it's working" tests evaluation depth, not confidence

**Title.** How do you know it's working: eval depth

**Summary.** 'How do you know it's working' tests evaluation depth, not confidence.

**Key points.**

- Offline answer-level eval exists.
- No retrieval metric layer.
- No faithfulness/claim scoring.
- No CI quality gate.

![diagram](assets/diagrams/0d798b3126ce1f3c931a54a6e894ed1ddd7aae95.png)

**Jiuwen.** Offline answer-level evaluation exists (exact match, LLM judge, weighted rubric, pipeline pass rate), but there is no retrieval metric layer, no faithfulness or claim-level scoring, and no quality regression gate in CI (the gate config is lint and type-check).

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Offline answer-level evaluation exists (`ExactMatchMetric`, `LLMAsJudgeMetric`, RSI weighted rubric, `evaluator_pipeline` pass-rate), but there is no retrieval metric layer, no faithfulness/claim-level scoring, no quality regression gate in CI (`ci_gate.yaml` is lint/type-check only), and no production quality monitoring or drift detection — so the "how would you know it got worse" question exposes real gaps.

<sub>&bull; `agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:47` — LLM judge; agent-core/openjiuwen/agent_evolving/evaluator/metrics/exact_match.py:12 — exact match<br>&bull; `agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:193` — weighted rubric<br>&bull; `agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:167` — benchmark eval<br>&bull; `agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21` — gates are only lint/type-check; agent-core/pyproject.toml:236 — level0/level1 markers (not invoked)<br>&bull; `jiuwenswarm/jiuwenswarm/observability/store.py:102` — has_error (operations, not quality)</sub>

</details>

---

## 5. Scaling questions test whether you've thought past the demo

**Title.** Scaling questions: thinking past the demo

**Summary.** Scaling questions test whether you've thought past the demo.

**Key points.**

- Per-process bounded resources.
- Shared HTTP pool + embedding/sub-agent semaphores.
- Missing: autoscaling, distributed queues.

![diagram](assets/diagrams/fe38b5d6bafb6ce33d080699d01b3d45d517bdca.png)

**Jiuwen.** Bounded resources exist per process: a shared HTTP pool (100 connections), embedding semaphore (50), sub-agent fan-out semaphore (10), bounded async queues, and parallel tool execution with resource lanes. What is missing is autoscaling and a distributed queue.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

Bounded resources exist per process: shared httpx pool (`max_connections=100`), embedding semaphore (50), sub-agent fan-out semaphore (10), bounded `asyncio.Queue`s, and parallel tool execution with resource lanes. What is missing is autoscaling, a distributed rate limiter, and any semantic response cache — so the design change at 10x is mostly "add replicas + a global limiter", which the repo does not provide.

<sub>&bull; `agent-core/openjiuwen/core/common/clients/connector_pool.py:21` — limit: 100, limit_per_host: 30<br>&bull; `agent-core/openjiuwen/core/retrieval/embedding/api_embedding.py:55` — concurrency semaphore<br>&bull; `agent-core/openjiuwen/core/runner/message_queue_inmemory.py:34` — bounded queue; agent-core/openjiuwen/harness/subagent_runtime/activity_events.py:53 — bounded activity queue<br>&bull; `agent-core/openjiuwen/core/single_agent/ability_manager.py:431` — _execute_parallel_tool_tasks; :467 parallel_safe lanes<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/memory/manager.py:773` — exact embedding cache (no semantic cache)</sub>

</details>

---

## 6. Security-adjacent questions are disguised as normal engineering questions

**Title.** Security-adjacent questions in disguise

**Summary.** Security-adjacent questions are disguised as normal engineering questions.

**Key points.**

- Tool results not framed as untrusted.
- Sanitizers exist, unused.
- Prompt safety is advisory.
- Real control is the shell/permission layer.

![diagram](assets/diagrams/bd23a2c582f0d84607fa39f87399c2cd80d3fe7e.png)

**Jiuwen.** This is the weakest area. Tool results are returned as a plain tool message with no untrusted-data framing; sanitizer helpers exist but have no production callers. Prompt-level safety is advisory, while the enforced controls live in the shell and permission layers.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

This is the weakest area. Tool results are returned as plain `ToolMessage` with no untrusted-data framing; sanitizer helpers exist but have no production callers. Prompt-level safety is advisory (`SafetyPromptRail` always allows), while the enforced controls live in the shell/permission layer (AST ASK floor, builtin deny rules) — not in retrieval. There is no mandatory untrusted-tool-result seam.

<sub>&bull; `agent-core/openjiuwen/core/single_agent/ability_manager.py:1612` — ToolMessage built with no untrusted wrapper; :431 parallel path<br>&bull; `agent-core/openjiuwen/harness/prompts/sanitize.py:20` — sanitizer (no production callers)<br>&bull; `agent-core/openjiuwen/harness/rails/security/prompt_security_rail.py:16/41` — SafetyPromptRail (advisory, always allows)<br>&bull; `agent-core/openjiuwen/harness/security/permission_engine/core.py:272` — check_permission (enforced tool/file/net)<br>&bull; `agent-core/openjiuwen/harness/resources/builtin_rules.yaml:59` — reverse-shell deny</sub>

![diagram](assets/diagrams/f2fc8022c1cc50f211ec29fab1824742dacac291.png)

</details>

---

## 7. Stakeholder questions test judgment under pressure, not technical depth

**Title.** Stakeholder questions: judgment under pressure

**Summary.** Stakeholder questions test judgment under pressure, not technical depth.

**Key points.**

- Config flags (enable_*) gate behavior.
- Human activation before hot-load.
- RSI rollback with hash re-validation.
- No eval-threshold gate or canary.

![diagram](assets/diagrams/be612da735ee6712c92301d459748e051902aac9.png)

**Jiuwen.** The closest code mechanisms are config flags, explicit human activation before hot-load, and RSI rollback with hash re-validation — plus a CI gate that is lint and type-check only. There is no eval-threshold release gate and no canary or percentage rollout.

<details open>
<summary><b>Technical detail (classes &amp; functions)</b></summary>

The closest code mechanisms are config flags (`enable_*`), explicit human activation before hot-load, and RSI rollback with hash re-validation — plus a CI gate that is lint/type-check only. There is no eval-threshold release gate and no canary/percentage rollout, so the answer is supported only by flags, explicit activation, and manual rollback.

<sub>&bull; `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:448` — enable_* flags<br>&bull; `agent-core/openjiuwen/auto_harness/stages/activate.py:99` — explicit accept/reject interaction before hot-load<br>&bull; `jiuwenswarm/jiuwenswarm/agents/harness/common/rsi/harness_activation.py:617` — rollback; :682 _assert_rollback_allowed<br>&bull; `agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21` — only lint/type-check</sub>

</details>

---
