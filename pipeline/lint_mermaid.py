#!/usr/bin/env python
"""Lint Mermaid diagrams in the interview docs without Node.

Catches the common breakages:
  - unclosed ```mermaid fences
  - sequence-diagram participants using reserved keywords (loop, alt, end, ...)
  - flowchart node ids using reserved keywords (end, graph, subgraph, ...)
  - unbalanced subgraph/end in flowcharts

Usage: python lint_mermaid.py            # exit 1 if problems found
"""
import os
import re
import glob
import sys

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
BASE = os.path.join(os.path.dirname(HERE), "content", "topics")

SEQ_RESERVED = {
    "participant", "actor", "activate", "deactivate", "note", "loop", "alt",
    "else", "opt", "par", "and", "rect", "critical", "option", "break",
    "end", "autonumber", "box", "link", "links", "properties", "details", "title",
}
FLOW_RESERVED = {"end"}

blocks_re = re.compile(r"```mermaid\r?\n(.*?)```", re.S)


def lint_file(path):
    text = open(path, encoding="utf-8").read()
    problems = []
    # fence balance (only count fences that start a line, ignoring inline code spans)
    fences = len(re.findall(r"(?m)^\s*```", text))
    if fences % 2:
        problems.append("odd number of ``` fences")
    for i, block in enumerate(blocks_re.finditer(text), 1):
        code = block.group(1).replace("\r", "")
        first = code.strip().split("\n", 1)[0].strip().lower()
        if first.startswith("sequencediagram"):
            for m in re.finditer(r"^\s*(?:participant|actor)\s+(\S+?)(?:\s+as\s+.*)?$", code, re.M):
                pid = m.group(1).strip().strip('"')
                if pid.lower() in SEQ_RESERVED:
                    problems.append(f"block#{i}: participant id '{pid}' is a reserved keyword")
        if first.startswith("flowchart") or first.startswith("graph"):
            for m in re.finditer(r"(?:^|\s)([A-Za-z0-9_]+)\s*[\[\(\{]", code):
                nid = m.group(1)
                if nid.lower() in FLOW_RESERVED:
                    problems.append(f"block#{i}: node id '{nid}' is a reserved keyword")
            opens = len(re.findall(r"^\s*subgraph\b", code, re.M))
            ends = len(re.findall(r"^\s*end\s*$", code, re.M))
            if opens != ends:
                problems.append(f"block#{i}: subgraph/end mismatch ({opens} vs {ends})")
    return problems


def main():
    files = sorted(glob.glob(os.path.join(BASE, "[01][0-9]-*.md"))) + \
            sorted(glob.glob(os.path.join(BASE, "[9][0-9]-*.md")))
    bad = 0
    for f in files:
        for p in lint_file(f):
            bad += 1
            print(f"{os.path.basename(f)}: {p}")
    print(f"\nlinted {len(files)} files | problems: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
