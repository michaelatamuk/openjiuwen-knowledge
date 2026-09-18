#!/usr/bin/env python
"""Reorder the interview docs: topics (files) and questions within each topic.

Run from this directory:  python reorder.py

The order is data-driven so it is reproducible and reviewable. It:
  1. reorders the numbered questions in each 01-10 file per QUESTION_ORDER,
     dropping leftover section headers / horizontal rules and renumbering;
  2. renames topic and reference files per RENAME (new number = study order).
"""
import os
import re
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
BASE = os.path.join(os.path.dirname(HERE), "content", "topics")

# old filename -> new filename (prefix = study order)
RENAME = {
    "01-llm-foundations.md": "01-llm-foundations.md",
    "02-prompting-and-output-control.md": "02-prompting-and-output-control.md",
    "04-rag-and-retrieval.md": "03-rag-and-retrieval.md",
    "05-rag-system-design.md": "04-rag-system-design.md",
    "06-agents-tools-and-memory.md": "05-agents-tools-and-memory.md",
    "07-evaluation.md": "06-evaluation.md",
    "08-production-cost-and-scale.md": "07-production-cost-and-scale.md",
    "09-security-and-safety.md": "08-security-and-safety.md",
    "03-fine-tuning-and-customization.md": "09-fine-tuning-and-customization.md",
    "10-general-engineering.md": "10-general-engineering.md",
    # reference block: glossary first, architecture patterns last
    "93-llm-terms-glossary.md": "90-llm-terms-glossary.md",
    "90-ai-engineer-interview-patterns.md": "91-ai-engineer-interview-patterns.md",
    "91-llm-interview-patterns.md": "92-llm-interview-patterns.md",
    "92-llm-architecture-patterns.md": "93-llm-architecture-patterns.md",
}

# new filename -> ordered list of case-insensitive title substrings
QUESTION_ORDER = {
    "01-llm-foundations.md": [
        "token and a word", "tokens and embeddings", "self-attention", "positional encoding",
        "encoder-only", "context window and its training data cutoff", "conversation exceeds",
        "degrade with very long context", "temperature", "top-k sampling", "greedy decoding",
        "counting or basic arithmetic", "hallucination, and why", 'being "wrong"',
    ],
    "02-prompting-and-output-control.md": [
        "system prompt and a user prompt", "zero-shot vs. few-shot", "parseable output like json",
        "validate a tool call's structured output", "version prompts the same way",
    ],
    "03-rag-and-retrieval.md": [
        "walking through a rag pipeline end to end", "the pipeline: query embedding",
        "how do you measure whether your retrieval step", "what is modular rag",
        "deciding chunk size", "what happens if your chunks are too small",
        "fixed-size vs. semantic chunking", "overlapping vs. non-overlapping chunks",
        "chunking structured content", "context relevant but answer vague",
        "picking an embedding model", "should queries and documents use the same embedding model",
        "why swapping embedding models", "multilingual documents",
        "dense vs. sparse retrieval", "when keyword search outperforms semantic search",
        "why a purely semantic system can fail", "retrieving 5 documents versus 20",
        "retrieval to work across structured data",
        "what reranking adds that initial retrieval", "reranker is actually improving results",
        "would you rerank every query", "how much latency reranking adds",
        "bi-encoder for retrieval vs. cross-encoder",
        "query rewriting or query expansion", "vague or ambiguous user query",
        "decompose a complex, multi-part question", "what is multi-hop retrieval",
        "requiring information from multiple documents", "when to skip rag",
        "retrieval looks correct, answer is wrong",
        "hallucinations when retrieved context doesn't actually answer",
        "documents contain conflicting or outdated", "no relevant documents exist",
        "same question, different answers on different days", "vocabulary mismatch",
        "structuring error handling for a pipeline", "cutting tokens without losing quality",
        "building a retrieval eval set", "multiple document types and formats",
        "pasting retrieved text into a long-context prompt",
    ],
    "04-rag-system-design.md": [
        "customer support chatbot handling 100,000", "codebase assistant", "legal firm with millions",
        "10,000 to 10 million", "shard or partition", "keeping retrieval fast as the vector database grows",
        "what database would you choose", "hosted vector database and a self-managed",
        "vector database is down", "document updated or deleted after",
        "never get an answer based on stale", "retrieval returns zero relevant documents",
        "sub-500ms responses",
    ],
    "05-agents-tools-and-memory.md": [
        "difference between a chatbot and an agent", "difference between a workflow and an agent",
        "difference between a linear chain and a graph", "what's the react pattern",
        "how does function calling actually work",
        "hard limit on iterations", "what decides when an agent stops", "how many retrieval hops are enough",
        "getting stuck in an infinite tool-calling", "agent decide when to retrieve again",
        "register and expose tools", "framework doesn't natively support",
        "tool call that fails or returns malformed", "retry logic that doesn't cause duplicate",
        "custom retry policy", "handling concurrent api calls", "framework handle a step that times out",
        "break a complex task into smaller subtasks", "plan needs to change mid-execution",
        "single-step agent and a multi-step planning", "planner-executor pattern",
        "track state across multiple steps", "pause an agent mid-execution and resume",
        "human-in-the-loop approval",
        "short-term and long-term memory", "what to store in memory versus what to discard",
        "memory from growing unbounded", "summarize conversation history",
        "agent framework actually give you", "graph-based framework like langgraph and a role-based",
        "decide between langgraph, crewai, and the anthropic", "heavier framework versus writing a lighter",
        "framework add unnecessary abstraction", "framework's abstractions don't match",
        "framework decide which node or agent runs next", "version and roll back an agent's workflow",
        "supervisor pattern and a peer-to-peer", "communication between multiple agents",
        "one agent's output becoming another agent's input", "multiple agents from producing conflicting",
        "unclear which agent in the chain", "multi-agent system overkill",
        "what is agentic rag", "agentic rag system from retrieving in an unnecessary loop",
        "controlling cost when an agent can call tools repeatedly",
    ],
    "06-evaluation.md": [
        "evaluate an llm's output beyond", "retrieval and generation as two separate stages",
        "exact-match scoring fails",
        "recall@k, and what a low score", "precision@k = relevant docs", "mrr, and when it matters",
        "ndcg: weights relevant results",
        "faithfulness vs. relevance in rag evaluation", "computing faithfulness",
        "measuring hallucination rate", "what is perplexity",
        "known limitations of using an llm as a judge",
        "no ground truth answer", "build an eval dataset from scratch", "statistically meaningful",
        "compare two models for a specific task",
        "building a regression test suite", "evaluating continuously in production",
        "retrieval quality has degraded over time", "high eval scores but users still complaining",
        "tying an eval metric back to a business outcome",
    ],
    "07-production-cost-and-scale.md": [
        "where cost concentrates", "reduce cost for a high-volume rag",
        "control cost in a system where usage scales unpredictably", "first cut at 50% cost reduction",
        "designing caching", "reducing latency in a multi-step", "multithreading vs. multiprocessing",
        "architecture at 10x",
    ],
    "08-security-and-safety.md": [
        "what prompt injection is", "untrusted content from a tool result", "jailbreak",
        "only retrieves documents they're actually authorized", "destructive or irreversible action",
        "harmful or biased content", "sensitive data from leaking", "multi-tenant rag system",
    ],
    "09-fine-tuning-and-customization.md": [
        "pretraining and fine-tuning", "instruction tuning", "full fine-tuning and parameter-efficient",
        "fine-tune instead of using a longer", "rag and fine-tuning", "risk of fine-tuning on a small",
    ],
    "10-general-engineering.md": [
        "deciding when a problem actually needs an llm", "larger model vs. smaller",
        "framework will scale with your team", "rollback plan if a prompt or model update",
        "stakeholder wants to ship before your eval scores",
    ],
}

