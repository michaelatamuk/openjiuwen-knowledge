# Jiuwen AI-Engineering Knowledge Base

A grounded AI-engineering reference. Every entry pairs a framework-agnostic
answer with how the **Jiuwen** codebase actually implements it, anchored by
`file:line` links into the source.

**207 entries · 14 sections · readable offline**

## Start here

- **Read online** — [michaelatamuk.github.io/openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/)
- **Read on GitHub** — jump to [LLM foundations](01-llm-foundations.md) or browse [Sections](#sections)
- **Download** — [latest release](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest): Android APK · EPUB · single-file HTML · Anki deck + CSV · Obsidian vault
- **Rebuild** — see [Rebuilding](#rebuilding)

## What this is

- **Two answers per concept.** The **General** half transfers to any stack. The
  **Jiuwen** half maps the concept to one real codebase, with `path:line` anchors
  — and says so explicitly when a mechanism is absent, config-gated, or inert.
- **Deduplicated.** 18 source documents were merged so each concept appears once,
  with provenance back to the originals.
- **Self-contained.** Diagrams are pre-rendered PNGs — no Mermaid runtime, no
  CDN, no network is needed to read any format.

It is useful for onboarding, design reviews, and self-study. The Jiuwen half is
specific to this codebase and does not transfer to other stacks.

## Sections

| Section | Entries | Files |
|---|---|---|
| **Foundations** | 39 | [01 LLM foundations](01-llm-foundations.md) · [02 Prompting & output](02-prompting-and-output-control.md) · [90 LLM terms glossary](90-llm-terms-glossary.md) |
| **Retrieval & RAG** | 54 | [03 RAG & retrieval](03-rag-and-retrieval.md) · [04 RAG system design](04-rag-system-design.md) |
| **Agents** | 45 | [05 Agents, tools & memory](05-agents-tools-and-memory.md) |
| **Evaluation & operations** | 29 | [06 Evaluation](06-evaluation.md) · [07 Production, cost & scale](07-production-cost-and-scale.md) |
| **Trust & safety** | 8 | [08 Security & safety](08-security-and-safety.md) |
| **Adaptation & engineering** | 11 | [09 Fine-tuning & customization](09-fine-tuning-and-customization.md) · [10 General engineering](10-general-engineering.md) |
| **Patterns** | 21 | [91 AI engineer patterns](91-ai-engineer-interview-patterns.md) · [92 LLM patterns](92-llm-interview-patterns.md) · [93 LLM architecture patterns](93-llm-architecture-patterns.md) |

## How to read an entry

Each entry is layered, fastest pass first:

1. **Title / Summary / Key points** — the quick pass.
2. **Explanation (General)** — the framework-agnostic answer, plus a concept diagram.
3. **Jiuwen** — how this codebase implements the mechanism, in plain language.
4. **Technical detail** — the `path:line` anchors and the implementation diagram.

Every entry also names its canonical source document and the other documents
that covered it.

## Formats

| Format | Best for | Where |
|---|---|---|
| **Website** | Desktop reading: nav, search, dark mode | [openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/) |
| **Markdown** | Reading on GitHub, diffing, the source of truth | `knowledge/` in this repository |
| **Single-file HTML** | Phone / plane: one file, search, tap-to-reveal | release `jiuwenswarm-knowledge-offline.html` |
| **EPUB** | E-readers | release `jiuwenswarm-knowledge.epub` |
| **Anki deck** | Spaced repetition (Anki / AnkiDroid) | release `jiuwen-knowledge.apkg` |
| **Obsidian vault** | Linked notes, local search | release `knowledge-vault.zip` |
| **Android app** | Native offline study (Kotlin, Room, FSRS) | release `jiuwen-study-2.0-debug.apk` |

## Repository layout

```
openjiuwen-knowledge/
├── knowledge/              the compiled knowledge base — read these
│   ├── *.md                one file per section
│   ├── index.md            this README, rendered as the site home
│   └── assets/diagrams/    rendered diagrams
├── content/                authored source
│   ├── topics/             the section documents (General + Jiuwen + anchors)
│   ├── summaries/          per-section Title / Summary / Key points
│   ├── jiuwen/             per-section plain-language Jiuwen answers
│   └── diagrams.json       concept-vs-technical diagram assignments
├── source/                 the 18 original documents, archived unchanged
├── pipeline/               build + publish scripts, MkDocs config
├── apps/android/           native offline study app (Kotlin, Room, FSRS)
└── build/                  generated artifacts — site, HTML, EPUB, Anki, … (gitignored)
```

`knowledge/` is generated from `content/` and committed, so the readable version
is available directly on GitHub. `build/` is disposable.

## Rebuilding

```bash
# one-time toolchain
uv venv .venv
uv pip install --python .venv/Scripts/python.exe mkdocs-material genanki ebooklib

cd pipeline
python build_all.py            # regenerate knowledge/ and build/ (--android also builds the APK)
python publish_site.py         # publish build/site to the gh-pages branch

cd ../apps/android && ./gradlew assembleDebug   # the Android app
```

Requires Python 3.11+, Node with `@mermaid-js/mermaid-cli` for diagram rendering
(cached under `build/`), and the Android SDK + a JDK for the app. See
`pipeline/README.md` for individual stages and options.

## Grounding & provenance

- **Anchors** are `path:line` into the Jiuwen source. They may drift as the code
  changes; they were verified to resolve when written, and their contents
  spot-checked. Where a mechanism is absent, config-gated, or inert, the entry
  says so rather than implying it works.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK
  plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/`
  layers. The product built on it is `jiuwenswarm/jiuwenswarm/`. Answers state
  which layer carries a mechanism.
- **Originals.** The uncompressed source documents are archived unchanged under
  `source/`. The numbered sections were assembled from them: near-identical and
  same-concept material was merged, so each concept appears once.
