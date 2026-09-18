# Jiuwen AI-Engineering Knowledge Base

Concepts and how the Jiuwen codebase implements them — organized by topic, with offline study formats. Every entry pairs a short framework-agnostic **General** answer with a **Jiuwen** answer describing how this codebase implements it (or explicitly does not), plus a diagram and `file:line` **Anchors**.

**Browse online:** https://michaelatamuk.github.io/openjiuwen-knowledge/
**Android app:** [download the latest APK](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest) (offline study app; debug-signed)

## Structure

```
openjiuwen-knowledge/
  README.md                     this guide
  knowledge/                    the knowledge base — read these
    01-llm-foundations.md …     Title → Summary → Key points → Explanation → Jiuwen
    index.md                    this README, as a site index
    assets/diagrams/            rendered diagrams
  content/                      source: topics + authored layers
  source/                       the original docs, archived unchanged
  pipeline/                     build scripts + mkdocs config
  apps/android/                 native offline study app (Room + FSRS)
  build/                        generated artifacts — site, EPUB, Anki, … (gitignored)
```

The numbered `01`–`10` files were assembled from the archived docs: near-identical and same-concept questions were merged, so each question appears once. The glossary and the pattern sections (`90`–`93`) are key material in their own right.

## Study offline (plane / phone)

`pipeline/` builds an offline kit from these docs into `build/`:

- `build/dist/jiuwenswarm-knowledge-offline.html` — one self-contained file with search, tap-to-reveal answers, and diagrams; works with no network on Windows and Android.
- `build/site/index.html` — a fully local website build (MkDocs Material) for desktop reading.
- `build/dist/jiuwen-knowledge.apkg` — an Anki deck for spaced repetition (Anki / AnkiDroid).
- `build/dist/jiuwenswarm-knowledge.epub` — an EPUB for e-readers.
- `build/knowledge-vault.zip` — an Obsidian vault.

Rebuild instructions are in `pipeline/README.md`.

## Topics

### Foundations
- [01-llm-foundations.md](01-llm-foundations.md) — 14 questions. Tokens, embeddings, self-attention, encoder/decoder, positional encoding, sampling, context window.
- [02-prompting-and-output-control.md](02-prompting-and-output-control.md) — 5 questions. Zero/few-shot/CoT, system vs user prompts, JSON output.
- [90-llm-terms-glossary.md](90-llm-terms-glossary.md) — 20-term glossary with where each term bites.

### Retrieval & RAG
- [03-rag-and-retrieval.md](03-rag-and-retrieval.md) — 41 questions. Pipeline, chunking, embeddings, dense/sparse, reranking, query understanding, failure modes.
- [04-rag-system-design.md](04-rag-system-design.md) — 13 questions. Whiteboard design prompts, scale, freshness, multi-tenancy, access control.

### Agents
- [05-agents-tools-and-memory.md](05-agents-tools-and-memory.md) — 45 questions. Function calling, loops, tools, planning, memory, frameworks, multi-agent.

### Evaluation & operations
- [06-evaluation.md](06-evaluation.md) — 21 questions. Retrieval metrics, faithfulness, LLM-as-judge, regression suites, production eval.
- [07-production-cost-and-scale.md](07-production-cost-and-scale.md) — 8 questions. Cost, latency, caching, concurrency, 10x scaling.

### Trust & safety
- [08-security-and-safety.md](08-security-and-safety.md) — 8 questions. Prompt injection, untrusted content, sensitive data, harmful output, jailbreaks.

### Adaptation & engineering
- [09-fine-tuning-and-customization.md](09-fine-tuning-and-customization.md) — 6 questions. Full FT vs LoRA, instruction tuning, when to fine-tune, small-dataset risk.
- [10-general-engineering.md](10-general-engineering.md) — 5 questions. Model selection, framework/team fit, rule-based vs LLM, release safety, stakeholder tradeoffs.

### Patterns
- [91-ai-engineer-interview-patterns.md](91-ai-engineer-interview-patterns.md) — 7 recurring technical-interview dynamics.
- [92-llm-interview-patterns.md](92-llm-interview-patterns.md) — 7 recurring LLM interview dynamics.
- [93-llm-architecture-patterns.md](93-llm-architecture-patterns.md) — 7 recurring LLM architecture patterns.

## How to read an entry

Each entry is layered, fastest pass first:

- **Title / Summary / Key points** — the quick pass.
- **Explanation** (General) — the framework-agnostic answer, followed by a concept diagram.
- **Jiuwen** — plain-language account of how this codebase implements the mechanism, or an explicit statement that it does not.
- **Technical detail (classes & functions)** — collapsed; the `path:line` **Anchors** and the implementation diagram.

Each entry also names its canonical source doc and the other docs that covered it, so you can trace it back.

## Conventions

- **Anchors** use full repository paths and are `file:line`; they may drift as code changes. Where a mechanism is absent, config-gated, or inert, that is stated rather than implied. All anchors were verified to resolve to a real file and line when written, and their line contents spot-checked.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/` layers. The product built on it is `jiuwenswarm/jiuwenswarm/`. Answers say which layer carries a mechanism.
- **Paths** are relative to the repository root. The uncompressed originals are archived under `source/`.
