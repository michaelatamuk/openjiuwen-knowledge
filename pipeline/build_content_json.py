#!/usr/bin/env python
"""Convert the knowledge markdown docs into a TYPED, LAYERED content.json (v2)
for the native Android app, plus DIAGRAM assets.

Diagrams now ship as SVG (light + dark) with parsed node geometry so the app can
highlight nodes, tap-to-inspect, and tint by theme. No Mermaid runtime is used.

Output: apps/android/app/src/main/assets/content.json (+ diagrams/)
"""
import os
import re
import glob
import json
import html
import hashlib
import shutil
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
OUT = os.path.join(ROOT, "apps", "android", "app", "src", "main", "assets")
SVG_CACHE = os.path.join(ROOT, "build", ".mmd-cache")
PNG_CACHE = os.path.join(ROOT, "build", ".mmd-png")
CONTENT_DIR = os.path.join(ROOT, "content")
TOPICS = os.path.join(CONTENT_DIR, "topics")
SUMMARIES = os.path.join(CONTENT_DIR, "summaries")
JIUWEN = os.path.join(CONTENT_DIR, "jiuwen")
DIAGRAMS_JSON = os.path.join(CONTENT_DIR, "diagrams.json")
SECTIONS_JSON = os.path.join(CONTENT_DIR, "sections.json")
CLASSIFICATION_JSON = os.path.join(CONTENT_DIR, "classification.json")

MH = re.compile(r"^##\s*(?:(\d+)\.\s*)?(.+)$")
DIAGRAM = re.compile(r"```mermaid\r?\n(.*?)```", re.S)
ANCHORS = re.compile(r"<details>\s*<summary>Anchors</summary>\s*\n\s*<sub>(.*?)</sub>\s*\n\s*</details>", re.S)
CODE = re.compile(r"<code>(.*?)</code>", re.S)
CANON = re.compile(r"_Canonical source:\s*`([^`]+)`(.*?)_</sub>", re.S)
NODE = re.compile(r'([A-Za-z0-9_]+)\s*(?:\[|\(|\{)\s*"?(.*?)"?\s*(?:\]|\)|\})')
EDGE = re.compile(r"([A-Za-z0-9_]+)\s*(?:-->|---|-\.->|==>|~~~|--x|--o)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)")
# node groups in mermaid SVG
GNODE = re.compile(r'<g[^>]*class="node[^"]*"[^>]*>')
GATTR = {}


def find_mmdc():
    env = os.environ.get("MMDC")
    if env and os.path.isfile(env):
        return [env]
    for name in ("mmdc.cmd", "mmdc"):
        p = os.path.join(HERE, "node_modules", ".bin", name)
        if os.path.isfile(p):
            return [p]
    return ["npx", "--yes", "@mermaid-js/mermaid-cli"]


PUPPETEER = os.path.join(SVG_CACHE, "puppeteer.json")
CONFIG = os.path.join(SVG_CACHE, "mermaid-config.json")
SVG_BUDGET = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--svg-budget=")), "10000"))
_svg_renders = 0


def _config():
    os.makedirs(SVG_CACHE, exist_ok=True)
    if not os.path.isfile(CONFIG):
        with open(CONFIG, "w", encoding="utf-8") as fh:
            json.dump({
                "theme": "default",
                "flowchart": {"htmlLabels": False, "useMaxWidth": False},
                "sequence": {"useMaxWidth": False},
                "class": {"htmlLabels": False},
                "state": {"htmlLabels": False},
                "er": {"htmlLabels": False},
            }, fh)
    return CONFIG


def _puppeteer():
    os.makedirs(SVG_CACHE, exist_ok=True)
    if not os.path.isfile(PUPPETEER):
        with open(PUPPETEER, "w", encoding="utf-8") as fh:
            json.dump({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}, fh)
    return PUPPETEER


