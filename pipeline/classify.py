#!/usr/bin/env python
"""Assign a difficulty label to every entry (basic / intermediate /
advanced) and write content/classification.json.

Heuristic first pass; see content/classification.md for the rubric. Edit the
output or the heuristics to tune.
"""
import os
import re
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, "content")
IN = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets", "content.json")
OUT_JSON = os.path.join(CONTENT, "classification.json")
OUT_MD = os.path.join(CONTENT, "classification.proposed.md")

FOUNDATIONAL = re.compile(
    r"^(what is|what's|what are|what does|why does|why is|define|"
    r"what's the difference|what is the difference)\b", re.I)
ADVANCED = re.compile(
    r"\bdesign\b|how would you|scale|10x|multi-tenant|failure mode|debug|"
    r"rollback|trade-?off|overkill|migrat|throttl|budget|shard|partition|"
    r"latency budget|cost per query|eval set|regression suite", re.I)

# Curated corrections applied after the heuristic (id -> difficulty).
OVERRIDES = {
    "01-1": "intermediate",   # definition + cost/context, not a design task
    "01-7": "intermediate",
}


def difficulty(topic: str, text: str) -> str:
    if topic == "03":            # glossary
        return "basic"
    if ADVANCED.search(text):
        return "advanced"
    if FOUNDATIONAL.search(text):
        return "basic"
    return "intermediate"


def main():
    data = json.load(open(IN, encoding="utf-8"))
    rows = []
    for t in data["topics"]:
        for q in t["questions"]:
            d = OVERRIDES.get(q["id"]) or difficulty(t["id"], q["question"])
            rows.append({"id": q["id"], "topic": t["id"], "section": t["section"],
                         "difficulty": d, "question": q["question"]})

    json.dump({r["id"]: r["difficulty"] for r in rows},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lines = ["# Classification — DRAFT for review", "",
             "Difficulty labels from a heuristic first pass. See "
             "`content/classification.md` for the rubric.", ""]
    cur = None
    for r in rows:
        if r["topic"] != cur:
            cur = r["topic"]
            lines += ["", f"## {r['topic']} · {r['section']}", "",
                      "| id | difficulty | question |", "|---|---|---|"]
        qtext = r["question"].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['difficulty']} | {qtext} |")
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(lines).rstrip() + "\n")

    from collections import Counter
    print("total:", len(rows), "difficulty:", dict(Counter(r["difficulty"] for r in rows)))
    print("wrote", os.path.relpath(OUT_JSON, ROOT), "and", os.path.relpath(OUT_MD, ROOT))


if __name__ == "__main__":
    main()
