# Jiuwen AI-Engineering Knowledge Base

> Every concept answered twice: the general idea, and how the Jiuwen codebase
> actually implements it.

Readable as a website, EPUB, Anki deck, or offline Android app.

## Start here

- **Website** — [michaelatamuk.github.io/openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/) (search, navigation, dark mode)
- **On GitHub** — the same content as markdown in [`knowledge/`](#contents)
- **Download** — [latest release](https://github.com/michaelatamuk/openjiuwen-knowledge/releases/latest): Android app, EPUB, single-file HTML, Anki deck, Obsidian vault
- **Build it** — see [Building](#building)

## How to read an entry

Each entry is layered so you can stop as soon as you have your answer:

1. **Title, TL;DR, Key points** — a ten-second pass.
2. **Concept** — the framework-agnostic explanation, plus a concept diagram.
3. **In Jiuwen** — how this codebase implements the mechanism, in plain language.
4. **Under the hood** — the implementation detail, diagram, and `file:line` anchors.

A real entry looks like this:

> **What's the difference between a system prompt and a user prompt**
>
> **TL;DR.** The system prompt sets persistent role and rules; the user prompt is the per-turn request.
>
> **Key points.**
>
> - The system prompt carries persistent role, persona, and constraints; the user prompt is the per-turn request.
> - Providers give the system message higher priority; some APIs pass it as a separate top-level field.
> - Keep stable rules in the system prompt and per-turn content in the user prompt.
>
> **Concept.** The system prompt sets persistent role, rules, persona, and constraints for the whole conversation; the user prompt is the per-turn request. Providers give the system message higher priority, and some APIs pass it as a separate top-level field.
>
> **In Jiuwen.** Jiuwen assembles the system prompt as one string from priority-ordered, host-injectable sections; rails can add or remove sections before the model call, and the ReAct agent renders it once as a system message passed separately.
>
> **Under the hood.** `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:1504` — builds one `SystemMessage`; `anthropic_model_client.py:379` — lifts system into top-level blocks.

## Contents

### Part I — Building with agents

#### The agent
- [Agent fundamentals and the loop](knowledge/05-agent-fundamentals-and-the-loop.md)
- [Agent frameworks](knowledge/08-agent-frameworks.md)

#### What the agent uses
- [Tools and function calling](knowledge/06-tools-and-function-calling.md)
- [Planning, memory and state](knowledge/07-planning-memory-and-state.md)

#### Multiple agents
- [Multi-agent systems](knowledge/09-multi-agent-systems.md)

#### Making agents reliable
- [Agent failure modes](knowledge/22-agent-failure-patterns.md)
- [Evaluation](knowledge/15-evaluation.md)

#### Running agents
- [Production, cost and scale](knowledge/16-production-cost-and-scale.md)
- [Model routing and gateways](knowledge/24-ai-gateway.md)

#### Securing agents
- [Security and safety](knowledge/18-security-and-safety.md)

### Part II — Under the hood

#### The model
- [LLM foundations](knowledge/01-llm-foundations.md)
- [AI system stack](knowledge/20-ai-system-stack.md)
- [Foundational papers](knowledge/19-foundational-papers.md)

#### Working with the model
- [Prompting and output control](knowledge/02-prompting-and-output-control.md)
- [Choosing models and approaches](knowledge/04-choosing-models-and-approaches.md)
- [Fine-tuning and customization](knowledge/17-fine-tuning-and-customization.md)
- [Cost, latency and accuracy tradeoffs](knowledge/23-cost-latency-accuracy.md)

#### Retrieval internals
- [RAG pipelines and patterns](knowledge/10-rag-pipelines-and-patterns.md)
- [Retrieval and ranking](knowledge/11-retrieval-and-ranking.md)
- [Query understanding](knowledge/12-query-understanding.md)
- [RAG system design](knowledge/14-rag-system-design.md)
- [RAG failure modes and evaluation](knowledge/13-rag-failure-modes-and-evaluation.md)

#### Background
- [ML foundations](knowledge/00-ml-foundations.md)
- [LLM terms glossary](knowledge/03-llm-terms-glossary.md)

## Formats

- **Website** — [openjiuwen-knowledge](https://michaelatamuk.github.io/openjiuwen-knowledge/), built with MkDocs Material.
- **Markdown** — `knowledge/` in this repository, one file per section.
- **Single-file HTML** — one offline file with search and expandable detail.
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
│   ├── summaries/          per-section Title / TL;DR / Key points
│   ├── jiuwen/             per-section plain-language Jiuwen answers
│   └── diagrams.json       concept-vs-technical diagram assignments
├── source/                 the 26 original documents, archived unchanged
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

## Provenance

- **Anchors** are `path:line` into the Jiuwen source.
- **Layers.** "The framework" is `agent-core/openjiuwen` — the thin `core/` SDK
  plus the heavier `harness/`, `agent_teams/`, `extensions/`, and `auto_harness/`
  layers. The product built on it is `jiuwenswarm/jiuwenswarm/`.
- **Originals.** The 26 source documents are archived under `source/`.
