# Classification rubric

One axis: **difficulty**. (An "importance" axis was tried and dropped — it came
out ~83% "must-know", so it carried no information.)

## Difficulty

| Level | What it means | Anchors |
|---|---|---|
| **foundational** | Recall / definition / recognition. One concept, no tradeoff. | "What is X?", "What's the difference between A and B?", glossary terms, single facts. |
| **intermediate** | Explain a mechanism or standard practice; one system, known pattern. | "How does X work?", "How do you handle Y?", typical pipeline steps, single-tool questions. |
| **advanced** | Open design, multi-component synthesis, tradeoffs, scale/failure analysis. | "Design …", "How would you …", scaling, debugging across agents, failure modes, cost/latency budgets. |

Rules of thumb:
- Difficulty is about **how much reasoning**, not **how deep into code**. A
  `mechanism` question can be foundational/intermediate.
- Do not derive it from `type` alone.

## Field on each entry (target shape)

```json
"meta": { "difficulty": "foundational | intermediate | advanced", "tags": ["<topic-id>"] }
```

## Workflow

1. `python pipeline/classify.py` writes `content/classification.json` (id →
   difficulty) plus a readable `content/classification.proposed.md`.
2. Edit the values (or the heuristics / `OVERRIDES`) to correct mistakes.
3. `build_content_json.py` merges them into each entry's `meta.difficulty`,
   surfaced as a badge in the site/HTML/EPUB/app and as an Anki tag.
