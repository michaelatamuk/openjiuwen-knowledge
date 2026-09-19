# Cost, latency and accuracy tradeoffs

## 1. Gathering constraints before designing

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Extract the four binding constraints — latency budget, query volume, accuracy floor, and cost envelope — before proposing any architecture.

**Key points.**

- A tight latency budget rules out reranking or large-model calls in the critical path
- A high accuracy floor rules out smaller models
- High query volume rules out expensive retrievers
- In Jiuwen these are manual levers: timeout, tpm/rpm, score_threshold, budget cap

**Concept.** Before proposing an architecture, extract the four constraints that determine every significant tradeoff: **latency budget** — real-time (≤200ms) or async?; **query volume** — requests per second, peak versus average; **accuracy floor** — is a wrong answer a minor inconvenience or a safety/legal risk?; and **cost envelope** — internal tooling or a consumer product at scale? These four drive every meaningful decision: a tight latency budget rules out reranking or large-model calls in the critical path, a high accuracy floor rules out smaller models, and high volume rules out expensive retrievers.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Latency is set via `ModelClientConfig.timeout`; volume via `IntelliRouterDeployment` `tpm`/`rpm`; accuracy via `score_threshold`; cost via the auto-harness `BudgetRail` dollar cap. The operator sets them per use case.

</details>

---

## 2. Justifying model size

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Match model capability to task difficulty rather than defaulting to the largest model.

**Key points.**

- Large models suit reasoning and ambiguity
- Small fast models suit classification, extraction, routing, formatting
- A leaderboard score is a prior, not a per-task decision

**Concept.** Match capability to task difficulty. Large models suit reasoning and ambiguity; small, fast models suit classification, extraction, routing, and formatting. A leaderboard score is a prior, not a per-task decision — using a large model everywhere is a cost and latency decision, not a safe default.

---

## 3. Planning for 10x traffic

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Scale decisions are made before the demo: identify the bottleneck and the first scaling lever for each stage.

**Key points.**

- First levers: caching, batching, and latency under load
- Bottleneck is generation, retrieval, or orchestration
- Each stage has a different first scaling lever

**Concept.** Scaling is decided before the demo, not after. The first levers are caching, batching, and confirming that latency holds under load. Identify the bottleneck — generation, retrieval, or orchestration — and the first scaling lever for each.

---

## 4. Retrieval depth versus speed

<span class="badge badge-type">Compare</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Retrieval depth versus speed is a use-case decision, not a universal rule.

**Key points.**

- Medical assistant: retrieve more and rerank, leaning accuracy
- Chat autocomplete: small top-k, no reranker, leaning speed
- Name the latency number or accuracy floor that forces the choice

**Concept.** The choice between retrieving more documents and retrieving faster is tied to the use case, not to a universal rule; 20 documents for accuracy versus 5 for speed has no universally correct answer. A medical assistant leans accuracy (retrieve more, rerank); a chat autocomplete leans speed (small top-k, no reranker). Name the latency number or accuracy floor that forces the decision.

---

## 5. What to cut first under a budget constraint

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Embedding is one-time; generation scales with traffic, so cut generation first.

**Key points.**

- Route simple queries to a smaller model, lower top-k, add semantic caching
- Safety and guardrail layers are the last to cut
- Know which components degrade gracefully versus break the system

**Concept.** Know which components cost the most and which degrade gracefully versus break the system. Embedding is one-time; generation scales with traffic — so cut generation first: route simple queries to a smaller model, lower top-k, add semantic caching. Safety and guardrail layers are the last thing to cut, because they prevent unsafe output.

---

## 6. Measuring the tradeoff empirically

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Operationalize the tradeoff: eval set, per-candidate quality/latency/cost, curves, and the knee.

**Key points.**

- Define a representative eval set and run every candidate on it
- Record quality score, latency, and cost per query
- Plot cost-accuracy and latency-accuracy curves and find the knee
- Pick the option meeting the requirement with minimum overhead

**Concept.** Define a representative eval set, run every candidate on it, and record quality score, latency, and cost per query. Plot the cost–accuracy and latency–accuracy curves, find the knee (the point of diminishing returns), and pick the option that meets the requirement with the minimum overhead — not the highest-accuracy option.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

`agent_evolving/evaluator/` provides metrics such as `ExactMatchMetric` and `LLMAsJudgeMetric`; session costs are tracked in `usage_cost.py`. Cost and latency are tracked separately from quality scores, so the cost-accuracy curve is assembled by the operator.

</details>

---

## 7. When the "best" model is the wrong choice

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** "Best" is relative to a constraint, not an absolute quality score.

**Key points.**

- A model too slow or too expensive to ship is not the right choice
- Justify against the constraint it satisfies or violates

**Concept.** Define "best" relative to a constraint, not as an absolute quality score. A model that is too slow or too expensive to ship at scale is not the right choice regardless of its accuracy; the justification is the constraint it satisfies or violates.

---
