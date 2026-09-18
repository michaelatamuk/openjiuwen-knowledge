#!/usr/bin/env python
"""Bundle the generated markdown into an Obsidian vault zip.

The zip wraps the markdown output in a top-level `openjiuwen-knowledge/` folder
so the whole thing opens directly as an Obsidian vault.

Output: build/dist/jiuwen-knowledge-vault.zip
"""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
SRC = os.path.join(ROOT, "knowledge")
DIST = os.path.join(ROOT, "build", "dist")
OUT = os.path.join(DIST, "jiuwen-knowledge-vault.zip")
VAULT = "openjiuwen-knowledge"


def main():
    if not os.path.isdir(SRC):
        raise SystemExit("knowledge/ not found. Run build_markdown.py first.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.isfile(OUT):
        os.remove(OUT)
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(SRC):
            for name in files:
                p = os.path.join(root, name)
                rel = os.path.relpath(p, SRC).replace(os.sep, "/")
                z.write(p, f"{VAULT}/{rel}")
                n += 1
    print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB, {n} entries)")


if __name__ == "__main__":
    main()
