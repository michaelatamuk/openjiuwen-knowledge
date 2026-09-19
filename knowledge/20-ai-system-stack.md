# Serving and infrastructure

## 1. The 7-layer AI application stack

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** A production AI application decomposes into seven layers, from the data pipeline to infrastructure and observability.

**Key points.**

- Data pipeline — ingestion, labeling, preprocessing, chunking
- Base model / training — pretrained foundation model or fine-tuned weights
- Inference engine — serving hardware, batching, KV cache, quantization
- RAG / retrieval — vector stores, rerankers, hybrid search
- Orchestration — agent loops, memory, tool use, context management
- Safety / guardrails — moderation, schema enforcement, circuit breakers
- Infrastructure / observability — load balancing, tracing, cost meters, deployment
- Identify which layers your code owns versus which are delegated to a provider or vendor
- Treat the model as one layer, not the entire stack

**Concept.** A structured decomposition of a production AI application into seven layers, from the data pipeline up to infrastructure and observability.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Layer 4: `core/retrieval/retriever/` (vector, hybrid, graph, agentic). Layer 5: `core/foundation/prompt/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/single_agent/agents/react_agent.py`. Layer 6: `harness/rails/security/` (prompt/tool security), `core/security/guardrail/builtin.py`, `harness/rails/subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/` and `extensions/observability/`. Layers 1-3 are external.

</details>

---
