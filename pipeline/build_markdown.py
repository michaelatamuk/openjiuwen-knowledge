#!/usr/bin/env python
"""Generate layered markdown from content.json (single source of truth).

Writes knowledge/<id>-<slug>.md + index.md + assets/diagrams/*.png, so the
MkDocs site, the Obsidian vault and GitHub all show Title -> Summary -> Key
points -> Explanation -> concept diagram -> Jiuwen (plain) -> Technical detail.
"""
import os
import re
import json
import html
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
ASSETS = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets")
OUT = os.path.join(ROOT, "knowledge")
CONTENT = os.path.join(ASSETS, "content.json")

FNAME = {
    "01": "01-llm-foundations", "02": "02-prompting-and-output-control",
    "03": "03-llm-terms-glossary", "04": "04-choosing-models-and-approaches",
    "05": "05-agent-fundamentals-and-the-loop", "06": "06-tools-and-function-calling",
    "07": "07-planning-memory-and-state", "08": "08-agent-frameworks",
    "09": "09-multi-agent-systems", "10": "10-rag-pipelines-and-patterns",
    "11": "11-retrieval-and-ranking", "12": "12-query-understanding",
    "13": "13-rag-failure-modes-and-evaluation", "14": "14-rag-system-design",
    "15": "15-evaluation", "16": "16-production-cost-and-scale",
    "17": "17-fine-tuning-and-customization", "18": "18-security-and-safety",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def anchors_md(cites):
    if not cites:
        return ""
    rows = ["| Code anchor | What it points to |", "|---|---|"]
    for c in cites:
        ref = c.get("ref", "")
        desc = (c.get("desc", "") or "").replace("|", "\\|")
        rows.append(f"| `{ref}` | {desc} |")
    return "\n".join(rows)


def write_diagram(rel):
    if not rel:
        return ""
    src = os.path.join(ASSETS, rel.replace("/", os.sep))
    if not os.path.isfile(src):
        return ""
    name = os.path.basename(rel)
    dst_dir = os.path.join(OUT, "assets", "diagrams")
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(dst_dir, name))
    return f"![diagram](assets/diagrams/{name})"


def main():
    data = json.load(open(CONTENT, encoding="utf-8"))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    for t in data["topics"]:
        lines = [f"# {t['title']}", ""]
        for i, q in enumerate(t["questions"], 1):
            lines.append(f"## {i}. {q['question']}")
            lines.append("")
            if q.get("title"):
                lines += [f"**Title.** {q['title']}", ""]
            if q.get("tldr"):
                lines += [f"**Summary.** {q['tldr']}", ""]
            if q.get("points"):
                lines.append("**Key points.**")
                lines.append("")
                for p in q["points"]:
                    lines.append(f"- {p}")
                lines.append("")
            if q.get("explain"):
                lines += [f"**General.** {q['explain']}", ""]
            for d in (q.get("diagrams") or [q.get("diagram", {})]):
                im = write_diagram(d.get("image", "") or d.get("svg", ""))
                if im:
                    lines += [im, ""]
            plain = q.get("jiuwenPlain") or ""
            jiu = plain or q.get("mechanism") or ""
            if jiu:
                lines += [f"**Jiuwen.** {jiu}", ""]
            tech_img = write_diagram((q.get("diagramTechnical", {}) or {}).get("image", "")
                                     or (q.get("diagramTechnical", {}) or {}).get("svg", ""))
            tech_text = q.get("mechanism", "") if plain else ""
            sources = q.get("provenance", {}).get("sources") or []
            if tech_text or q.get("citations") or tech_img or sources:
                lines.append('<details markdown="1">')
                lines.append("<summary><b>Jiuwen technical detail (classes &amp; functions)</b></summary>")
                lines.append("")
                if tech_text:
                    lines += ["**Implementation**", "", tech_text, ""]
                if q.get("citations"):
                    lines += ["**Code anchors**", "", anchors_md(q["citations"]), ""]
                if tech_img:
                    lines += ["**Implementation diagram**", "", tech_img, ""]
                if sources:
                    srcs = ", ".join(f"`{s}`" for s in sources)
                    lines += ["**Canonical source**", "", f"<sub>{srcs}</sub>", ""]
                lines.append("</details>")
                lines.append("")
            lines += ["---", ""]
        fname = FNAME.get(t["id"], f"{t['id']}-{slug(t['title'])}") + ".md"
        open(os.path.join(OUT, fname), "w", encoding="utf-8", newline="\n").write("\n".join(lines).rstrip() + "\n")

    readme = os.path.join(ROOT, "README.md")
    if os.path.isfile(readme):
        text = open(readme, encoding="utf-8").read()
        text = (text.replace("](README.md)", "](index.md)")
                    .replace("](source/README.md)", "](index.md)")
                    .replace("](knowledge/", "]("))
        open(os.path.join(OUT, "index.md"), "w", encoding="utf-8", newline="\n").write(text)
    print(f"wrote {len(data['topics'])} markdown files to {OUT}")


if __name__ == "__main__":
    main()
