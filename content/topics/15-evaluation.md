# Evaluation

## 1. How do you evaluate an LLM's output beyond "it looks correct"

**General:** Combine automatic metrics (exact match, F1, ROUGE/BLEU where applicable, functional/tests for code), an LLM-as-judge with a rubric for open-ended quality, and human review for a sample. Build a held-out eval set with representative and adversarial cases, score consistently, and track regressions across changes. The judge itself must be validated against human agreement; a single metric rarely captures "quality".

**Jiuwen:** Several independent eval layers exist. `agent_evolving/evaluator/` provides `BaseEvaluator`/`DefaultEvaluator` plus `Metric`s: `ExactMatchMetric` (normalized string match) and `LLMAsJudgeMetric` (model judge returns 0/1 with a template). The RSI subsystem has a rigorous LLM-as-judge contract requiring a structured JSON verdict with per-behavior scores, evidence, weights, and forbidden-behavior penalties. The online RL judge scores single turns as reward with `num_votes` voting. PerStream uses GPT-3.5 as a judge and aggregates accuracy/score/latency/VRAM, and `rsi best_of_n` scores workspaces by test pass counts, diff size, and lint errors. `EvolutionPipeline` runs an agent against a benchmark for N iterations and reports pass rate/convergence.

```mermaid
flowchart TD
    OUT["model/agent output"] --> M1["ExactMatchMetric (normalized string)"]
    OUT --> M2["LLMAsJudgeMetric (rubric → 0/1)"]
    OUT --> M3["RSI judge: per-behavior scores + evidence + weights + forbidden penalties"]
    OUT --> M4["RL judge: reward in 0,1 · num_votes voting"]
    OUT --> M5["best_of_n: tests / lint / diff size"]
    OUT --> M6["PerStream: aggregate accuracy/score/latency/VRAM"]
    M1 --> AGG(["eval result"])
    M2 --> AGG
    M3 --> AGG
    M4 --> AGG
    M5 --> AGG
    M6 --> AGG
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:17-66</code> — <code>LLMAsJudgeMetric</code>; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/exact_match.py:12-45</code> — <code>ExactMatchMetric</code>; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/__init__.py:7-11</code> registry<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator.py:1-9</code> — <code>DefaultEvaluator</code> / <code>MetricEvaluator</code><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:57-88</code> — rubric/required/forbidden contract; <code>:167-214</code> weighted scoring + evidence<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/judge_scorer.py:28-104</code> — judge reward, <code>num_votes</code><br>&bull; <code>agent-core/examples/PerStream/src/eval/score_passive_judge.py:28-124</code> GPT-3.5 judge; <code>:247-366</code> aggregate metrics<br>&bull; <code>agent-core/openjiuwen/rsi/auto_harness/pipelines/best_of_n/attempt_scorer.py:17-119</code> — tests/lint/diff scoring<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/evaluators.py:1-16</code> — static/trace evaluators incl. <code>LLMJudgeEvaluator</code></sub>

</details>

**Gap.** No unified/standard benchmark harness, no statistical-significance testing, and no inter-rater agreement validation for the LLM judge; eval is spread across several subsystems with different contracts (`agent_evolving`, `rsi`, `symphony`, `dev_tools/tune`, `dev_tools/skill_evaluator`).

<sub>_Canonical source: `source/llm-fundamentals-interview-questions_for_engineers.md`; also covered in: engineering, genai, llm-applied, llm-fund, rag-eval, rag-1._</sub>

---

## 2. Why evaluate retrieval and generation as two separate stages instead of one end-to-end score

**General:** An end-to-end score tells you "the answer was wrong" but not why. If retrieval missed the document, no generator can fix it; if the document was retrieved but the answer is wrong, the generator (or grounding) is at fault. Stage-level metrics — Recall@k / precision@k / NDCG for retrieval, faithfulness / correctness for generation — let you attribute the failure and fix the right component. End-to-end stays as the final acceptance check.

**Jiuwen:** The stages are structurally separate but also separately un-instrumented. Retrieval (`core/retrieval`) has no quality metric of any kind (no Recall@k/Precision@k/MRR/NDCG). Generation has answer-level judges that do not receive the retrieved context. So the codebase can produce end-to-end grader scores (`evaluator_pipeline` `pass_rate`, RSI weighted score) but cannot say whether a failure was retrieval or generation.

```mermaid
flowchart TD
    E2E["end-to-end score"] --> Q{"why did it fail?"}
    Q --> R["retrieval stage metric (Recall@k/Precision@k/NDCG)"]
    Q --> G["generation stage metric (faithfulness/correctness)"]
    R -.->|"absent"| X["no retrieval-quality metric anywhere"]
    G -.->|"judges lack retrieved context"| Y["cannot attribute to grounding"]
    E2E --> AGG["evaluator_pipeline pass_rate / RSI weighted score (present)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/base.py:42</code> — <code>Metric.compute(prediction, label)</code>, no ranked-list/k signature<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/__init__.py:11</code> — exports only <code>Metric</code>, <code>ExactMatchMetric</code>, <code>LLMAsJudgeMetric</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:47</code> — judge gets question/expected/answer, not retrieved context<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:311</code> — end-to-end <code>pass_rate</code><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:193</code> — end-to-end weighted score</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>

---

## 3. Why exact-match scoring fails when a correct answer can be phrased multiple valid ways

**General:** Exact match requires the output string to equal the reference, so "Paris" vs "The capital is Paris" both fail even when correct. It is brittle to wording, formatting, articles, and ordering. Use it only for tasks with a canonical form (classification labels, IDs, single tokens); otherwise use semantic/normalized metrics (LLM judge, embedding similarity, or task-specific parsers).

**Jiuwen:** Two exact-match implementations exist. `ExactMatchMetric` normalizes lowercase/strip/whitespace but still requires full-string equality; RSI's `ExactMatchJudger` is strict `==` with no normalization. The LLM judges cover paraphrase — the `LLMAsJudgeMetric` prompt judges semantic consistency, and PerStream's GPT judge explicitly accepts synonyms/paraphrases — but they are non-deterministic and uncalibrated, and there is no deterministic paraphrase-robust metric (e.g. normalized/embedding similarity).

```mermaid
flowchart TD
    ANS["answer"] --> EM{"exact match?"}
    EM -->|"normalized == (ExactMatchMetric)"| OK["pass only on identical form"]
    EM -->|"strict == (RSI)"| OK
    ANS --> LLM["LLM semantic judge (accepts paraphrase)"]
    LLM --> N["non-deterministic, uncalibrated"]
    ANS -.->|"absent"| X["deterministic paraphrase-robust metric"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/exact_match.py:36</code> — normalized equality; <code>:40</code> <code>_normalize</code> (lower/strip/collapse)<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/exact_match.py:50</code> — strict <code>== expected</code>; <code>:30</code> rejects rubric/files<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:4</code> — semantic consistency judge<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/evaluators.py:520</code> — exact-match shortcut then LLM fallback<br>&bull; <code>agent-core/examples/PerStream/src/eval/score_passive_judge.py:57</code> — "Consider synonyms or paraphrases as valid matches"</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>

---

## 4. Recall@k, and what a low score tells you about your retrieval setup

**General:** Recall@k is the fraction of a query's relevant documents that are retrieved in the top-k, averaged over queries (when each query has exactly one relevant document this reduces to hit-rate/success@k). A low score means retrieval (not generation) is the failure: relevant content is missing from the candidate set, so no reranker or prompt can recover it. Diagnose by checking chunking (answer split/lost), embedding fit, whether the query and index use the same model, and whether exact-match terms need a sparse leg.

**Jiuwen:** There is no `Recall@k` implementation. The only recall-looking code is a **classification** evaluator for the proactive-memory gate in `examples/PerStream/src/eval/` ("TA (Recall)" = TP/(TP+FN) over proactive-memory moments), which is not ranking retrieval against gold documents. `recall_compressed_context` is named "recall" but is a BM25 lookup returning chunks, not a metric. Nothing computes retrieved-vs-relevant overlap at rank k.

```mermaid
flowchart TD
    Q["eval queries + gold relevant docs"] --> R["run retrieval top-k"]
    R --> M["Recall@k = |retrieved ∩ relevant| / |relevant|"]
    M --> LOW{"low?"}
    LOW -->|yes| DIAG["candidate set incomplete: chunking · embedding fit · model mismatch · no sparse leg"]
    LOW -->|no| OK["retrieval reachable — optimize generation"]
    M -.->|"absent in codebase"| X["no implementation"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/examples/PerStream/src/eval/score_proactive_judge.py:355</code> — <code>get_ta_recall</code> = TP/(TP+FN) (classification, not retrieval@k)<br>&bull; <code>agent-core/examples/PerStream/src/eval/test_remember_gate.py:180</code> — sklearn <code>recall_score</code> (gate classifier)<br>&bull; <code>agent-core/examples/PerStream/src/eval/eval_proactive_reduction.py:92</code> — LLM-judged memory metrics<br>&bull; <code>agent-core/openjiuwen/core/context_engine/processor/forked/compressor/recall/retriever.py:27</code> — <code>recall_compressed_context</code> (name only)</sub>

</details>

**Gap.** Recall@k is absent. The closest thing is the PerStream proactive-memory classification recall, a different task.

<sub>_Canonical source: `source/rag-retrieval-interview-questions_for_engineers.md`; also covered in: rag-eval, rag-retrieval._</sub>

---

## 5. How does Precision@k differ from Recall@k?

**General:** Precision@k is the fraction of the top-k that are relevant; recall@k is the fraction of all relevant documents that were retrieved. They trade off: raising k raises recall but usually lowers precision.

**Jiuwen:** Precision@k is **absent**. The only precision present is classification/answer precision: PerStream's “TV (Precision)” = TP/(TP+FP) and sklearn `precision_score` in a gate test. The retrieval stack returns an ordered candidate list and a cross-encoder can re-sort it, but never compares the ordering to graded relevance.

```mermaid
flowchart LR
    R["ranked top-k"] --> P["Precision@k = relevant in top-k / k"]
    G["all relevant docs"] --> RC["Recall@k = relevant in top-k / all relevant"]
    P <-->|"k ↑ → recall ↑, precision ↓"| RC
    P -.->|"absent in codebase"| X["classification precision only (PerStream)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/examples/PerStream/src/eval/score_proactive_judge.py:362</code> — `get_tv_precision()` = `tp / total_pred_not_nil`<br>&bull; <code>agent-core/examples/PerStream/src/eval/eval_proactive_reduction.py:188</code> — `tv_precision`<br>&bull; <code>agent-core/examples/PerStream/src/eval/test_remember_gate.py:22</code> — sklearn `precision_score`<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/milvus/milvus_support.py:87</code> — `rerank(...)` re-sorts, no precision measurement</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval, rag-1, rag-retrieval._</sub>

---

## 6. Why can precision and recall both look fine while the pipeline is broken?

**General:** Both can be low even when the outputs look plausible: if the embedding or chunking is wrong, nothing relevant is ranked highly; and if the corpus simply lacks the answer, no retriever can find it. A plausible top-3 can still be mostly irrelevant — which is exactly why you need numbers, not vibes.

**Jiuwen:** The retrieval stack produces an ordered candidate list — and a cross-encoder can re-sort it — but never compares that ordering against graded relevance, so there is no precision@k/recall@k to reveal the gap. Evaluation metrics zip predictions/labels without any relevance-per-rank notion.

```mermaid
flowchart TD
    A["answer looks plausible"] --> B{"embedding/chunking wrong? → nothing relevant ranked"}
    A --> C{"corpus lacks the answer? → nothing to retrieve"}
    B --> Z["precision@k / recall@k absent → gap invisible"]
    C --> Z
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/milvus/milvus_support.py:87</code> — `rerank(...)` re-sorts, no precision measurement<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/base.py:60</code> — `compute_batch` zips predictions/labels, no relevance-per-rank</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval, rag-1, rag-retrieval._</sub>


---

## 7. MRR, and when it matters more than Recall@k

**General:** MRR is the mean of `1/rank` of the first relevant result. It matters when the user/system mostly needs the single best hit and the position of the first correct answer is what counts (FAQ lookup, "open the right doc", navigation). Recall@k matters when a set of results is consumed together (context stuffing). MRR ignores everything after the first relevant hit, so it is blind to recall.

**Jiuwen:** MRR is not implemented anywhere; there is no reciprocal-rank or first-relevant-rank helper. The retrieval stack uses Reciprocal **Rank Fusion** (`rrf_fusion`, `1/(k+rank)`) and a separate weighted score combination (`WeightedRankConfig`) in the graph store — rank-fusion algorithms, not an evaluation metric. The product's `bm25_rank_to_score` converts an FTS5 rank to a similarity score, also not MRR.

```mermaid
flowchart TD
    R["ranked list"] --> F["first relevant rank r"]
    F --> M["RR = 1/r ; MRR = mean over queries"]
    M --> USE["matters when the first correct hit is what counts"]
    R -.->|"RRF uses 1/(k+rank) for fusion, not evaluation"| X["no MRR metric in codebase"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/utils/fusion.py:15</code> — <code>rrf_fusion</code> (rank fusion, not MRR)<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/result_ranking.py:85</code> — <code>RRFRankConfig</code> (k=40 fusion config); <code>:61</code> <code>WeightedRankConfig</code><br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/memory/internal.py:165</code> — <code>bm25_rank_to_score</code> (rank→score)<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/index/simple_memory_index.py:348</code> — sorts by score only</sub>

</details>

<sub>_Canonical source: `source/rag-retrieval-interview-questions_for_engineers.md`; also covered in: rag-eval, rag-retrieval._</sub>


---

## 8. NDCG: weights relevant results by position against an ideal ranking — why position matters beyond "was it retrieved"

**General:** NDCG discounts each relevant result by `log2(rank+1)` and normalizes by the ideal (best-possible) ordering, so it rewards putting the most relevant documents at the top and supports graded relevance (not just binary). It matters when ranking quality — not just presence — drives the user experience, and is the standard metric for reranker comparisons. Recall@k treats all positions within k equally; NDCG does not.

**Jiuwen:** NDCG is **absent** — no discounted cumulative gain, no gain/discount term, and no graded relevance anywhere. Ranking code produces cross-encoder scores and RRF fusion scores used to sort, but never evaluates an ordering against relevance grades.

```mermaid
flowchart TD
    R["ranked list"] --> G["grade each result (0..n)"]
    G --> D["DCG = Σ rel / log2(rank+1)"]
    D --> N["NDCG = DCG / ideal DCG"]
    N --> USE["rewards top-positioned, graded relevance"]
    N -.->|"absent in codebase; no graded relevance"| X["no NDCG/DCG"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/milvus/milvus_support.py:87</code> — cross-encoder re-rank produces scores, no DCG<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/graph/result_ranking.py:85</code> — RRF/WeightedRank configs; no gain/discount<br>&bull; <code>agent-core/openjiuwen/core/retrieval/utils/fusion.py:20</code> — RRF only<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/__init__.py:11</code> — only three metrics exported</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 9. Faithfulness vs. relevance in RAG evaluation

**General:** Relevance asks whether retrieved passages are on-topic for the query (context precision/recall). Faithfulness/groundedness asks whether the answer's claims are actually supported by the retrieved context (does it hallucinate beyond the evidence). A system can retrieve relevant context and still be unfaithful, or be faithful to irrelevant context. Measuring faithfulness requires giving the judge the context and checking claim support/citations, not just answer-vs-reference correctness.

**Jiuwen:** There is no retrieval-groundedness, faithfulness, attribution, or context-relevance metric. The closest concepts: symphony's `AccuracyEvaluator` judges factual correctness with a rubric about hallucination but does not receive the retrieved context, so it cannot detect unsupported-but-plausible claims; the reviewer rubric lists a `Correctness` dimension ("no hallucination") at weight 0.3; and the RSI judge accepts arbitrary `rubric`/`required_behaviors`, so a user *could* encode a groundedness rule, but none is defined.

```mermaid
flowchart TD
    CTX["retrieved context"] --> REL["relevance: context precision/recall"]
    ANS["answer"] --> FAITH["faithfulness: are claims supported by context?"]
    CTX --> FAITH
    REL --> JUDGE["RAG eval"]
    FAITH --> JUDGE
    CTX -.->|"not passed to judge"| X["no faithfulness/attribution metric implemented"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/evaluators.py:438</code> — <code>AccuracyEvaluator</code> (correctness, no context input); <code>:560</code> <code>Completeness</code>; <code>:621</code> <code>CapabilitySelection</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:58</code> — parses only <code>result: true/false</code>, no context/attribution input<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:68</code> — generic rubric contract (no built-in faithfulness dimension)<br>&bull; <code>agent-core/openjiuwen/harness/tools/web/free_search.py:299</code> — "simple relevance checks" (lexical, not RAG relevance)</sub>

</details>

**Gap.** Fully absent. No metric receives retrieved passages alongside the answer; no RAG-quality citation extraction or attribution check (a web-search citation URL parser exists, but it does not link answer claims to retrieved passages).

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`; also covered in: engineering, llm-applied, rag-1, genai, rag-eval._</sub>


---

## 10. Computing faithfulness: decomposing an answer into atomic claims, scoring each against the source with an NLI model or LLM-as-judge

**General:** Faithfulness = supported claims / total claims. Decompose the answer into atomic, verifiable claims; for each, ask an NLI model or LLM judge whether the retrieved source entails it; average. It needs the source context and is claim-level, not answer-level. Low faithfulness with high relevance points at the generator skipping or distorting retrieved evidence.

**Jiuwen:** **Absent.** No judge receives a retrieved source context for faithfulness. `agent_evolving`'s judge template has fields `[Question]`, `[Expected Answer]`, `[Model Response]` with no context/evidence slot; RSI's judge receives task/reference/rubric/evidence artifacts but no retrieval context and does no claim decomposition. Symphony's judge payload can incidentally include the message trace, but it is not a faithfulness pipeline.

```mermaid
flowchart TD
    ANS["answer"] --> ATOMS["atomic claims"]
    CTX["retrieved source"] --> NLI["NLI / LLM judge: entailed?"]
    ATOMS --> NLI
    NLI --> F["faithfulness = supported / total"]
    CTX -.->|"not an input"| X["no context field in any judge"]
    ATOMS -.->|"absent"| Y["no claim decomposition"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/templates.py:32</code> — template fields <code>[Question]</code>/<code>[Expected Answer]</code>/<code>[Model Response]</code>; no context<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:47</code> — prompt formatted with three fields only<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator.py:116</code> — same three fields<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/base.py:336</code> — redacted fingerprint+case (incidental context)<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/evaluators.py:546</code> — payload filters trace</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 11. Measuring hallucination rate: claim extraction from the output, then verification against retrieved context

**General:** Extract atomic claims from the answer, then verify each against the retrieved context (LLM-judge or NLI). Hallucination rate = unsupported claims / total claims (or fraction of answers with any unsupported claim). This is stricter than "is the answer correct": it catches answers that are plausible but not grounded, and it requires passing the retrieved context to the checker.

**Jiuwen:** Claim extraction and verification are **absent**. There is no atomic-claim decomposition, NLI/entailment model, or groundedness/attribution scorer. The closest is the RSI judge, which is instructed to cite concrete evidence and not invent observations, but grades supplied rubric behaviors rather than extracted claims; Symphony's `AccuracyEvaluator` asks an LLM to find factual errors but produces a single score with no claim-level decomposition.

```mermaid
flowchart TD
    ANS["answer"] --> CE["claim extraction → atomic claims"]
    CE --> V["verify each claim vs retrieved context (NLI / LLM judge)"]
    V --> HR["hallucination rate = unsupported / total claims"]
    CE -.->|"absent"| X["no claim extraction"]
    V -.->|"absent"| Y["no NLI/attribution; judges lack context"]
    RSI["RSI judge: evidence-citation rubric (not claim-level)"] -.-> V
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/judge_prompt.md:61</code> — "Cite concrete evidence for every verdict… Do not invent observations"<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/judge_evidence.py:90</code> — <code>prepare_judge_workspace</code> (evidence snapshot, no claim checker)<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/evaluators.py:438</code> — <code>AccuracyEvaluator</code>; <code>:447</code> factual-error rubric<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/templates.py:7</code> — judge compares response vs expected answer (no context)</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 12. What is perplexity, and what does a lower score actually tell you

**General:** Perplexity is the exponentiated average negative log-likelihood the model assigns to a token sequence: `exp(-(1/N)·Σ log p(token_i))`. Lower means the model finds the text more predictable — useful for comparing language models on the same data or detecting distribution shift/overfitting. It does not measure factuality, reasoning, instruction-following, or usefulness, and it is only comparable across models that share a tokenizer and data.

**Jiuwen:** Perplexity is absent as a concept or metric — no `perplexity`/`ppl`/loss-based language-modeling metric is computed anywhere. The nearest primitives are token log-probabilities and a softmax over candidate logits: candidate logits are normalized to probabilities for retrieval selection, per-completion `cumulative_logprob` is captured (used for generation summaries/RL) but not converted to perplexity, and `ChatReranker` exponentiates token logprobs for a yes/no rerank score. The only literal "perplexity" strings are the Perplexity web-search vendor, not the metric.

```mermaid
flowchart TD
    PPL["Perplexity = exp(-1/N · Σ log p(token_i))"] --> LOWER["lower → text more predictable (same tokenizer + data)"]
    PPL -.->|"not implemented"| X["absent in codebase"]
    LP["token logprobs / cumulative_logprob"] --> USE1["RL trajectories (capture pipeline)"]
    LP --> USE2["ChatReranker: exp(logprob) yes/no score"]
    LP --> USE3["retrieval candidate scoring: softmax over logits"]
    USE1 -.->|"no length-normalized averaging"| PPL
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/symphony/retrieval/llm/base/scoring.py:98-115</code> — softmax over candidate logits → probability (retrieval)<br>&bull; <code>agent-core/openjiuwen/symphony/retrieval/llm/vllm/client.py:847</code> — <code>cumulative_logprob</code> per completion (not perplexity)<br>&bull; <code>agent-core/openjiuwen/core/retrieval/reranker/chat_reranker.py:94-107</code> — <code>exp(logprob)</code> yes/no<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/capture_pipeline.py:408-418</code> — stores token logprobs for RL<br>&bull; <code>agent-core/openjiuwen/harness/tools/web/paid_search.py:44</code> — "Perplexity" is the search vendor, not the metric</sub>

</details>

**Gap.** No token-loss averaging, no length normalization, no corpus-level perplexity.

<sub>_Canonical source: `source/llm-fundamentals-interview-questions_for_engineers.md`; also covered in: llm-fund._</sub>


---

## 13. Known limitations of using an LLM as a judge

**General:** LLM judges are biased (position/order, verbosity, self-preference), noisy, non-deterministic, and can be gamed or prompt-injected. They need position-swapping, multiple votes, agreement reporting, human calibration on a golden set, and must distinguish "judge failed" from "answer wrong". A single unvalidated judge score is a weak signal.

**Jiuwen:** Four judge implementations exist. `agent_evolving`'s `LLMAsJudgeMetric` is a single call, parses to `true/false`, and converts exceptions to `0.0` (conflating "judge failed" with "answer wrong"). RSI's judge does one format retry on frozen evidence and guards against injecting "prior output" as trusted data, but is still single-judgment. Symphony's `LLMJudgeEvaluator` is `temperature=0.0` with one repair retry. Only the online RL `JudgeScorer` uses `num_votes` parallel votes averaged together. None handles position bias or reports agreement.

```mermaid
flowchart TD
    J["LLM judge"] --> B["biases: position/order · verbosity · self-preference"]
    J --> V["variance: non-deterministic"]
    J --> I["injection: judge prompt can be gamed"]
    J --> C["calibration: needs human golden set"]
    J --> F["failure vs wrong: must not collapse to 0"]
    J -.->|"only num_votes (RL)"| MULTI["multiple votes / agreement"]
    J -.->|"absent"| SWAP["position swap · agreement metric · bias probe"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:53</code> — single invoke, exception → <code>0.0</code>; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator.py:123</code> — same failure pattern<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/llm_as_judge.py:121</code> — two-attempt loop; <code>:152</code> untrusted prior-output guard<br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/base.py:262</code> — single judge call + one repair retry; <code>:401</code> <code>temperature=0.0</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/evaluator.py:66</code> — <code>num_votes</code> averaged; <code>:92</code> raw votes retained<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/judge_scorer.py:38</code> — <code>num_votes</code><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:127</code> — strict single-verdict parsing</sub>

</details>

**Gap.** No position/order-bias control, no inter-rater agreement (Cohen/Krippendorff), no variance threshold, and no human calibration. Some paths convert judge/infra failure to `0.0` (the `LLMAsJudgeMetric` and the RL judge dispatcher), while others distinguish it: RSI raises `EvaluationInfrastructureError` and Symphony returns `status="error"` with `score=None`.



<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`; also covered in: engineering, genai, rag-eval._</sub>


---

## 14. How do you evaluate when there's no ground truth answer, only a query and a corpus

**General:** Bootstraps without gold labels: (a) generate synthetic queries from known documents and treat the source document as the gold retrieval target (cheap, works well for retrieval metrics); (b) use an LLM to answer and treat cited passages as relevant (RAGAS-style); (c) judge faithfulness against the retrieved context rather than a reference answer; (d) sample and label by hand a small set to calibrate. The key is that retrieval can be graded with synthetic (query, source-doc) pairs even when answers are unlabeled.

**Jiuwen:** Synthetic dataset generation is largely not runnable. The advertised `rsi/dataset_generator` (`DatasetGenerator`, "model-driven synthetic evaluation dataset generation") exists only as compiled bytecode; its `case_generator`/`task_analyzer`/`coverage_validator` sources are stubs raising `NotImplementedError`, and the harness explicitly "never generates a dataset". The one runnable label-free builder is the PerStream example, which generates QA/memory pairs from source datasets using GPT-4o-mini. There is no query-generation loop tied to the core evaluator.

```mermaid
flowchart TD
    CORPUS["query + corpus, no labels"] --> S1["synthetic queries from known docs (doc = gold)"]
    CORPUS --> S2["LLM answer + cite → cited = relevant"]
    CORPUS --> S3["faithfulness judgment vs retrieved context"]
    CORPUS --> S4["small hand-labeled calibration set"]
    S1 -.->|"rsi generator: stub/bytecode"| X["no runnable core synthetic-eval loop"]
    S2 -.->|"PerStream example only"| Y["generate_dataset.sh"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/single_harness/iterative.py:134</code> — "never generates a dataset"<br>&bull; <code>agent-core/examples/PerStream/scripts/generate_dataset.sh:31</code> — LLM-driven QA/memory generation (example only)<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:47</code> — LLM judge usable on unlabeled answers but no context<br>&bull; <code>agent-core/openjiuwen/rsi/dataset_generator/__pycache__/case_generator.cpython-311.pyc</code> — <code>NotImplementedError</code> stubs (no <code>.py</code> source)</sub>

</details>



<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 15. How would you build an eval dataset from scratch if you don't have one yet

**General:** Mine queries from real logs or user questions, then label relevance by (a) synthetic queries generated from known documents (the document is the gold target), (b) LLM answering and treating cited chunks as relevant, or (c) a small hand-labeled calibration set. Start small (50–200 queries), cover query types including exact-match and multi-hop, and iterate. For retrieval you can bootstrap (query, source-doc) pairs with no answer labels at all.

**Jiuwen:** The advertised `rsi/dataset_generator` is not runnable source: `DatasetGenerator` exists only as compiled bytecode, and `case_generator`/`task_analyzer`/`coverage_validator` are stubs raising `NotImplementedError`; the harness "never generates a dataset". The one runnable label-free builder is the PerStream example (`generate_dataset.sh` → GPT-4o-mini QA/memory generation). There is no query-generation loop integrated with the core evaluator.

```mermaid
flowchart TD
    LOGS["real queries"] --> MINE["mine"]
    DOCS["known documents"] --> SYN["synthetic queries (doc = gold)"]
    MINE --> SET["small labeled eval set (50–200, multiple types)"]
    SYN --> SET
    SET -.->|"absent"| MET["Recall@k · Precision@k · MRR · NDCG (not implemented)"]
    SYN -.->|"rsi generator: stub/bytecode"| X["no runnable core generator (PerStream example only)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/single_harness/iterative.py:134</code> — "never generates a dataset"<br>&bull; <code>agent-core/examples/PerStream/scripts/generate_dataset.sh:31</code> — LLM-driven QA/memory generation (example)<br>&bull; <code>agent-core/openjiuwen/rsi/dataset_generator/__pycache__/case_generator.cpython-311.pyc</code> — <code>NotImplementedError</code> stubs (no source)<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/base.py:42</code> — metric interface lacks ranked-list eval</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 16. How many examples before eval results are statistically meaningful, not just noise

**General:** It depends on the effect size and metric variance. As a rule of thumb, ~100–200 examples give a usable signal for a common metric, but if you are comparing two systems you need enough to detect the delta above noise — report confidence intervals (bootstrap) and use paired significance tests on the same examples. For rare events (e.g. hallucination) you need far more, and minority-slice analysis needs hundreds per slice. Never quote a bare average without an error bound.

**Jiuwen:** There is no statistical reasoning. The closest construct is Symphony's `_confidence(sample_count)`, which buckets counts into qualitative labels (0→NONE, 1→LOW, <10→NORMAL, ≥10→HIGH) — a hard-coded heuristic, not a confidence interval. Aggregation reports `sample_count` and pass/fail counts but computes no standard error, bootstrap, or significance test.

```mermaid
flowchart TD
    N["N examples"] --> C["_confidence(sample_count): 0/1/<10/≥10 → NONE/LOW/NORMAL/HIGH"]
    N --> AGG["report sample_count + pass/fail"]
    N --> NEED["need: bootstrap CI · paired significance · power for rare events"]
    C -.->|"heuristic, not statistics"| X["no confidence interval / variance / significance"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/symphony/evaluation/suite.py:560</code> — <code>_confidence(sample_count)</code> heuristic; <code>:362</code> <code>sample_count</code> attached<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/metrics_collector.py:34</code> — <code>total_cases</code>/<code>passed_cases</code>/<code>average_score</code> (no variance/CI)<br>&bull; <code>agent-core/openjiuwen/symphony/orchestration/config.py:50</code> — <code>min_successes_verified</code> (threshold, not statistics)<br>&bull; <code>agent-core/openjiuwen/symphony/retrieval/build/tree/schema.py:232</code> — <code>structure_sample_size</code> (sampling config)</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 17. How would you compare two models for a specific task, not just a general leaderboard score

**General:** Run both models on the same held-out task set with the same prompts/decoding, score with task-appropriate metrics (exact match, tests, rubric judge), and compare accuracy plus latency and cost; check statistical significance and inspect failure cases. A leaderboard is a prior, not a decision — task fit, cost, latency, and controllability often matter more than a few points of general score.

**Jiuwen:** Model selection here is infrastructure routing, not benchmark comparison. `agent_teams/models/pool.py` defines `ModelRouterConfig` (one endpoint, many model names) and `IntelliRouterConfig` (many deployments behind a reliable client router), with allocator strategies chosen by `build_model_allocator`. IntelliRouter routes by adaptive multi-factor scoring (health, tokens, RPM, latency) and fails over — it does **not** choose by task accuracy. For comparing configs/attempts there is real per-task evaluation: `Trainer` evaluates each candidate on a validation set and keeps the highest score; `rsi best_of_n` ranks attempts by tests/diff/lint; the online judge uses `num_votes` voting. Comparing two models for a task therefore means running your own eval, not a leaderboard feature.

```mermaid
flowchart TD
    CMP{"compare two models"} --> ROUTE["IntelliRouter (health/tokens/RPM/latency — NOT accuracy)"]
    CMP --> EVAL["run both on same held-out task set"]
    EVAL --> TR["Trainer: per-candidate validation score → keep best"]
    EVAL --> BON["best_of_n: tests / diff / lint"]
    EVAL --> JUDGE["judge: num_votes voting"]
    TR --> DEC(["task-specific decision"])
    BON --> DEC
    JUDGE --> DEC
    ROUTE -.->|"absent"| X["no leaderboard / A-B model-accuracy harness"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_teams/models/pool.py:133-235</code> — <code>ModelRouterConfig</code>; <code>:314-392</code> — <code>IntelliRouterConfig</code> / deployments<br>&bull; <code>agent-core/openjiuwen/agent_teams/models/allocator.py:176/240/357/452/559</code> — allocator strategies + <code>build_model_allocator</code><br>&bull; <code>agent-core/examples/intelli_router/intelliRouter_demo.py:142-160</code> — adaptive routing weights; <code>:249-264</code> route within a pinned model pool<br>&bull; <code>agent-core/openjiuwen/agent_evolving/trainer/trainer.py:241-272</code> — per-candidate validation scoring, commits best<br>&bull; <code>agent-core/openjiuwen/rsi/auto_harness/pipelines/best_of_n/attempt_scorer.py:17-119</code> — rank by tests/lint/diff<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/judge_scorer.py:38/58</code> — <code>num_votes</code> judge voting</sub>

</details>

**Gap.** No leaderboard, no A/B model-comparison harness, no per-task model-accuracy registry. Routing optimizes availability/cost/latency, not task quality.

<sub>_Canonical source: `source/llm-fundamentals-interview-questions_for_engineers.md`; also covered in: llm-fund._</sub>


---

## 18. Building a regression test suite to catch a quality drop before it ships

**General:** Combine fast deterministic unit tests on the pipeline components with a quality eval suite on a fixed dataset scored by the same metrics each time; store a baseline and fail the build when the score drops beyond a threshold. Add golden/snapshot tests for prompts and outputs, and gate merges on the suite.

**Jiuwen:** Tests split into `tests/unit_tests/` (fast, deterministic, CI) and `tests/system_tests/` (E2E, usually skipped). `pytest` defines markers `level0` ("smoke / happy-path; PR gate must stay green") and `level1`, with `testpaths=["tests"]`. Quality evaluation exists separately: `evaluator_pipeline` emits `pass_rate`/`improvement`/`converged`, and `Trainer` compares a candidate's validation score against `best_score` and commits only improvements. But the CI gate that blocks merges (`ci_gate.yaml`) declares only `lint` and `type-check` — no pytest gate and no eval threshold.

```mermaid
flowchart TD
    PR["PR"] --> L["lint"] --> TC["type-check"] --> G{"gate (ci_gate.yaml)"}
    G -->|"configured"| LINT["lint + type-check only"]
    G -.->|"not configured"| PY["pytest level0 (advertised PR gate, not invoked)"]
    EVAL["evaluator_pipeline / Trainer"] -.->|"offline CLI, no baseline threshold"| Q["quality regression gate ABSENT"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/pyproject.toml:230</code> — pytest config + <code>level0</code>/<code>level1</code> markers<br>&bull; <code>agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21</code> — gates are only <code>lint</code> and <code>type-check</code><br>&bull; <code>agent-core/openjiuwen/auto_harness/infra/ci_gate_runner.py:1098</code> — gate dispatch; <code>agent-core/openjiuwen/auto_harness/stages/verify.py:451</code> <code>ci_gate.run("all")</code>; <code>:509</code> revert on exhaustion<br>&bull; <code>agent-core/openjiuwen/agent_evolving/trainer/trainer.py:217</code> — <code>improved = val_score &gt; progress.best_score</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:664</code> — <code>_compute_evolution_metrics</code></sub>

</details>

**Gap.** No model/agent-quality regression gate in CI, no golden/snapshot tests for prompts/retrieval/outputs, and credential-requiring system tests are skipped. A quality drop would not be caught before ship by the configured automation.

<sub>_Canonical source: `source/ai-engineer-technical-questions_for_engineers.md`; also covered in: engineering, genai, llm-applied, rag-eval, rag-1._</sub>


---

## 19. Evaluating continuously in production, not just once before launch

**General:** Sample live traffic, score it on a schedule or on feedback, and alert on quality drops — separate from error/latency monitoring. Look for drift in query distribution and retrieval hit rates, track online metrics (thumbs, task success, escalation), and periodically re-run the offline suite on fresh data. The goal is to detect degradation before users report it.

**Jiuwen:** There is a live capture-and-score path, but it serves **online RL training, not quality monitoring**: `CapturePipeline` stages each production completion and a judge later attaches an LLM score or user reward, persisting to a trajectory sample store. The product writes all spans into a per-session SQLite trajectory store (diagnostic, 7-day retention) for replay. There is no drift detection, no eval traffic-sampling policy, no dashboard, and no quality alert.

```mermaid
flowchart TD
    LIVE["live traffic"] --> CAP["CapturePipeline: stage request/response"]
    CAP --> JUD["judge → score or user reward"]
    JUD --> STORE["trajectory sample store (RL training data)"]
    LIVE --> TRJ["trajectory store: spans, 7-day retention (diagnostic)"]
    CAP -.->|"absent"| X["no quality monitoring · drift detection · sampling for eval · alerts"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/capture_pipeline.py:59</code> — <code>CapturePipeline</code>; <code>:73</code> before; <code>:110</code> after; <code>:170</code> <code>submit_reward</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/gateway/trajectory/judge_dispatcher.py:30</code> — flush + judge on follow-up/session end<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/judge_scorer.py:28</code> — live LLM judge score<br>&bull; <code>jiuwenswarm/jiuwenswarm/observability/store.py:304</code> — <code>TrajectoryStore</code>; <code>:307</code> 7-day retention (diagnostic)<br>&bull; <code>jiuwenswarm/jiuwenswarm/observability/sink.py:578</code> — <code>TrajectorySessionSinkRouter</code>; <code>jiuwenswarm/jiuwenswarm/observability/runtime.py:69</code> — runtime<br>&bull; <code>agent-core/openjiuwen/harness/observability/rail.py:355</code> — span emission</sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: ai-agent, rag-eval, rag-system._</sub>


---

## 20. How do you detect when your retrieval quality has degraded over time

**General:** Monitor retrieval-specific signals over time — zero-result rate, top-score distributions, click/select rate, and a periodic re-run of a frozen labeled set (Recall@k/NDCG) — and alert on shifts. Slice by query type/tenant/language, since degradation is often localized (a new format, a corpus change, an embedding-model update). Pair it with generation-side faithfulness/relevance tracking so you can tell a retrieval regression from a generation one.

**Jiuwen:** There is no retrieval-quality monitoring and no drift detection. Production observability is span-based: OTel spans with an error flag, a per-session trajectory store, and cost/usage facts — error/latency/trajectory, not quality. Offline evaluation exists (`rsi/evaluator`, `evaluator_pipeline`) but is not an online quality monitor, and there is no frozen retrieval metric to trend.

```mermaid
flowchart TD
    P["production"] --> SP["OTel spans: error/latency/trajectory (present)"]
    P -.->|"absent"| Q["retrieval quality trends: zero-result rate · score drift · frozen Recall@k/NDCG · alerts"]
    P --> OFF["offline rsi/evaluator + evaluator_pipeline (not online)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/harness/observability/run_span.py:289</code> — error status recorded; <code>agent-core/openjiuwen/harness/observability/setup.py:54</code> — OTel lifecycle<br>&bull; <code>jiuwenswarm/jiuwenswarm/observability/store.py:102</code> — <code>has_error</code>; <code>:137</code> <code>trajectory_current_records</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:167</code> — offline <code>bench.evaluate</code>; <code>:668</code> <code>_compute_evolution_metrics</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/trainer/trainer.py:217</code> — validation-score gate (offline)</sub>

</details>



<sub>_Canonical source: `source/rag-part1-interview-questions_for_engineers.md`; also covered in: rag-1._</sub>


---

## 21. High eval scores but users still complaining — what does that gap tell you about your eval set

**General:** The gap means the eval set does not represent real usage: too-easy or synthetic queries, no adversarial or long-tail cases, missing slices (language, domain, intent), a metric that rewards style over usefulness, or unmeasured dimensions (latency, verbosity, tone, refusals). The fix is to mine real complaints/failed sessions for queries, add them to the set, and re-baseline — the eval set is a moving target aligned to production.

**Jiuwen:** Feedback capture is partial, so the gap is not detectable in-product. Explicit like/dislike exists only for **proactive recommendations** (`feedback_collector.record_feedback`); for normal chat, feedback is inferred (an LLM classifying whether a user message is corrective, and the online-RL judge consuming the next user turn as feedback). Session tracking records runtime outcome (`succeeded/failed/waiting_user`), which is execution success, not answer quality. There is no general thumbs-up/down or satisfaction signal to reconcile against eval scores.

```mermaid
flowchart TD
    HIGH["high eval scores"] --> GAP["users still complain"]
    GAP --> WHY["eval set unrepresentative: easy/synthetic · missing slices · wrong metric · unmeasured dims"]
    WHY --> MINE["mine complaints/failed sessions → add to set → re-baseline"]
    FB["explicit like/dislike: proactive only; chat feedback inferred; runtime outcome (not quality)"] -.->|"absent general quality feedback"| X["cannot reconcile eval vs users in-product"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/recommendation/feedback_collector.py:47</code> — <code>record_feedback</code> (explicit, proactive only); <code>jiuwenswarm/jiuwenswarm/common/schema/message.py:141</code> — <code>PROACTIVE_FEEDBACK</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/signal/from_conv.py:327</code> — <code>detect_user_intent</code> infers corrective feedback<br>&bull; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/judge/evaluator.py:39</code> — judge takes <code>followup_user_feedback</code>; <code>agent-core/openjiuwen/agent_evolving/agent_rl/online/gateway/trajectory/judge_dispatcher.py:30</code><br>&bull; <code>jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:544</code> — <code>_TurnOutcomeTracker</code> (runtime outcome)<br>&bull; <code>agent-core/openjiuwen/agent_evolving/signal/review_feedback.py:117</code> — <code>ReviewFeedbackAttributor</code></sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 22. Tying an eval metric back to a business outcome a stakeholder actually cares about

**General:** Translate model quality into the business proxy it moves: task success rate, deflection/containment, time-to-resolution, conversion, retention, or cost-per-resolution. Build a labeled bridge — correlate your offline metric with the business KPI on a sample — and report both. A metric no stakeholder can act on will not survive budget season; pick one that maps to money or time saved.

**Jiuwen:** Metrics here are engineering/task-completion, not business KPIs. `GoalEvaluator` scores whether an agent objective is `complete`/`blocked`; `SuccessDetector` maps a task to `success/partial/fail`; `evaluator_pipeline`/team verification aggregate `pass_rate`/`avg_score`. The only stakeholder-adjacent signal is **cost**: per-session tracking with an optional limit (`CostLimitExceededError`). There is no conversion, retention, engagement, or user-satisfaction mapping.

```mermaid
flowchart TD
    Q["business outcome?"] --> KPI["task success · deflection · time-to-resolution · conversion · retention"]
    KPI --> BRIDGE["correlate offline metric ↔ KPI on a sample"]
    EVAL["GoalEvaluator / SuccessDetector / pass_rate (engineering metrics)"] -.->|"no KPI mapping"| X["only cost tracked (usage_cost), never correlated with quality"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/harness/goal/evaluation.py:74</code> — <code>GoalEvaluator</code> (goal completion)<br>&bull; <code>agent-core/openjiuwen/agent_evolving/ttse/success.py:267</code> — <code>SignalBasedSuccessDetector</code> (<code>success/partial/fail</code>); <code>:92</code> <code>classify_explicit_score</code><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/base.py:232</code> — <code>aggregate()</code><br>&bull; <code>agent-core/openjiuwen/agent_teams/verification/memory.py:160</code> — aggregates <code>pass_rate</code>/<code>avg_score</code><br>&bull; <code>jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:32</code> — cost settings; <code>:65</code> <code>CostLimitExceededError</code></sub>

</details>

<sub>_Canonical source: `source/rag-evaluation-interview-questions_for_engineers.md`; also covered in: rag-eval._</sub>


---

## 23. "How do you know it's working" tests evaluation depth, not confidence

**General:** "It looked good to me" ends the conversation. They want a fixed eval set, faithfulness scoring on generated claims, and how you'd catch silent degradation after an unflagged prompt change. The real trap is "how would you know if it got *worse*", not "how do you know it works now". A strong answer includes: a frozen labeled eval set scored on every change, stage-level metrics (retrieval recall/NDCG; generation faithfulness), a regression gate in CI, and production sampling with drift alerts. Name the baseline and the threshold.

**Jiuwen:** Offline answer-level evaluation exists (`ExactMatchMetric`, `LLMAsJudgeMetric`, RSI weighted rubric, `evaluator_pipeline` pass-rate), but there is no retrieval metric layer, no faithfulness/claim-level scoring, no quality regression gate in CI (`ci_gate.yaml` is lint/type-check only), and no production quality monitoring or drift detection — so the "how would you know it got worse" question exposes real gaps.

```mermaid
flowchart TD
    Q["how do you know it works / got worse?"] --> FIX["frozen eval set (absent)"]
    Q --> M["stage metrics: recall/NDCG + faithfulness (retrieval/faithfulness absent)"]
    Q --> G["CI regression gate (lint/type-check only)"]
    Q --> P["production sampling + drift alerts (absent)"]
    Q --> OK["offline: exact-match + LLM judge + RSI rubric (present)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:47</code> — LLM judge; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/exact_match.py:12</code> — exact match<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:193</code> — weighted rubric<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:167</code> — benchmark eval<br>&bull; <code>agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21</code> — gates are only <code>lint</code>/<code>type-check</code>; <code>agent-core/pyproject.toml:236</code> — <code>level0</code>/<code>level1</code> markers (not invoked)<br>&bull; <code>jiuwenswarm/jiuwenswarm/observability/store.py:102</code> — <code>has_error</code> (operations, not quality)</sub>

</details>


---

## 24. "How do you know it's working" is testing evaluation depth

**General:** faithfulness scoring (does output match retrieved context), relevance scoring (does it answer the query), human eval on a rotating sample, and regression testing before every deploy — not just at launch. A strong answer includes: a frozen labeled set, stage-level metrics (retrieval recall/NDCG; generation faithfulness/relevance), a CI regression gate with a baseline threshold, periodic human sampling, and production monitoring with drift alerts.

**Jiuwen:** Offline answer-level evaluation exists (`ExactMatchMetric`, `LLMAsJudgeMetric`, RSI rubric, `evaluator_pipeline`), but there is no faithfulness/relevance metric (judges lack the retrieved context), no retrieval metric layer, no CI quality gate (lint/type-check only), no human-sampling pipeline, and no production quality monitoring. The "how would you know it got worse" follow-up exposes real gaps.

```mermaid
flowchart TD
    Q["how do you know it works / got worse?"] --> F["faithfulness (absent: no context to judge)"]
    Q --> R["relevance (absent)"]
    Q --> H["human sampling (absent)"]
    Q --> G["regression before deploy (CI = lint/type-check only)"]
    Q --> OK["offline: exact-match + LLM judge + RSI rubric (present)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/llm_as_judge.py:40</code> — no context input; <code>agent-core/openjiuwen/agent_evolving/evaluator/metrics/exact_match.py:12</code> — exact match<br>&bull; <code>agent-core/openjiuwen/rsi/harness_rsi/evaluator/judger/scoring.py:193</code> — weighted rubric<br>&bull; <code>agent-core/openjiuwen/agent_evolving/evaluator/evaluator_pipeline/pipeline.py:167</code> — benchmark eval<br>&bull; <code>agent-core/openjiuwen/auto_harness/resources/ci_gate.yaml:21</code> — lint/type-check only; <code>agent-core/pyproject.toml:236</code> — markers not invoked<br>&bull; <code>jiuwenswarm/jiuwenswarm/observability/store.py:102</code> — <code>has_error</code> (operations, not quality)</sub>

</details>