def render_png(code, mmdc):
    """Render to PNG (2x) for reliable on-device display."""
    h = hashlib.sha1(code.encode("utf-8")).hexdigest()
    out = os.path.join(PNG_CACHE, h + ".png")
    if os.path.isfile(out):
        return out
    os.makedirs(PNG_CACHE, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "in.mmd")
        with open(inp, "w", encoding="utf-8") as fh:
            fh.write(code)
        cmd = mmdc + ["-i", inp, "-o", out, "-b", "white", "-s", "2", "-p", _puppeteer()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out


def fix_svg_size(path):
    """Give the SVG root an explicit width/height so AndroidSVG has an intrinsic size."""
    t = open(path, encoding="utf-8", errors="replace").read()
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', t)
    head = re.search(r"<svg[^>]*>", t)
    if not (vb and head):
        return
    w, h = vb.group(1), vb.group(2)
    tag = head.group(0)
    new = re.sub(r'\swidth="[^"]*"', "", tag)
    new = re.sub(r'\sheight="[^"]*"', "", new)
    new = new[:-1] + f' width="{w}" height="{h}">'
    t = t.replace(tag, new, 1)
    open(path, "w", encoding="utf-8").write(t)


def fix_svg_labels(path):
    """Replace Mermaid's <foreignObject> labels with real <text> so AndroidSVG renders them."""
    t = open(path, encoding="utf-8", errors="replace").read()
    if "foreignObject" not in t:
        return

    def repl(m):
        label = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return ('<text x="0" y="0" text-anchor="middle" dominant-baseline="central" '
                'font-family="sans-serif" font-size="14" fill="#333333">' + label + "</text>")

    t = re.sub(r"<foreignObject[^>]*>(.*?)</foreignObject>", repl, t, flags=re.S)
    open(path, "w", encoding="utf-8").write(t)


def render_svg(code, theme, mmdc):
    """AndroidSVG-compatible SVG (htmlLabels off), keyed by content+config."""
    global _svg_renders
    h = hashlib.sha1(("svg2\x00" + code).encode("utf-8")).hexdigest()
    out = os.path.join(SVG_CACHE, h + ".svg")
    if os.path.isfile(out):
        return out
    if _svg_renders >= SVG_BUDGET:
        return None
    os.makedirs(SVG_CACHE, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "in.mmd")
        with open(inp, "w", encoding="utf-8") as fh:
            fh.write(code)
        cmd = mmdc + ["-i", inp, "-o", out, "-b", "transparent", "-t", "default",
                      "-c", _config(), "-p", _puppeteer()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    fix_svg_size(out)
    fix_svg_labels(out)
    _svg_renders += 1
    return out


def node_labels(code):
    labels = {}
    for m in NODE.finditer(code):
        labels.setdefault(m.group(1), (m.group(2) or m.group(1)).strip())
    return labels


def svg_geometry(path, labels):
    """Return (width, height, nodes [{label,x,y}]) using source labels by node id."""
    text = open(path, encoding="utf-8", errors="replace").read()
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    w, h = (float(vb.group(1)), float(vb.group(2))) if vb else (800.0, 400.0)
    nodes = []
    for m in GNODE.finditer(text):
        tag = m.group(0)
        tm = re.search(r'transform="translate\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)"', tag)
        if not tm:
            continue
        x, y = float(tm.group(1)), float(tm.group(2))
        gid = re.search(r'id="flowchart-([A-Za-z0-9_]+)-\d+"', tag) or re.search(r'id="[^"]*?([A-Za-z0-9_]+)-\d+"', tag)
        nid = gid.group(1) if gid else ""
        label = labels.get(nid, "")
        if not label:
            window = text[m.end():m.end() + 1200]
            fm = re.search(r"<foreignObject[^>]*>(.*?)</foreignObject>", window, re.S)
            if fm:
                label = html.unescape(re.sub(r"<[^>]+>", "", fm.group(1))).strip()
            else:
                lm = re.search(r"<text[^>]*>(.*?)</text>", window, re.S)
                if lm:
                    label = html.unescape(re.sub(r"<[^>]+>", "", lm.group(1))).strip()
        nodes.append({"label": label or nid, "x": x, "y": y})
    return w, h, nodes


def mermaid_steps(code):
    labels = node_labels(code)
    order = []
    for m in EDGE.finditer(code):
        for nid in (m.group(1), m.group(2)):
            if nid in labels and nid not in order:
                order.append(nid)
    for nid in labels:
        if nid not in order:
            order.append(nid)
    return [labels[i] for i in order][:12]


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 15]


def strip_md_header(body, label):
    m = re.search(r"\*\*" + label + r":\*\*\s*(.*?)(?:\n\n|\Z)", body, re.S)
    return m.group(1).strip() if m else ""


def parse_anchors(body):
    m = ANCHORS.search(body)
    if not m:
        return []
    out = []
    for chunk in m.group(1).split("<br>"):
        codes = CODE.findall(chunk)
        if not codes:
            continue
        ref = html.unescape(codes[0]).strip()
        rest = chunk.split("</code>", 1)[1] if "</code>" in chunk else ""
        rest = re.sub(r"<[^>]+>", "", rest)
        rest = html.unescape(rest).replace("&bull;", "").strip(" —-:").strip()
        sm = re.search(r"([A-Za-z_][A-Za-z0-9_\.]{2,})", rest)
        lines = ""
        lm = re.search(r":(\d+(?:[/-]\d+)*)\s*$", ref)
        if lm:
            lines = lm.group(1)
        out.append({"kind": "code", "ref": ref, "symbol": sm.group(1) if sm else "",
                    "lines": lines, "desc": rest})
    return out


def infer_type(q, citations):
    ql = q.lower()
    if "tell me about a time" in ql or "a time when" in ql:
        return "behavioral"
    if "difference between" in ql or " vs " in ql or " versus " in ql or ql.startswith("compare"):
        return "compare"
    if "design a" in ql or "how would you design" in ql or "architect" in ql or "what's your strategy" in ql:
        return "design"
    if "under the hood" in ql or "how does the framework" in ql or "how does an agent" in ql or citations:
        return "mechanism"
    return "concept"


def mermaid_steps(code):
    labels = {}
    for m in NODE.finditer(code):
        labels.setdefault(m.group(1), (m.group(2) or m.group(1)).strip())
    order = []
    for m in EDGE.finditer(code):
        for nid in (m.group(1), m.group(2)):
            if nid in labels and nid not in order:
                order.append(nid)
    for m in NODE.finditer(code):
        if m.group(1) not in order:
            order.append(m.group(1))
    return [labels[i] for i in order][:12]


def parse_file(path):
    text = open(path, encoding="utf-8").read()
    title = ""
    for ln in text.split("\n"):
        if ln.startswith("# "):
            title = ln[2:].strip()
            break
    lines = text.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith("## ")), None)
    if idx is None:
        return title, []
    questions, cur, auto = [], None, 0
    for ln in lines[idx:]:
        if ln.startswith("### "):
            if cur is not None:
                cur["body"].append(ln)
            continue
        m = MH.match(ln)
        if m and ln.startswith("## "):
            if cur:
                questions.append(cur)
                cur = None
            qtext = m.group(2).strip()
            if re.match(r"^(summary|why this matters)", qtext, re.I):
                continue
            num = m.group(1)
            auto += 1
            cur = {"number": int(num) if num else auto, "question": qtext, "body": []}
        elif ln.startswith("# "):
            if cur:
                questions.append(cur)
                cur = None
        elif cur is not None:
            cur["body"].append(ln)
    if cur:
        questions.append(cur)
    return title, questions


