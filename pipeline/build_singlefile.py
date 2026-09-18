#!/usr/bin/env python
"""Build ONE self-contained offline HTML study app from content.json (the
authored, layered model): Title -> Summary -> Key points -> Explanation ->
concept diagram -> Jiuwen (plain) -> Technical detail (expanded).

Browsers render Mermaid SVG correctly, so the HTML inlines SVG (crisp at any zoom).

Output: build/dist/jiuwen-knowledge-offline.html
Run with an interpreter that has `markdown` (the mkdocs venv does).
"""
import os
import re
import json
import html
import base64

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
ASSETS = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets")
DIST = os.path.join(ROOT, "build", "dist")
CONTENT = os.path.join(ASSETS, "content.json")

try:
    import markdown
    HAVE_MD = True
except Exception:
    HAVE_MD = False


def md(text):
    if not text:
        return ""
    if HAVE_MD:
        return markdown.markdown(text, extensions=["extra", "sane_lists", "tables"])
    return "<p>" + html.escape(text).replace("\n\n", "</p><p>") + "</p>"


def inline_img(rel):
    if not rel:
        return ""
    p = os.path.join(ASSETS, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        return ""
    data = base64.b64encode(open(p, "rb").read()).decode("ascii")
    return f'<div class="diagram"><img src="data:image/png;base64,{data}" alt="diagram"></div>'


def anchors_table(cites):
    if not cites:
        return ""
    rows = "".join(
        f'<tr><td class="a"><code>{html.escape(c.get("ref",""))}</code></td>'
        f'<td>{html.escape(c.get("desc",""))}</td></tr>'
        for c in cites
    )
    return f'<table class="anchors"><tbody>{rows}</tbody></table>'


def points_html(points):
    if not points:
        return ""
    items = "".join(f"<li>{html.escape(p)}</li>" for p in points)
    return f'<ul class="points">{items}</ul>'


CSS = """
:root{--fg:#17171c;--bg:#fff;--muted:#5b5b66;--line:#e3e3ea;--accent:#4c5bd4;--soft:#f6f7fb}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg)}
header{position:sticky;top:0;z-index:20;display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px 14px;background:var(--accent);color:#fff}
header h1{font-size:15px;margin:0;flex:1 1 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
header input{flex:0 1 260px;padding:8px 12px;border-radius:8px;border:0;font-size:14px}
header select{padding:8px;border-radius:8px;border:0;font-size:13px;max-width:200px}
header button{padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.6);background:transparent;color:#fff;font-size:13px;cursor:pointer}
main{max-width:860px;margin:0 auto;padding:18px}
h1.section{margin:30px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
h1.topic{margin:14px 0 8px;padding-top:10px;border-top:2px solid var(--line);font-size:21px}
.qa{background:var(--soft);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:14px 0}
.qa h2{font-size:17px;margin:0 0 8px;cursor:pointer}
.qa .title{display:inline-block;background:rgba(76,91,212,.14);color:var(--accent);border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;margin-bottom:4px}
.summary{font-size:15px;color:#333}
.points{margin:8px 0 0;padding-left:22px}.points li{margin:2px 0}
.answer{display:none}body.study .qa.revealed .answer{display:block}
body:not(.study) .answer{display:block}
.btn{display:inline-block;margin-top:8px;padding:8px 14px;border-radius:10px;background:var(--accent);color:#fff;border:0;cursor:pointer}
.section-t{color:var(--accent);font-weight:700;margin:12px 0 4px;font-size:14px}
details{margin:8px 0}summary{cursor:pointer;color:var(--accent);font-weight:600}
.diagram{text-align:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px;margin:8px 0}
.diagram svg{max-width:100%;height:auto}
.badges{margin:2px 0 6px}
.badge{display:inline-block;padding:1px 8px;margin-right:4px;border-radius:999px;border:1px solid #b9c0ef;color:var(--accent);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.tech-t{color:var(--accent);font-weight:700;margin:12px 0 4px;font-size:13px}
table.anchors{width:100%;border-collapse:collapse;font-size:12px}
table.anchors td{border-bottom:1px solid var(--line);padding:3px 6px;vertical-align:top}
table.anchors td.a{white-space:nowrap}
table.anchors code{font-size:11px;word-break:break-all}
.src{font-size:12px;color:var(--muted)}
mark{background:#ffe680}
"""


def build():
    data = json.load(open(CONTENT, encoding="utf-8"))
    parts, opts = [], []
    last_section = None
    for t in data["topics"]:
        tid = "t" + t["id"]
        opts.append(f'<option value="{tid}">{html.escape(t["title"])}</option>')
        section = t.get("section", "")
        if section and section != last_section:
            parts.append(f'<h1 class="section">{html.escape(section)}</h1>')
            last_section = section
        parts.append(f'<h1 class="topic" id="{tid}">{html.escape(t["title"])}</h1>')
        for q in t["questions"]:
            title = f'<div class="title">{html.escape(q["title"])}</div>' if q.get("title") else ""
            summary = f'<div class="summary">{html.escape(q.get("tldr",""))}</div>' if q.get("tldr") else ""
            mp = q.get("meta", {}) or {}
            db = mp.get("difficulty", "")
            badges = f'<div class="badges"><span class="badge">{html.escape(db)}</span></div>' if db else ""
            concept = "".join(inline_img(d.get("image", "")) for d in (q.get("diagrams") or [q.get("diagram", {})]))
            tech = inline_img(q.get("diagramTechnical", {}).get("image", ""))
            plain = q.get("jiuwenPlain", "")
            jiu = md(plain) or md(q.get("mechanism", ""))
            tech_text = q.get("mechanism", "") if plain else ""
            tparts = []
            if tech_text:
                tparts.append('<div class="tech-t">Implementation</div>' + md(tech_text))
            if tech:
                tparts.append('<div class="tech-t">Implementation diagram</div>' + tech)
            if q.get("citations"):
                tparts.append('<div class="tech-t">Code anchors</div>' + anchors_table(q["citations"]))
            tech_block = ""
            if tparts:
                tech_block = (
                    "<details><summary>Under the hood</summary>"
                    + "".join(tparts) + "</details>"
                )
            parts.append(
                f'<section class="qa"><h2>{html.escape(q["question"])}</h2>{badges}{title}{summary}'
                f'<button class="btn" onclick="this.parentElement.classList.toggle(\'revealed\')">Show / hide answer</button>'
                f'<div class="answer">{points_html(q.get("points", []))}'
                f'<div class="section-t">Concept</div>{md(q.get("explain",""))}'
                f'{concept}'
                f'<div class="section-t">In Jiuwen</div>{jiu}'
                f'{tech_block}'
                f'</div></section>'
            )
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jiuwen Knowledge Base - offline</title><style>{CSS}</style></head><body>
<header><h1>Jiuwen Knowledge Base</h1>
<select id="jump"><option value="">Jump to...</option>{''.join(opts)}</select>
<input id="q" placeholder="search questions...">
<button id="mode">Study mode</button></header>
<main>{''.join(parts)}</main>
<script>
var q=document.getElementById('q');
q.addEventListener('input',function(){{var t=q.value.toLowerCase();
 document.querySelectorAll('.qa').forEach(function(c){{c.style.display=!t||c.textContent.toLowerCase().indexOf(t)>=0?'':'none';}});}});
document.getElementById('jump').addEventListener('change',function(e){{if(e.target.value)location.hash=e.target.value;}});
var mode=document.getElementById('mode');var KEY='jq-study';
function setMode(v){{document.body.classList.toggle('study',v);localStorage.setItem(KEY,v?'1':'0');}}
setMode(localStorage.getItem(KEY)==='1');
mode.addEventListener('click',function(){{setMode(!document.body.classList.contains('study'));}});
document.querySelectorAll('.qa>h2').forEach(function(h){{h.addEventListener('click',function(){{h.parentElement.classList.toggle('revealed');}});}});
</script></body></html>"""
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "jiuwen-knowledge-offline.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"wrote {out} ({len(doc)//1024} KB, {sum(len(t['questions']) for t in data['topics'])} questions)")


if __name__ == "__main__":
    build()
