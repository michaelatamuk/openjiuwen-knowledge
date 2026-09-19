# Cost, latency and accuracy tradeoffs

## 1. Gathering constraints before designing

**Definition:** Before proposing an architecture, extract the four constraints that determine every significant tradeoff: **latency budget** — real-time (≤200ms) or async?; **query volume** — requests per second, peak versus average; **accuracy floor** — is a wrong answer a minor inconvenience or a safety/legal risk?; and **cost envelope** — internal tooling or a consumer product at scale? These four drive every meaningful decision: a tight latency budget rules out reranking or large-model calls in the critical path, a high accuracy floor rules out smaller models, and high volume rules out expensive retrievers.

**Jiuwen:** Latency is set via `ModelRequestConfig.timeout`; volume via `ModelPoolEntry` `tpm`/`rpm`; accuracy via `score_threshold`; cost via the `auto_harness` `budget_rail` dollar cap. None are inferred automatically.

---

## 2. Justifying model size

**Definition:** Match capability to task difficulty. Large models suit reasoning and ambiguity; small, fast models suit classification, extraction, routing, and formatting. A leaderboard score is a prior, not a per-task decision — using a large model everywhere is a cost and latency decision, not a safe default.

---

## 3. Planning for 10x traffic

**Definition:** Scaling is decided before the demo, not after. The first levers are caching, batching, and confirming that latency holds under load. Identify the bottleneck — generation, retrieval, or orchestration — and the first scaling lever for each.

---

## 4. Retrieval depth versus speed

**Definition:** The choice between retrieving more documents and retrieving faster is tied to the use case, not to a universal rule; 20 documents for accuracy versus 5 for speed has no universally correct answer. A medical assistant leans accuracy (retrieve more, rerank); a chat autocomplete leans speed (small top-k, no reranker). Name the latency number or accuracy floor that forces the decision.

---

## 5. What to cut first under a budget constraint

**Definition:** Know which components cost the most and which degrade gracefully versus break the system. Embedding is one-time; generation scales with traffic — so cut generation first: route simple queries to a smaller model, lower top-k, add semantic caching. Safety and guardrail layers are the last thing to cut, because they prevent unsafe output.

---

## 6. Measuring the tradeoff empirically

**Definition:** Define a representative eval set, run every candidate on it, and record quality score, latency, and cost per query. Plot the cost–accuracy and latency–accuracy curves, find the knee (the point of diminishing returns), and pick the option that meets the requirement with the minimum overhead — not the highest-accuracy option.

**Jiuwen:** `agent_evolving/evaluator/` provides `FaithfulnessEvaluator`, `CorrectnessEvaluator`, and `LLMAsJudge`; session costs are tracked in `usage_cost.py`. Cost and latency are not correlated to per-query eval scores.

---

## 7. When the "best" model is the wrong choice

**Definition:** Define "best" relative to a constraint, not as an absolute quality score. A model that is too slow or too expensive to ship at scale is not the right choice regardless of its accuracy; the justification is the constraint it satisfies or violates.

---
