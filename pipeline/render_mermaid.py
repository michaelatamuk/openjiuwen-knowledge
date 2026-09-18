#!/usr/bin/env python
"""Render ```mermaid fences to inline SVG so the browser needs no Mermaid JS.

Used by build_study.py and build_singlefile.py. Results are cached by content
hash in .mmd-cache/, so re-builds are fast.

Needs @mermaid-js/mermaid-cli (`mmdc`). Resolution order:
    $MMDC  ->  pipeline/node_modules/.bin/mmdc[.cmd]  ->  npx @mermaid-js/mermaid-cli
If mmdc cannot be found/run, the original fence is left untouched (the site
then falls back to the bundled runtime Mermaid).
"""
import os
import re
import sys
import json
import hashlib
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
CACHE = os.path.join(os.path.dirname(HERE), "build", ".mmd-cache")
PUPPETEER = os.path.join(CACHE, "puppeteer.json")
BLOCK = re.compile(r"```mermaid\r?\n(.*?)```", re.S)


def find_mmdc():
    env = os.environ.get("MMDC")
    if env and os.path.isfile(env):
        return [env]
    for name in ("mmdc.cmd", "mmdc"):
        p = os.path.join(HERE, "node_modules", ".bin", name)
        if os.path.isfile(p):
            return [p]
    return ["npx", "--yes", "@mermaid-js/mermaid-cli"]


def _puppeteer_config():
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.isfile(PUPPETEER):
        with open(PUPPETEER, "w", encoding="utf-8") as fh:
            json.dump({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}, fh)
    return PUPPETEER


def render_svg(code, mmdc):
    h = hashlib.sha1(code.encode("utf-8")).hexdigest()
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, h + ".svg")
    if os.path.isfile(cached):
        with open(cached, encoding="utf-8") as fh:
            return fh.read()
    with tempfile.TemporaryDirectory() as d:
        inp, out = os.path.join(d, "in.mmd"), os.path.join(d, "out.svg")
        with open(inp, "w", encoding="utf-8") as fh:
            fh.write(code)
        cmd = mmdc + ["-i", inp, "-o", out, "-b", "transparent", "-p", _puppeteer_config()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        with open(out, encoding="utf-8") as fh:
            svg = fh.read()
    # unique ids per diagram so multiple inlined SVGs don't collide
    svg = svg.replace("my-svg", "mmd-" + h[:8])
    with open(cached, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg


def transform(md_text, mmdc=None):
    mmdc = mmdc or find_mmdc()

    def repl(m):
        code = m.group(1).replace("\r", "").strip()
        try:
            return "\n<div class=\"mermaid-svg\">\n" + render_svg(code, mmdc) + "\n</div>\n"
        except Exception as e:
            sys.stderr.write("mmdc failed, leaving fence: " + str(e)[:200] + "\n")
            return m.group(0)

    return BLOCK.sub(repl, md_text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python render_mermaid.py <file.md>  (prints transformed markdown)")
        sys.exit(2)
    txt = open(sys.argv[1], encoding="utf-8").read()
    sys.stdout.write(transform(txt))
