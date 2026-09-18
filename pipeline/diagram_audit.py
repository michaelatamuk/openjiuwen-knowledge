#!/usr/bin/env python
"""Audit every question's diagrams: concept vs Jiuwen-specific, and what it should be.

Writes build/diagram_audit.csv and prints a summary + the questions that still
show a Jiuwen-specific diagram in the concept slot (i.e. need a concept diagram
authored and the Jiuwen one demoted to Technical detail).
"""
import os
import re
import json
import csv

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # .../interview_questions
CONTENT = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets", "content.json")
BUILD = os.path.join(ROOT, "build")

TECH = re.compile(
    r"[a-z_]+\.py|agent-core|jiuwenswarm/|Manager|Counter|Processor|Rail|Client|Store|"
    r"Indexer|Retriever|Config|Schema|Provider|Handler|Executor|Builder|Pipeline|"
    r"Channel|Buffer|Registry|Adapter|Factory|Dispatcher|Controller|Service|Resolver"
)


def tech(labels):
    return bool(TECH.search(" ".join(labels)))


def main():
    data = json.load(open(CONTENT, encoding="utf-8"))
    rows = []
    for t in data["topics"]:
        for q in t["questions"]:
            ds = q.get("diagrams") or ([q["diagram"]] if q.get("diagram", {}).get("image") else [])
            kinds = []
            for d in ds:
                kinds.append("jiuwen" if tech(x.get("label", "") for x in d.get("nodes", [])) else "concept")
            has_tech = bool((q.get("diagramTechnical") or {}).get("image"))
            if not ds:
                verdict = "NONE"
            elif has_tech:
                verdict = "ok (concept shown + jiuwen hidden)"
            elif "jiuwen" in kinds and "concept" not in kinds:
                verdict = "FIX: jiuwen shown as concept -> author concept + demote"
            elif "concept" in kinds and "jiuwen" not in kinds:
                verdict = "concept only (ok)"
            else:
                verdict = "mixed concept/jiuwen shown"
            rows.append({
                "id": q["id"], "section": t["id"] + " " + t["title"][:28],
                "question": q["question"][:70], "n_diagrams": len(ds),
                "kinds": "+".join(kinds) if kinds else "-",
                "has_hidden_tech": has_tech, "verdict": verdict,
            })

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "diagram_audit.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    c = Counter(r["verdict"] for r in rows)
    print("total:", len(rows))
    for k, v in c.most_common():
        print(f"  {v:3d}  {k}")
    print("\n-- still showing a Jiuwen diagram as concept --")
    for r in rows:
        if r["verdict"].startswith("FIX"):
            print(f"  {r['id']}  {r['question']}")


if __name__ == "__main__":
    main()