EMPTY_DIAGRAM = {"source": "", "svg": "", "image": "", "svgDark": "", "width": 0.0, "height": 0.0,
                 "alt": "", "steps": [], "nodes": []}


def build_diagram(code, mmdc, question):
    if not code:
        return None
    light = render_svg(code, "default", mmdc)
    if light is None:
        return None
    png = render_png(code, mmdc)
    h = hashlib.sha1(("svg2\x00" + code).encode("utf-8")).hexdigest()
    shutil.copyfile(light, os.path.join(OUT, "diagrams", h + ".svg"))
    shutil.copyfile(png, os.path.join(OUT, "diagrams", h + ".png"))
    w, ht, nodes = svg_geometry(light, node_labels(code))
    return {
        "source": code, "svg": "diagrams/" + h + ".svg", "image": "diagrams/" + h + ".png",
        "svgDark": "", "width": w, "height": ht, "alt": f"Diagram for: {question}",
        "steps": mermaid_steps(code), "nodes": nodes,
    }


def load_merge(directory):
    out = {}
    for p in sorted(glob.glob(os.path.join(directory, "*.json"))):
        out.update(json.load(open(p, encoding="utf-8")))
    return out


def load_sections():
    """Return (topic order map, topic -> section title) from content/sections.json."""
    data = json.load(open(SECTIONS_JSON, encoding="utf-8"))
    order, section_of = {}, {}
    for si, sec in enumerate(data["sections"]):
        for ti, tid in enumerate(sec["topics"]):
            order[tid] = (si, ti)
            section_of[tid] = sec["title"]
    return order, section_of