HEAD = re.compile(r"^## (\d+)\.\s*(.+)$")


def parse(text):
    lines = text.split("\n")
    idx = next(i for i, l in enumerate(lines) if HEAD.match(l))
    preamble = lines[:idx]
    blocks, cur = [], None
    for ln in lines[idx:]:
        if HEAD.match(ln):
            if cur:
                blocks.append(cur)
            cur = {"head": ln, "title": HEAD.match(ln).group(2).strip(), "lines": []}
        elif cur is not None:
            cur["lines"].append(ln)
    if cur:
        blocks.append(cur)
    for b in blocks:
        b["lines"] = [l for l in b["lines"] if not l.startswith("# ") and l.strip() != "---"]
        while b["lines"] and not b["lines"][-1].strip():
            b["lines"].pop()
    return preamble, blocks


def apply_order(blocks, order):
    def key(i_b):
        i, b = i_b
        t = b["title"].lower()
        for k, sub in enumerate(order):
            if sub in t:
                return (k, i)
        return (10 ** 6, i)
    return [b for _, b in sorted(enumerate(blocks), key=key)]


def main():
    total = 0
    for old, new in RENAME.items():
        path = os.path.join(BASE, old)
        if not os.path.isfile(path):
            print("missing:", old)
            continue
        if new in QUESTION_ORDER:
            text = open(path, encoding="utf-8").read()
            preamble, blocks = parse(text)
            orig_titles = sorted(b["title"] for b in blocks)
            ordered = apply_order(blocks, QUESTION_ORDER[new])
            new_titles = sorted(b["title"] for b in ordered)
            if orig_titles != new_titles:
                print("!! TITLE MISMATCH", new)
            body = []
            for i, b in enumerate(ordered, 1):
                body.append(f"## {i}. {b['title']}")
                body.extend(b["lines"])
                body.append("")
            out = "\n".join(preamble).rstrip() + "\n" + "\n".join(body).rstrip() + "\n"
            open(path, "w", encoding="utf-8", newline="\n").write(out)
            total += len(ordered)
        # rename (direct; no target collisions)
        if old != new:
            os.replace(path, os.path.join(BASE, new))
    print(f"reordered {total} questions; renamed {sum(1 for a,b in RENAME.items() if a!=b)} files")


if __name__ == "__main__":
    main()
