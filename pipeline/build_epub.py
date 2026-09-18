#!/usr/bin/env python
"""Build an EPUB3 from content.json (the authored, layered model).

Title -> Summary -> Key points -> Explanation -> concept diagram -> Jiuwen
(plain) -> Technical detail (as a labeled section; EPUB readers don't reliably
support <details>). Diagrams are embedded PNGs.

Output: build/dist/jiuwen-knowledge.epub
"""
import os
import re
import json
import html
import hashlib

try:
    import markdown
    from ebooklib import epub
except Exception as e:
    raise SystemExit("needs markdown + ebooklib: " + str(e))

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
ASSETS = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets")
DIST = os.path.join(ROOT, "build", "dist")
CONTENT = os.path.join(ASSETS, "content.json")

CSS = """
body{font-family:serif;line-height:1.5}
h1{font-size:1.5em;border-bottom:1px solid #ccc;padding-bottom:.2em}
h2{font-size:1.15em;margin-top:1.1em}
h3{font-size:1em;color:#4c5bd4;margin:.8em 0 .2em}
.title{color:#4c5bd4;font-weight:700;font-size:.85em}
.summary{font-style:italic;color:#333}
code{font-family:monospace;background:#f2f2f2;padding:0 2px}
.diagram{text-align:center;margin:.6em 0}.diagram img{max-width:100%}
.cite{font-size:.8em;color:#555}
h4{font-size:.9em;color:#4c5bd4;margin:.7em 0 .15em}
table.anchors{width:100%;border-collapse:collapse;font-size:.8em}
table.anchors td{border-bottom:1px solid #ddd;padding:2px 4px;vertical-align:top}
table.anchors td.a{white-space:nowrap}
table.anchors code{font-size:.85em;word-break:break-all}
"""


def md(t):
    return markdown.markdown(t, extensions=["extra", "sane_lists", "tables"]) if t else ""


def main():
    data = json.load(open(CONTENT, encoding="utf-8"))
    book = epub.EpubBook()
    book.set_identifier("jiuwen-knowledge-base")
    book.set_title("Jiuwen Knowledge Base")
    book.set_language("en")
    book.add_author("Jiuwenswarm")
    style = epub.EpubItem(uid="style", file_name="style/main.css", media_type="text/css", content=CSS)
    book.add_item(style)

    images = {}
    chapters, toc_groups = [], {}
    for t in data["topics"]:
        fname = f"{t['id']}-{re.sub(r'[^a-z0-9]+','-',t['title'].lower()).strip('-')}.xhtml"
        parts = [f"<h1>{html.escape(t['title'])}</h1>"]
        links = []
        for q in t["questions"]:
            qid = "q" + q["id"].replace("-", "_")
            links.append(epub.Link(fname + "#" + qid, q["question"][:80], qid))
            title = f'<div class="title">{html.escape(q["title"])}</div>' if q.get("title") else ""
            summary = f'<div class="summary">{html.escape(q.get("tldr",""))}</div>' if q.get("tldr") else ""
            pts = ("<ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in q.get("points", [])) + "</ul>") if q.get("points") else ""
            concept = ""
            for c in (q.get("diagrams") or [q.get("diagram", {}) or {}]):
                if c.get("image"):
                    p = os.path.join(ASSETS, c["image"].replace("/", os.sep))
                    if os.path.isfile(p):
                        images[os.path.basename(p)] = p
                        concept += f'<div class="diagram"><img src="images/{os.path.basename(p)}"/></div>'
            tech = ""
            plain = q.get("jiuwenPlain", "")
            tech_text = q.get("mechanism", "") if plain else ""
            sources = q.get("provenance", {}).get("sources") or []
            td = q.get("diagramTechnical", {}) or {}
            if tech_text or q.get("citations") or sources or td.get("image"):
                tparts = ["<h3>Jiuwen technical detail (classes &amp; functions)</h3>"]
                if tech_text:
                    tparts.append("<h4>Implementation</h4>" + md(tech_text))
                if q.get("citations"):
                    rows = "".join(
                        f'<tr><td class="a"><code>{html.escape(x.get("ref",""))}</code></td>'
                        f'<td>{html.escape(x.get("desc",""))}</td></tr>'
                        for x in q.get("citations", []))
                    tparts.append("<h4>Code anchors</h4><table class='anchors'>" + rows + "</table>")
                if td.get("image"):
                    tp = os.path.join(ASSETS, td["image"].replace("/", os.sep))
                    if os.path.isfile(tp):
                        images[os.path.basename(tp)] = tp
                        tparts.append("<h4>Implementation diagram</h4>"
                                      f'<div class="diagram"><img src="images/{os.path.basename(tp)}"/></div>')
                if sources:
                    tparts.append("<h4>Canonical source</h4><div class='cite'>"
                                  + "".join(f'<code>{html.escape(s)}</code> ' for s in sources) + "</div>")
                tech = "".join(tparts)
            parts.append(
                f'<h2 id="{qid}">{html.escape(q["question"])}</h2>{title}{summary}{pts}'
                f'<h3>Explanation</h3>{md(q.get("explain",""))}{concept}'
                f'<h3>Jiuwen</h3>{md(q.get("jiuwenPlain","")) or md(q.get("mechanism",""))}{tech}'
            )
        ch = epub.EpubHtml(title=t["title"], file_name=fname, lang="en")
        ch.content = "".join(parts)
        ch.add_item(style)
        book.add_item(ch)
        chapters.append(ch)
        toc_groups.setdefault(t.get("section", "") or t["title"], []).append(
            (epub.Section(t["title"]), links))

    for name, p in images.items():
        with open(p, "rb") as fh:
            book.add_item(epub.EpubItem(uid="img_" + hashlib.sha1(name.encode()).hexdigest()[:10],
                                        file_name="images/" + name, media_type="image/png", content=fh.read()))
    book.toc = [(epub.Section(section), items) for section, items in toc_groups.items()]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "jiuwen-knowledge.epub")
    epub.write_epub(out, book)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, {len(chapters)} chapters, {len(images)} images)")


if __name__ == "__main__":
    main()
