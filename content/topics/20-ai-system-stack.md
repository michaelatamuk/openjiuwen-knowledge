# Serving and infrastructure

## 1. The 7-layer AI application stack

**Definition:** A structured decomposition of a production AI application into seven layers, from the data pipeline up to infrastructure and observability.

**Jiuwen:** Layer 4: `core/retrieval/retriever/` (vector, hybrid, graph, agentic). Layer 5: `core/foundation/prompt/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/single_agent/agents/react_agent.py`. Layer 6: `harness/rails/security/` (prompt/tool security), `core/security/guardrail/builtin.py`, `harness/rails/subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/` and `extensions/observability/`. Layers 1-3 are external.

---
