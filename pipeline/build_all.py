#!/usr/bin/env python
"""Rebuild every generated artifact in one shot.

Runs, in order:
    build_content_json.py   content.json + diagram assets for the app
    build_study.py          build/markdown -> build/docs -> build/site (+ site zip)
    build_singlefile.py     build/dist/jiuwenswarm-interview-offline.html
    anki_export.py          build/dist/*.apkg + *.csv
    build_epub.py           build/dist/*.epub
    build_vault.py          build/interview_questions-vault.zip

Options:
    --android       also run `gradlew assembleDebug` for the Android app
    --no-content    skip content.json regeneration (reuse the existing one)
    --svg-budget=N  max new Mermaid SVG renders passed to build_content_json
                    (0 = cache only; default 10000)

Interpreter: the doc-format steps need `markdown`, `genanki`, and `ebooklib`.
Point MKDOCS_PYTHON (or create a `.venv` next to this folder) at an
interpreter that has them; otherwise this process's interpreter is used.

    python build_all.py
    python build_all.py --android
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
ROOT = os.path.dirname(HERE)                         # .../interview_questions
BUILD = os.path.join(ROOT, "build")
APP = os.path.join(ROOT, "apps", "android")


def docs_python():
    env = os.environ.get("MKDOCS_PYTHON")
    if env and os.path.isfile(env):
        return env
    for c in (os.path.join(ROOT, ".venv", "Scripts", "python.exe"),
              os.path.join(ROOT, ".venv", "bin", "python")):
        if os.path.isfile(c):
            return c
    return sys.executable


def run(script, py, extra=None):
    cmd = [py, os.path.join(HERE, script)] + (extra or [])
    print("\n>> " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    args = sys.argv[1:]
    android = "--android" in args
    skip_content = "--no-content" in args
    budget = next((a for a in args if a.startswith("--svg-budget=")), None)

    py = docs_python()
    print("docs interpreter:", py)

    if not skip_content:
        run("build_content_json.py", py, [budget] if budget else [])
    run("build_study.py", py)
    run("build_singlefile.py", py)
    run("anki_export.py", py)
    run("build_epub.py", py)
    run("build_vault.py", py)

    if android:
        gradlew = os.path.join(APP, "gradlew.bat" if os.name == "nt" else "gradlew")
        print("\n>> " + gradlew + " assembleDebug")
        subprocess.run([gradlew, "assembleDebug"], cwd=APP, check=True)

    print("\ndone. outputs in", BUILD)


if __name__ == "__main__":
    main()
