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
    "03": "03-rag-and-retrieval", "04": "04-rag-system-design",
    "05": "05-agents-tools-and-memory", "06": "06-evaluation",
    "07": "07-production-cost-and-scale", "08": "08-security-and-safety",
    "09": "09-fine-tuning-and-customization", "10": "10-general-engineering",
    "90": "90-llm-terms-glossary", "91": "91-ai-engineer-interview-patterns",
    "92": "92-llm-interview-patterns", "93": "93-llm-architecture-patterns",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def anchors_md(cites):
    if not cites:
        return ""
    parts = []
    for c in cites:
        ref = c.get("ref", "")
        desc = c.get("desc", "")
        parts.append(f"&bull; `{ref}`" + (f" — {desc}" if desc else ""))
    return "<br>".join(parts)


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
            if tech_text or q.get("citations") or tech_img:
                lines.append("<details open>")
                lines.append("<summary><b>Technical detail (classes &amp; functions)</b></summary>")
                lines.append("")
                if tech_text:
                    lines += [tech_text, ""]
                if q.get("citations"):
                    lines += [f"<sub>{anchors_md(q['citations'])}</sub>", ""]
                if tech_img:
                    lines += [tech_img, ""]
                lines.append("</details>")
                lines.append("")
            if q.get("provenance", {}).get("sources"):
                srcs = ", ".join(f"`{s}`" for s in q["provenance"]["sources"])
                lines += [f"<sub>_Canonical source: {srcs}_</sub>", ""]
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
