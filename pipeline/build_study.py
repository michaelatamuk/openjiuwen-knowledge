#!/usr/bin/env python
"""Prepare and build the offline study site for the interview question bank.

Usage:
    python build_study.py            # prepare docs/ and build site/
    python build_study.py --no-build # only prepare docs/

The site is built with mkdocs-material. Install the toolchain once into an
isolated venv, e.g.:
    uv venv .venv
    uv pip install --python .venv/Scripts/python.exe mkdocs-material
Then run this script with that venv's python, or set MKDOCS_PYTHON to it.
"""
import os
import re
import sys
import glob
import shutil
import zipfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # .../interview_questions
BUILD = os.path.join(ROOT, "build")
DOCS = os.path.join(BUILD, "docs")
SITE = os.path.join(BUILD, "site")
DIST = os.path.join(BUILD, "dist")
ASSETS = os.path.join(HERE, "assets")
CONFIG = os.path.join(HERE, "mkdocs.yml")
MD_DIR = os.path.join(ROOT, "knowledge")


def prep():
    # Generate layered markdown from content.json (single source of truth).
    subprocess.run([sys.executable, os.path.join(HERE, "build_markdown.py")], check=True)
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(MD_DIR, DOCS)
    # study-mode assets
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    for a in glob.glob(os.path.join(ASSETS, "study.*")):
        shutil.copyfile(a, os.path.join(DOCS, "assets", os.path.basename(a)))
    print("prepared docs from", MD_DIR)


def find_python():
    env = os.environ.get("MKDOCS_PYTHON")
    if env and os.path.isfile(env):
        return env
    candidate = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    if os.path.isfile(candidate):
        return candidate
    return sys.executable


def build():
    py = find_python()
    try:
        subprocess.run([py, "-c", "import mkdocs"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("mkdocs is not installed for", py)
        print("Install it:  uv venv .venv && uv pip install --python .venv/Scripts/python.exe mkdocs-material")
        print("then re-run, or set MKDOCS_PYTHON to that interpreter.")
        return 1
    # Fail fast on broken Mermaid before building.
    lint = subprocess.run([sys.executable, os.path.join(HERE, "lint_mermaid.py")])
    if lint.returncode != 0:
        print("Mermaid lint reported problems; fix them before publishing.")
    subprocess.run([py, "-m", "mkdocs", "build", "-f", CONFIG, "--clean"], check=True)
    site = SITE
    offline_fix(site)
    zip_site()
    print("built site ->", site)
    print("open:", os.path.join(site, "index.html"))
    return 0


def zip_site():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "jiuwenswarm-site.zip")
    if os.path.isfile(out):
        os.remove(out)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(SITE):
            for name in files:
                p = os.path.join(root, name)
                z.write(p, os.path.relpath(p, SITE).replace(os.sep, "/"))
                n += 1
    print(f"zipped site -> {out} ({os.path.getsize(out)//1024} KB, {n} files)")


def offline_fix(site):
    """Rewrite the one CDN script Material injects so the site is fully offline."""
    for root, _dirs, files in os.walk(site):
        for name in files:
            if not name.endswith(".html"):
                continue
            p = os.path.join(root, name)
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
            fixed = text.replace(
                "https://unpkg.com/iframe-worker/shim",
                "assets/iframe-worker-shim.js",
            )
            if fixed != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(fixed)


if __name__ == "__main__":
    prep()
    if "--no-build" not in sys.argv:
        sys.exit(build())