def main():
    if "--fix-cache" in sys.argv:
        n = 0
        for p in glob.glob(os.path.join(SVG_CACHE, "*.svg")):
            fix_svg_size(p); fix_svg_labels(p); n += 1
        print("fixed", n, "cached SVGs")
        return
    mmdc = find_mmdc()
    authored = load_merge(SUMMARIES)
    authored_j = load_merge(JIUWEN)
    authored_d = json.load(open(DIAGRAMS_JSON, encoding="utf-8"))
    order, section_of = load_sections()
    classification = {}
    if os.path.isfile(CLASSIFICATION_JSON):
        classification = json.load(open(CLASSIFICATION_JSON, encoding="utf-8"))
    files = sorted(f for f in glob.glob(os.path.join(TOPICS, "*.md"))
                   if re.match(r"^(0[0-9]|1[0-8])-", os.path.basename(f)))
    os.makedirs(os.path.join(OUT, "diagrams"), exist_ok=True)
    today = date.today().isoformat()
    topics, missing, total, rendered, pending = [], 0, 0, 0, 0
    for f in files:
        prefix = os.path.basename(f)[:2]
        title, questions = parse_file(f)
        t = {"id": prefix, "title": title, "section": section_of.get(prefix, ""),
             "questions": []}
        n = len(questions)
        for qi, q in enumerate(questions, 1):
            total += 1
            body = "\n".join(q["body"])
            explain = (strip_md_header(body, "General") or strip_md_header(body, "Definition")
                       or strip_md_header(body, "Pattern"))
            mechanism = strip_md_header(body, "Jiuwen")
            gap = (strip_md_header(body, "Gap") or strip_md_header(body, "Where it bites")
                   or strip_md_header(body, "Used for"))
            citations = parse_anchors(body)
            qtype = infer_type(q["question"], citations)
            sents = sentences(explain)
            key = f"{prefix}-{qi}"
            ov = authored.get(key, {})
            qt = ov.get("title", "")
            tldr = ov.get("tldr", "")
            points = ov.get("points", [])
            jiuwen_plain = authored_j.get(key, "")
            sources = []
            cm = CANON.search(body)
            if cm:
                sources.append(cm.group(1).strip())

            fences = [c.replace("\r", "").strip() for c in DIAGRAM.findall(body)]
            authd = authored_d.get(key, {})
            concept = authd.get("concept")
            if isinstance(concept, list):
                concept_srcs = concept
            elif concept:
                concept_srcs = [concept]
            else:
                concept_srcs = fences
            tech_src = (fences[0] if fences else "") if authd.get("technical") == "__existing__" \
                else authd.get("technical", "")
            diagrams = []
            diagram_tech = EMPTY_DIAGRAM
            try:
                for src in concept_srcs:
                    d = build_diagram(src, mmdc, q["question"])
                    if d is None:
                        pending += 1
                    else:
                        diagrams.append(d)
                        rendered += 1
                if tech_src:
                    d = build_diagram(tech_src, mmdc, q["question"])
                    if d is None:
                        pending += 1
                    else:
                        diagram_tech = d
                        rendered += 1
            except Exception as e:
                missing += 1
                print("diagram render failed:", str(e)[:120])
            diagram = diagrams[0] if diagrams else EMPTY_DIAGRAM

            t["questions"].append({
                "id": f"{prefix}-{qi}", "topicId": prefix, "topicTitle": title, "number": qi,
                "type": qtype, "question": q["question"], "title": qt, "tldr": tldr, "points": points,
                "explain": explain, "mechanism": mechanism, "jiuwenPlain": jiuwen_plain,
                "citations": citations,
                "pitfalls": sentences(gap), "followups": [],
                "diagram": diagram,
                "diagrams": diagrams,
                "diagramTechnical": diagram_tech,
                "meta": {"difficulty": classification.get(
                             key, "advanced" if qtype in ("design", "compare", "mechanism") else "core"),
                         "tags": [prefix],
                         "related": [f"{prefix}-{j}" for j in (qi - 1, qi + 1) if 1 <= j <= n]},
                "provenance": {"sources": sources, "reviewedAt": today},
            })
        topics.append(t)

    uncovered = [t["id"] for t in topics if t["id"] not in order]
    if uncovered:
        print("WARNING: topics missing from content/sections.json:", ", ".join(uncovered))
    topics.sort(key=lambda t: order.get(t["id"], (10 ** 6, 0)))

    data = {"version": 3, "topics": topics}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "content.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"topics={len(topics)} questions={total} diagrams={rendered} failed={missing} pending={pending}")


if __name__ == "__main__":
    main()
