# Interview question bank — Jiuwen

Twenty-six docs covering recurring AI-engineering interview material — fifteen question sets plus eleven reference docs (four patterns docs, an architecture-patterns doc, a glossary, a tradeoffs guide, a foundational-papers coverage map, and four full-stack / design-patterns / learning-path / gateway coverage docs), grouped by topic below.

Each question set has the same shape: a short **General** answer that transfers to any interview, then a **Jiuwen** answer describing how this codebase implements it, with a Mermaid diagram and an **Anchors** list for each question. Reference docs map the same mechanisms without the Q&A shape.

---

## Real interview reports

Verbatim question sets from reported hiring screens, preserving round structure and interviewer framing.

| Doc | Questions | Focus |
|---|---|---|
| [real-interview-ai-engineer-4rounds_for_engineers.md](real-interview-ai-engineer-4rounds_for_engineers.md) | 25 | Round 1: coding + ML fundamentals (gradient descent, cosine similarity, KNN, P/R/F1); Round 2: deep learning + transformers (backprop, vanishing gradient, batch/layer norm, multi-head attention, overfitting); Round 3: LLMs + RAG; Round 4: agents + system design (multi-provider routing, fallback) |
| [ai-engineer-levelled-interview-questions_for_engineers.md](ai-engineer-levelled-interview-questions_for_engineers.md) | 34 | Beginner: AI/ML/DL taxonomy, supervised/unsupervised/RL, overfitting, bias-variance, gradient descent, parameters vs hyperparameters; Intermediate: backprop, vanishing gradient, batch/layer norm, dropout, CNNs vs RNNs, transfer learning, classification eval, cross-validation; Advanced: attention, multi-head attention, encoder-decoder, fine-tuning vs prompting vs RAG, LoRA, RLHF vs DPO, hallucination eval, quantization; LLM+RAG; Agents+System Design |

---

## General AI engineering

Broad sets that span LLM, RAG, agents, evaluation, scale, and security.

| Doc | Questions | Focus |
|---|---|---|
| [ai-engineer-technical-questions_for_engineers.md](ai-engineer-technical-questions_for_engineers.md) | 30 | Python and software engineering, LLM fundamentals, RAG, agents and tool use, evaluation, system design and scale, security, judgment and tradeoffs |
| [genai-interview-questions_for_engineers.md](genai-interview-questions_for_engineers.md) | 31 | Foundational concepts, prompting, RAG, fine-tuning and customization, agents and tool use, evaluation, production and scale, safety and ethics |
| [ai-engineer-linkedin-interview-questions_for_engineers.md](ai-engineer-linkedin-interview-questions_for_engineers.md) | 26 | Questions-only compilation from LinkedIn, Blind, and interview prep forums: system design and architecture, RAG and retrieval, agents and tool use, evaluation, cost/latency/scale, security, behavioral/judgment |

## Agents and frameworks

Agent loops, tool use, state, multi-agent orchestration, and framework design.

| Doc | Questions | Focus |
|---|---|---|
| [ai-agent-interview-questions_for_engineers.md](ai-agent-interview-questions_for_engineers.md) | 27 | Core concepts, planning and reasoning, tool use and reliability, memory, multi-agent, cost and production, safety |
| [ai-agent-framework-interview-questions_for_engineers.md](ai-agent-framework-interview-questions_for_engineers.md) | 24 | Framework value, state and execution, tool integration, multi-agent orchestration, reliability and control, framework selection |

## RAG and retrieval

Read in order: Part 1 → Part 2 → practical → retrieval deep dive → evaluation → system design.

| Doc | Questions | Focus |
|---|---|---|
| [rag-part1-interview-questions_for_engineers.md](rag-part1-interview-questions_for_engineers.md) | 23 | RAG architecture and pipeline, chunking and embedding, retrieval quality, failure modes, scale and production, evaluation |
| [rag-part2-interview-questions_for_engineers.md](rag-part2-interview-questions_for_engineers.md) | 18 | Multi-hop and complex retrieval, hybrid search, agentic RAG, query understanding, production-grade retrieval |
| [rag-practical-interview-questions_for_engineers.md](rag-practical-interview-questions_for_engineers.md) | 25 | RAG conceptual basics, chunking and embeddings, retrieval and ranking, failure scenarios, comparisons, real-world systems, cost and practicality |
| [rag-retrieval-interview-questions_for_engineers.md](rag-retrieval-interview-questions_for_engineers.md) | 28 | Embeddings and similarity, chunking, sparse vs. dense, reranking, retrieval evaluation, multi-document and complex queries, scale and freshness |
| [rag-evaluation-interview-questions_for_engineers.md](rag-evaluation-interview-questions_for_engineers.md) | 19 | Core evaluation concepts, retrieval metrics, generation metrics, practical eval setup, business-facing evaluation |
| [rag-system-design-interview-questions_for_engineers.md](rag-system-design-interview-questions_for_engineers.md) | 20 | Whiteboard design prompts, scale and infrastructure, latency and cost, freshness and consistency, reliability and failure handling, security and access control |

