#!/usr/bin/env python
"""Build Anki cards from content.json (the authored, layered model).

Front: question. Back: key points + summary + explanation + concept diagram +
Jiuwen (plain) + technical detail (expanded). Concept diagrams are embedded PNGs.

Outputs (build/dist/): jiuwen-knowledge.apkg, jiuwen-knowledge-anki.csv
"""
import os
import re
import json
import html
import hashlib

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
    return "<p>" + html.escape(text) + "</p>"


def points(points_):
    if not points_:
        return ""
    return "<ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in points_) + "</ul>"


def diagram_img(rel):
    if not rel:
        return ""
    return f'<div style="text-align:center"><img src="{os.path.basename(rel)}" style="max-width:100%"></div>'


def main():
    data = json.load(open(CONTENT, encoding="utf-8"))
    media = {}
    cards = []
    for t in data["topics"]:
        for q in t["questions"]:
            concept = q.get("diagram", {}) or {}
            tech = q.get("diagramTechnical", {}) or {}
            img = ""
            for c in (q.get("diagrams") or [concept]):
                if c.get("image"):
                    p = os.path.join(ASSETS, c["image"].replace("/", os.sep))
                    if os.path.isfile(p):
                        media[os.path.basename(p)] = p
                        img += diagram_img(c["image"])
            tech_html = ""
            plain = q.get("jiuwenPlain", "")
            tech_text = q.get("mechanism", "") if plain else ""
            if tech_text or q.get("citations") or tech.get("image"):
                cites = "".join(
                    f'<div><code>{html.escape(c.get("ref",""))}</code> {html.escape(c.get("desc",""))}</div>'
                    for c in q.get("citations", [])
                )
                tech_img = ""
                if tech.get("image"):
                    tp = os.path.join(ASSETS, tech["image"].replace("/", os.sep))
                    if os.path.isfile(tp):
                        media[os.path.basename(tp)] = tp
                        tech_img = diagram_img(tech["image"])
                tech_html = (
                    "<details open><summary>Technical detail (classes &amp; functions)</summary>"
                    + md(tech_text) + cites + tech_img + "</details>"
                )
            title = f'<div style="color:#4c5bd4;font-weight:700;font-size:13px">{html.escape(q["title"])}</div>' if q.get("title") else ""
            summary = f'<p style="color:#333">{html.escape(q.get("tldr",""))}</p>' if q.get("tldr") else ""
            back = (
                title + summary + points(q.get("points", []))
                + "<h4>Explanation</h4>" + md(q.get("explain", ""))
                + img
                + "<h4>Jiuwen</h4>" + (md(q.get("jiuwenPlain", "")) or md(q.get("mechanism", "")))
                + tech_html
            )
            section = t.get("section", "")
            topic_label = (section + " · " if section else "") + t["title"] + " · " + t["id"]
            cards.append({"q": q["question"], "topic": topic_label, "a": back})

    os.makedirs(DIST, exist_ok=True)
    import csv
    with open(os.path.join(DIST, "jiuwen-knowledge-anki.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Question", "Topic", "Answer"])
        for c in cards:
            w.writerow([c["q"], c["topic"], c["a"]])

    try:
        import genanki
    except Exception:
        print("genanki not installed; CSV written")
        return
    mid = int(hashlib.sha1(b"jiuwen-qa-v2").hexdigest()[:8], 16)
    did = int(hashlib.sha1(b"jiuwen-knowledge-base").hexdigest()[:8], 16)
    model = genanki.Model(
        mid, "Jiuwen Knowledge Q&A",
        fields=[{"name": "Question"}, {"name": "Topic"}, {"name": "Answer"}],
        templates=[{
            "name": "Recall",
            "qfmt": '<div style="color:#3f51b5;font-size:12px;font-weight:700">{{Topic}}</div><div style="font-size:18px;font-weight:600">{{Question}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:16px;text-align:left;background:#fff;color:#222;line-height:1.5}code{background:#f2f2f2;padding:1px 4px;border-radius:4px}details{margin-top:8px}",
    )
    deck = genanki.Deck(did, "Jiuwen Knowledge Base")
    for c in cards:
        guid = hashlib.sha1((c["topic"] + "|" + c["q"]).encode("utf-8")).hexdigest()
        deck.add_note(genanki.Note(model=model, guid=guid, fields=[c["q"], c["topic"], c["a"]]))
    pkg = genanki.Package(deck)
    pkg.media_files = list(media.values())
    pkg.write_to_file(os.path.join(DIST, "jiuwen-knowledge.apkg"))
    print(f"wrote apkg + csv ({len(cards)} cards, {len(media)} images)")


if __name__ == "__main__":
    main()
