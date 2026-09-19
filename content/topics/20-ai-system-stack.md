# AI system stack

## 1. The 7-layer AI application stack

**Definition:** A structured decomposition of a production AI application into seven layers, from the data pipeline up to infrastructure and observability.

**Jiuwen:** Layer 4: `agent-core/openjiuwen/core/retrieval/` (vector, hybrid, graph, agentic). Layer 5: `harness/prompts/template.py`, `core/context_engine/`, `core/foundation/tool/base.py`, `core/agentic/react_agent.py`. Layer 6: `harness/rails/security_rail.py`, `guardrail_rail.py`, `subagent/verification_rail.py`. Layer 7: Milvus (vector store), vLLM (inference), `harness/observability/event.py`. Layers 1-3 are external.

---

## 2. KV cache and prompt caching

**Definition:** The key-value cache in the transformer attention mechanism stores the K and V tensors for every processed token. On a subsequent request with the same prefix, the provider reuses the cached tensors, skipping recomputation and reducing input cost (typically ~10% of normal input token price for cache hits). The implication for application design: stable prompt prefixes (system prompt, few-shot examples) should go first; variable content at the end.

**Jiuwen:** `ProviderUsage` (`core/context_engine/usage/provider_usage.py:14`) normalizes `cached_input_tokens` from provider usage metadata. `session_aggregator.py:45` tracks cache hit rates. `full_compact_processor.py:184` compacts at 180 k tokens — this indirectly stabilizes prefixes. The framework observes hits; it does not control caching.

---

## 3. Base model versus instruct model

**Definition:** A base model is the raw pretrained checkpoint — next-token prediction on web-scale data, no instruction following. An instruct (or chat) model is the same weights after the alignment pipeline: supervised fine-tuning (SFT) on demonstration data, reward model training, and RLHF or DPO to match human preferences. The practical difference: a base model will continue text; an instruct model will follow instructions, decline harmful requests, and produce structured responses.

**Jiuwen:** `agent_rl/online/backends/sft/trainer.py` is the SFT stage that produces instruct-model-like behavior from demonstration data. `GuardrailRail` (`harness/rails/guardrail_rail.py`) provides inference-time safety supplement. The framework does not tag served models as base vs instruct in the config schema — `ProviderType + model_name` selects a model.

---

## 4. LLM API call lifecycle

**Definition:** What happens between calling `client.chat()` and receiving the first token, step by step, and which of those steps the provider owns versus the caller.

**Jiuwen:** Model clients (`core/foundation/llm/model_clients/openai_model_client.py:865`) send requests and receive streamed responses. `ProviderUsage` (`provider_usage.py:14`) captures input, output, and cached tokens from response metadata. `ObservabilityHandler` (`harness/observability/event.py:1`) logs model call events. `usage_cost.py:101` is the session billing meter. Steps 1-3 (API gateway, load balancer, tokenization) are the provider's infrastructure.

---
