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

The numbered `01`–`10` files were assembled from the archived docs: near-identical and same-concept questions were merged, so each question appears once. Patterns and the glossary are reference material, not questions.

## Study offline (plane / phone)

`pipeline/` builds an offline kit from these docs into `build/`:

- `build/dist/jiuwenswarm-interview-offline.html` — one self-contained file with search, tap-to-reveal answers, and diagrams; works with no network on Windows and Android.
- `build/site/index.html` — a fully local website build (MkDocs Material) for desktop reading.
- `build/dist/jiuwen-interview.apkg` — an Anki deck for spaced repetition (Anki / AnkiDroid).
- `build/dist/jiuwenswarm-interview.epub` — an EPUB for e-readers.
- `build/interview_questions-vault.zip` — an Obsidian vault.

Rebuild instructions are in `pipeline/README.md`.

## Read in this order

The numbered files are in recommended study order: foundations → prompting → RAG → agents → evaluation → production → security → fine-tuning → general, with reference docs first (glossary) and last (architecture patterns).

| File | Questions | Focus |
|---|---|---|
| [01-llm-foundations.md](knowledge/01-llm-foundations.md) | 14 | Tokens, embeddings, self-attention, encoder/decoder, positional encoding, sampling, context window |
| [02-prompting-and-output-control.md](knowledge/02-prompting-and-output-control.md) | 5 | Zero/few-shot/CoT, system vs user prompts, JSON output |
| [03-rag-and-retrieval.md](knowledge/03-rag-and-retrieval.md) | 41 | Pipeline, chunking, embeddings, dense/sparse, reranking, query understanding, failure modes |
| [04-rag-system-design.md](knowledge/04-rag-system-design.md) | 13 | Whiteboard design prompts, scale, freshness, multi-tenancy, access control |
| [05-agents-tools-and-memory.md](knowledge/05-agents-tools-and-memory.md) | 45 | Function calling, loops, tools, planning, memory, frameworks, multi-agent |
| [06-evaluation.md](knowledge/06-evaluation.md) | 21 | Retrieval metrics, faithfulness, LLM-as-judge, regression suites, production eval |
| [07-production-cost-and-scale.md](knowledge/07-production-cost-and-scale.md) | 8 | Cost, latency, caching, concurrency, 10x scaling |
| [08-security-and-safety.md](knowledge/08-security-and-safety.md) | 8 | Prompt injection, untrusted content, sensitive data, harmful output, jailbreaks |
| [09-fine-tuning-and-customization.md](knowledge/09-fine-tuning-and-customization.md) | 6 | Full FT vs LoRA, instruction tuning, when to fine-tune, small-dataset risk |
| [10-general-engineering.md](knowledge/10-general-engineering.md) | 5 | Model selection, framework/team fit, rule-based vs LLM, release safety, stakeholder tradeoffs |

## Reference docs

| File | Scope |
|---|---|
| [90-llm-terms-glossary.md](knowledge/90-llm-terms-glossary.md) | 20-term glossary with where each term bites (read first) |
| [91-ai-engineer-interview-patterns.md](knowledge/91-ai-engineer-interview-patterns.md) | 7 recurring technical-interview dynamics |
| [92-llm-interview-patterns.md](knowledge/92-llm-interview-patterns.md) | 7 recurring LLM interview dynamics |
| [93-llm-architecture-patterns.md](knowledge/93-llm-architecture-patterns.md) | 7 recurring LLM architecture patterns (read last) |

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
