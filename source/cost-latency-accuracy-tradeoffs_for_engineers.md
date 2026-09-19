# How Interviewers Test for Cost, Latency, and Accuracy Tradeoff Thinking

> **The pattern worth noticing:** None of these questions have one correct answer. You are scored on whether your reasoning connects the technical choice back to a real constraint, not on which option you pick.

## 1. They give you a vague requirement on purpose

**What they're testing:** Whether you ask before you design. Jumping straight into architecture without asking about query volume, budget, or latency needs is the first flag.

**What a strong answer includes:** Identify the four binding constraints before proposing any architecture: (1) latency budget — real-time or async? (2) query volume — RPS, peak vs average; (3) accuracy floor — cost of a wrong answer; (4) cost envelope — $/query. Each constraint rules out or forces specific choices.

**Jiuwen:** Latency via `ModelRequestConfig.timeout`; volume via `ModelPoolEntry` `tpm`/`rpm`; accuracy via `score_threshold`; cost via `auto_harness` `budget_rail` dollar cap. None are inferred automatically.

**Gap.** No constraint-gathering interface; operators set levers manually without system-enforced prompting to define constraints first.

---

## 2. They ask you to justify model size

**What they're testing:** Whether "bigger is better" is your only framework. Using a large model everywhere reads as a red flag, not a safe choice.

**What a strong answer includes:** Match capability to task difficulty. Large models for reasoning/ambiguity; small/fast models for classification, extraction, routing, and formatting. A leaderboard score is a prior, not a per-task decision.

**Coverage map:** Covered by 04-2.

---

## 3. They ask what happens at 10x current traffic

**What they're testing:** Whether your architecture was built for the demo or built to scale.

**What a strong answer includes:** Caching, batching, and whether latency holds under load. Identify the bottleneck (generation, retrieval, or orchestration) and the first scaling lever for each.

**Coverage map:** Covered by 16-8.

---

## 4. They ask: more retrieval or faster retrieval

**What they're testing:** Whether your choice connects to the use case, not a universal rule. 20 documents for accuracy vs. 5 for speed — no universally correct answer.

**What a strong answer includes:** Tie the choice to the use case. A medical assistant leans accuracy (retrieve more, rerank). A chat autocomplete leans speed (small top-k, no reranker). Name the latency number or accuracy floor that forces the decision.

**Coverage map:** Covered by 04-3.

---

## 5. They ask what you'd cut first under a budget constraint

**What they're testing:** Whether you know which components cost the most, and which degrade gracefully vs. break the system entirely.

**What a strong answer includes:** Embedding is one-time; generation scales with traffic — cut generation first. First levers: route simple queries to a smaller model, lower top-k, add semantic caching. Last to cut: safety/guardrail layers that prevent unsafe outputs.

**Coverage map:** Covered by 16-1 and 16-4.

---

## 6. They ask how you'd measure the tradeoff, not just describe it

**What they're testing:** Whether "there's a tradeoff" is your complete answer, or whether you can operationalize it.

**What a strong answer includes:** Define a representative eval set; run every candidate on it; record quality score, latency, and cost per query; plot the cost-accuracy and latency-accuracy curves; identify the knee (diminishing-returns point); pick the option that meets the requirement with minimum overhead — not the highest-accuracy option.

**Jiuwen:** `agent_evolving/evaluator/` has `FaithfulnessEvaluator`, `CorrectnessEvaluator`, `LLMAsJudge`. Session costs tracked in `usage_cost.py`. Gap: cost and latency are not correlated to per-query eval scores.

---

## 7. They present a case where the "best" model failed

**What they're testing:** Whether you can admit the top-accuracy option isn't always right and articulate what you'd choose instead with a business justification.

**What a strong answer includes:** Define "best" relative to a constraint, not an absolute quality score. A model that is too slow or too expensive to ship at scale is not the right choice, regardless of accuracy.

**Coverage map:** Covered by 04-2 and 04-3.

---

## How to practice this

Take any AI system you'd build and write three versions: cheapest, fastest, most accurate. Explain out loud which one you'd ship and why, given a specific business context.

| Pattern | Signal | Coverage |
|---|---|---|
| Ask before design | Clarifying questions | 04-4 (new) |
| Justify model size | Constraint-matched reasoning | 04-2 |
| 10x traffic | Beyond the demo | 16-8 |
| Retrieval depth vs speed | Use-case tradeoff | 04-3 |
| What to cut first | Cost concentration knowledge | 16-1, 16-4 |
| Measure empirically | Evidence-based selection | 04-5 (new) |
| Best model failed | Relative not absolute "best" | 04-2, 04-3 |
