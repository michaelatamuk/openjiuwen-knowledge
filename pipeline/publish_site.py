#!/usr/bin/env python
"""Publish the built site (build/site) to the gh-pages branch (GitHub Pages).

Run build_study.py (or build_all.py) first, then:

    python publish_site.py

Pushes the static site to the `gh-pages` branch of the `origin` remote with
force (the branch is a build artifact). A `.nojekyll` file is added so GitHub
serves the MkDocs asset folders verbatim.
"""
import os
import re
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # repo root
SITE = os.path.join(ROOT, "build", "site")


def git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True)


def pages_url(remote):
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote.strip())
    if not m:
        return ""
    owner, repo = m.group(1), m.group(2)
    if repo.lower() == owner.lower() + ".github.io":
        return f"https://{owner}.github.io/"
    return f"https://{owner}.github.io/{repo}/"


def main():
    if not os.path.isdir(SITE):
        raise SystemExit("build/site not found. Run build_study.py (or build_all.py) first.")
    remote = subprocess.run(["git", "remote", "get-url", "origin"],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()

    with tempfile.TemporaryDirectory() as d:
        for name in os.listdir(SITE):
            src = os.path.join(SITE, name)
            dst = os.path.join(d, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        open(os.path.join(d, ".nojekyll"), "w").close()
        git(["init", "-b", "gh-pages"], d)
        git(["add", "-A"], d)
        git(["-c", "core.autocrlf=false", "commit", "-q",
             "-m", "Publish offline site to GitHub Pages"], d)
        git(["remote", "add", "origin", remote], d)
        git(["push", "-f", "origin", "gh-pages"], d)

    url = pages_url(remote)
    print("published gh-pages")
    if url:
        print("Pages:", url)


if __name__ == "__main__":
    main()
