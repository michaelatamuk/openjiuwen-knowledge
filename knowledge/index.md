# Jiuwen AI-Engineering Knowledge Base

> Every concept answered twice: the general idea, and how the Jiuwen codebase
> actually implements it.

205 entries · 18 topics in 6 sections · readable as a website, EPUB, Anki deck, or offline Android app.

## Start here

- **Website** — [michaelatamuk.github.io/openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/) (search, navigation, dark mode)
- **On GitHub** — the same content as markdown in [`knowledge/`](#contents)
- **Download** — [latest release](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest): Android app, EPUB, single-file HTML, Anki deck, Obsidian vault
- **Build it** — see [Building](#building)

## How an entry reads

Each entry is layered so you can stop as soon as you have your answer:

1. **Title, Summary, Key points** — a ten-second pass.
2. **Explanation** — the framework-agnostic answer, plus a concept diagram.
3. **Jiuwen** — how this codebase implements it, in plain language (or an explicit "it doesn't").
4. **Jiuwen technical detail** — the classes, functions, and `file:line` anchors (this part is specific to the Jiuwen codebase).

A real entry looks like this:

> **What's the difference between a system prompt and a user prompt**
>
> **Summary.** The system prompt sets persistent role and rules; the user prompt is the per-turn request.
>
> **Explanation.** The system prompt sets persistent role, rules, persona, and constraints for the whole conversation; the user prompt is the per-turn request. Providers give the system message higher priority, and some APIs pass it as a separate top-level field.
>
> **Jiuwen.** Jiuwen assembles the system prompt as one string from priority-ordered, host-injectable sections; rails can add or remove sections before the model call, and the ReAct agent renders it once as a system message passed separately.
>
> **Technical detail.** `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:1504` — builds one `SystemMessage`; `anthropic_model_client.py:379` — lifts system into top-level blocks.

## Contents

### Model foundations (44)
- [LLM foundations](01-llm-foundations.md) — 15
- [Prompting and output control](02-prompting-and-output-control.md) — 6
- [LLM terms glossary](03-llm-terms-glossary.md) — 20
- [Choosing models and approaches](04-choosing-models-and-approaches.md) — 3

### Agents (51)
- [Agent fundamentals and the loop](05-agent-fundamentals-and-the-loop.md) — 11
- [Tools and function calling](06-tools-and-function-calling.md) — 10
- [Planning, memory and state](07-planning-memory-and-state.md) — 15
- [Agent frameworks](08-agent-frameworks.md) — 9
- [Multi-agent systems](09-multi-agent-systems.md) — 6

### RAG (60)
- [RAG pipelines and patterns](10-rag-pipelines-and-patterns.md) — 19
- [Retrieval and ranking](11-retrieval-and-ranking.md) — 11
- [Query understanding](12-query-understanding.md) — 6
- [RAG failure modes and evaluation](13-rag-failure-modes-and-evaluation.md) — 11
- [RAG system design](14-rag-system-design.md) — 13

### Evaluation and production (34)
- [Evaluation](15-evaluation.md) — 23
- [Production, cost and scale](16-production-cost-and-scale.md) — 11

### Model adaptation (6)
- [Fine-tuning and customization](17-fine-tuning-and-customization.md) — 6

### Safety and security (10)
- [Security and safety](18-security-and-safety.md) — 10

## Formats

- **Website** — [openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/), built with MkDocs Material.
- **Markdown** — `knowledge/` in this repository, one file per section.
- **Single-file HTML** — one offline file with search and tap-to-reveal answers.
- **EPUB** — for e-readers.
- **Anki deck / CSV** — spaced repetition in Anki or AnkiDroid.
- **Obsidian vault** — linked notes with local search.
- **Android app** — native offline study app (Kotlin, Room, FSRS).

Everything except the website is attached to the [latest release](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest).

## Repository layout

```
openjiuwen-knowledge/
├── knowledge/              the compiled knowledge base — read these
│   ├── *.md                one file per section
│   ├── index.md            this README, rendered as the site home
│   └── assets/diagrams/    rendered diagrams
├── content/                authored source
│   ├── topics/             the section documents
│   ├── summaries/          per-section Title / Summary / Key points
│   ├── jiuwen/             per-section plain-language Jiuwen answers
│   └── diagrams.json       concept-vs-technical diagram assignments
├── source/                 the 18 original documents, archived unchanged
├── pipeline/               build and publish scripts, MkDocs config
├── apps/android/           the native offline study app
└── build/                  generated artifacts (gitignored)
```

`knowledge/` is generated from `content/` and committed, so the readable version
is available directly on GitHub. `build/` is disposable.

## Building

```bash
# one-time toolchain
uv venv .venv
uv pip install --python .venv/Scripts/python.exe mkdocs-material genanki ebooklib

cd pipeline
python build_all.py            # regenerate knowledge/ and build/ (--android also builds the APK)
python publish_site.py         # publish build/site to the gh-pages branch

cd ../apps/android && ./gradlew assembleDebug   # the Android app
```

Requires Python 3.11+, Node with `@mermaid-js/mermaid-cli` (diagram rendering is
cached under `build/`), and the Android SDK plus a JDK for the app. Individual
stages are documented in `pipeline/README.md`.

## Grounding and provenance

- **Anchors** are `path:line` into the Jiuwen source. They may drift as the code
  changes; they were verified to resolve when written, and their contents
  spot-checked. Where a mechanism is absent, config-gated, or inert, the entry
  says so rather than implying it works.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK
  plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/`
  layers. The product built on it is `jiuwenswarm/jiuwenswarm/`. Answers say
  which layer carries a mechanism.
- **Originals.** The 18 source documents are archived unchanged under `source/`.
  The sections were assembled from them: near-identical and same-concept material
  was merged, so each concept appears once, and every entry names its canonical
  source.
