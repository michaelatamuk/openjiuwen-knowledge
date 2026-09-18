# Offline study kit — build pipeline

`knowledge/` (the readable knowledge base) and everything under `build/` are
generated from `../content/topics` (plus the authored layers in
`../content/summaries`, `../content/jiuwen`, and `../content/diagrams.json`).
`knowledge/` is committed; `build/` is disposable and gitignored. It is designed
to be read **offline / on a plane** on both Windows and Android.

## Layout

| Path | Role |
|---|---|
| `content/topics/*.md` | the question bank (source of truth) |
| `content/summaries/*.json` | authored title / summary / key points, per topic |
| `content/jiuwen/*.json` | authored plain-language Jiuwen answers, per topic |
| `content/diagrams.json` | concept-vs-technical diagram assignments |
| `knowledge/*.md` | the compiled, layered knowledge base (committed) |
| `pipeline/` | these build scripts + `mkdocs.yml` |
| `apps/android/` | native offline study app (consumes `content.json`) |
| `build/` | every generated artifact (gitignored) |

## Artifacts

| Artifact | Path | Use |
|---|---|---|
| **Single-file HTML app** | `build/dist/jiuwenswarm-interview-offline.html` | Best phone/plane option: one file, no server, no internet. Search, tap-to-reveal, dark/light. |
| **Offline website** | `build/site/index.html` | Desktop reading (MkDocs Material): nav, search, dark mode. Fully local. |
| **Anki deck** | `build/dist/jiuwen-interview.apkg` | Spaced repetition (Anki / AnkiDroid). |
| **Anki CSV** | `build/dist/jiuwen-interview-anki.csv` | Same cards as plain import. |
| **EPUB** | `build/dist/jiuwenswarm-interview.epub` | E-readers. |
| **Obsidian vault** | `build/interview_questions-vault.zip` | Open as a vault: one note per topic. |
| **App content** | `apps/android/app/src/main/assets/content.json` | Consumed by the Android app. |

## Build

One command rebuilds everything:

```bash
# one-time toolchain (isolated venv)
uv venv .venv
uv pip install --python .venv/Scripts/python.exe mkdocs-material genanki ebooklib

# rebuild all artifacts (add --android to also build the APK)
python build_all.py
python build_all.py --android
```

`build_all.py` picks the doc interpreter from `$MKDOCS_PYTHON` or `.venv/` and
runs, in order: `build_content_json.py` → `build_study.py` →
`build_singlefile.py` → `anki_export.py` → `build_epub.py` → `build_vault.py`.
Flags: `--no-content` (reuse existing `content.json`), `--svg-budget=N`
(`0` = cache-only), `--android`.

Run a single stage directly if you prefer:

```bash
python build_content_json.py   # content.json + diagrams  (needs mmdc on PATH or $MMDC)
python build_study.py          # knowledge -> build/docs, site -> build/site (+ site zip)
python build_singlefile.py     # single-file HTML
python anki_export.py          # Anki .apkg + csv
python build_epub.py           # EPUB
python build_vault.py          # Obsidian vault zip
```

`build_markdown.py` writes the compiled knowledge base to `knowledge/` (committed).
`build_study.py` copies `knowledge/` into `build/docs`, so `build/` is disposable
and gitignored.

Helpers: `lint_mermaid.py` (Mermaid syntax check), `diagram_audit.py`
(concept-vs-Jiuwen report → `build/diagram_audit.csv`), `serve.py` (serve
`build/site`), `reorder.py` (historical; already applied).

## Publish (GitHub Pages)

The built site is published to the `gh-pages` branch and served at
https://michaelatamuk.github.io/openjiuwen-knowledge/.

```bash
python build_study.py     # build/site must exist
python publish_site.py    # force-pushes build/site to origin gh-pages
```

## Read it

**Windows**
- Read: open `build/dist/jiuwenswarm-interview-offline.html`, or the site at `build/site/index.html`.
- Spaced repetition: install Anki, `File -> Import` the `.apkg` (or the CSV).

**Android**
- Copy `build/dist/jiuwenswarm-interview-offline.html` to the phone and open it
  in Chrome (works with no network).
- Spaced repetition: install **AnkiDroid**, open the `.apkg`, sign in to AnkiWeb
  to sync with desktop.
- Alternative readers: **Obsidian** (open the vault zip) or **Markor**.

## Read the wiki on Android (offline)

The wiki is `build/site/` — one page per topic. Pick one:

1. **Local HTTP server (full search).** Build once, then:
   - Desktop: `python serve.py` and open `http://localhost:8000/`.
   - Phone on the same Wi-Fi: open the LAN URL `serve.py` prints.
   - Fully offline on the phone: install **Termux**, copy `build/dist/jiuwenswarm-site.zip`
     (or the `build/site/` folder) over, then `pkg install python` and
     `python -m http.server 8000`; open `http://localhost:8000/`.
   - *Why a server:* Android opens local HTML through `content://` URIs, which
     breaks relative links between topic pages. A localhost server fixes
     navigation **and** makes search work.
2. **PWA (nicest phone feel).** Host `build/site/` on any static host, open it in
   Chrome, then *Add to Home screen* — an offline, app-like wiki.
3. **Obsidian (no build).** Open `build/interview_questions-vault.zip` as a vault:
   separate notes per topic, links, search, fully offline.

## Study features

- **Study mode** toggles hiding of every answer; tap a question to reveal it.
- **Search** filters questions as you type.
- **Jump to topic** dropdown for quick navigation.
- Progress is not tracked (keep it stateless); use Anki for retention tracking.