## LLM

Model internals (fundamentals) and building with the model (applied).

| Doc | Questions | Focus |
|---|---|---|
| [llm-fundamentals-interview-questions_for_engineers.md](llm-fundamentals-interview-questions_for_engineers.md) | 24 | Architecture, tokens and sampling, context and memory, prompting, fine-tuning, model behavior, evaluation and comparison |
| [llm-applied-interview-questions_for_engineers.md](llm-applied-interview-questions_for_engineers.md) | 23 | Core LLM concepts, RAG, agents and tool use, evaluation, production and cost, security |

## Patterns and reference

Non-Q&A companions: interview dynamics, recurring architecture patterns, and a glossary.

| Doc | Scope | Focus |
|---|---|---|
| [ai-engineer-interview-patterns_for_engineers.md](ai-engineer-interview-patterns_for_engineers.md) | 7 patterns | Recurring interview dynamics: failure-mode awareness, tradeoffs with numbers, shipped-agent signals, evaluation depth, scaling, disguised security, stakeholder judgment |
| [llm-interview-patterns_for_engineers.md](llm-interview-patterns_for_engineers.md) | 7 patterns | Recurring LLM interview dynamics: context handling, hallucination, tradeoffs, cost/loop control, prompt versioning, evaluation, untrusted input |
| [agent-failure-patterns_for_engineers.md](agent-failure-patterns_for_engineers.md) | 6 patterns | Agent failure modes as interview depth probes: tool idempotency, stuck loops + divergence, ungrounded confidence + output validation, memory carrying errors, missing observability, undefined termination |
| [llm-architecture-patterns_for_engineers.md](llm-architecture-patterns_for_engineers.md) | 7 patterns | Recurring LLM architecture patterns: simple RAG, modular RAG + rerank, agentic tools, planner-executor, critic loop, memory-augmented, router |
| [llm-terms-interview-reference_for_engineers.md](llm-terms-interview-reference_for_engineers.md) | 20 terms | Glossary: core model concepts, RAG and retrieval, customization, agents and tools, production concerns |
| [cost-latency-accuracy-tradeoffs_for_engineers.md](cost-latency-accuracy-tradeoffs_for_engineers.md) | 7 patterns | How interviewers test tradeoff reasoning: asking clarifying constraints, justifying model size, 10x traffic, retrieval depth vs speed, budget cuts, empirical measurement, best-model-failed |
| [15-foundational-papers_for_engineers.md](15-foundational-papers_for_engineers.md) | 15 papers | Coverage map of foundational papers: Transformer, BERT, GPT-3, Chinchilla, InstructGPT, DPO, LoRA, RAG, CoT, ReAct, DDPM, CLIP, FlashAttention, Switch Transformers, Constitutional AI |
| [ai-system-full-stack_for_engineers.md](ai-system-full-stack_for_engineers.md) | 4 concepts | Full-stack AI system reference: 7-layer architecture stack, KV cache and prompt caching, base vs instruct model pipeline, LLM API call lifecycle |
| [agent-design-patterns-2026_for_engineers.md](agent-design-patterns-2026_for_engineers.md) | 4 patterns | Agent design pattern reference: workflows vs agents, MCP vs A2A protocol comparison, 4 MAS architecture types and 5 components, invariant-based testing for non-deterministic agents |
| [ai-engineer-learning-path_for_engineers.md](ai-engineer-learning-path_for_engineers.md) | coverage map | 6-month AI engineer learning path mapped to KB entries; all topics already covered — no new entries |
| [ai-gateway-architecture_for_engineers.md](ai-gateway-architecture_for_engineers.md) | coverage map | AI gateway pattern (routing, rate-limiting, caching, safety enforcement) mapped to KB entries; all topics already covered under topics 16 and 18 |

Most sets open with a `> **The pattern worth noticing:**` line; every question set closes with a strong-vs-weak summary table.

## How to read an answer

- **General** — the framework-agnostic answer; this is the part that transfers to any interview.
- **Jiuwen** — how this codebase implements the mechanism, or an explicit statement that it does not. Code references are collected in the **Anchors** list under each Jiuwen answer, as `path:line` — short description.

## Conventions

- **Anchors** use full repository paths and are `file:line`; they may drift as code changes. Where a mechanism is absent, config-gated, or inert, that is stated rather than implied. All anchors were verified to resolve to a real file and line when written, and their line contents spot-checked.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/` layers. The product built on it is `jiuwenswarm/jiuwenswarm/`. Answers say which layer carries a mechanism.
- **Paths** are relative to the repository root.
