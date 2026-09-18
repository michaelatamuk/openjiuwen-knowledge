# Jiuwen AI-Engineering Knowledge Base

A grounded reference for AI-engineering concepts. Every entry gives a
framework-agnostic answer, then shows how the **Jiuwen** codebase actually
implements it — with `file:line` anchors into the source. 207 entries across 14
sections, readable as a website, a single-file HTML app, an EPUB, an Anki deck,
an Obsidian vault, or a native offline Android app.

**Read online:** https://michaelatamuk.github.io/openjiuwen-knowledge/
**Downloads:** [latest release](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest) — Android APK, EPUB, single-file HTML, Anki deck + CSV, Obsidian vault, site zip.

## Why this exists

Most AI-engineering references are either generic (textbook) or tied to one
repo (API docs). This one deliberately does both halves:

- The **General** half is the concept — it transfers to any stack.
- The **Jiuwen** half is a verified map from that concept to one real codebase,
  and it says so explicitly when a mechanism is absent, config-gated, or inert.

That pairing is useful for onboarding, design reviews, and self-study: the
abstract idea is always grounded in code you can open. Note that the Jiuwen half
is specific to this codebase and does not transfer to other stacks.

## What's inside

- **207 entries** — 166 concept and practice questions, plus a 20-term glossary
  and 21 pattern/architecture entries.
- **Layered answers** — Title → Summary → Key points → Explanation (with a
  concept diagram) → Jiuwen → Technical detail (implementation notes, `path:line`
  anchors, implementation diagram; shown expanded, collapsible).
- **Deduplicated** — 18 source documents were merged so each concept appears
  once, with provenance back to the originals.
- **Self-contained** — diagrams are pre-rendered to PNG, so no Mermaid runtime,
  no CDN, and no network are needed to read any format.

## Sections

| Section | Entries | Files |
|---|---|---|
| **Foundations** | 39 | [01 LLM foundations](knowledge/01-llm-foundations.md) · [02 Prompting & output control](knowledge/02-prompting-and-output-control.md) · [90 LLM terms glossary](knowledge/90-llm-terms-glossary.md) |
| **Retrieval & RAG** | 54 | [03 RAG & retrieval](knowledge/03-rag-and-retrieval.md) · [04 RAG system design](knowledge/04-rag-system-design.md) |
| **Agents** | 45 | [05 Agents, tools & memory](knowledge/05-agents-tools-and-memory.md) |
| **Evaluation & operations** | 29 | [06 Evaluation](knowledge/06-evaluation.md) · [07 Production, cost & scale](knowledge/07-production-cost-and-scale.md) |
| **Trust & safety** | 8 | [08 Security & safety](knowledge/08-security-and-safety.md) |
| **Adaptation & engineering** | 11 | [09 Fine-tuning & customization](knowledge/09-fine-tuning-and-customization.md) · [10 General engineering](knowledge/10-general-engineering.md) |
| **Patterns** | 21 | [91 AI engineer patterns](knowledge/91-ai-engineer-interview-patterns.md) · [92 LLM patterns](knowledge/92-llm-interview-patterns.md) · [93 LLM architecture patterns](knowledge/93-llm-architecture-patterns.md) |

## How to read an entry

Each entry is layered, fastest pass first:

- **Title / Summary / Key points** — the quick pass.
- **Explanation** (General) — the framework-agnostic answer, followed by a
  concept diagram.
- **Jiuwen** — plain-language account of how this codebase implements the
  mechanism, or an explicit statement that it does not.
- **Technical detail (classes & functions)** — the `path:line` anchors and the
  implementation diagram.

Each entry also names its canonical source document and the other documents that
covered it, so you can trace it back to the archive.

## Formats

| Format | Best for | Where |
|---|---|---|
| **Website** | Desktop reading: nav, search, dark mode | https://michaelatamuk.github.io/openjiuwen-knowledge/ |
| **Markdown** | Reading on GitHub, diffing, the source of truth | `knowledge/` in this repository |
| **Single-file HTML** | Phone / plane: one file, search, tap-to-reveal | release `jiuwenswarm-knowledge-offline.html` |
| **EPUB** | E-readers | release `jiuwenswarm-knowledge.epub` |
| **Anki deck / CSV** | Spaced repetition (Anki / AnkiDroid) | release `jiuwen-knowledge.apkg` |
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
is available directly on GitHub; `build/` is disposable.

## Rebuilding

```bash
# one-time toolchain
uv venv .venv
uv pip install --python .venv/Scripts/python.exe mkdocs-material genanki ebooklib

cd pipeline
python build_all.py            # regenerate knowledge/ + build/ (add --android for the APK)
python publish_site.py         # publish build/site to the gh-pages branch

cd ../apps/android && ./gradlew assembleDebug   # the Android app
```

Requires Python 3.11+, Node with `@mermaid-js/mermaid-cli` for diagram rendering
(results are cached under `build/`), and the Android SDK + a JDK for the app. See
`pipeline/README.md` for the individual stages and options.

## Grounding & conventions

- **Anchors** are `path:line` into the Jiuwen source and may drift as the code
  changes; they were verified to resolve when written, and their contents
  spot-checked. Where a mechanism is absent, config-gated, or inert, the entry
  says so rather than implying it works.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK
  plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/`
  layers. The product built on it is `jiuwenswarm/jiuwenswarm/`. Answers state
  which layer carries a mechanism.

## Source & provenance

The original documents are archived unchanged under `source/`. The numbered
sections were assembled from them: near-identical and same-concept material was
merged, so each concept appears once, and every entry lists its canonical source
and the other documents that covered it.
